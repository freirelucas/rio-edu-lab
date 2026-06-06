"""Moran's I global + LISA local em IDEB e IDS por bairro — Tier 2 [4].

Endereça a lente 4 (GIS) do balanço: "sem Moran's I/LISA, sem teste de
sensibilidade MAUP sobre os 66%". Implementa Moran's I global + LISA local
sobre bairros do Rio (163 polígonos do IPP), com matriz de pesos espaciais
queen contiguity, sem dep nova (libpysal/esda não estão em requirements).

Métricas calculadas pra IDEB 2023 e IDS 2010 (ambos com bairro como unidade):
- **Moran's I global**: autocorrelação espacial overall (∈ [-1, +1])
- **Pseudo-p via permutação**: 999 shuffles, %≥ observado → significância
- **Local Moran's I per bairro**: I_i = z_i * (Σ w_ij * z_j)
- **Classificação LISA**: HH (hot spot), LL (cold spot), HL (high near lows),
  LH (low near highs), NS (não significativo) — significância pseudo-p ≤ 0.05

Outputs:
- `data/processed/moran_lisa_ideb.csv`: bairro × {ideb, z, lag, local_i, p, classe}
- `data/processed/moran_lisa_ids.csv`: análogo pra IDS
- `data/processed/moran_lisa_summary.json`: global I + p + counts por classe

Uso:
  python3 analysis/37_moran_lisa.py
  python3 analysis/37_moran_lisa.py --permutations 9999  # mais tight
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import unicodedata
from pathlib import Path

try:
    import geopandas as gpd
except ImportError:
    print("geopandas required: pip install geopandas", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"
IDEB_CSV = ROOT / "data" / "processed" / "ideb_bairros.csv"
VULN_CSV = ROOT / "data" / "processed" / "vuln_edu_bairros.csv"  # tem IDS por bairro

OUT_IDEB = ROOT / "data" / "processed" / "moran_lisa_ideb.csv"
OUT_IDS = ROOT / "data" / "processed" / "moran_lisa_ids.csv"
OUT_SUMMARY = ROOT / "data" / "processed" / "moran_lisa_summary.json"

DEFAULT_PERMUTATIONS = 999
SIG_THRESHOLD = 0.05


def _normalize_name(s: str) -> str:
    """Lowercase + strip accents pra match bairro names entre datasets."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s))
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accents.lower().strip()


def build_queen_weights(gdf) -> tuple[list[list[int]], list[str]]:
    """Queen contiguity: dois polígonos são vizinhos se geometrias se intersectam
    (touches at a point conta — diferente de rook que exige edge compartilhada).

    Returns (neighbors, names): neighbors[i] = list of j's; names[i] = bairro name.
    Row-normalization é feita on-the-fly em compute_lag.
    """
    # IPP geojson usa "nome" (lowercase). Fallback pra "NOME" se schema mudar.
    name_col = "nome" if "nome" in gdf.columns else "NOME"
    names = [_normalize_name(n) for n in gdf[name_col]]
    geoms = list(gdf.geometry)
    n = len(geoms)
    neighbors: list[list[int]] = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if geoms[i].intersects(geoms[j]):
                neighbors[i].append(j)
                neighbors[j].append(i)
    return neighbors, names


def compute_lag(values: list[float], neighbors: list[list[int]]) -> list[float]:
    """Spatial lag: media simples dos vizinhos (row-normalized W).

    Bairros sem vizinhos (ilhas/erros geométricos) → lag = 0 (degenerate).
    """
    lag = []
    for nbrs in neighbors:
        if not nbrs:
            lag.append(0.0)
        else:
            lag.append(sum(values[j] for j in nbrs) / len(nbrs))
    return lag


def standardize(values: list[float]) -> tuple[list[float], float, float]:
    """z = (x - mean) / std. Returns (z, mean, std)."""
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    std = var ** 0.5
    if std == 0:
        return [0.0] * n, mean, 0.0
    return [(v - mean) / std for v in values], mean, std


def morans_i(z: list[float], neighbors: list[list[int]]) -> tuple[float, list[float]]:
    """Global Moran's I + lista de local I's per bairro.

    Com z standardizado e W row-normalized:
      Moran I_global = mean(z * lag_z) onde lag_z = mean dos vizinhos
      Local I_i = z_i * lag_z_i

    Returns (global_I, local_Is).
    """
    n = len(z)
    if n == 0:
        return 0.0, []
    lag_z = compute_lag(z, neighbors)
    local_i = [z[i] * lag_z[i] for i in range(n)]
    global_i = sum(local_i) / n
    return global_i, local_i


def permutation_test_global(
    z: list[float], neighbors: list[list[int]],
    observed_i: float, n_permutations: int, seed: int = 42,
) -> float:
    """Pseudo-p via permutação: shuffle z, recompute I, % ≥ observed.

    Two-tailed test: usa |I| pra distribuição. Pseudo-p = (count + 1) / (n + 1).
    """
    rng = random.Random(seed)
    n = len(z)
    n_extreme = 0
    abs_obs = abs(observed_i)
    for _ in range(n_permutations):
        shuffled = z[:]
        rng.shuffle(shuffled)
        lag_z = compute_lag(shuffled, neighbors)
        i_perm = sum(shuffled[i] * lag_z[i] for i in range(n)) / n
        if abs(i_perm) >= abs_obs:
            n_extreme += 1
    return (n_extreme + 1) / (n_permutations + 1)


def permutation_test_local(
    z: list[float], neighbors: list[list[int]], local_i: list[float],
    n_permutations: int, seed: int = 42,
) -> list[float]:
    """Pseudo-p per bairro: pra cada i, shuffle os OUTROS z's e recompute local_I_i.

    O z_i fica fixo; só os vizinhos são permutados. Padrão da lit.
    """
    rng = random.Random(seed)
    n = len(z)
    pseudo_ps: list[float] = []
    for i in range(n):
        if not neighbors[i]:
            pseudo_ps.append(1.0)
            continue
        z_i = z[i]
        abs_obs = abs(local_i[i])
        n_extreme = 0
        # Pool: todos os outros z's
        other_z = [z[j] for j in range(n) if j != i]
        for _ in range(n_permutations):
            rng.shuffle(other_z)
            # Os primeiros len(neighbors[i]) são os "vizinhos"
            lag = sum(other_z[:len(neighbors[i])]) / len(neighbors[i])
            i_perm = z_i * lag
            if abs(i_perm) >= abs_obs:
                n_extreme += 1
        pseudo_ps.append((n_extreme + 1) / (n_permutations + 1))
    return pseudo_ps


def classify_lisa(z: list[float], lag_z: list[float], p: list[float]) -> list[str]:
    """HH/LL/HL/LH/NS baseado em sinais + significância (p ≤ 0.05)."""
    out: list[str] = []
    for i in range(len(z)):
        if p[i] > SIG_THRESHOLD:
            out.append("NS")
            continue
        if z[i] > 0 and lag_z[i] > 0:
            out.append("HH")
        elif z[i] < 0 and lag_z[i] < 0:
            out.append("LL")
        elif z[i] > 0 and lag_z[i] < 0:
            out.append("HL")
        elif z[i] < 0 and lag_z[i] > 0:
            out.append("LH")
        else:
            out.append("NS")
    return out


def analyze_variable(
    gdf, values_by_name: dict[str, float], var_name: str, n_perm: int,
) -> tuple[dict, list[dict]]:
    """Carrega bairros, join com values_by_name, rode Moran's I + LISA."""
    print(f"\n=== {var_name} ===", file=sys.stderr)
    neighbors, names = build_queen_weights(gdf)
    n = len(names)
    print(f"  {n} bairros; queen neighbors média: "
          f"{sum(len(nbrs) for nbrs in neighbors) / n:.1f}", file=sys.stderr)

    # Join: bairros sem valor → drop. Mas precisa preservar índice consistente.
    values: list[float | None] = [values_by_name.get(n) for n in names]
    valid_idx = [i for i, v in enumerate(values) if v is not None]
    n_valid = len(valid_idx)
    print(f"  bairros com valor de {var_name}: {n_valid}/{n}", file=sys.stderr)

    # Subset arrays para os válidos
    valid_names = [names[i] for i in valid_idx]
    valid_values = [values[i] for i in valid_idx]
    # Renumera os neighbors pra novo índice
    old_to_new = {old: new for new, old in enumerate(valid_idx)}
    valid_neighbors = [
        [old_to_new[j] for j in neighbors[i] if j in old_to_new]
        for i in valid_idx
    ]

    z, mean, std = standardize(valid_values)
    print(f"  mean={mean:.3f}, std={std:.3f}", file=sys.stderr)

    global_i, local_i = morans_i(z, valid_neighbors)
    print(f"  Moran's I global = {global_i:.4f}", file=sys.stderr)

    global_p = permutation_test_global(z, valid_neighbors, global_i, n_perm)
    print(f"  pseudo-p (n={n_perm}): {global_p:.4f}", file=sys.stderr)

    lag_z = compute_lag(z, valid_neighbors)
    local_p = permutation_test_local(z, valid_neighbors, local_i, n_perm)
    classes = classify_lisa(z, lag_z, local_p)
    class_counts = {c: classes.count(c) for c in ("HH", "LL", "HL", "LH", "NS")}
    print(f"  LISA classes: {class_counts}", file=sys.stderr)

    summary = {
        "variable": var_name,
        "n_bairros": n_valid,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "morans_i_global": round(global_i, 4),
        "pseudo_p_global": round(global_p, 4),
        "n_permutations": n_perm,
        "class_counts": class_counts,
        "significant_at_0.05": sum(1 for c in classes if c != "NS"),
    }
    rows = [
        {
            "bairro": valid_names[i],
            "value": round(valid_values[i], 4),
            "z": round(z[i], 4),
            "lag_z": round(lag_z[i], 4),
            "local_i": round(local_i[i], 4),
            "pseudo_p": round(local_p[i], 4),
            "lisa_class": classes[i],
        }
        for i in range(n_valid)
    ]
    return summary, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--permutations", type=int, default=DEFAULT_PERMUTATIONS,
                    help=f"N permutações (default {DEFAULT_PERMUTATIONS})")
    args = ap.parse_args()

    if not BAIRROS_GEOJSON.exists():
        print(f"missing {BAIRROS_GEOJSON.relative_to(ROOT)}", file=sys.stderr)
        return 1

    gdf = gpd.read_file(BAIRROS_GEOJSON)
    print(f"loaded {len(gdf)} bairros from geojson", file=sys.stderr)

    summaries: list[dict] = []

    # IDEB 2023
    if IDEB_CSV.exists():
        ideb_by_name: dict[str, float] = {}
        with IDEB_CSV.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["year"] == "2023":
                    ideb_by_name[_normalize_name(row["bairro"])] = float(row["ideb"])
        summary, rows = analyze_variable(gdf, ideb_by_name, "IDEB_2023", args.permutations)
        summaries.append(summary)

        OUT_IDEB.parent.mkdir(parents=True, exist_ok=True)
        with OUT_IDEB.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"wrote {OUT_IDEB.relative_to(ROOT)}")

    # IDS (do vuln_edu_bairros.csv) — coluna correta = `ids_median`
    if VULN_CSV.exists():
        ids_by_name: dict[str, float] = {}
        with VULN_CSV.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                v = row.get("ids_median") or row.get("ids_mean")
                if v:
                    try:
                        ids_by_name[_normalize_name(row["bairro"])] = float(v)
                    except (ValueError, KeyError):
                        continue
        if ids_by_name:
            summary, rows = analyze_variable(gdf, ids_by_name, "IDS_2010", args.permutations)
            summaries.append(summary)

            with OUT_IDS.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            print(f"wrote {OUT_IDS.relative_to(ROOT)}")

    OUT_SUMMARY.write_text(json.dumps(summaries, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
