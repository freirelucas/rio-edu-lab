"""Tests pro match enriched (v0.15) — sub-scores normalizados + composite.

Cobre os 5 helpers novos em `analysis/_match.py`:
  - _parse_year_range
  - temporal_overlap_score
  - api_capability_score
  - schema_match_score
  - granularity_match_score
  - domain_match_score
  - match_detail (compositor)

Foco em casos de borda: missing code_book, neutral 0.5, overlap parcial,
domain conflict, schema precision (asymmetric Jaccard).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_match():
    spec = importlib.util.spec_from_file_location("match_v015", str(ANALYSIS / "_match.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── _parse_year_range ────────────────────────────────────────────────────


def test_parse_year_range_simple():
    m = _import_match()
    assert m._parse_year_range("2007-2023 (bienal)") == (2007, 2023)
    assert m._parse_year_range("2010 (Censo IBGE)") == (2010, 2010)
    assert m._parse_year_range("2014-2019") == (2014, 2019)


def test_parse_year_range_handles_noise():
    m = _import_match()
    # Out-of-range years ignored (rejects 1850 below the 1900 floor)
    assert m._parse_year_range("dados desde 1850 até 2020 mas válidos só 2000+") == (2000, 2020)
    assert m._parse_year_range("v2.0 referência de 1999 e 2021") == (1999, 2021)


def test_parse_year_range_none_when_no_year():
    m = _import_match()
    assert m._parse_year_range("freeform string sem ano") is None
    assert m._parse_year_range("") is None
    assert m._parse_year_range(None) is None


# ─── temporal_overlap_score ───────────────────────────────────────────────


def test_temporal_full_coverage():
    m = _import_match()
    cb = {"temporal_coverage_parsed": {"start_year": 2007, "end_year": 2023}}
    exp = {"temporal_min_year": 2010, "temporal_max_year": 2023}
    # cat needs 2010-2023 (14 yrs); item covers 2007-2023 → all 14 covered.
    assert m.temporal_overlap_score(cb, exp) == 1.0


def test_temporal_partial_coverage():
    m = _import_match()
    cb = {"temporal_coverage_parsed": {"start_year": 2015, "end_year": 2023}}
    exp = {"temporal_min_year": 2010, "temporal_max_year": 2023}
    # needed 2010-2023 (14 yrs); item covers 2015-2023 (9 yrs)
    score = m.temporal_overlap_score(cb, exp)
    assert abs(score - 9 / 14) < 1e-6


def test_temporal_no_overlap():
    m = _import_match()
    cb = {"temporal_coverage_parsed": {"start_year": 1990, "end_year": 1995}}
    exp = {"temporal_min_year": 2010, "temporal_max_year": 2023}
    assert m.temporal_overlap_score(cb, exp) == 0.0


def test_temporal_fallback_to_string_parse():
    """Sem temporal_coverage_parsed, função tenta parsear string."""
    m = _import_match()
    cb = {"temporal_coverage": "2010-2020 (anual)"}
    exp = {"temporal_min_year": 2010, "temporal_max_year": 2020}
    assert m.temporal_overlap_score(cb, exp) == 1.0


def test_temporal_neutral_when_missing():
    """Sem dado temporal de qualquer lado → 0.5 neutral (não penaliza legacy)."""
    m = _import_match()
    assert m.temporal_overlap_score({}, {"temporal_min_year": 2010, "temporal_max_year": 2023}) == 0.5
    assert m.temporal_overlap_score({"temporal_coverage_parsed": {"start_year": 2010, "end_year": 2020}}, {}) == 0.5
    assert m.temporal_overlap_score(None, None) == 0.5


# ─── api_capability_score ─────────────────────────────────────────────────


def test_api_score_feature_service_max():
    m = _import_match()
    assert m.api_capability_score({"api_capability": "feature_service"}) == 1.0


def test_api_score_tiers():
    m = _import_match()
    assert m.api_capability_score({"api_capability": "static_file"}) == 0.7
    assert m.api_capability_score({"api_capability": "document_link"}) == 0.3
    assert m.api_capability_score({"api_capability": "none"}) == 0.0


def test_api_score_neutral_missing():
    m = _import_match()
    assert m.api_capability_score({}) == 0.5
    assert m.api_capability_score(None) == 0.5


def test_api_score_unknown_capability_zero():
    """String não-reconhecida → 0 (defensivo, não silenciosamente neutro)."""
    m = _import_match()
    assert m.api_capability_score({"api_capability": "wat"}) == 0.0


# ─── schema_match_score ───────────────────────────────────────────────────


def test_schema_full_match():
    m = _import_match()
    cb = {"key_variables": ["ideb", "ano", "bairro"]}
    exp = {"key_variables_needed": ["ideb", "ano"]}
    assert m.schema_match_score(cb, exp) == 1.0


def test_schema_partial_match():
    m = _import_match()
    cb = {"key_variables": ["ideb"]}
    exp = {"key_variables_needed": ["ideb", "matricula"]}
    assert m.schema_match_score(cb, exp) == 0.5


def test_schema_zero_when_nothing_overlaps():
    m = _import_match()
    cb = {"key_variables": ["foo", "bar"]}
    exp = {"key_variables_needed": ["ideb", "matricula"]}
    assert m.schema_match_score(cb, exp) == 0.0


def test_schema_accent_insensitive():
    m = _import_match()
    cb = {"key_variables": ["Área", "MATRÍCULA"]}
    exp = {"key_variables_needed": ["area", "matricula"]}
    assert m.schema_match_score(cb, exp) == 1.0


def test_schema_neutral_missing():
    m = _import_match()
    assert m.schema_match_score({}, {"key_variables_needed": ["ideb"]}) == 0.5
    assert m.schema_match_score({"key_variables": ["ideb"]}, {}) == 0.5


# ─── granularity_match_score ──────────────────────────────────────────────


def test_granularity_both_match():
    m = _import_match()
    cb = {"unit_of_observation": "bairro", "spatial_granularity": "bairro"}
    exp = {"unit_of_observation": [bairro := "bairro", "ra"], "spatial_granularity": [bairro, "ap"]}
    assert m.granularity_match_score(cb, exp) == 1.0


def test_granularity_one_match():
    m = _import_match()
    cb = {"unit_of_observation": "bairro", "spatial_granularity": "ponto"}
    exp = {"unit_of_observation": "bairro", "spatial_granularity": "bairro"}
    assert m.granularity_match_score(cb, exp) == 0.5


def test_granularity_neither_match():
    m = _import_match()
    cb = {"unit_of_observation": "individuo", "spatial_granularity": "ponto"}
    exp = {"unit_of_observation": "bairro", "spatial_granularity": "bairro"}
    assert m.granularity_match_score(cb, exp) == 0.0


def test_granularity_neutral_missing():
    m = _import_match()
    assert m.granularity_match_score({}, {"unit_of_observation": "bairro"}) == 0.5


# ─── domain_match_score ───────────────────────────────────────────────────


def test_domain_match():
    m = _import_match()
    assert m.domain_match_score({"domain": "educacao-basica"}, {"domain": "educacao-basica"}) == 1.0


def test_domain_conflict():
    m = _import_match()
    assert m.domain_match_score({"domain": "saude"}, {"domain": "educacao-basica"}) == 0.0


def test_domain_neutral_missing():
    m = _import_match()
    assert m.domain_match_score({}, {"domain": "educacao-basica"}) == 0.5
    assert m.domain_match_score({"domain": "saude"}, {}) == 0.5


# ─── match_detail composite ───────────────────────────────────────────────


def test_match_detail_full_alignment():
    """IDEB-bairro × performance-aggregated → composite máximo."""
    m = _import_match()
    item = {
        "code_book": {
            "domain": "educacao-basica",
            "unit_of_observation": "bairro",
            "spatial_granularity": "bairro",
            "temporal_coverage_parsed": {"start_year": 2007, "end_year": 2023},
            "api_capability": "static_file",
            "key_variables": ["ideb", "ano", "bairro"],
        }
    }
    cat = {
        "expects": {
            "domain": "educacao-basica",
            "unit_of_observation": ["bairro", "ra"],
            "spatial_granularity": ["bairro", "ra"],
            "temporal_min_year": 2010,
            "temporal_max_year": 2023,
            "key_variables_needed": ["ideb", "ano"],
        }
    }
    md = m.match_detail(item, cat)
    assert md["domain_match"] == 1.0
    assert md["granularity_match"] == 1.0
    assert md["temporal_match"] == 1.0
    assert md["schema_match"] == 1.0
    assert md["api_match"] == 0.7
    # composite = 1*2 + 1*3 + 1*2 + 1*2 + 0.7*1 = 9.7
    assert abs(md["composite"] - 9.7) < 1e-6


def test_match_detail_no_codebook_returns_neutrals():
    m = _import_match()
    md = m.match_detail({}, {"expects": {"domain": "educacao-basica"}})
    # Item sem code_book → todos sub-scores 0.5 (neutral)
    assert md["domain_match"] == 0.5
    assert md["granularity_match"] == 0.5
    assert md["temporal_match"] == 0.5
    assert md["schema_match"] == 0.5
    assert md["api_match"] == 0.5
    # composite = 0.5 * (2+3+2+2+1) = 5.0
    assert md["composite"] == 5.0


def test_match_detail_includes_composite_key():
    m = _import_match()
    md = m.match_detail({}, {})
    assert set(md.keys()) == {
        "domain_match", "granularity_match", "temporal_match",
        "schema_match", "api_match", "composite",
    }


def test_match_detail_weights_documented():
    m = _import_match()
    # Sanity: pesos somam 10 (range esperado pro composite quando tudo é 1.0)
    assert sum(m.MATCH_DETAIL_WEIGHTS.values()) == 10.0
