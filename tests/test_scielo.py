"""Tests pro adapter `analysis/_scielo.py` (SciELO ArticleMeta API).

Mocks urlopen pra evitar HTTP real. Valida cache, parse_article shape,
search loop, retry behavior.
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


def _import_scielo():
    spec = importlib.util.spec_from_file_location("scielo", str(ANALYSIS / "_scielo.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mock_response(payload):
    class Resp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return json.dumps(payload).encode("utf-8")
    return Resp()


# ─── cache get/set ────────────────────────────────────────────────────────


def test_cache_roundtrip(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    s._cache_set("foo", {"x": 1})
    assert s._cache_get("foo") == {"x": 1}


def test_cache_miss_returns_none(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    assert s._cache_get("never_set") is None


def test_cache_expired_returns_none(tmp_path, monkeypatch):
    import os
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    s._cache_set("x", {"a": 1})
    # Backdate mtime > TTL
    p = s._cache_path("x")
    old = time.time() - 100 * 86400
    os.utime(p, (old, old))
    assert s._cache_get("x") is None


def test_cache_safe_filename():
    s = _import_scielo()
    # PID contains slashes/dashes
    assert "/" not in s._safe_filename("S0101-7330/2007")
    assert ":" not in s._safe_filename("scl:1234")


# ─── fetch_article_by_pid ─────────────────────────────────────────────────


def test_fetch_article_empty_pid_returns_none(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    assert s.fetch_article_by_pid("scl", "") is None


def test_fetch_article_cache_hit_skips_network(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    s._cache_set("article_scl_S123", {"cached": True})
    # Network call não deve acontecer
    with patch("urllib.request.urlopen", side_effect=AssertionError("network used")):
        result = s.fetch_article_by_pid("scl", "S123")
    assert result == {"cached": True}


def test_fetch_article_populates_cache(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    monkeypatch.setattr(s, "THROTTLE_S", 0)
    monkeypatch.setattr(s, "_RETRY_DELAYS", ())
    with patch("urllib.request.urlopen", return_value=_mock_response({"code": "S123"})):
        result = s.fetch_article_by_pid("scl", "S123")
    assert result == {"code": "S123"}
    # 2nd call serves from cache
    with patch("urllib.request.urlopen", side_effect=AssertionError("network used")):
        result2 = s.fetch_article_by_pid("scl", "S123")
    assert result2 == {"code": "S123"}


# ─── retry behavior ───────────────────────────────────────────────────────


def test_http_404_returns_none_no_retry(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    monkeypatch.setattr(s, "_RETRY_DELAYS", (0,))
    err = urllib.error.HTTPError(url="x", code=404, msg="Not Found", hdrs=None, fp=io.BytesIO(b""))
    call_count = [0]

    def counting_urlopen(*a, **kw):
        call_count[0] += 1
        raise err

    with patch("urllib.request.urlopen", side_effect=counting_urlopen):
        result = s.fetch_article_by_pid("scl", "S999")
    assert result is None
    assert call_count[0] == 1  # no retry for 404


def test_http_500_retries(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    monkeypatch.setattr(s, "_RETRY_DELAYS", (0, 0))  # 2 retries, no delay
    err = urllib.error.HTTPError(url="x", code=500, msg="boom", hdrs=None, fp=io.BytesIO(b""))
    call_count = [0]

    def counting_urlopen(*a, **kw):
        call_count[0] += 1
        raise err

    with patch("urllib.request.urlopen", side_effect=counting_urlopen):
        result = s.fetch_article_by_pid("scl", "S123")
    assert result is None
    assert call_count[0] == 3  # 1 initial + 2 retries


# ─── parse_article ────────────────────────────────────────────────────────


def test_parse_article_extracts_basic_fields():
    s = _import_scielo()
    raw = {
        "code": "S0101-73302007000300016",
        "collection": "scl",
        "v12": [{"_": "Eliminação adiada"}],
        "v83": [{"_": "Abstract sobre desigualdade educacional"}],
        "v65": [{"_": "20070801"}],
        "v237": [{"_": "10.1590/s0101-73302007000300016"}],
        "v10": [
            {"s": "Patto", "n": "Maria Helena Souza"},
            {"s": "Silva", "n": "João"},
        ],
    }
    parsed = s.parse_article(raw)
    assert parsed["scielo_pid"] == "S0101-73302007000300016"
    assert parsed["title"] == "Eliminação adiada"
    assert "desigualdade" in parsed["abstract"]
    assert parsed["year"] == 2007
    assert parsed["doi"] == "10.1590/s0101-73302007000300016"
    assert parsed["authors"] == ["Patto, Maria Helena Souza", "Silva, João"]
    assert parsed["is_brazilian"] is True
    assert "scielo" in parsed["discovered_via"]


def test_parse_article_handles_missing_fields():
    s = _import_scielo()
    parsed = s.parse_article({"code": "S1", "collection": "scl"})
    assert parsed["scielo_pid"] == "S1"
    assert parsed["title"] == ""
    assert parsed["year"] is None
    assert parsed["authors"] == []


def test_parse_article_empty_input():
    s = _import_scielo()
    assert s.parse_article({}) == {}
    assert s.parse_article(None) == {}


def test_parse_article_non_br_collection_not_brazilian():
    s = _import_scielo()
    parsed = s.parse_article({"code": "S1", "collection": "arg"})
    assert parsed["is_brazilian"] is False


def test_parse_article_invalid_year_returns_none():
    s = _import_scielo()
    parsed = s.parse_article({"code": "S1", "v65": [{"_": "invalid"}]})
    assert parsed["year"] is None


# ─── search_articles_edu (orchestration) ──────────────────────────────────


def test_search_loop_caps_at_max_results(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    monkeypatch.setattr(s, "THROTTLE_S", 0)

    def fake_list(collection, offset, limit, from_date=None):
        return [{"code": f"S{offset + i:04d}"} for i in range(limit)]

    def fake_fetch(collection, pid):
        return {"code": pid, "collection": collection,
                "v12": [{"_": f"Title {pid}"}], "v65": [{"_": "20100101"}]}

    monkeypatch.setattr(s, "list_article_identifiers", fake_list)
    monkeypatch.setattr(s, "fetch_article_by_pid", fake_fetch)

    results = s.search_articles_edu(year_min=2010, max_results=10)
    assert len(results) == 10


def test_search_stops_when_identifiers_exhausted(tmp_path, monkeypatch):
    s = _import_scielo()
    monkeypatch.setattr(s, "CACHE_DIR", tmp_path / "scielo")
    monkeypatch.setattr(s, "THROTTLE_S", 0)

    # Returns smaller batch → indicates last page
    call_count = [0]
    def fake_list(collection, offset, limit, from_date=None):
        call_count[0] += 1
        if call_count[0] == 1:
            return [{"code": "S1"}, {"code": "S2"}]  # smaller than batch_size (50)
        return []

    def fake_fetch(collection, pid):
        return {"code": pid, "collection": collection}

    monkeypatch.setattr(s, "list_article_identifiers", fake_list)
    monkeypatch.setattr(s, "fetch_article_by_pid", fake_fetch)

    results = s.search_articles_edu(max_results=100)
    assert len(results) == 2
