"""Unit tests for the canonical Theil-T implementation.

Validate:
- T = 0 in the perfect-equality case (all values equal).
- T > 0 in any non-degenerate case.
- Decomposition is exact: T_b + T_w == T (within float precision).
- Weighted with all weights = 1 reproduces the unit-weighted result.
- Single-group decomposition has T_b = 0 and T_w = T.
- Empty / single-value inputs return 0.
- Theil of a known reference distribution matches the closed-form.
- Real-data sanity: every row in theil_ideb_anos_iniciais.csv passes
  T_b + T_w - T < 1e-6 (this catches regressions from any pipeline change).
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis._theil import theil_decompose, theil_t  # noqa: E402

EPS = 1e-12


class TestTheilT:
    def test_perfect_equality_is_zero(self):
        assert theil_t([1.0, 1.0, 1.0, 1.0]) == pytest.approx(0.0, abs=EPS)
        assert theil_t([5.5] * 100) == pytest.approx(0.0, abs=EPS)

    def test_max_inequality_is_log_n(self):
        # All mass on one unit: T should approach ln(N) for unit weights.
        # We approximate with very small epsilon-replacements for the zeros.
        eps = 1e-10
        n = 5
        vals = [1.0] + [eps] * (n - 1)
        # Should approach ln(N) - small correction
        t = theil_t(vals)
        # Most of the entropy comes from the one large value; verify it's > 1.
        assert t > 1.0
        assert t < math.log(n)

    def test_returns_zero_for_short_input(self):
        assert theil_t([]) == 0.0
        assert theil_t([3.14]) == 0.0
        assert theil_t([0.0, 0.0]) == 0.0  # both invalid (cleaned out)

    def test_drops_nonpositive_values(self):
        # Negative or zero values should be silently dropped and not crash.
        assert theil_t([5.0, -1.0, 5.0, 0.0]) == pytest.approx(0.0, abs=EPS)
        # Mix of valid + invalid; valid pair is uniform, so T = 0.
        assert theil_t([3.0, None, 3.0]) == pytest.approx(0.0, abs=EPS)  # type: ignore

    def test_known_distribution(self):
        # Two-point distribution with values 1 and 3, equal weights:
        #   mean = 2
        #   T = 0.5 * (1/2) ln(1/2) + 0.5 * (3/2) ln(3/2)
        #     = 0.25 * ln(0.5) + 0.75 * ln(1.5)
        #     ≈ -0.1733 + 0.3041 ≈ 0.1308
        expected = 0.25 * math.log(0.5) + 0.75 * math.log(1.5)
        got = theil_t([1.0, 3.0])
        assert got == pytest.approx(expected, abs=1e-9)

    def test_weights_none_equals_uniform_weights(self):
        vals = [4.5, 5.0, 5.5, 6.0, 6.5]
        t1 = theil_t(vals)
        t2 = theil_t(vals, weights=[1.0] * len(vals))
        assert t1 == pytest.approx(t2, abs=EPS)

    def test_weights_invariance_under_scaling(self):
        # Scaling all weights by the same constant should not change T.
        vals = [4.0, 5.0, 6.0, 7.0]
        weights_a = [1.0, 1.0, 1.0, 1.0]
        weights_b = [3.7, 3.7, 3.7, 3.7]
        assert theil_t(vals, weights_a) == pytest.approx(
            theil_t(vals, weights_b), abs=EPS
        )

    def test_weights_change_result(self):
        # Asymmetric weights should change T_total, period. Direction depends
        # on subtle interaction: putting weight on an outlier pulls the
        # weighted mean toward it (lowers T); putting weight elsewhere reduces
        # the outlier's weight share (also lowers T). So uniform is often a
        # local maximum of T over weight perturbations, not a baseline below
        # which all alternatives sit.
        vals = [5.0, 5.0, 5.0, 10.0]
        t_uniform = theil_t(vals)
        t_a = theil_t(vals, weights=[1.0, 1.0, 1.0, 5.0])
        t_b = theil_t(vals, weights=[5.0, 5.0, 5.0, 1.0])
        assert t_a != pytest.approx(t_uniform, abs=EPS)
        assert t_b != pytest.approx(t_uniform, abs=EPS)
        assert t_a != pytest.approx(t_b, abs=EPS)


class TestTheilDecompose:
    def test_additive_identity(self):
        # T_total ≡ T_between + T_within, always.
        vals = [4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
        groups = ["A", "A", "A", "B", "B", "B"]
        t, tb, tw = theil_decompose(vals, groups)
        assert t == pytest.approx(tb + tw, abs=EPS)

    def test_perfect_equality_zero_decomposition(self):
        vals = [5.0] * 6
        groups = ["A", "A", "A", "B", "B", "B"]
        t, tb, tw = theil_decompose(vals, groups)
        assert t == pytest.approx(0.0, abs=EPS)
        assert tb == pytest.approx(0.0, abs=EPS)
        assert tw == pytest.approx(0.0, abs=EPS)

    def test_single_group_pure_within(self):
        vals = [4.5, 5.0, 5.5, 6.0]
        t, tb, tw = theil_decompose(vals, ["A"] * 4)
        assert tb == pytest.approx(0.0, abs=EPS)
        assert tw == pytest.approx(t, abs=EPS)

    def test_homogeneous_groups_pure_between(self):
        # Each group internally uniform: T_within should be 0,
        # T_between picks up the cross-group inequality.
        vals = [4.0, 4.0, 4.0, 8.0, 8.0, 8.0]
        groups = ["A", "A", "A", "B", "B", "B"]
        t, tb, tw = theil_decompose(vals, groups)
        assert tw == pytest.approx(0.0, abs=EPS)
        assert tb == pytest.approx(t, abs=EPS)

    def test_weighted_additivity(self):
        vals = [4.5, 5.0, 5.5, 6.0, 6.5]
        groups = ["A", "A", "B", "B", "B"]
        weights = [10.0, 5.0, 3.0, 8.0, 2.0]
        t, tb, tw = theil_decompose(vals, groups, weights=weights)
        assert t == pytest.approx(tb + tw, abs=EPS)

    def test_weights_none_equals_uniform(self):
        vals = [4.5, 5.0, 5.5, 6.0]
        groups = ["A", "B", "A", "B"]
        a = theil_decompose(vals, groups)
        b = theil_decompose(vals, groups, weights=[1.0] * 4)
        for x, y in zip(a, b):
            assert x == pytest.approx(y, abs=EPS)

    def test_short_input_returns_zeros(self):
        assert theil_decompose([], []) == (0.0, 0.0, 0.0)
        assert theil_decompose([5.0], ["A"]) == (0.0, 0.0, 0.0)


class TestRealDataSanity:
    """Integration tests against the committed CSV outputs."""

    def test_anos_iniciais_check_sum(self):
        path = ROOT / "data" / "processed" / "theil_ideb_anos_iniciais.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        assert len(rows) >= 5, "expected at least 5 years of Theil decomposition"
        for r in rows:
            cs = float(r["check_sum"])
            assert abs(cs) < 1e-6, f"row {r['year']}: check_sum {cs} not within tolerance"

    def test_anos_finais_check_sum(self):
        path = ROOT / "data" / "processed" / "theil_ideb_anos_finais.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        assert len(rows) >= 5
        for r in rows:
            assert abs(float(r["check_sum"])) < 1e-6

    def test_components_check_sum(self):
        path = ROOT / "data" / "processed" / "theil_components.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        assert len(rows) >= 9 * 3  # 9 years × 3 components
        for r in rows:
            assert abs(float(r["check_sum"])) < 1e-6

    def test_within_dominates_in_anos_iniciais(self):
        """Headline finding bound bilaterally: share_within ∈ [55%, 75%] em todo
        ano. A narrativa pública (docs/achados.md) diz "entre 59% e 73%"; este
        bound buffereia ~3pp dos extremos observados (0.59 mínimo, 0.73 máximo
        arredondado) — apertado o suficiente pra falhar se o número cair pra
        51% (atual `> 0.5` deixava passar), com folga pra variação ano-a-ano."""
        path = ROOT / "data" / "processed" / "theil_ideb_anos_iniciais.csv"
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        for r in rows:
            sw = float(r["share_within"])
            assert 0.55 <= sw <= 0.75, (
                f"year {r['year']}: share_within {sw:.0%} fora de [55%, 75%], "
                "guarda-corpo do achado central quebrou"
            )
