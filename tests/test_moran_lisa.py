"""Tests pro `analysis/37_moran_lisa.py`.

Cobre helpers puros (normalize_name, standardize, classify_lisa, compute_lag),
e Moran's I em dado sintético com resultado conhecido.

NÃO testa o pipeline full (requer geopandas + bairros.geojson; testes mais
caros). Testa regression nos CSVs commitados.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_37():
    spec = importlib.util.spec_from_file_location(
        "moran_lisa", str(ANALYSIS / "37_moran_lisa.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── _normalize_name ───────────────────────────────────────────────────────

def test_normalize_strips_accents_lowercases():
    ml = _import_37()
    assert ml._normalize_name("Botafogo") == "botafogo"
    assert ml._normalize_name("São Cristóvão") == "sao cristovao"
    assert ml._normalize_name("  Engenho Novo  ") == "engenho novo"


def test_normalize_empty():
    ml = _import_37()
    assert ml._normalize_name("") == ""
    assert ml._normalize_name(None) == ""


# ─── standardize ──────────────────────────────────────────────────────────

def test_standardize_zero_mean_unit_std():
    ml = _import_37()
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    z, mean, std = ml.standardize(values)
    assert abs(mean - 3.0) < 1e-9
    # Std populacional (não amostral): sqrt(2)
    assert abs(std - 1.4142135623) < 1e-6
    # Z scores devem somar ~0
    assert abs(sum(z)) < 1e-9


def test_standardize_constant_returns_zeros():
    """Var=0 → all zeros (graceful, sem divide-by-zero)."""
    ml = _import_37()
    z, _, std = ml.standardize([5.0, 5.0, 5.0])
    assert std == 0.0
    assert z == [0.0, 0.0, 0.0]


# ─── compute_lag ──────────────────────────────────────────────────────────

def test_compute_lag_simple_chain():
    ml = _import_37()
    # 3 bairros em cadeia: 0 - 1 - 2; valores [10, 20, 30]
    neighbors = [[1], [0, 2], [1]]
    lag = ml.compute_lag([10.0, 20.0, 30.0], neighbors)
    assert lag[0] == 20.0  # vizinhança = só {1} → media = 20
    assert lag[1] == 20.0  # média de {0, 2} = (10+30)/2 = 20
    assert lag[2] == 20.0  # vizinhança = só {1} → media = 20


def test_compute_lag_isolated_bairro():
    """Bairro sem vizinhos → lag = 0 (degenerate but graceful)."""
    ml = _import_37()
    lag = ml.compute_lag([5.0, 10.0], [[], [0]])
    assert lag[0] == 0.0
    assert lag[1] == 5.0


# ─── morans_i + permutação ────────────────────────────────────────────────

def test_morans_i_constant_field_is_zero():
    """Sem variância → Moran's I = 0."""
    ml = _import_37()
    z = [0.0, 0.0, 0.0, 0.0]
    neighbors = [[1, 2], [0, 3], [0, 3], [1, 2]]
    global_i, local_i = ml.morans_i(z, neighbors)
    assert global_i == 0.0
    assert all(li == 0.0 for li in local_i)


def test_morans_i_positive_autocorrelation():
    """Padrão checkerboard inverso (vizinhos similares) → I > 0."""
    ml = _import_37()
    # Cadeia 0-1-2-3 com [-1, -1, 1, 1] (clusters positivos vizinhos)
    z = [-1.0, -1.0, 1.0, 1.0]
    neighbors = [[1], [0, 2], [1, 3], [2]]
    global_i, _ = ml.morans_i(z, neighbors)
    # Esperado positivo (vizinhos com sinais iguais ou opostos por par)
    # I = mean(z_i * lag_z_i) onde lag_z = média vizinhos
    # = mean(-1*-1, -1*(- 1+1)/2, 1*(1+-1)/2, 1*1) = mean(1, 0, 0, 1) = 0.5
    assert global_i == 0.5


def test_morans_i_negative_autocorrelation():
    """Checkerboard (vizinhos opostos) → I < 0."""
    ml = _import_37()
    # Cadeia 0-1-2-3 com [-1, 1, -1, 1]
    z = [-1.0, 1.0, -1.0, 1.0]
    neighbors = [[1], [0, 2], [1, 3], [2]]
    global_i, _ = ml.morans_i(z, neighbors)
    # I = mean(-1*1, 1*(-1-1)/2, -1*(1+1)/2, 1*(-1)) = mean(-1, -1, -1, -1) = -1
    assert global_i == -1.0


# ─── classify_lisa ────────────────────────────────────────────────────────

def test_classify_lisa_hot_cold():
    ml = _import_37()
    z = [1.5, -1.5, 0.5]
    lag_z = [1.0, -1.0, 0.0]
    p = [0.01, 0.01, 0.5]  # 1 e 2 significativos, 3 não
    classes = ml.classify_lisa(z, lag_z, p)
    assert classes[0] == "HH"
    assert classes[1] == "LL"
    assert classes[2] == "NS"


def test_classify_lisa_outliers():
    ml = _import_37()
    z = [1.5, -1.5]
    lag_z = [-1.0, 1.0]  # high near lows / low near highs
    p = [0.01, 0.01]
    classes = ml.classify_lisa(z, lag_z, p)
    assert classes[0] == "HL"
    assert classes[1] == "LH"


def test_classify_lisa_not_significant():
    ml = _import_37()
    z = [1.5, -1.5]
    lag_z = [1.0, -1.0]
    p = [0.1, 0.5]  # > 0.05 → NS
    classes = ml.classify_lisa(z, lag_z, p)
    assert all(c == "NS" for c in classes)


# ─── output CSV (regression guard) ────────────────────────────────────────

def test_moran_lisa_ideb_csv_schema():
    """CSV commitado tem colunas esperadas + n_bairros plausível."""
    out = ROOT / "data" / "processed" / "moran_lisa_ideb.csv"
    if not out.exists():
        return  # CI sem o output — skip
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) > 100, f"esperado >100 bairros com IDEB, got {len(rows)}"
    expected_cols = {"bairro", "value", "z", "lag_z", "local_i", "pseudo_p", "lisa_class"}
    assert set(rows[0].keys()) == expected_cols
    # Toda lisa_class deve estar em {HH, LL, HL, LH, NS}
    valid = {"HH", "LL", "HL", "LH", "NS"}
    for r in rows:
        assert r["lisa_class"] in valid, f"invalid class: {r['lisa_class']}"


def test_moran_lisa_summary_json_morans_i_in_range():
    """Sanity: Moran's I sempre em [-1, +1]."""
    import json
    out = ROOT / "data" / "processed" / "moran_lisa_summary.json"
    if not out.exists():
        return
    summary = json.loads(out.read_text(encoding="utf-8"))
    for entry in summary:
        i = entry["morans_i_global"]
        assert -1.0 <= i <= 1.0, f"{entry['variable']}: I={i} fora de [-1, 1]"
        # Pseudo-p ∈ [0, 1]
        assert 0.0 <= entry["pseudo_p_global"] <= 1.0
