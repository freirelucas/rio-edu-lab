"""Tests pro `analysis/66_scout.py` (S4 Scout — varredura determinística)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_66():
    spec = importlib.util.spec_from_file_location("scout", str(ANALYSIS / "66_scout.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── scan_seed_saturation ─────────────────────────────────────────────────


def test_seed_saturation_computes_pct(tmp_path, monkeypatch):
    m = _import_66()
    seeds = tmp_path / "seeds.yml"
    seeds.write_text(
        "version: 1\nseeds:\n"
        + "".join(f"  - openalex_id: W{i}\n    enabled: true\n" for i in range(20)),
        encoding="utf-8",
    )
    monkeypatch.setattr(m, "SEEDS_YML", seeds)
    monkeypatch.setattr(m, "SEED_CAP", 40)
    result = m.scan_seed_saturation()
    assert result["n_seeds_enabled"] == 20
    assert result["saturation_pct"] == 50.0


def test_seed_saturation_excludes_disabled(tmp_path, monkeypatch):
    m = _import_66()
    seeds = tmp_path / "seeds.yml"
    seeds.write_text(
        "version: 1\nseeds:\n"
        "  - openalex_id: W1\n    enabled: true\n"
        "  - openalex_id: W2\n    enabled: false\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(m, "SEEDS_YML", seeds)
    result = m.scan_seed_saturation()
    assert result["n_seeds_enabled"] == 1


def test_seed_saturation_skipped_when_missing(tmp_path, monkeypatch):
    m = _import_66()
    monkeypatch.setattr(m, "SEEDS_YML", tmp_path / "nope.yml")
    assert m.scan_seed_saturation()["status"] == "skipped"


# ─── scan_funnel_gaps ─────────────────────────────────────────────────────


def test_funnel_gaps_detects_underrepresented(tmp_path, monkeypatch):
    m = _import_66()
    funnel = tmp_path / "funnel.yml"
    # 3 candidates de performance, 0 de geometry-schools
    funnel.write_text(
        "version: 1\ncandidates:\n"
        "  - id: a\n    suggested_requirements:\n      - category_id: performance-aggregated\n"
        "  - id: b\n    suggested_requirements:\n      - category_id: performance-aggregated\n"
        "  - id: c\n    suggested_requirements:\n      - category_id: performance-aggregated\n",
        encoding="utf-8",
    )
    tax = tmp_path / "tax.yml"
    tax.write_text(
        "vocabularies: {}\ncategories:\n"
        "  - id: performance-aggregated\n"
        "  - id: geometry-schools\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(m, "FUNNEL_YML", funnel)
    monkeypatch.setattr(m, "TAXONOMY_YML", tax)
    result = m.scan_funnel_gaps()
    assert result["status"] == "ok"
    assert "geometry-schools" in result["underrepresented"]
    assert "performance-aggregated" not in result["underrepresented"]


def test_funnel_gaps_balanced(tmp_path, monkeypatch):
    m = _import_66()
    funnel = tmp_path / "funnel.yml"
    funnel.write_text(
        "version: 1\ncandidates:\n"
        "  - id: a\n    suggested_requirements:\n      - category_id: cat1\n"
        "  - id: b\n    suggested_requirements:\n      - category_id: cat2\n",
        encoding="utf-8",
    )
    tax = tmp_path / "tax.yml"
    tax.write_text("categories:\n  - id: cat1\n  - id: cat2\n", encoding="utf-8")
    monkeypatch.setattr(m, "FUNNEL_YML", funnel)
    monkeypatch.setattr(m, "TAXONOMY_YML", tax)
    result = m.scan_funnel_gaps()
    assert result["underrepresented"] == []


# ─── scan_inbox_health ────────────────────────────────────────────────────


def test_inbox_health_counts(tmp_path, monkeypatch):
    import json
    m = _import_66()
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    (processed / "curatorial_inbox.json").write_text(json.dumps([
        {"title": "BR paper", "is_brazilian": True, "n_dataset_refs": 1, "priority_score": 30},
        {"title": "US paper", "is_brazilian": False, "n_dataset_refs": 0, "priority_score": 20},
    ]), encoding="utf-8")
    monkeypatch.setattr(m, "ROOT", tmp_path)
    result = m.scan_inbox_health()
    assert result["n_inbox"] == 2
    assert result["n_brazilian"] == 1
    assert result["n_with_dataset_refs"] == 1


def test_inbox_health_skipped_when_missing(tmp_path, monkeypatch):
    m = _import_66()
    monkeypatch.setattr(m, "ROOT", tmp_path)
    assert m.scan_inbox_health()["status"] == "skipped"


# ─── check_rio_endpoint ───────────────────────────────────────────────────


def test_check_rio_endpoint_alive(monkeypatch):
    m = _import_66()

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    with patch("urllib.request.urlopen", return_value=FakeResp()):
        result = m.check_rio_endpoint()
    assert result["model_card_alive"] is True


def test_check_rio_endpoint_down(monkeypatch):
    m = _import_66()
    with patch("urllib.request.urlopen", side_effect=Exception("boom")):
        result = m.check_rio_endpoint()
    assert result["model_card_alive"] is False


# ─── render_markdown ──────────────────────────────────────────────────────


def test_render_markdown_includes_sections():
    m = _import_66()
    report = {
        "funnel_gaps": {"status": "ok", "recommendation": "test gap rec"},
        "seed_saturation": {"status": "ok", "recommendation": "test seed rec"},
        "inbox_health": {"status": "skipped"},
    }
    md = m.render_markdown(report)
    assert "S4 Scout" in md
    assert "test gap rec" in md
    assert "test seed rec" in md
    # skipped section omitted
    assert "Inbox health" not in md or "skipped" not in md
