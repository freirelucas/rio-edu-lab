"""Testes pro `analysis/_semanticscholar.py` (SS fallback v2).

Cobre: safe doi keys, env var auth, cache round-trip + TTL,
fetch_paper_by_doi (cache hit / miss), fetch_papers_batch (parcial cache).
NÃO testa chamadas HTTP reais — patcheia `_fetch_with_retry`.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))

import _semanticscholar as ss  # noqa: E402

# ─── safe_doi_key ──────────────────────────────────────────────────────────

def test_safe_doi_key_replaces_slashes():
    assert ss._safe_doi_key("10.1234/abc") == "10.1234_abc"


def test_safe_doi_key_replaces_multiple():
    assert ss._safe_doi_key("10.1234/abc:xyz") == "10.1234_abc_xyz"


def test_safe_doi_key_no_special_chars():
    assert ss._safe_doi_key("abc123") == "abc123"


# ─── env vars ──────────────────────────────────────────────────────────────

def test_get_api_key_returns_none_when_unset():
    env = dict(os.environ)
    env.pop("SEMANTIC_SCHOLAR_API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        assert ss._get_api_key() is None


def test_get_api_key_returns_value_when_set():
    with patch.dict(os.environ, {"SEMANTIC_SCHOLAR_API_KEY": "sk_test"}):
        assert ss._get_api_key() == "sk_test"


def test_get_api_key_strips_whitespace():
    with patch.dict(os.environ, {"SEMANTIC_SCHOLAR_API_KEY": "  sk_test  "}):
        assert ss._get_api_key() == "sk_test"


# ─── cache layer ───────────────────────────────────────────────────────────

@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(ss, "_CACHE_DIR", tmp_path / "semscholar")
    return tmp_path / "semscholar"


def test_cache_round_trip(tmp_cache):
    data = {"abstract": "hello world", "title": "Test"}
    ss._cache_set("10.1/abc", data)
    assert ss._cache_get("10.1/abc") == data


def test_cache_miss_returns_none(tmp_cache):
    assert ss._cache_get("10.1/notexist") is None


def test_cache_ttl_expired(tmp_cache):
    data = {"abstract": "x"}
    ss._cache_set("10.1/abc", data)
    cache_file = ss._cache_path("10.1/abc")
    old_time = time.time() - (31 * 86400)
    os.utime(cache_file, (old_time, old_time))
    assert ss._cache_get("10.1/abc", ttl_days=30) is None
    assert ss._cache_get("10.1/abc", ttl_days=60) == data


# ─── fetch_paper_by_doi ────────────────────────────────────────────────────

def test_fetch_paper_by_doi_uses_cache_first(tmp_cache):
    cached_data = {"abstract": "from cache"}
    ss._cache_set("10.1/cached", cached_data)
    # _fetch_with_retry should not be called
    with patch.object(ss, "_fetch_with_retry") as mock_fetch:
        result = ss.fetch_paper_by_doi("10.1/cached", verbose=False)
    assert result == cached_data
    mock_fetch.assert_not_called()


def test_fetch_paper_by_doi_caches_after_fetch(tmp_cache, monkeypatch):
    monkeypatch.setattr(ss, "THROTTLE_S", 0)  # skip sleep
    mock_response = {"abstract": "freshly fetched"}
    with patch.object(ss, "_fetch_with_retry", return_value=mock_response) as mock_fetch:
        result = ss.fetch_paper_by_doi("10.1/fresh", verbose=False)
    assert result == mock_response
    mock_fetch.assert_called_once()
    # Cache should now hit
    assert ss._cache_get("10.1/fresh") == mock_response


def test_fetch_paper_by_doi_empty_doi():
    assert ss.fetch_paper_by_doi("") is None


def test_fetch_paper_by_doi_404_returns_none(tmp_cache, monkeypatch):
    monkeypatch.setattr(ss, "THROTTLE_S", 0)
    with patch.object(ss, "_fetch_with_retry", return_value=None):
        result = ss.fetch_paper_by_doi("10.1/notfound", verbose=False)
    assert result is None
    # Should NOT be cached when None
    assert ss._cache_get("10.1/notfound") is None


# ─── fetch_papers_batch ────────────────────────────────────────────────────

def test_fetch_papers_batch_empty():
    assert ss.fetch_papers_batch([]) == {}


def test_fetch_papers_batch_mixes_cache_and_fetch(tmp_cache, monkeypatch):
    monkeypatch.setattr(ss, "THROTTLE_S", 0)
    # Pre-populate cache for one DOI
    ss._cache_set("10.1/cached", {"abstract": "from cache"})
    # Mock SS response for the missing one
    mock_response = [{"abstract": "freshly fetched"}]  # list, ordered same as input
    with patch.object(ss, "_fetch_with_retry", return_value=mock_response) as mock_fetch:
        result = ss.fetch_papers_batch(["10.1/cached", "10.1/fresh"], verbose=False)
    assert result["10.1/cached"]["abstract"] == "from cache"
    assert result["10.1/fresh"]["abstract"] == "freshly fetched"
    # Only the missing one should hit HTTP
    mock_fetch.assert_called_once()


def test_fetch_papers_batch_handles_missing_in_response(tmp_cache, monkeypatch):
    """SS pode retornar null pra DOIs não-encontrados na list."""
    monkeypatch.setattr(ss, "THROTTLE_S", 0)
    mock_response = [{"abstract": "ok"}, None]  # 2º DOI não encontrado
    with patch.object(ss, "_fetch_with_retry", return_value=mock_response):
        result = ss.fetch_papers_batch(["10.1/a", "10.1/b"], verbose=False)
    assert "10.1/a" in result
    assert "10.1/b" not in result


def test_fetch_papers_batch_chunks_over_500(tmp_cache, monkeypatch):
    """Verifica que >500 DOIs → múltiplos batches."""
    monkeypatch.setattr(ss, "THROTTLE_S", 0)
    monkeypatch.setattr(ss, "BATCH_CHUNK", 2)  # força chunks pequenos
    dois = ["10.1/a", "10.1/b", "10.1/c"]
    mock_responses = [
        [{"abstract": "a"}, {"abstract": "b"}],  # chunk 1
        [{"abstract": "c"}],                       # chunk 2
    ]
    with patch.object(ss, "_fetch_with_retry", side_effect=mock_responses) as mock_fetch:
        result = ss.fetch_papers_batch(dois, verbose=False)
    assert mock_fetch.call_count == 2
    assert len(result) == 3


# ─── get_abstract helper ──────────────────────────────────────────────────

def test_get_abstract_returns_string(tmp_cache):
    ss._cache_set("10.1/x", {"abstract": "hello"})
    assert ss.get_abstract("10.1/x") == "hello"


def test_get_abstract_returns_empty_when_no_paper(tmp_cache, monkeypatch):
    monkeypatch.setattr(ss, "THROTTLE_S", 0)
    with patch.object(ss, "_fetch_with_retry", return_value=None):
        assert ss.get_abstract("10.1/nonexistent") == ""


def test_get_abstract_returns_empty_when_paper_has_no_abstract(tmp_cache):
    ss._cache_set("10.1/noabs", {"title": "X"})  # paper sem abstract
    assert ss.get_abstract("10.1/noabs") == ""
