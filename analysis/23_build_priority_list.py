"""Cross PM-12 SAMI + FUN-Rio Δ to rank bairros by need.

Combines two orthogonal signals from the MVP-1:

  - SAMI (PM-12, relatório 13)  — desvio da lei de escala. Negativo =
    bairro tem MENOS escolas que o esperado pelo seu volume de matrícula
    (sub-servido em infraestrutura).
  - Δ médio (FUN-Rio, relatório 12) — média da queda 5º→9º entre
    pseudocoortes. Negativo = a turma piora ao longo do fundamental.

Bairros com SAMI negativo E Δ negativo são duplamente prioritários: têm
infraestrutura defasada e perdem qualidade educacional ao longo do ciclo.

Outputs:
  - data/processed/bairros_prioritarios.csv — long: bairro, ap, sami, delta_mean,
    sami_z, delta_z, priority_score, rank.
  - data/processed/bairros_prioritarios_top20.csv — copy do top 20 para easy
    consumption pelo site.

Usage:
  python3 analysis/23_build_priority_list.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PM12_CSV = ROOT / "data" / "processed" / "pm12_scaling.csv"
FUN_TRANS = ROOT / "data" / "processed" / "fun_rio_transitions.csv"

OUT = ROOT / "data" / "processed" / "bairros_prioritarios.csv"
OUT_TOP = ROOT / "data" / "processed" / "bairros_prioritarios_top20.csv"


def main() -> int:
    if not PM12_CSV.exists() or not FUN_TRANS.exists():
        print("missing PM-12 or FUN-Rio CSVs; run sessions 14 and 13 first")
        return 1

    pm = pd.read_csv(PM12_CSV)[["bairro", "ap", "ra", "matriculas", "escolas", "ideb", "sami"]]
    fun = pd.read_csv(FUN_TRANS)
    fun_by_bairro = fun.groupby("bairro", as_index=False).agg(
        delta_mean=("delta", "mean"),
        delta_n=("delta", "count"),
        ideb5_mean=("ideb_5", "mean"),
        ideb9_mean=("ideb_9", "mean"),
    )

    merged = pm.merge(fun_by_bairro, on="bairro", how="inner").dropna(
        subset=["sami", "delta_mean"]
    )
    print(f"matched {len(merged)} bairros with both PM-12 SAMI and FUN-Rio Δ")

    # z-scores; negate so that "more priority" → larger.
    merged["sami_z"] = (merged["sami"] - merged["sami"].mean()) / merged["sami"].std()
    merged["delta_z"] = (
        (merged["delta_mean"] - merged["delta_mean"].mean()) / merged["delta_mean"].std()
    )
    merged["priority_score"] = -(merged["sami_z"] + merged["delta_z"])

    merged = merged.sort_values("priority_score", ascending=False).reset_index(drop=True)
    merged.insert(0, "rank", merged.index + 1)

    # Round numerics for cleaner CSV
    for col in ("sami", "sami_z", "delta_mean", "delta_z", "priority_score",
                "ideb5_mean", "ideb9_mean", "ideb"):
        if col in merged.columns:
            merged[col] = merged[col].round(3)

    cols = [
        "rank", "bairro", "ap", "ra",
        "matriculas", "escolas", "ideb",
        "sami", "delta_mean", "delta_n",
        "ideb5_mean", "ideb9_mean",
        "sami_z", "delta_z", "priority_score",
    ]
    merged = merged[cols]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT, index=False)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(merged)} bairros)")

    top20 = merged.head(20)
    top20.to_csv(OUT_TOP, index=False)
    print(f"wrote {OUT_TOP.relative_to(ROOT)}")

    print("\nTop 5 bairros prioritários:")
    print(top20.head(5)[["rank", "bairro", "ap", "sami", "delta_mean", "priority_score"]].to_string(index=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
