"""Theil-T entropy index and additive decomposition.

Promoted from `rio-edu-lab/analysis/_theil.py`. Single source of truth
for the inequality stats used across all ACEC-Hub products. The
`rio-edu-lab` repo's pipeline scripts will be migrated to import from
here in a follow-up.

Decomposição aditiva por grupos g:

    T_total   = Σ_i (w_i / W) · (y_i / ȳ_w) · ln(y_i / ȳ_w)
    T_between = Σ_g (W_g / W) · (ȳ_g / ȳ) · ln(ȳ_g / ȳ)
    T_within  = Σ_g (W_g / W) · (ȳ_g / ȳ) · T_g
    T_total   = T_between + T_within           (exato)

Conventions: y_i positive; non-positive values dropped silently to
avoid log domain errors.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Sequence


def _clean(
    values: Sequence[float],
    weights: Sequence[float] | None = None,
) -> tuple[list[float], list[float]]:
    if weights is None:
        weights = [1.0] * len(values)
    out_v: list[float] = []
    out_w: list[float] = []
    for v, w in zip(values, weights, strict=False):
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

    With weights all 1 (default), reduces to the unit-weighted form:
    T = (1/N) Σ_i (y_i / ȳ) · ln(y_i / ȳ).

    Returns 0.0 if fewer than 2 strictly-positive values survive.
    """
    v, w = _clean(values, weights)
    if len(v) < 2:
        return 0.0
    W = sum(w)
    mean = sum(vi * wi for vi, wi in zip(v, w, strict=True)) / W
    return sum(
        (wi / W) * (vi / mean) * math.log(vi / mean)
        for vi, wi in zip(v, w, strict=True)
    )


def theil_decompose(
    values: Sequence[float],
    groups: Sequence[str],
    weights: Sequence[float] | None = None,
) -> tuple[float, float, float]:
    """Additive Theil-T decomposition into (T_total, T_between, T_within).

    The identity T_total == T_between + T_within holds exactly in real
    arithmetic and within float precision (~1e-12).
    """
    if weights is None:
        weights = [1.0] * len(values)
    triples = [
        (vi, gi, wi)
        for vi, gi, wi in zip(values, groups, weights, strict=False)
        if vi is not None and wi is not None and vi > 0 and wi > 0
    ]
    if len(triples) < 2:
        return 0.0, 0.0, 0.0

    v = [t[0] for t in triples]
    g = [t[1] for t in triples]
    w = [t[2] for t in triples]
    W = sum(w)
    mean = sum(vi * wi for vi, wi in zip(v, w, strict=True)) / W

    by_group: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    for vi, gi, wi in zip(v, g, w, strict=True):
        by_group[gi][0].append(vi)
        by_group[gi][1].append(wi)

    t_total = theil_t(v, w)
    t_between = 0.0
    t_within = 0.0
    for _, (gv, gw) in by_group.items():
        Wg = sum(gw)
        if Wg <= 0:
            continue
        mug = sum(vi * wi for vi, wi in zip(gv, gw, strict=True)) / Wg
        weight = (Wg / W) * (mug / mean)
        if mug > 0 and weight > 0:
            t_between += weight * math.log(mug / mean)
            t_within += weight * theil_t(gv, gw)
    return t_total, t_between, t_within


def theil_decompose_nested(
    values: Sequence[float],
    inner_groups: Sequence[str],
    outer_groups: Sequence[str],
    weights: Sequence[float] | None = None,
) -> dict[str, float]:
    """Three-level Theil decomposition for nested groupings.

    For ACEC-Hub THESHA-Rio: bairros nested in RAs nested in APs.
    Returns:
      - T_total            — full inequality across all units
      - T_between_outer    — inequality between outer (e.g. APs)
      - T_within_outer     — inequality within outer; further split
      - T_between_inner    — inequality between inner-within-outer
                             (e.g. RAs within their AP)
      - T_within_inner     — inequality within inner-within-outer
                             (e.g. bairros within their RA)

    Identity (exact in real arithmetic):
        T_total = T_between_outer + T_between_inner + T_within_inner

    All groups must align element-wise with values.
    """
    if weights is None:
        weights = [1.0] * len(values)

    # Total Theil
    t_total = theil_t(values, weights)

    # Between outer = inequality of outer-group means
    t_outer, t_between_outer, t_within_outer = theil_decompose(values, outer_groups, weights)

    # Within each outer, decompose further by inner.
    # T_between_inner = sum over outer g of (share_g) * (theil_between of inner-in-g)
    # T_within_inner  = sum over outer g of (share_g) * (theil_within of inner-in-g) summed
    if not values:
        return {
            "T_total": 0.0,
            "T_between_outer": 0.0,
            "T_within_outer": 0.0,
            "T_between_inner": 0.0,
            "T_within_inner": 0.0,
        }

    pairs = [
        (vi, ig, og, wi)
        for vi, ig, og, wi in zip(values, inner_groups, outer_groups, weights, strict=True)
        if vi is not None and wi is not None and vi > 0 and wi > 0
    ]
    if len(pairs) < 2:
        return {
            "T_total": 0.0,
            "T_between_outer": 0.0,
            "T_within_outer": 0.0,
            "T_between_inner": 0.0,
            "T_within_inner": 0.0,
        }
    v = [p[0] for p in pairs]
    ig = [p[1] for p in pairs]
    og = [p[2] for p in pairs]
    w = [p[3] for p in pairs]
    W = sum(w)
    mean = sum(vi * wi for vi, wi in zip(v, w, strict=True)) / W

    # Group by outer
    by_outer: dict[str, list[tuple[float, str, float]]] = defaultdict(list)
    for vi, ig_i, og_i, wi in zip(v, ig, og, w, strict=True):
        by_outer[og_i].append((vi, ig_i, wi))

    t_between_inner = 0.0
    t_within_inner = 0.0
    for og_label, items in by_outer.items():
        gv = [it[0] for it in items]
        gig = [it[1] for it in items]
        gw = [it[2] for it in items]
        Wg = sum(gw)
        if Wg <= 0:
            continue
        mug = sum(vi * wi for vi, wi in zip(gv, gw, strict=True)) / Wg
        share_outer = (Wg / W) * (mug / mean)
        # Decompose inner within this outer
        _, tb_inner, tw_inner = theil_decompose(gv, gig, gw)
        t_between_inner += share_outer * tb_inner
        t_within_inner += share_outer * tw_inner

    return {
        "T_total": t_total,
        "T_between_outer": t_between_outer,
        "T_within_outer": t_within_outer,
        "T_between_inner": t_between_inner,
        "T_within_inner": t_within_inner,
    }


__all__ = ["theil_t", "theil_decompose", "theil_decompose_nested"]
