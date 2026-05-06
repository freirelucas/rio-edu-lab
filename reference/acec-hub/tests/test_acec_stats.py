"""Tests for acec.stats canonical Theil implementation.

Mirrors the lab's tests/test_theil.py against the production-package
import path. Future change: lab pipeline will migrate to import from
acec.stats so the lab tests + these tests converge.
"""

from __future__ import annotations

import math

import pytest

from acec.stats import theil_decompose, theil_decompose_nested, theil_t

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
