"""Testes pros helpers v2 de `analysis/_openalex.py`.

Cobre: helpers puros (is_brazilian, institutions_summary, concepts_structured,
topics_structured, reconstruct_abstract sem truncation), env var auth, cache
round-trip + TTL. NÃO testa chamadas HTTP reais (essas precisam de smoke
manual contra OpenAlex).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))

import _openalex as oa  # noqa: E402

# ─── is_brazilian ──────────────────────────────────────────────────────────

def test_is_brazilian_true_when_BR_institution():
    authorships = [
        {"institutions": [{"country_code": "US"}, {"country_code": "BR"}]},
        {"institutions": [{"country_code": "DE"}]},
    ]
    assert oa.is_brazilian(authorships) is True


def test_is_brazilian_false_when_no_BR():
    authorships = [
        {"institutions": [{"country_code": "US"}, {"country_code": "DE"}]},
    ]
    assert oa.is_brazilian(authorships) is False


def test_is_brazilian_empty_authorships():
    assert oa.is_brazilian([]) is False


def test_is_brazilian_handles_lowercase_country_code():
    authorships = [{"institutions": [{"country_code": "br"}]}]
    assert oa.is_brazilian(authorships) is True


# ─── institutions_summary ──────────────────────────────────────────────────

def test_institutions_summary_dedup_by_ror():
    authorships = [
        {"institutions": [{"ror": "ror1", "display_name": "Univ A", "country_code": "BR"}]},
        {"institutions": [{"ror": "ror1", "display_name": "Univ A", "country_code": "BR"}]},
        {"institutions": [{"ror": "ror2", "display_name": "Univ B", "country_code": "US"}]},
    ]
    result = oa.institutions_summary(authorships)
    assert len(result) == 2
    rors = {inst["ror"] for inst in result}
    assert rors == {"ror1", "ror2"}


def test_institutions_summary_dedup_by_name_when_no_ror():
    authorships = [
        {"institutions": [{"display_name": "X"}]},
        {"institutions": [{"display_name": "X"}]},
    ]
    result = oa.institutions_summary(authorships)
    assert len(result) == 1
    assert result[0]["display_name"] == "X"


def test_institutions_summary_empty():
    assert oa.institutions_summary([]) == []


# ─── concepts_structured ──────────────────────────────────────────────────

def test_concepts_structured_returns_top5():
    concepts = [{"id": f"C{i}", "level": 1, "score": 0.5, "display_name": f"c{i}"} for i in range(10)]
    result = oa.concepts_structured(concepts)
    assert len(result) == 5
    assert result[0]["id"] == "C0"


def test_concepts_structured_preserves_fields():
    c = [{"id": "C123", "level": 2, "score": 0.8, "display_name": "Education"}]
    r = oa.concepts_structured(c)[0]
    assert r == {"id": "C123", "level": 2, "score": 0.8, "display_name": "Education"}


# ─── topics_structured ─────────────────────────────────────────────────────

def test_topics_structured_extracts_hierarchy():
    topics = [{
        "id": "T1",
        "display_name": "Spatial Inequality",
        "score": 0.95,
        "subfield": {"display_name": "Urban Studies"},
        "field": {"display_name": "Social Sciences"},
        "domain": {"display_name": "Social Sciences"},
    }]
    r = oa.topics_structured(topics)[0]
    assert r["display_name"] == "Spatial Inequality"
    assert r["subfield"] == "Urban Studies"
    assert r["field"] == "Social Sciences"


def test_topics_structured_handles_missing_hierarchy():
    """topics sem subfield/field/domain devem retornar None nesses campos."""
    topics = [{"id": "T1", "display_name": "X", "score": 0.5}]
    r = oa.topics_structured(topics)[0]
    assert r["subfield"] is None
    assert r["field"] is None
    assert r["domain"] is None


# ─── reconstruct_abstract ──────────────────────────────────────────────────

def test_reconstruct_abstract_no_truncation():
    """v2: era 500 chars; agora full length."""
    # Build a long inverted index (1000+ chars when reconstructed)
    words = [f"word{i}" for i in range(200)]
    inverted = {w: [i] for i, w in enumerate(words)}
    result = oa.reconstruct_abstract(inverted)
    assert len(result) > 500
    assert not result.endswith("…")
    assert result.startswith("word0")
    assert "word199" in result


def test_reconstruct_abstract_empty():
    assert oa.reconstruct_abstract(None) == ""
    assert oa.reconstruct_abstract({}) == ""


def test_reconstruct_abstract_ordering():
    inverted = {"hello": [1], "world": [2], "foo": [0]}
    assert oa.reconstruct_abstract(inverted) == "foo hello world"


# ─── primary_topic_dict ────────────────────────────────────────────────────

def test_primary_topic_dict_full():
    work = {"primary_topic": {
        "id": "T1", "display_name": "X", "score": 0.9,
        "subfield": {"display_name": "S"},
        "field": {"display_name": "F"},
    }}
    r = oa.primary_topic_dict(work)
    assert r == {"id": "T1", "display_name": "X", "score": 0.9, "subfield": "S", "field": "F"}


def test_primary_topic_dict_none():
    assert oa.primary_topic_dict({}) is None
    assert oa.primary_topic_dict({"primary_topic": None}) is None


# ─── parse_work integration ───────────────────────────────────────────────

def test_parse_work_persists_v2_fields():
    """Check that parse_work output has all 13+ rich fields."""
    work = {
        "id": "https://openalex.org/W123",
        "doi": "https://doi.org/10.1/abc",
        "title": "Foo",
        "publication_year": 2020,
        "cited_by_count": 50,
        "abstract_inverted_index": {"hello": [0]},
        "authorships": [{"institutions": [{"country_code": "BR", "ror": "rorA"}]}],
        "concepts": [{"id": "C1", "level": 1, "score": 0.7, "display_name": "Education"}],
        "topics": [{"id": "T1", "display_name": "X", "score": 0.9}],
        "primary_topic": {"id": "T1", "display_name": "X", "score": 0.9},
        "keywords": [{"display_name": "kw1"}],
        "type": "article",
        "related_works": ["W456", "W789"],
        "referenced_works": ["W111", "W222", "W333"],
        "best_oa_location": {"pdf_url": "http://example.com/pdf"},
        "fwci": 2.5,
        "counts_by_year": [{"year": 2020, "cited_by_count": 10}],
        "is_retracted": False,
        "mesh": [{"descriptor_name": "Schools"}],
        "sustainable_development_goals": [{"display_name": "SDG 4"}],
    }
    r = oa.parse_work(work)
    # Legacy preserved
    assert r["openalex_id"] == "https://openalex.org/W123"
    assert r["abstract"] == "hello"
    # v2 rich fields present
    assert r["is_brazilian"] is True
    assert r["concepts"][0]["display_name"] == "Education"
    assert len(r["topics"]) == 1
    assert r["primary_topic"]["id"] == "T1"
    assert r["keywords"] == ["kw1"]
    assert len(r["institutions"]) == 1
    assert r["related_works"] == ["W456", "W789"]
    # v0.16 bug fix: referenced_works (citações reais) é separado de
    # related_works (similaridade). Ambos persistidos.
    assert r["referenced_works"] == ["W111", "W222", "W333"]
    # v0.17 — top-level type pra filtrar refs por dataset/software
    assert r["type"] == "article"  # default tipo em fixture
    assert r["best_oa_pdf_url"] == "http://example.com/pdf"
    assert r["fwci"] == 2.5
    assert r["counts_by_year"][0]["year"] == 2020
    assert r["is_retracted"] is False
    assert r["mesh"] == ["Schools"]
    assert r["sdg"] == ["SDG 4"]


# ─── env vars ──────────────────────────────────────────────────────────────

def test_get_email_uses_env_var():
    with patch.dict(os.environ, {"OPENALEX_EMAIL": "user@example.com"}):
        assert oa._get_email() == "user@example.com"


def test_get_email_fallback_when_unset():
    env = dict(os.environ)
    env.pop("OPENALEX_EMAIL", None)
    with patch.dict(os.environ, env, clear=True):
        assert oa._get_email() == oa.DEFAULT_EMAIL


def test_get_api_key_returns_none_when_unset():
    env = dict(os.environ)
    env.pop("OPENALEX_API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        assert oa._get_api_key() is None


def test_get_api_key_returns_value_when_set():
    with patch.dict(os.environ, {"OPENALEX_API_KEY": "sk_test"}):
        assert oa._get_api_key() == "sk_test"


def test_with_mailto_includes_email():
    with patch.dict(os.environ, {"OPENALEX_EMAIL": "x@y.com"}):
        url = oa._with_mailto("https://api.openalex.org/works")
        assert "mailto=x@y.com" in url


# ─── cache layer ───────────────────────────────────────────────────────────

@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    """Redireciona _CACHE_DIR pra tmp_path durante o test."""
    monkeypatch.setattr(oa, "_CACHE_DIR", tmp_path / "openalex")
    return tmp_path / "openalex"


def test_cache_round_trip(tmp_cache):
    data = {"id": "W123", "title": "Test"}
    oa._cache_set("work", "W123", data)
    assert oa._cache_get("work", "W123") == data


def test_cache_miss_returns_none(tmp_cache):
    assert oa._cache_get("work", "W_not_exist") is None


def test_cache_ttl_expired(tmp_cache):
    """Arquivo mais velho que TTL retorna None."""
    data = {"id": "W123"}
    oa._cache_set("work", "W123", data)
    # Idade artificial: 31 dias atrás
    cache_file = oa._cache_path("work", "W123")
    old_time = time.time() - (31 * 86400)
    os.utime(cache_file, (old_time, old_time))
    assert oa._cache_get("work", "W123", ttl_days=30) is None
    # Mas com TTL maior, ainda lê
    assert oa._cache_get("work", "W123", ttl_days=60) == data


def test_cache_corrupted_json_returns_none(tmp_cache):
    p = oa._cache_path("work", "W_corrupt")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not valid json {", encoding="utf-8")
    assert oa._cache_get("work", "W_corrupt") is None
