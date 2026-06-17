"""Tests pro `analysis/60_top_scorecard.py`.

Cobre cada um dos 8 scorers (S1-S8) em casos típicos + edge.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_60():
    spec = importlib.util.spec_from_file_location(
        "top_scorecard", str(ANALYSIS / "60_top_scorecard.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── S1 Citation ──────────────────────────────────────────────────────────


def test_s1_doi_plus_openalex_is_level_2():
    m = _import_60()
    assert m.score_s1_citation({"doi_or_url": "10.x/y", "openalex_id": "W123"}) == 2


def test_s1_only_doi_is_level_1():
    m = _import_60()
    assert m.score_s1_citation({"doi_or_url": "10.x/y"}) == 1


def test_s1_neither_is_zero():
    m = _import_60()
    assert m.score_s1_citation({}) == 0


# ─── S2 Data Transparency ─────────────────────────────────────────────────


def test_s2_das_public_with_sources_is_2():
    m = _import_60()
    p = {"data_availability_statement": {"summary": "public", "sources": [{"name": "x"}]}}
    assert m.score_s2_data(p) == 2


def test_s2_das_public_no_sources_is_1():
    m = _import_60()
    p = {"data_availability_statement": {"summary": "public", "sources": []}}
    assert m.score_s2_data(p) == 1


def test_s2_no_das_with_legacy_coverage_is_1():
    """Fallback pra papers sem DAS mas com data_rio_coverage (legacy)."""
    m = _import_60()
    p = {"data_rio_coverage": [{"requirement": "x"}]}
    assert m.score_s2_data(p) == 1


def test_s2_no_das_no_coverage_is_0():
    m = _import_60()
    assert m.score_s2_data({}) == 0


# ─── S3 Code Transparency ─────────────────────────────────────────────────


def test_s3_scripts_plus_full_is_2():
    m = _import_60()
    p = {"scripts": [10, 16], "replication_status": "full"}
    assert m.score_s3_code(p) == 2


def test_s3_scripts_plus_partial_is_2():
    m = _import_60()
    p = {"scripts": [26], "replication_status": "partial"}
    assert m.score_s3_code(p) == 2


def test_s3_scripts_no_status_is_1():
    m = _import_60()
    assert m.score_s3_code({"scripts": [10]}) == 1


def test_s3_no_scripts_is_0():
    m = _import_60()
    assert m.score_s3_code({"replication_status": "pending"}) == 0


# ─── S4 Materials Transparency ────────────────────────────────────────────


def test_s4_report_ids_is_1():
    m = _import_60()
    assert m.score_s4_materials({"report_ids": [6, 7]}) == 1


def test_s4_empty_is_0():
    m = _import_60()
    assert m.score_s4_materials({}) == 0


# ─── S5 Design + Analysis ─────────────────────────────────────────────────


def test_s5_full_with_randomness_is_2():
    m = _import_60()
    p = {
        "data_requirements": ["x"],
        "method": ["theil"],
        "controlled_randomness": {"seeds": [42]},
    }
    assert m.score_s5_design(p) == 2


def test_s5_partial_no_randomness_is_1():
    m = _import_60()
    p = {"data_requirements": ["x"], "method": ["y"]}
    assert m.score_s5_design(p) == 1


def test_s5_only_requirements_is_0():
    m = _import_60()
    p = {"data_requirements": ["x"]}
    assert m.score_s5_design(p) == 0


# ─── S6 Study Preregistration ─────────────────────────────────────────────


def test_s6_prospective_with_osf_is_2():
    m = _import_60()
    p = {"preregistration": {"type": "prospective", "osf_url": "https://osf.io/x"}}
    assert m.score_s6_study_prereg(p) == 2


def test_s6_retrospective_capped_at_1():
    """Replications retrospectivas não podem pre-registrar paper publicado."""
    m = _import_60()
    p = {"preregistration": {"type": "retrospective_replication_recipe", "osf_url": "https://osf.io/y"}}
    assert m.score_s6_study_prereg(p) == 1


def test_s6_no_prereg_is_0():
    m = _import_60()
    assert m.score_s6_study_prereg({}) == 0


# ─── S7 Analysis Plan Preregistration ─────────────────────────────────────


def test_s7_recipe_with_osf_is_2():
    m = _import_60()
    p = {"preregistration": {"type": "retrospective_replication_recipe", "osf_url": "https://osf.io/y"}}
    assert m.score_s7_analysis_plan(p) == 2


def test_s7_recipe_no_osf_is_1():
    m = _import_60()
    p = {"preregistration": {"type": "retrospective_replication_recipe", "osf_url": None}}
    assert m.score_s7_analysis_plan(p) == 1


def test_s7_empty_is_0():
    m = _import_60()
    assert m.score_s7_analysis_plan({}) == 0


# ─── S8 Replication ───────────────────────────────────────────────────────


def test_s8_full_is_2():
    m = _import_60()
    assert m.score_s8_replication({"replication_status": "full"}) == 2


def test_s8_partial_is_1():
    m = _import_60()
    assert m.score_s8_replication({"replication_status": "partial"}) == 1


def test_s8_pending_is_0():
    m = _import_60()
    assert m.score_s8_replication({"replication_status": "pending"}) == 0


# ─── compute_scorecard end-to-end ─────────────────────────────────────────


def test_compute_scorecard_returns_per_paper_rows():
    m = _import_60()
    papers = [
        {"id": "p1", "doi_or_url": "10.x", "openalex_id": "W1",
         "replication_status": "full", "scripts": [10]},
        {"id": "p2", "replication_status": "pending"},
    ]
    rows = m.compute_scorecard(papers)
    assert len(rows) == 2
    assert rows[0]["id"] == "p1"
    assert "S1" in rows[0]
    assert "total" in rows[0]
    assert rows[0]["total"] > 0
    assert rows[1]["total"] == 0  # pending, sem nada populado


def test_compute_scorecard_max_possible_is_16():
    """8 standards × 2 levels = 16."""
    m = _import_60()
    rows = m.compute_scorecard([{"id": "x", "replication_status": "?"}])
    assert rows[0]["max_possible"] == 16
