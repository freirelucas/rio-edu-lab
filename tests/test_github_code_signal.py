"""Tests pro adapter `analysis/_github.py` + script `analysis/45b_code_signal.py`.

Mocks de rede via monkey-patching de urlopen. Validamos:
- cache hit/miss (TTL + filesystem)
- 403 sem token vira `auth_required` (não cacheado)
- estrutura do payload (n_hits, repos colapsado pra unique)
- empty DOI graceful
- priority_pool() ordena: full > partial > BR; dentro por citação desc
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import time
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_gh():
    spec = importlib.util.spec_from_file_location("gh_adapter", str(ANALYSIS / "_github.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _import_45b():
    spec = importlib.util.spec_from_file_location("code_signal", str(ANALYSIS / "45b_code_signal.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── _safe_filename + _cache_path ─────────────────────────────────────────


def test_safe_filename_sanitizes_doi_separators():
    gh = _import_gh()
    assert gh._safe_filename("10.1234/abc") == "10.1234_abc"
    assert gh._safe_filename("10.5281/zenodo.123") == "10.5281_zenodo.123"
    assert gh._safe_filename("not/a:real\\doi") == "not_a_real_doi"


def test_cache_path_under_cache_dir(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    p = gh._cache_path("10.1234/x")
    assert str(p).endswith("10.1234_x.json")
    assert str(p).startswith(str(tmp_path / "github"))


# ─── cache get/set ────────────────────────────────────────────────────────


def test_cache_roundtrip(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    payload = {"n_hits": 7, "repos": [{"full_name": "a/b"}], "doi": "10.x/y", "queried_at": 0}
    gh._cache_set("10.x/y", payload)
    got = gh._cache_get("10.x/y")
    assert got == payload


def test_cache_miss_returns_none(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    assert gh._cache_get("10.x/y") is None


def test_cache_expired_returns_none(tmp_path, monkeypatch):
    gh = _import_gh()
    import os
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    gh._cache_set("10.x/y", {"n_hits": 0})
    # Backdate mtime to 100d ago (TTL is 30d)
    p = gh._cache_path("10.x/y")
    old = time.time() - 100 * 86400
    os.utime(p, (old, old))
    assert gh._cache_get("10.x/y") is None


def test_cache_corrupt_returns_none(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    p = gh._cache_path("10.x/y")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json{{{")
    assert gh._cache_get("10.x/y") is None


# ─── _get_token ───────────────────────────────────────────────────────────


def test_get_token_reads_github_token(monkeypatch):
    gh = _import_gh()
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_abc")
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert gh._get_token() == "ghp_abc"


def test_get_token_falls_back_to_gh_token(monkeypatch):
    gh = _import_gh()
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GH_TOKEN", "ghp_xyz")
    assert gh._get_token() == "ghp_xyz"


def test_get_token_strips_whitespace(monkeypatch):
    gh = _import_gh()
    monkeypatch.setenv("GITHUB_TOKEN", "  ghp_xyz\n")
    assert gh._get_token() == "ghp_xyz"


def test_get_token_returns_none_when_missing(monkeypatch):
    gh = _import_gh()
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert gh._get_token() is None


# ─── search_code_by_doi ───────────────────────────────────────────────────


def _mock_response(json_body: dict):
    class Resp:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(json_body).encode("utf-8")
    return Resp()


def test_search_empty_doi_short_circuits(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    result = gh.search_code_by_doi("")
    assert result["n_hits"] == 0
    assert result["repos"] == []
    assert result["error"] == "no_doi"


def test_search_cache_hit_bypasses_network(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    gh._cache_set("10.x/y", {"n_hits": 99, "repos": [{"full_name": "z/w"}], "doi": "10.x/y", "queried_at": 0})
    # urlopen should not be called
    with patch("urllib.request.urlopen", side_effect=AssertionError("network used")):
        result = gh.search_code_by_doi("10.x/y")
    assert result["n_hits"] == 99


def test_search_collapses_repo_duplicates(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    monkeypatch.setattr(gh, "THROTTLE_S", 0)
    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    # 3 hits but 2 unique repos
    body = {
        "total_count": 3,
        "items": [
            {"repository": {"full_name": "a/b", "html_url": "u1", "stargazers_count": 5}},
            {"repository": {"full_name": "a/b", "html_url": "u1", "stargazers_count": 5}},  # dup
            {"repository": {"full_name": "c/d", "html_url": "u2", "stargazers_count": 1}},
        ],
    }
    with patch("urllib.request.urlopen", return_value=_mock_response(body)):
        result = gh.search_code_by_doi("10.x/y", max_results=5)
    assert result["n_hits"] == 3
    assert [r["full_name"] for r in result["repos"]] == ["a/b", "c/d"]


def test_search_respects_max_results(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    monkeypatch.setattr(gh, "THROTTLE_S", 0)
    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    body = {
        "total_count": 5,
        "items": [{"repository": {"full_name": f"r/{i}", "html_url": "u", "stargazers_count": 0}} for i in range(5)],
    }
    with patch("urllib.request.urlopen", return_value=_mock_response(body)):
        result = gh.search_code_by_doi("10.x/y", max_results=2)
    assert len(result["repos"]) == 2


def test_search_403_without_token_returns_auth_required(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    monkeypatch.setattr(gh, "THROTTLE_S", 0)
    monkeypatch.setattr(gh, "_RETRY_DELAYS", ())
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    err = urllib.error.HTTPError(url="x", code=403, msg="Forbidden", hdrs=None, fp=io.BytesIO(b""))
    with patch("urllib.request.urlopen", side_effect=err):
        result = gh.search_code_by_doi("10.x/y")
    assert result["error"] == "auth_required"
    # auth_required NÃO deve persistir cache (token pode chegar depois)
    assert gh._cache_get("10.x/y") is None


def test_search_500_eventually_gives_up(tmp_path, monkeypatch):
    gh = _import_gh()
    monkeypatch.setattr(gh, "CACHE_DIR", tmp_path / "github")
    monkeypatch.setattr(gh, "THROTTLE_S", 0)
    monkeypatch.setattr(gh, "_RETRY_DELAYS", (0, 0))  # 2 retries fast
    monkeypatch.setenv("GITHUB_TOKEN", "fake")
    err = urllib.error.HTTPError(url="x", code=500, msg="boom", hdrs=None, fp=io.BytesIO(b""))
    with patch("urllib.request.urlopen", side_effect=err):
        result = gh.search_code_by_doi("10.x/y")
    assert result["error"] == "fetch_failed"


# ─── priority_pool ────────────────────────────────────────────────────────


def test_priority_pool_orders_tiers_then_citations():
    p45b = _import_45b()
    # 5 candidates:
    # idx 0: full coverage, 100 cit                 → tier1
    # idx 1: full coverage, 500 cit                 → tier1 (should come first)
    # idx 2: partial coverage, 1000 cit             → tier2
    # idx 3: BR + partial (any) coverage external   → tier3
    # idx 4: no coverage                            → skipped
    cands = [
        {"coverage": [{"status": "available"}, {"status": "available"}], "citations": 100},
        {"coverage": [{"status": "available"}], "citations": 500},
        {"coverage": [{"status": "available"}, {"status": "external"}], "citations": 1000},
        {"coverage": [{"status": "external"}], "citations": 50, "is_brazilian": True},
        {"coverage": [], "citations": 9999},
    ]
    pool = p45b.priority_pool(cands)
    # tier1 ordered: 500 cit before 100 cit
    # tier2: just idx 2
    # tier3: just idx 3
    # idx 4 dropped
    assert pool == [1, 0, 2, 3]


def test_priority_pool_skips_no_coverage():
    p45b = _import_45b()
    cands = [
        {"citations": 9999},  # no coverage key at all
        {"coverage": None, "citations": 9999},
        {"coverage": [], "citations": 9999},
        {"coverage": [{"status": "available"}], "citations": 1},  # only one valid
    ]
    pool = p45b.priority_pool(cands)
    assert pool == [3]


def test_priority_pool_br_without_coverage_excluded():
    """BR papers WITHOUT any coverage (no `coverage` list populated) are out of scope."""
    p45b = _import_45b()
    cands = [
        {"is_brazilian": True, "coverage": [], "citations": 100},  # BR sem cov → skip
        {"is_brazilian": True, "coverage": [{"status": "external"}], "citations": 50},  # tier 3
    ]
    pool = p45b.priority_pool(cands)
    assert pool == [1]
