"""Testes pra lógica v2 de `analysis/45_bulk_discover.py`:
- visited tracker (load/save em JSON)
- pick_pass2_seeds (filter por abstract + citations + visited)
- enrich_with_semscholar (com SS mocked)

NÃO testa snowball end-to-end (rede). Helpers puros + I/O cacheado.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

ANALYSIS = Path(__file__).resolve().parent.parent / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_45():
    """Importa o 45 (nome começa com dígito → importlib)."""
    spec = importlib.util.spec_from_file_location(
        "bulk_discover", str(ANALYSIS / "45_bulk_discover.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── visited tracker ──────────────────────────────────────────────────────

def test_load_visited_returns_empty_when_no_file(tmp_path, monkeypatch):
    bd = _import_45()
    monkeypatch.setattr(bd, "VISITED_FILE", tmp_path / "visited.json")
    assert bd.load_visited() == set()


def test_save_then_load_visited_round_trip(tmp_path, monkeypatch):
    bd = _import_45()
    monkeypatch.setattr(bd, "VISITED_FILE", tmp_path / "visited.json")
    bd.save_visited({"W1", "W2", "W3"})
    assert bd.load_visited() == {"W1", "W2", "W3"}


def test_load_visited_handles_corrupted_json(tmp_path, monkeypatch):
    bd = _import_45()
    visited_file = tmp_path / "visited.json"
    visited_file.write_text("not valid json {", encoding="utf-8")
    monkeypatch.setattr(bd, "VISITED_FILE", visited_file)
    assert bd.load_visited() == set()


def test_save_visited_writes_sorted(tmp_path, monkeypatch):
    bd = _import_45()
    monkeypatch.setattr(bd, "VISITED_FILE", tmp_path / "visited.json")
    bd.save_visited({"W3", "W1", "W2"})
    data = json.loads((tmp_path / "visited.json").read_text())
    assert data["visited"] == ["W1", "W2", "W3"]
    assert data["n"] == 3


# ─── _norm_id ──────────────────────────────────────────────────────────────

def test_norm_id_strips_url_prefix():
    bd = _import_45()
    assert bd._norm_id("https://openalex.org/W123") == "W123"
    assert bd._norm_id("W456") == "W456"
    assert bd._norm_id("") == ""


def test_norm_id_strips_whitespace():
    bd = _import_45()
    assert bd._norm_id("  W123  ") == "W123"


# ─── pick_pass2_seeds ──────────────────────────────────────────────────────

def test_pick_pass2_seeds_filters_by_abstract():
    bd = _import_45()
    agg = {
        "https://openalex.org/W1": {"abstract": "rich text", "cited_by_count": 100},
        "https://openalex.org/W2": {"abstract": "", "cited_by_count": 200},  # sem abstract
    }
    result = bd.pick_pass2_seeds(agg, n=10, visited=set())
    assert "https://openalex.org/W1" in result
    assert "https://openalex.org/W2" not in result


def test_pick_pass2_seeds_filters_by_min_citations():
    bd = _import_45()
    agg = {
        "https://openalex.org/W1": {"abstract": "x", "cited_by_count": 100},
        "https://openalex.org/W2": {"abstract": "x", "cited_by_count": 5},   # baixo
    }
    result = bd.pick_pass2_seeds(agg, n=10, visited=set(), min_citations=10)
    assert "https://openalex.org/W1" in result
    assert "https://openalex.org/W2" not in result


def test_pick_pass2_seeds_skips_visited():
    bd = _import_45()
    agg = {
        "https://openalex.org/W1": {"abstract": "x", "cited_by_count": 100},
        "https://openalex.org/W2": {"abstract": "x", "cited_by_count": 200},
    }
    result = bd.pick_pass2_seeds(agg, n=10, visited={"W1"})
    assert "https://openalex.org/W1" not in result
    assert "https://openalex.org/W2" in result


def test_pick_pass2_seeds_skips_retracted():
    bd = _import_45()
    agg = {
        "https://openalex.org/W1": {"abstract": "x", "cited_by_count": 100, "is_retracted": True},
        "https://openalex.org/W2": {"abstract": "x", "cited_by_count": 50, "is_retracted": False},
    }
    result = bd.pick_pass2_seeds(agg, n=10, visited=set())
    assert "https://openalex.org/W1" not in result
    assert "https://openalex.org/W2" in result


def test_pick_pass2_seeds_sorts_by_citations_desc():
    bd = _import_45()
    agg = {
        "https://openalex.org/W1": {"abstract": "x", "cited_by_count": 50},
        "https://openalex.org/W2": {"abstract": "x", "cited_by_count": 200},
        "https://openalex.org/W3": {"abstract": "x", "cited_by_count": 100},
    }
    result = bd.pick_pass2_seeds(agg, n=10, visited=set())
    assert result == [
        "https://openalex.org/W2",
        "https://openalex.org/W3",
        "https://openalex.org/W1",
    ]


def test_pick_pass2_seeds_caps_at_n():
    bd = _import_45()
    agg = {
        f"https://openalex.org/W{i}": {"abstract": "x", "cited_by_count": 100 - i}
        for i in range(10)
    }
    result = bd.pick_pass2_seeds(agg, n=3, visited=set())
    assert len(result) == 3


# ─── enrich_with_semscholar ────────────────────────────────────────────────

def test_enrich_marks_openalex_when_abstract_present():
    bd = _import_45()
    agg = {
        "W1": {"abstract": "real abstract", "doi": "10.1/abc"},
    }
    bd.enrich_with_semscholar(agg, verbose=False)
    assert agg["W1"]["abstract_source"] == "openalex"


def test_enrich_marks_none_when_no_abstract_no_doi():
    bd = _import_45()
    agg = {"W1": {"abstract": "", "doi": ""}}
    bd.enrich_with_semscholar(agg, verbose=False)
    assert agg["W1"]["abstract_source"] == "none"


def test_enrich_calls_ss_when_empty_abstract_has_doi():
    bd = _import_45()
    agg = {
        "W1": {"abstract": "", "doi": "10.1/abc"},
    }
    with patch.object(
        bd, "ss_fetch_papers_batch",
        return_value={"10.1/abc": {"abstract": "found via SS"}},
    ) as mock_ss:
        bd.enrich_with_semscholar(agg, verbose=False)
    mock_ss.assert_called_once()
    assert agg["W1"]["abstract"] == "found via SS"
    assert agg["W1"]["abstract_source"] == "semscholar"


def test_enrich_marks_none_when_ss_doesnt_find():
    bd = _import_45()
    agg = {"W1": {"abstract": "", "doi": "10.1/abc"}}
    with patch.object(bd, "ss_fetch_papers_batch", return_value={}):
        bd.enrich_with_semscholar(agg, verbose=False)
    assert agg["W1"]["abstract_source"] == "none"
    assert agg["W1"]["abstract"] == ""
