"""Canonical Theil-T implementation for the lab.

Extracted from the duplicated copies in 10_theil_ideb.py, 15_anos_finais.py,
16_theil_weighted.py, 17_theil_components.py. Future refactor will migrate
those scripts to import from here. For now, this module is the single
testable source of truth, exercised by tests/test_theil.py.

Definitions:

    T_total = Σ_i (w_i / W) · (y_i / ȳ_w) · ln(y_i / ȳ_w)

where w_i are nonnegative weights, W = Σ w_i, and ȳ_w = (Σ w_i y_i) / W.
With weights all 1 (default), this reduces to the standard unit-weighted
Theil-T:

    T_total = (1/N) Σ_i (y_i / ȳ) · ln(y_i / ȳ)

Decomposition by groups g (e.g. RAs):

    T_between = Σ_g (W_g / W) · (ȳ_g / ȳ) · ln(ȳ_g / ȳ)
    T_within  = Σ_g (W_g / W) · (ȳ_g / ȳ) · T_g
    T_total   = T_between + T_within           (exact)

Conventions: y_i must be positive. Zero or negative values are silently
dropped (with a paired weight) to avoid log domain errors. A pair with
w_i ≤ 0 is also dropped. Sequences with fewer than 2 surviving points
return T_total = 0.0 (all decomposition components 0).
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Iterable, Sequence


def _clean(
    values: Sequence[float],
    weights: Sequence[float] | None = None,
) -> tuple[list[float], list[float]]:
    if weights is None:
        weights = [1.0] * len(values)
    out_v: list[float] = []
    out_w: list[float] = []
    for v, w in zip(values, weights):
        if v is None or w is None:
            continue
        if not (v > 0 and w > 0):
            continue
        out_v.append(float(v))
        out_w.append(float(w))
    return out_v, out_w


def theil_t(
    values: Sequence[float],
    weights: Sequence[float] | None = None,
) -> float:
    """Theil-T entropy index (a.k.a. GE(1)).

    Returns 0.0 if fewer than 2 strictly-positive values survive cleaning.
    """
    v, w = _clean(values, weights)
    if len(v) < 2:
        return 0.0
    W = sum(w)
    mean = sum(vi * wi for vi, wi in zip(v, w)) / W
    return sum(
        (wi / W) * (vi / mean) * math.log(vi / mean)
        for vi, wi in zip(v, w)
    )


def theil_decompose(
    values: Sequence[float],
    groups: Sequence[str],
    weights: Sequence[float] | None = None,
) -> tuple[float, float, float]:
    """Additive Theil-T decomposition into (T_total, T_between, T_within).

    The identity T_total == T_between + T_within holds exactly in real
    arithmetic and within float precision (~1e-12 typically) here.

    Returns (0, 0, 0) if fewer than 2 strictly-positive values survive.
    """
    if weights is None:
        weights = [1.0] * len(values)
    triples = [
        (vi, gi, wi)
        for vi, gi, wi in zip(values, groups, weights)
        if vi is not None and wi is not None and vi > 0 and wi > 0
    ]
    if len(triples) < 2:
        return 0.0, 0.0, 0.0

    v = [t[0] for t in triples]
    g = [t[1] for t in triples]
    w = [t[2] for t in triples]
    W = sum(w)
    mean = sum(vi * wi for vi, wi in zip(v, w)) / W

    by_group: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    for vi, gi, wi in zip(v, g, w):
        by_group[gi][0].append(vi)
        by_group[gi][1].append(wi)

    t_total = theil_t(v, w)
    t_between = 0.0
    t_within = 0.0
    for _, (gv, gw) in by_group.items():
        Wg = sum(gw)
        if Wg <= 0:
            continue
        mug = sum(vi * wi for vi, wi in zip(gv, gw)) / Wg
        weight = (Wg / W) * (mug / mean)
        if mug > 0 and weight > 0:
            t_between += weight * math.log(mug / mean)
            t_within += weight * theil_t(gv, gw)
    return t_total, t_between, t_within


__all__ = ["theil_t", "theil_decompose"]
