"""Bootstrap intervalo de confiança no `share_within` — Tier 1 [5] do plano.

n=1000 resamples por ano, bairros com reposição, recompute Theil-T via
`acec.stats.theil_decompose`, persiste percentil 2.5/50/97.5 em
`data/processed/theil_bootstrap_ci.csv`.

Endereça a lente 5 (estatístico) do balanço:
> `tests/test_theil.py:177-186` assegura share_within > 0.5, mas a narrativa
> pública diz [59%, 73%] — guarda-corpo frouxo; weighted Theil só sobrevive
> em 2011/2013; sem CIs em lugar nenhum.

Bootstrap CI testifica empiricamente que o achado central (66% within-RA) é
robusto a variação de amostragem nos bairros. Espera-se ci_lo > 0.5 em todo
ano (paridade 50% fora do IC95).

Usa primitivas canônicas do `acec.stats` (mesmas que `10_theil_ideb.py` usa
via cópia local) — single-source-of-truth.

Uso:
  python3 analysis/35_bootstrap_theil_ci.py
  python3 analysis/35_bootstrap_theil_ci.py --n 2000 --seed 17
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

try:
    from acec.stats import theil_decompose
except ImportError:
    print("acec required: pip install -e reference/acec-hub", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
IDEB_LONG = ROOT / "data" / "processed" / "ideb_bairros.csv"
OUT = ROOT / "data" / "processed" / "theil_bootstrap_ci.csv"

DEFAULT_N_BOOTSTRAP = 1000
DEFAULT_SEED = 42


def load_by_year(path: Path) -> dict[int, list[dict]]:
    """`ideb_bairros.csv` long format → {year: [{ra, bairro, ideb}, ...]}."""
    by_year: dict[int, list[dict]] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            year = int(row["year"])
            by_year.setdefault(year, []).append({
                "ra": row["ra"],
                "bairro": row["bairro"],
                "ideb": float(row["ideb"]),
            })
    return by_year


def bootstrap_share_within(
    rows: list[dict], n_bootstrap: int, seed: int,
) -> list[float]:
    """Stratified bootstrap por RA: preserva membership (RAs continuam fixos),
    resample bairros WITHIN cada RA com reposição.

    Por que stratified, não IID:
    - Theil decomposition é sensível a quais RAs estão representados
    - IID resample de bairros pode produzir RAs com 0-1 bairros (T_within colapsa)
      OU duplicar bairros dentro de uma RA (T_within artificialmente baixo)
    - Stratified preserva a estrutura hierárquica que é o próprio ponto da
      decomposição entre/dentro, e mede a sensibilidade da estimativa ao
      conjunto específico de bairros amostrados dentro de cada RA

    Interpretação: NÃO é CI frequentista clássico (não há sampling externo
    — os bairros são a população). É **sensitivity analysis**: "se tivéssemos
    um conjunto diferente de bairros dentro das mesmas RAs, share_within
    seria onde?". Reportar como tal.
    """
    rng = random.Random(seed)

    # Pré-agrupa bairros por RA
    by_ra: dict[str, list[dict]] = {}
    for r in rows:
        by_ra.setdefault(r["ra"], []).append(r)

    shares: list[float] = []
    for _ in range(n_bootstrap):
        sample: list[dict] = []
        for ra_rows in by_ra.values():
            n_in_ra = len(ra_rows)
            # Resample bairros dentro desta RA com reposição
            sample.extend(ra_rows[rng.randrange(n_in_ra)] for _ in range(n_in_ra))
        values = [r["ideb"] for r in sample]
        groups = [r["ra"] for r in sample]
        t_total, _t_between, t_within = theil_decompose(values, groups)
        if t_total > 0:
            shares.append(t_within / t_total)
    return shares


def percentile(values: list[float], p: float) -> float | None:
    """Linear interpolation percentile (np.percentile equivalent), `p` in [0, 100]."""
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (k - f) * (s[c] - s[f])


def compute_point_estimate(rows: list[dict]) -> float | None:
    """Point estimate = share_within sobre os dados originais (sem resample)."""
    values = [r["ideb"] for r in rows]
    groups = [r["ra"] for r in rows]
    t_total, _, t_within = theil_decompose(values, groups)
    return (t_within / t_total) if t_total > 0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Bootstrap CI no share_within")
    ap.add_argument("--n", type=int, default=DEFAULT_N_BOOTSTRAP,
                    help=f"Resamples por ano (default {DEFAULT_N_BOOTSTRAP})")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed")
    args = ap.parse_args()

    if not IDEB_LONG.exists():
        print(f"missing {IDEB_LONG.relative_to(ROOT)} — rode 10_theil_ideb.py primeiro",
              file=sys.stderr)
        return 1

    by_year = load_by_year(IDEB_LONG)
    print(f"loaded {len(by_year)} years from {IDEB_LONG.relative_to(ROOT)}")

    out_rows: list[dict] = []
    for year in sorted(by_year.keys()):
        rows = by_year[year]
        n_bairros = len(rows)
        n_ras = len({r["ra"] for r in rows})
        print(f"  {year}: {n_bairros} bairros / {n_ras} RAs → bootstrap n={args.n}",
              file=sys.stderr)

        point = compute_point_estimate(rows)
        shares = bootstrap_share_within(rows, args.n, args.seed + year)  # seed varia por ano
        if not shares:
            print(f"    [warn] {year}: no valid Theil decomp (T_total=0 em todas resamples)",
                  file=sys.stderr)
            continue

        ci_lo = percentile(shares, 2.5)
        ci_hi = percentile(shares, 97.5)
        median = percentile(shares, 50)

        out_rows.append({
            "year": year,
            "n_bairros": n_bairros,
            "n_ras": n_ras,
            "share_within_point": round(point, 4),
            "ci_lo": round(ci_lo, 4),
            "ci_hi": round(ci_hi, 4),
            "median": round(median, 4),
            "n_bootstrap": args.n,
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year", "n_bairros", "n_ras",
                "share_within_point", "ci_lo", "ci_hi", "median", "n_bootstrap",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print("\nyear  share_within  CI95          width  paridade?")
    for row in out_rows:
        width = row["ci_hi"] - row["ci_lo"]
        far_from_paridade = "✓" if row["ci_lo"] > 0.5 else "✗ (50% no IC!)"
        print(
            f"  {row['year']}  {row['share_within_point']:.4f}     "
            f"[{row['ci_lo']:.3f}, {row['ci_hi']:.3f}]   "
            f"{width:.3f}  {far_from_paridade}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
