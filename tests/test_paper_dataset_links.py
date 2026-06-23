"""Tests pro `analysis/64_render_paper_dataset_links.py`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_64():
    spec = importlib.util.spec_from_file_location(
        "paper_dataset_links", str(ANALYSIS / "64_render_paper_dataset_links.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_collect_links_skips_empty_refs():
    m = _import_64()
    cands = [
        {"openalex_id": "W1", "title": "X", "dataset_refs": []},
        {"openalex_id": "W2", "title": "Y", "dataset_refs": [{"openalex_id": "Wd1"}]},
    ]
    rows = m.collect_links(cands)
    assert len(rows) == 1
    assert rows[0]["openalex_id"] == "W2"


def test_collect_links_sorts_br_first():
    m = _import_64()
    cands = [
        {"openalex_id": "W1", "title": "us", "is_brazilian": False,
         "citations": 5000, "dataset_refs": [{"openalex_id": "Wd1"}]},
        {"openalex_id": "W2", "title": "br", "is_brazilian": True,
         "citations": 100, "dataset_refs": [{"openalex_id": "Wd2"}]},
    ]
    rows = m.collect_links(cands)
    assert rows[0]["openalex_id"] == "W2"  # BR first


def test_collect_links_sorts_by_n_refs_within_group():
    m = _import_64()
    cands = [
        {"openalex_id": "W1", "title": "x", "citations": 500,
         "dataset_refs": [{"openalex_id": "Wd1"}]},
        {"openalex_id": "W2", "title": "y", "citations": 100,
         "dataset_refs": [{"openalex_id": "Wd1"}, {"openalex_id": "Wd2"}]},
    ]
    rows = m.collect_links(cands)
    assert rows[0]["openalex_id"] == "W2"  # 2 refs > 1 ref


def test_render_markdown_empty_shows_admonition():
    m = _import_64()
    md = m.render_markdown([], n_total_funnel=2266)
    assert "Nenhum candidate" in md
    assert "45d_dataset_refs" in md


def test_render_markdown_includes_paper_count():
    m = _import_64()
    rows = [
        {"openalex_id": "W1", "title": "Paper X", "citations": 100,
         "year": 2020, "is_brazilian": False, "doi": "10.x/y",
         "n_dataset_refs": 2,
         "dataset_refs": [
             {"openalex_id": "Wd1", "doi": "10.5281/zenodo.1", "title": "Dataset A"},
             {"openalex_id": "Wd2", "doi": None, "title": "Dataset B"},
         ]},
    ]
    md = m.render_markdown(rows, n_total_funnel=2266)
    assert "1 papers com" in md
    assert "Paper X" in md
    assert "Dataset A" in md
    assert "10.5281/zenodo.1" in md
    assert "🇧🇷" not in md  # not Brazilian
