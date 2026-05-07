"""HEX-EDU acessibilidade — replicação simplificada Pereira et al. (2019) IPEA.

Para cada hexágono H3 do Rio Municipal, computa métricas de acesso a
equipamentos educacionais:

  - n_2km, n_5km    contagem de equipamentos em raios respectivos
  - dist_min_km     distância haversine ao equipamento mais próximo
  - acesso_qty      soma de exp(-d/d0) sobre equipamentos em raio (impedância)
  - acesso_quality  soma de IDEB_bairro × exp(-d/d0)  (Pereira-style: qualidade × proximidade)

Filtro de equipamento: apenas Escolas Municipais + CIEP + Escola Especial
Municipal (1022 unidades) — os que de fato participam do IDEB séries iniciais.
EDIs e creches são pré-escola e ficam fora.

A métrica `acesso_quality` é o coração do framework Pereira: a oportunidade
educacional acessível ao morador de cada célula é a soma das opções viáveis
ponderadas pela qualidade de cada uma e penalizadas pela distância. d0 = 1.5 km
(parâmetro de impedância calibrado para distâncias caminháveis).

Importante: esta v0.6.1 usa **distância haversine** entre centroide do hex e
ponto da escola. A versão v0.7 substitui pela distância via OSM road network
(isócronas reais). O método de decomposição em si não muda.

Outputs:
  - data/processed/hex_accessibility.csv

Uso:
  python3 analysis/26_hex_accessibility.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
HEX_GEOJSON = ROOT / "data" / "processed" / "h3_grid.geojson"
ESCOLAS_GEOJSON = ROOT / "data" / "raw" / "geo" / "escolas_municipais.geojson"
IDEB_LONG = ROOT / "data" / "processed" / "ideb_bairros.csv"
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"

OUT_CSV = ROOT / "data" / "processed" / "hex_accessibility.csv"

# Impedance & buffer parameters (in km).
IMPEDANCE_D0 = 1.5  # ~ 18 minutos a pé no ritmo médio
RADIUS_2KM = 2.0
RADIUS_5KM = 5.0
RADIUS_MAX_FOR_QUALITY = 5.0  # don't sum quality contributions beyond this

# Equipment types eligible for IDEB séries iniciais (1º ao 5º ano).
ELIGIBLE_TYPES = {
    "Escola Municipal",
    "CIEP",
    "Escola Especial Municipal",
}


def haversine_km_vec(lat1, lon1, lat2_arr, lon2_arr):
    """Vectorized haversine distance (km) from one point to many."""
    R = 6371.0
    lat1_r = math.radians(lat1)
    lon1_r = math.radians(lon1)
    lat2_r = np.radians(lat2_arr)
    lon2_r = np.radians(lon2_arr)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2) ** 2 + math.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def main() -> int:
    if not all(p.exists() for p in (HEX_GEOJSON, ESCOLAS_GEOJSON, IDEB_LONG, BAIRROS_GEOJSON)):
        print("missing inputs; run sessions 11, 12, 25 first")
        return 1

    print(f"loading {HEX_GEOJSON.relative_to(ROOT)}")
    hexes = gpd.read_file(HEX_GEOJSON).to_crs(4326)
    hexes["centroid"] = hexes.geometry.to_crs(31983).centroid.to_crs(4326)
    hexes["c_lon"] = hexes["centroid"].x
    hexes["c_lat"] = hexes["centroid"].y
    print(f"  {len(hexes)} hexes")

    print(f"loading {ESCOLAS_GEOJSON.relative_to(ROOT)}")
    escolas = gpd.read_file(ESCOLAS_GEOJSON)
    if escolas.crs is None:
        escolas = escolas.set_crs(4326)
    elif escolas.crs.to_epsg() != 4326:
        escolas = escolas.to_crs(4326)
    print(f"  {len(escolas)} equipamentos totais")

    # Filter to eligible equipment types
    type_col = "tipo_unidade" if "tipo_unidade" in escolas.columns else "tipo"
    if type_col not in escolas.columns:
        # Try to detect the category column
        for cand in ("tipo", "tipo_unidade", "categoria", "TIPO"):
            if cand in escolas.columns:
                type_col = cand
                break
    print(f"  type column: {type_col}; values: {escolas[type_col].value_counts().head(8).to_dict()}")

    eligible = escolas[escolas[type_col].isin(ELIGIBLE_TYPES)].copy()
    eligible["e_lon"] = eligible.geometry.x
    eligible["e_lat"] = eligible.geometry.y
    print(f"  {len(eligible)} eligible (Escolas Munic + CIEP + Especial)")

    # Spatial join to get the bairro of each school.
    bairros = gpd.read_file(BAIRROS_GEOJSON).to_crs(4326)
    bairros["nome"] = bairros["nome"].astype(str).str.strip()
    eligible = gpd.sjoin(eligible, bairros[["nome", "geometry"]], how="left", predicate="within")
    eligible = eligible.rename(columns={"nome": "bairro"})

    # Use last available IDEB year as quality proxy (2023).
    ideb = pd.read_csv(IDEB_LONG)
    ideb["bairro"] = ideb["bairro"].astype(str).str.strip()
    ideb_2023 = ideb[ideb["year"] == 2023].set_index("bairro")["ideb"]
    eligible["ideb_quality"] = eligible["bairro"].map(ideb_2023)

    n_with_ideb = eligible["ideb_quality"].notna().sum()
    median_ideb = eligible["ideb_quality"].median()
    eligible["ideb_quality"] = eligible["ideb_quality"].fillna(median_ideb)
    print(f"  {n_with_ideb}/{len(eligible)} equipamentos têm IDEB do bairro; "
          f"missing preenchido com mediana ({median_ideb:.2f})")

    # Build kd-tree over equipment locations in projected coords (for fast radius queries).
    eligible_proj = eligible.to_crs(31983)
    e_xy = np.array([(g.x, g.y) for g in eligible_proj.geometry])
    tree = cKDTree(e_xy)

    hexes_proj = hexes.set_geometry("centroid").to_crs(31983)
    h_xy = np.array([(g.x, g.y) for g in hexes_proj.geometry])

    print("\ncomputing access metrics per hex …")
    results = []
    for i, hxy in enumerate(h_xy):
        # Radius queries (5 km in meters; tree is in projected coords).
        idx_5km = tree.query_ball_point(hxy, r=RADIUS_5KM * 1000)
        # Switch to haversine for accuracy (we'll use lat/lon).
        c_lat = hexes.iloc[i]["c_lat"]
        c_lon = hexes.iloc[i]["c_lon"]
        if not idx_5km:
            results.append({
                "hex_id": hexes.iloc[i]["hex_id"],
                "n_2km": 0, "n_5km": 0,
                "dist_min_km": np.nan,
                "acesso_qty": 0.0, "acesso_quality": 0.0,
            })
            continue

        nearby = eligible.iloc[idx_5km]
        d = haversine_km_vec(c_lat, c_lon, nearby["e_lat"].values, nearby["e_lon"].values)
        within_2 = d <= RADIUS_2KM
        within_5 = d <= RADIUS_5KM
        within_radius_for_quality = d <= RADIUS_MAX_FOR_QUALITY
        weights = np.exp(-d[within_radius_for_quality] / IMPEDANCE_D0)
        quality = nearby["ideb_quality"].values[within_radius_for_quality]
        acesso_qty = float(weights.sum())
        acesso_quality = float((quality * weights).sum())
        results.append({
            "hex_id": hexes.iloc[i]["hex_id"],
            "n_2km": int(within_2.sum()),
            "n_5km": int(within_5.sum()),
            "dist_min_km": float(d.min()),
            "acesso_qty": round(acesso_qty, 4),
            "acesso_quality": round(acesso_quality, 4),
        })

    df = pd.DataFrame(results)

    # Attach hex → bairro/RA/AP from h3_grid (already joined in session 12).
    keep = ["hex_id", "ideb_bairro", "rp", "area_plane", "codra"]
    keep_cols = [c for c in keep if c in hexes.columns]
    df = df.merge(hexes[keep_cols].rename(columns={"ideb_bairro": "bairro"}),
                  on="hex_id", how="left")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"\nwrote {OUT_CSV.relative_to(ROOT)} ({len(df)} hexes)")

    # Quick stats
    print(f"\n=== distribuição ===")
    print(f"  n_2km:   p10={df['n_2km'].quantile(0.10):.0f}  p50={df['n_2km'].quantile(0.50):.0f}  p90={df['n_2km'].quantile(0.90):.0f}")
    print(f"  n_5km:   p10={df['n_5km'].quantile(0.10):.0f}  p50={df['n_5km'].quantile(0.50):.0f}  p90={df['n_5km'].quantile(0.90):.0f}")
    print(f"  dist_min: p10={df['dist_min_km'].quantile(0.10):.2f}  p50={df['dist_min_km'].quantile(0.50):.2f}  p90={df['dist_min_km'].quantile(0.90):.2f} km")
    print(f"  acesso_quality: p10={df['acesso_quality'].quantile(0.10):.2f}  p50={df['acesso_quality'].quantile(0.50):.2f}  p90={df['acesso_quality'].quantile(0.90):.2f}")
    n_zero = (df["n_5km"] == 0).sum()
    if n_zero:
        print(f"  hexes sem nenhuma escola em 5 km: {n_zero}")

    # By AP (5 zones)
    if "area_plane" in df.columns:
        print(f"\n=== média de acesso_quality por AP ===")
        print(df.groupby("area_plane")["acesso_quality"].agg(["count", "mean", "median"]).round(2).to_string())

    return 0


if __name__ == "__main__":
    sys.exit(main())
