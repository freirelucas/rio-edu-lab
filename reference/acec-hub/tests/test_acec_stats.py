"""Tests for acec.stats canonical implementations.

Covers the original Theil-T primitives + the regression/correlation
primitives promoted in v0.7 from rio-edu-lab/analysis/29_vuln_edu.py.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from acec.stats import (
    ols_simple,
    pearson,
    quintile_grid,
    spearman,
    theil_decompose,
    theil_decompose_nested,
    theil_t,
)

EPS = 1e-12


class TestTheilT:
    def test_perfect_equality_is_zero(self):
        assert theil_t([1.0, 1.0, 1.0]) == pytest.approx(0.0, abs=EPS)

    def test_short_input_returns_zero(self):
        assert theil_t([]) == 0.0
        assert theil_t([5.0]) == 0.0

    def test_known_distribution(self):
        # 2-point [1, 3], unit weights:
        expected = 0.25 * math.log(0.5) + 0.75 * math.log(1.5)
        assert theil_t([1.0, 3.0]) == pytest.approx(expected, abs=1e-9)

    def test_drops_nonpositive_values(self):
        assert theil_t([5.0, -1.0, 5.0, 0.0]) == pytest.approx(0.0, abs=EPS)

    def test_weights_none_equals_uniform(self):
        v = [4.0, 5.0, 6.0]
        assert theil_t(v) == pytest.approx(theil_t(v, [1, 1, 1]), abs=EPS)


class TestTheilDecompose:
    def test_additive_identity(self):
        v = [4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
        g = ["A", "A", "A", "B", "B", "B"]
        t, tb, tw = theil_decompose(v, g)
        assert t == pytest.approx(tb + tw, abs=EPS)

    def test_homogeneous_groups_pure_between(self):
        v = [4.0, 4.0, 8.0, 8.0]
        g = ["A", "A", "B", "B"]
        t, tb, tw = theil_decompose(v, g)
        assert tw == pytest.approx(0.0, abs=EPS)
        assert tb == pytest.approx(t, abs=EPS)


class TestTheilDecomposeNested:
    def test_three_level_identity(self):
        # 4 inner groups (RAs) in 2 outer groups (APs)
        v = [4.0, 5.0, 5.0, 6.0, 7.0, 7.0, 8.0, 9.0]
        inner = ["I", "I", "II", "II", "III", "III", "IV", "IV"]
        outer = ["A", "A", "A", "A", "B", "B", "B", "B"]
        d = theil_decompose_nested(v, inner, outer)
        # Three-level identity: T_total = T_between_outer + T_between_inner + T_within_inner
        identity_check = (
            d["T_total"] - d["T_between_outer"] - d["T_between_inner"] - d["T_within_inner"]
        )
        assert abs(identity_check) < 1e-10

    def test_no_inner_variation(self):
        # Each inner group internally uniform — T_within_inner should be 0.
        v = [5.0, 5.0, 7.0, 7.0]
        inner = ["I", "I", "II", "II"]
        outer = ["A", "A", "B", "B"]
        d = theil_decompose_nested(v, inner, outer)
        assert d["T_within_inner"] == pytest.approx(0.0, abs=1e-10)


class TestPearson:
    def test_perfect_positive(self):
        assert pearson([1, 2, 3, 4], [2, 4, 6, 8]) == pytest.approx(1.0, abs=EPS)

    def test_perfect_negative(self):
        assert pearson([1, 2, 3, 4], [8, 6, 4, 2]) == pytest.approx(-1.0, abs=EPS)

    def test_centered_orthogonal_is_zero(self):
        # Two centered orthogonal vectors -> r = 0 exactly
        x = [-2.0, -1.0, 0.0, 1.0, 2.0]
        y = [2.0, -1.0, -2.0, -1.0, 2.0]   # symmetric quadratic-ish
        assert pearson(x, y) == pytest.approx(0.0, abs=EPS)


class TestSpearman:
    def test_perfect_monotone(self):
        # Monotone but nonlinear: pearson < 1, spearman == 1
        x = [1, 2, 3, 4, 5]
        y = [1, 4, 9, 16, 25]
        assert spearman(x, y) == pytest.approx(1.0, abs=EPS)

    def test_handles_ties_average_rank(self):
        x = [1, 2, 2, 3]
        y = [1, 2, 2, 3]
        # Identical ties should give spearman == 1
        assert spearman(x, y) == pytest.approx(1.0, abs=EPS)


class TestOLSSimple:
    def test_recovers_known_line(self):
        rng = np.random.default_rng(seed=42)
        x = np.linspace(0, 10, 100)
        y = 3.0 + 2.0 * x + rng.normal(scale=0.01, size=len(x))
        out = ols_simple(x, y)
        assert out["slope"] == pytest.approx(2.0, abs=1e-3)
        assert out["intercept"] == pytest.approx(3.0, abs=1e-2)
        assert out["r2"] > 0.999
        assert out["n"] == 100

    def test_perfect_line_r2_one(self):
        x = [1.0, 2.0, 3.0, 4.0]
        y = [2.0, 4.0, 6.0, 8.0]
        out = ols_simple(x, y)
        assert out["slope"] == pytest.approx(2.0, abs=EPS)
        assert out["intercept"] == pytest.approx(0.0, abs=EPS)
        assert out["r2"] == pytest.approx(1.0, abs=EPS)

    def test_degenerate_n_below_2(self):
        out = ols_simple([1.0], [2.0])
        assert math.isnan(out["slope"])
        assert out["n"] == 1


class TestQuintileGrid:
    def test_diagonal_perfect_when_x_eq_y(self):
        x = list(range(100))
        y = list(range(100))
        out = quintile_grid(x, y, k=5)
        assert out["n_total"] == 100
        assert out["n_diagonal"] == 100
        assert out["share_diagonal"] == pytest.approx(1.0, abs=EPS)

    def test_anti_diagonal_when_x_eq_neg_y(self):
        x = list(range(100))
        y = list(range(99, -1, -1))
        out = quintile_grid(x, y, k=5)
        # With k=5, the middle quintile is shared by x and -y, so n_diagonal
        # equals the size of the middle bin (20). All other diagonal cells
        # must be zero.
        matrix = out["matrix"]
        assert matrix[2][2] == 20
        assert matrix[0][0] == 0
        assert matrix[4][4] == 0
        # Anti-diagonal carries the rest
        assert matrix[0][4] == 20
        assert matrix[4][0] == 20

    def test_matrix_sums_to_n(self):
        rng = np.random.default_rng(seed=7)
        x = rng.normal(size=200)
        y = x + rng.normal(scale=0.5, size=200)
        out = quintile_grid(x, y, k=5)
        total = sum(sum(row) for row in out["matrix"])
        assert total == out["n_total"] == 200
