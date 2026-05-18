"""VULN-EDU — cruzamento vulnerabilidade socioeconômica (IDS) × IDEB por bairro.

Operacionaliza a ideia central de Reardon (2011) "The widening academic-
achievement gap between the rich and the poor": medir empiricamente o
gradiente entre posição socioeconômica e desempenho educacional. No
nosso caso, IDS por bairro (proxy SES composto, Censo 2010 ajustado pelo
IPP) cruzado com IDEB séries iniciais por bairro (2023).

Pipeline:

  1. Carrega 10.504 setores IDS (Sessão 28) → agrega para bairro via
     mediana (robusta a outliers de bairros heterogêneos).
  2. Carrega IDEB 2023 por bairro (Sessão 06).
  3. Inner-join por nome (149/152 bairros casam).
  4. Computa Pearson e Spearman, regressão linear simples.
  5. Quintis cruzados (5×5 IDS × IDEB).
  6. 4-quadrant assignment: alta/baixa IDS × alta/baixa IDEB (mediana).
  7. Score VULN composto = -z(IDS) + -z(IDEB) — bairros mais
     vulneráveis (alta vuln, baixo desempenho) ranqueiam alto.

Outputs:
  - data/processed/vuln_edu_bairros.csv  (1 linha por bairro)
  - data/processed/vuln_edu_summary.json (estatísticas agregadas)

Uso:
  python3 analysis/29_vuln_edu.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IDS_CSV = ROOT / "data" / "raw" / "geo" / "ids_setores.csv"
IDEB_LONG = ROOT / "data" / "processed" / "ideb_bairros.csv"
OUT_CSV = ROOT / "data" / "processed" / "vuln_edu_bairros.csv"
OUT_JSON = ROOT / "data" / "processed" / "vuln_edu_summary.json"

IDEB_YEAR = 2023
SUB_INDICATORS = [
    "I_AGUA_ADEQUADA",
    "I_ESGOTO_ADEQUADO",
    "I_LIXO_ADEQUADO",
    "I_MEDBANH_PES",
    "I_ANALFAB_10A14",
    "I_RENDARESP_POS_SM",
    "I_RENDARESP_POS_ATE2SM",
    "I_RENDARESP_P_MAISDE10SM",
]


def load_ids_by_bairro() -> pd.DataFrame:
    """Aggregate IDS by NM_BAIRRO via median (robust to within-bairro heterogeneity)."""
    df = pd.read_csv(IDS_CSV)
    df["bairro"] = df["NM_BAIRRO"].astype(str).str.strip()
    df = df[df["bairro"] != ""].copy()
    n_setores_total = len(df)

    grouped = (
        df.groupby("bairro")
          .agg(
              n_setores=("IDS", "size"),
              ids_median=("IDS", "median"),
              ids_mean=("IDS", "mean"),
              ids_p25=("IDS", lambda s: s.quantile(0.25)),
              ids_p75=("IDS", lambda s: s.quantile(0.75)),
              **{f"{k.lower()}_median": (k, "median") for k in SUB_INDICATORS},
          )
          .reset_index()
    )
    grouped["ids_iqr"] = grouped["ids_p75"] - grouped["ids_p25"]
    print(f"  {n_setores_total} setores → {len(grouped)} bairros")
    return grouped


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    return float(np.corrcoef(x, y)[0, 1])


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    return pearson(rx, ry)


def ols_simple(x: np.ndarray, y: np.ndarray) -> dict:
    """Ordinary least squares IDEB ~ a + b * IDS."""
    n = len(x)
    xbar, ybar = x.mean(), y.mean()
    sxx = float(((x - xbar) ** 2).sum())
    sxy = float(((x - xbar) * (y - ybar)).sum())
    b = sxy / sxx
    a = ybar - b * xbar
    yhat = a + b * x
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - ybar) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    # standard error of slope
    s2 = ss_res / max(n - 2, 1)
    se_b = math.sqrt(s2 / sxx) if sxx > 0 else math.nan
    t_stat = b / se_b if se_b > 0 else math.nan
    return {
        "intercept": a,
        "slope": b,
        "r2": r2,
        "se_slope": se_b,
        "t_slope": t_stat,
        "n": n,
    }


def quadrants(df: pd.DataFrame) -> pd.DataFrame:
    ids_med = df["ids_median"].median()
    ideb_med = df["ideb"].median()

    def assign(row):
        hi_ids = row["ids_median"] >= ids_med
        hi_ideb = row["ideb"] >= ideb_med
        if hi_ids and hi_ideb:
            return "Q1: alto IDS · alto IDEB"
        if not hi_ids and hi_ideb:
            return "Q2: baixo IDS · alto IDEB (resiliente)"
        if hi_ids and not hi_ideb:
            return "Q3: alto IDS · baixo IDEB (sub-performance)"
        return "Q4: baixo IDS · baixo IDEB (vulnerável)"

    df["quadrante"] = df.apply(assign, axis=1)
    df["_ids_med_ref"] = ids_med
    df["_ideb_med_ref"] = ideb_med
    return df


def vuln_score(df: pd.DataFrame) -> pd.DataFrame:
    """VULN score = média de -z(IDS) e -z(IDEB). Maior = mais vulnerável."""
    zids = (df["ids_median"] - df["ids_median"].mean()) / df["ids_median"].std(ddof=0)
    zideb = (df["ideb"] - df["ideb"].mean()) / df["ideb"].std(ddof=0)
    df["vuln_score"] = ((-zids) + (-zideb)) / 2
    return df


def quintile_grid(df: pd.DataFrame) -> dict:
    """Cross-tabulate IDS quintiles × IDEB quintiles → 5x5 count matrix."""
    df = df.copy()
    df["q_ids"] = pd.qcut(df["ids_median"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
    df["q_ideb"] = pd.qcut(df["ideb"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
    grid = pd.crosstab(df["q_ids"], df["q_ideb"]).astype(int)
    # Diagonal share (concordance): bairros where IDS and IDEB quintiles match
    diag = sum(grid.iloc[i, i] for i in range(5))
    return {
        "matrix": grid.values.tolist(),
        "rows_ids_quintiles": grid.index.tolist(),
        "cols_ideb_quintiles": grid.columns.tolist(),
        "n_total": int(grid.values.sum()),
        "n_diagonal": int(diag),
        "share_diagonal": float(diag / grid.values.sum()),
    }


def main() -> int:
    if not (IDS_CSV.exists() and IDEB_LONG.exists()):
        print("missing inputs; run sessions 06 + 28 first")
        return 1

    print(f"loading {IDS_CSV.relative_to(ROOT)}")
    ids = load_ids_by_bairro()

    print(f"loading {IDEB_LONG.relative_to(ROOT)} (year={IDEB_YEAR})")
    ideb = pd.read_csv(IDEB_LONG)
    ideb["bairro"] = ideb["bairro"].astype(str).str.strip()
    ideb_y = ideb[ideb["year"] == IDEB_YEAR][["ap", "ra", "bairro", "ideb"]].dropna()
    print(f"  {len(ideb_y)} bairros com IDEB {IDEB_YEAR}")

    df = ideb_y.merge(ids, on="bairro", how="inner")
    n_matched = len(df)
    n_dropped_ideb = len(ideb_y) - n_matched
    n_only_in_ids = len(ids) - n_matched
    print(f"  matched {n_matched} bairros "
          f"(droppped {n_dropped_ideb} IDEB sem IDS; {n_only_in_ids} IDS sem IDEB)")

    if n_matched < 50:
        print("too few matches for analysis", file=sys.stderr)
        return 1

    df = quadrants(df).pipe(vuln_score)

    # Correlations + regression
    x = df["ids_median"].to_numpy()
    y = df["ideb"].to_numpy()
    r_p = pearson(x, y)
    r_s = spearman(x, y)
    ols = ols_simple(x, y)
    grid = quintile_grid(df[["ids_median", "ideb"]])

    # AP-level aggregation
    ap_summary = (
        df.groupby("ap")
          .agg(n=("bairro", "size"),
               ids_med=("ids_median", "median"),
               ideb_med=("ideb", "median"),
               vuln_med=("vuln_score", "median"))
          .round(3)
          .reset_index()
          .sort_values("vuln_med", ascending=False)
    )

    # Quadrant counts
    quad_counts = df["quadrante"].value_counts().sort_index().to_dict()

    # Top vulnerable
    top_vuln = (
        df.sort_values("vuln_score", ascending=False)
          [["bairro", "ra", "ap", "ids_median", "ideb", "vuln_score", "quadrante"]]
          .head(15)
    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_out = df.drop(columns=["_ids_med_ref", "_ideb_med_ref"]).copy()
    df_out = df_out.sort_values("vuln_score", ascending=False)
    df_out.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_CSV.relative_to(ROOT)} ({len(df_out)} bairros × {len(df_out.columns)} cols)")

    summary = {
        "ideb_year": IDEB_YEAR,
        "ids_source": "Censo 2010 (IPP / data.rio IDS_RM_2010)",
        "n_bairros_matched": int(n_matched),
        "n_bairros_ideb_dropped": int(n_dropped_ideb),
        "n_bairros_only_in_ids": int(n_only_in_ids),
        "correlation": {
            "pearson_ids_ideb": round(r_p, 4),
            "spearman_ids_ideb": round(r_s, 4),
        },
        "ols_ideb_on_ids": {
            "intercept": round(ols["intercept"], 4),
            "slope": round(ols["slope"], 4),
            "r2": round(ols["r2"], 4),
            "se_slope": round(ols["se_slope"], 4),
            "t_slope": round(ols["t_slope"], 4),
            "interpretation": (
                f"+0.1 IDS ↔ {ols['slope']*0.1:+.3f} IDEB (séries iniciais 2023)"
            ),
        },
        "quintile_grid": grid,
        "quadrants": {
            "ids_median_threshold": round(float(df["ids_median"].median()), 4),
            "ideb_median_threshold": round(float(df["ideb"].median()), 4),
            "counts": quad_counts,
        },
        "by_ap": ap_summary.to_dict("records"),
        "top_15_vulneraveis": top_vuln.round(4).to_dict("records"),
    }

    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")

    # Console summary
    print("\n=== headline ===")
    print(f"  Pearson(IDS, IDEB) = {r_p:+.3f}   Spearman = {r_s:+.3f}")
    print(f"  OLS: IDEB = {ols['intercept']:.2f} + {ols['slope']:.2f}·IDS   "
          f"R² = {ols['r2']:.2f}  (n={ols['n']})")
    print(f"  +0.1 IDS ↔ {ols['slope']*0.1:+.3f} pontos de IDEB")
    print(f"\n=== quadrantes (medianas: IDS={summary['quadrants']['ids_median_threshold']:.3f}, "
          f"IDEB={summary['quadrants']['ideb_median_threshold']:.2f}) ===")
    for q, n in quad_counts.items():
        print(f"  {q}: {n}")
    print("\n=== concordância quintis ===")
    print(f"  diagonal (5×5) = {grid['n_diagonal']}/{grid['n_total']} = "
          f"{grid['share_diagonal']:.0%}")
    print("\n=== top 5 mais vulneráveis ===")
    for r in top_vuln.head(5).to_dict("records"):
        print(f"  {r['bairro']:30s} (RA {r['ra']:18s}) IDS={r['ids_median']:.3f} "
              f"IDEB={r['ideb']:.2f}  score={r['vuln_score']:+.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
