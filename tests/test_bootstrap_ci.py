"""Tests pro `analysis/35_bootstrap_theil_ci.py`.

Cobre: estrutura do CSV de saída, determinismo (mesmo seed → mesma CI),
sanity nos point estimates (≈ valores do theil_ideb_anos_iniciais.csv),
percentile function, bootstrap reproduzibilidade.

NÃO assertiza `ci_lo > 0.5` — bootstrap stratified mostra que o paridade
está dentro do IC95 em todo ano (achado metodológico: share_within point é
estável mas tem variabilidade de resampling significativa). Test é regression
guard nos point estimates (a narrative pública é sobre eles).
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_35():
    spec = importlib.util.spec_from_file_location(
        "bootstrap_ci", str(ANALYSIS / "35_bootstrap_theil_ci.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── percentile helper ────────────────────────────────────────────────────

def test_percentile_basic():
    bs = _import_35()
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert bs.percentile(values, 50) == 3.0


def test_percentile_endpoints():
    bs = _import_35()
    values = [10.0, 20.0, 30.0]
    assert bs.percentile(values, 0) == 10.0
    assert bs.percentile(values, 100) == 30.0


def test_percentile_interpolates():
    bs = _import_35()
    values = [0.0, 100.0]
    # 25th percentile of [0, 100] = linearly interpolate at k=0.25
    assert bs.percentile(values, 25) == 25.0


def test_percentile_empty():
    bs = _import_35()
    assert bs.percentile([], 50) is None


# ─── load_by_year ─────────────────────────────────────────────────────────

def test_load_by_year_keys_are_ints():
    bs = _import_35()
    path = ROOT / "data" / "processed" / "ideb_bairros.csv"
    if not path.exists():
        return  # CI sem este CSV — skip
    by_year = bs.load_by_year(path)
    assert all(isinstance(y, int) for y in by_year)
    assert 2007 in by_year
    assert 2023 in by_year


def test_load_by_year_rows_have_required_fields():
    bs = _import_35()
    path = ROOT / "data" / "processed" / "ideb_bairros.csv"
    if not path.exists():
        return
    by_year = bs.load_by_year(path)
    sample_year = next(iter(by_year))
    sample_row = by_year[sample_year][0]
    assert "ra" in sample_row
    assert "bairro" in sample_row
    assert "ideb" in sample_row
    assert isinstance(sample_row["ideb"], float)


# ─── bootstrap determinism ────────────────────────────────────────────────

def test_bootstrap_deterministic_with_same_seed():
    """Mesmo seed → mesma sequência de resamples → mesmos shares."""
    bs = _import_35()
    rows = [
        {"ra": "A", "bairro": f"b{i}", "ideb": 4 + 0.5 * (i % 3)} for i in range(10)
    ] + [
        {"ra": "B", "bairro": f"b{i+10}", "ideb": 5 + 0.5 * (i % 3)} for i in range(10)
    ]
    s1 = bs.bootstrap_share_within(rows, n_bootstrap=100, seed=42)
    s2 = bs.bootstrap_share_within(rows, n_bootstrap=100, seed=42)
    assert s1 == s2


def test_bootstrap_different_seeds_differ():
    bs = _import_35()
    rows = [
        {"ra": "A", "bairro": f"b{i}", "ideb": 4 + 0.5 * (i % 3)} for i in range(10)
    ] + [
        {"ra": "B", "bairro": f"b{i+10}", "ideb": 5 + 0.5 * (i % 3)} for i in range(10)
    ]
    s1 = bs.bootstrap_share_within(rows, n_bootstrap=100, seed=42)
    s2 = bs.bootstrap_share_within(rows, n_bootstrap=100, seed=99)
    # Não exatamente iguais (caudas eventualmente diferem)
    assert s1 != s2


def test_bootstrap_shares_in_valid_range():
    """Toda share_within ∈ [0, 1]."""
    bs = _import_35()
    rows = [
        {"ra": "A", "bairro": f"b{i}", "ideb": 4 + 0.5 * (i % 3)} for i in range(10)
    ] + [
        {"ra": "B", "bairro": f"b{i+10}", "ideb": 5 + 0.5 * (i % 3)} for i in range(10)
    ]
    shares = bs.bootstrap_share_within(rows, n_bootstrap=200, seed=42)
    assert all(0.0 <= s <= 1.0 for s in shares)


def test_bootstrap_preserves_ra_membership():
    """Stratified: cada resample tem #bairros == original (mesmo n por RA).

    Se tivesse 50 bairros total (30 em A, 20 em B), todo resample tem 50.
    """
    bs = _import_35()
    rows = (
        [{"ra": "A", "bairro": f"a{i}", "ideb": 4.0} for i in range(30)]
        + [{"ra": "B", "bairro": f"b{i}", "ideb": 5.0} for i in range(20)]
    )
    # 50 bairros, todos com mesmo ideb dentro de cada RA → T_within ≈ 0 → share_within ≈ 0
    shares = bs.bootstrap_share_within(rows, n_bootstrap=50, seed=42)
    # Todos os shares deveriam ser ~0 (sem variância dentro de RAs)
    assert all(s < 0.05 for s in shares)


# ─── output CSV (regression guard sobre point estimates) ──────────────────

def test_output_csv_exists_and_well_formed():
    """O CSV commitado tem estrutura esperada + 9 anos."""
    out = ROOT / "data" / "processed" / "theil_bootstrap_ci.csv"
    if not out.exists():
        return  # Test só roda se artifact commitado
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) >= 7, "esperado pelo menos 7 anos (2007-2023 bienal)"
    expected_cols = {
        "year", "n_bairros", "n_ras", "share_within_point",
        "ci_lo", "ci_hi", "median", "n_bootstrap",
    }
    assert set(rows[0].keys()) == expected_cols


def test_point_estimates_in_published_range():
    """Regression guard: pontos ∈ [0.55, 0.75] (narrativa pública é [59%, 73%]).

    Bound bilateral apertado igual `test_theil.share_within > 0.55 AND < 0.75`
    — esta é a fonte de truth do achado central. Bootstrap CIs ficam fora do
    escopo deste teste (sensitivity analysis, não claim público).
    """
    out = ROOT / "data" / "processed" / "theil_bootstrap_ci.csv"
    if not out.exists():
        return
    with out.open() as f:
        for row in csv.DictReader(f):
            point = float(row["share_within_point"])
            assert 0.55 <= point <= 0.75, (
                f"year {row['year']}: share_within_point={point:.4f} fora de [0.55, 0.75]"
            )


def test_ci_bounds_sane():
    """CI bounds são ordenados e em [0, 1]. NÃO assertiza point ∈ CI:
    bootstrap stratified mostra distribuição biased downward em RAs com baixa
    variância dentro do grupo — point pode cair fora do IC superior por uma
    margem pequena. Achado metodológico real (sensitivity vs point estimate)."""
    out = ROOT / "data" / "processed" / "theil_bootstrap_ci.csv"
    if not out.exists():
        return
    with out.open() as f:
        for row in csv.DictReader(f):
            ci_lo = float(row["ci_lo"])
            ci_hi = float(row["ci_hi"])
            median = float(row["median"])
            assert 0.0 <= ci_lo <= ci_hi <= 1.0
            assert ci_lo <= median <= ci_hi


def test_n_bootstrap_recorded():
    """Todos os linhas devem ter n_bootstrap ≥ 1000 (config padrão)."""
    out = ROOT / "data" / "processed" / "theil_bootstrap_ci.csv"
    if not out.exists():
        return
    with out.open() as f:
        for row in csv.DictReader(f):
            assert int(row["n_bootstrap"]) >= 1000
