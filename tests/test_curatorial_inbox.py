"""Tests pro `analysis/65_curatorial_inbox.py`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_65():
    spec = importlib.util.spec_from_file_location(
        "curatorial_inbox", str(ANALYSIS / "65_curatorial_inbox.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── priority_score ────────────────────────────────────────────────────────


def test_priority_score_combines_signals():
    m = _import_65()
    c = {
        "coverage": [{"match_detail": {"composite": 8.0}}],
        "citations": 1000,
        "dataset_refs": [{}, {}],
        "is_brazilian": True,
    }
    # 8.0×2 + log10(1001)×1.5 + 2×3.0 + 2.0 = 16 + 4.5 + 6 + 2 ≈ 28.5
    score = m.compute_priority_score(c)
    assert score > 25


def test_priority_score_handles_empty():
    m = _import_65()
    assert m.compute_priority_score({}) == 0


def test_priority_score_br_bonus():
    m = _import_65()
    base = {"coverage": [], "citations": 0}
    br = {**base, "is_brazilian": True}
    assert m.compute_priority_score(br) > m.compute_priority_score(base)


# ─── is_inbox_eligible ─────────────────────────────────────────────────────


def test_inbox_eligible_excludes_already_in_catalog():
    m = _import_65()
    c = {
        "openalex_id": "https://openalex.org/W1",
        "coverage": [{"status": "available", "match_detail": {"composite": 10}}],
    }
    assert m.is_inbox_eligible(c, catalog_ids={"W1"}) is False
    assert m.is_inbox_eligible(c, catalog_ids={"W2"}) is True


def test_inbox_eligible_requires_some_available():
    m = _import_65()
    c = {
        "openalex_id": "W1",
        "coverage": [{"status": "external"}, {"status": "missing"}],
    }
    assert m.is_inbox_eligible(c, catalog_ids=set()) is False


def test_inbox_eligible_accepts_high_composite():
    m = _import_65()
    c = {
        "openalex_id": "W1",
        "coverage": [{"status": "available", "match_detail": {"composite": 7.0}}],
    }
    assert m.is_inbox_eligible(c, catalog_ids=set()) is True


def test_inbox_eligible_accepts_dataset_refs_even_low_composite():
    m = _import_65()
    c = {
        "openalex_id": "W1",
        "coverage": [{"status": "available", "match_detail": {"composite": 2.0}}],
        "dataset_refs": [{"openalex_id": "Wd1", "type": "dataset"}],
    }
    assert m.is_inbox_eligible(c, catalog_ids=set()) is True


def test_inbox_eligible_accepts_brazilian_even_low_composite():
    m = _import_65()
    c = {
        "openalex_id": "W1",
        "coverage": [{"status": "available", "match_detail": {"composite": 2.0}}],
        "is_brazilian": True,
    }
    assert m.is_inbox_eligible(c, catalog_ids=set()) is True


# ─── collect_inbox_rows ────────────────────────────────────────────────────


def test_collect_inbox_caps_at_top_n():
    m = _import_65()
    cands = []
    for i in range(100):
        cands.append({
            "openalex_id": f"W{i}",
            "title": f"Paper {i}",
            "coverage": [{"status": "available", "match_detail": {"composite": 8.0}}],
            "citations": i,
        })
    rows = m.collect_inbox_rows(cands, catalog_ids=set(), top_n=10)
    assert len(rows) == 10


def test_collect_inbox_sorts_by_priority_desc():
    m = _import_65()
    cands = [
        {"openalex_id": "W_low", "title": "Low", "coverage": [{"status": "available",
         "match_detail": {"composite": 5.5}}], "citations": 10},
        {"openalex_id": "W_high", "title": "High", "coverage": [{"status": "available",
         "match_detail": {"composite": 9.0}}], "citations": 1000, "is_brazilian": True,
         "dataset_refs": [{}]},
    ]
    rows = m.collect_inbox_rows(cands, catalog_ids=set())
    assert rows[0]["openalex_id"] == "W_high"


# ─── render_markdown ───────────────────────────────────────────────────────


def test_render_includes_action_link():
    m = _import_65()
    rows = [{
        "openalex_id": "W123", "title": "X", "year": 2020, "citations": 100,
        "is_brazilian": True, "doi": "10.x/y", "max_composite": 8.5,
        "n_dataset_refs": 2, "n_coverage": 3, "priority_score": 30.0,
    }]
    md = m.render_markdown(rows, n_total_funnel=2266, n_catalog=18)
    assert "🇧🇷" in md
    assert "W123" in md
    assert "issues/new?template=replication-claim" in md
    assert "issues/new?template=sugerir-paper" in md


def test_render_empty_shows_admonition():
    m = _import_65()
    md = m.render_markdown([], n_total_funnel=2266, n_catalog=18)
    assert "Inbox vazio" in md
    assert "47_check_coverage" in md
