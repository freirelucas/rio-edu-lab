"""Lightweight regression and correlation primitives used across the lab.

Promoted from `rio-edu-lab/analysis/29_vuln_edu.py` (VULN-EDU v0.1) so new
replication scripts in v0.7+ can import a single canonical implementation
instead of redefining OLS / Spearman / quintile grids inline. Numpy-only,
no scipy or statsmodels dependency.

Functions:
  - pearson(x, y)
  - spearman(x, y)
  - ols_simple(x, y)            -> dict (slope, intercept, R², SE, t)
  - quintile_grid(x, y, k=5)    -> dict with k×k count matrix + diagonal
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def _to_array(a: Sequence[float]) -> np.ndarray:
    return np.asarray(a, dtype=float)


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    """Pearson product-moment correlation between x and y."""
    x_a, y_a = _to_array(x), _to_array(y)
    return float(np.corrcoef(x_a, y_a)[0, 1])


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """Spearman rank correlation between x and y (ties: average rank)."""
    x_a, y_a = _to_array(x), _to_array(y)
    rx = _rankdata(x_a)
    ry = _rankdata(y_a)
    return float(np.corrcoef(rx, ry)[0, 1])


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average-rank ties handling (equivalent to scipy.stats.rankdata default)."""
    order = a.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(a) + 1)
    # Average ranks of tied values
    _, inv, counts = np.unique(a, return_inverse=True, return_counts=True)
    for idx, cnt in enumerate(counts):
        if cnt > 1:
            mask = inv == idx
            ranks[mask] = ranks[mask].mean()
    return ranks


def ols_simple(x: Sequence[float], y: Sequence[float]) -> dict:
    """Univariate ordinary least squares: y = a + b*x.

    Returns dict with intercept, slope, r2, se_slope, t_slope, n. NaN-safe
    for degenerate inputs (n < 3 or zero variance in x).
    """
    x_a, y_a = _to_array(x), _to_array(y)
    n = len(x_a)
    if n < 2:
        return {
            "intercept": math.nan,
            "slope": math.nan,
            "r2": math.nan,
            "se_slope": math.nan,
            "t_slope": math.nan,
            "n": n,
        }
    xbar, ybar = x_a.mean(), y_a.mean()
    sxx = float(((x_a - xbar) ** 2).sum())
    sxy = float(((x_a - xbar) * (y_a - ybar)).sum())
    if sxx == 0:
        return {
            "intercept": float(ybar),
            "slope": math.nan,
            "r2": math.nan,
            "se_slope": math.nan,
            "t_slope": math.nan,
            "n": n,
        }
    b = sxy / sxx
    a = ybar - b * xbar
    yhat = a + b * x_a
    ss_res = float(((y_a - yhat) ** 2).sum())
    ss_tot = float(((y_a - ybar) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    s2 = ss_res / max(n - 2, 1)
    se_b = math.sqrt(s2 / sxx) if sxx > 0 else math.nan
    t_stat = b / se_b if se_b > 0 else math.nan
    return {
        "intercept": float(a),
        "slope": float(b),
        "r2": float(r2),
        "se_slope": float(se_b),
        "t_slope": float(t_stat),
        "n": int(n),
    }


def quintile_grid(
    x: Sequence[float],
    y: Sequence[float],
    k: int = 5,
) -> dict:
    """Cross-tabulate k-quantiles of x against k-quantiles of y.

    Returns a dict with the k×k count matrix, diagonal count (concordant
    quantiles), and total. Useful for measuring rank-concordance between
    two distributions without committing to a parametric model.
    """
    import pandas as pd  # local import; pandas is optional for callers

    x_a, y_a = _to_array(x), _to_array(y)
    if len(x_a) < k:
        return {
            "matrix": [[0] * k for _ in range(k)],
            "rows_quantiles": [f"Q{i+1}" for i in range(k)],
            "cols_quantiles": [f"Q{i+1}" for i in range(k)],
            "n_total": int(len(x_a)),
            "n_diagonal": 0,
            "share_diagonal": 0.0,
        }
    labels = [f"Q{i+1}" for i in range(k)]
    qx = pd.qcut(x_a, k, labels=labels, duplicates="drop")
    qy = pd.qcut(y_a, k, labels=labels, duplicates="drop")
    grid = pd.crosstab(qx, qy).reindex(index=labels, columns=labels, fill_value=0)
    grid = grid.astype(int)
    diag = sum(grid.iloc[i, i] for i in range(k))
    total = int(grid.values.sum())
    return {
        "matrix": grid.values.tolist(),
        "rows_quantiles": labels,
        "cols_quantiles": labels,
        "n_total": total,
        "n_diagonal": int(diag),
        "share_diagonal": float(diag / total) if total else 0.0,
    }


__all__ = ["pearson", "spearman", "ols_simple", "quintile_grid"]
