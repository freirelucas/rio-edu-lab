"""Grade H3 sobre o município do Rio + linkagem hex→bairro.

Para cada célula H3 cujo centro cai dentro de algum bairro:
  - hex_id (H3 string)
  - codbairro, nome (do `bairros.geojson`)
  - codra, ap, rp, cod_rp (atributos da Feature Layer IPP)
  - ideb_bairro (nome normalizado: matches the bairro names in
    data/processed/ideb_bairros.csv, after accent/parenthetical fixup)

Saídas:
  - data/processed/h3_grid.geojson    (FeatureCollection com hex polygons)
  - data/processed/hex_to_bairro.csv  (lookup table)
  - data/processed/bairros_aliases.csv (mapping geom-name -> ideb-name; só
    onde diferem)

Uso:
  python3 analysis/12_h3_grid.py
  python3 analysis/12_h3_grid.py --resolution 9   # mais fino (~12k hexes)

Resolução default = 8 (~0.7 km², ~1.7k hexes para Rio). Trade-off:
- res 8: mais coarse, processa rápido, fácil de visualizar
- res 9: ~7x mais hexes, captura variação intra-bairro melhor
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import h3
import pandas as pd
from shapely.geometry import Polygon, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"
IDEB_CSV = ROOT / "data" / "processed" / "ideb_bairros.csv"
OUT_GRID = ROOT / "data" / "processed" / "h3_grid.geojson"
OUT_LOOKUP = ROOT / "data" / "processed" / "hex_to_bairro.csv"
OUT_ALIASES = ROOT / "data" / "processed" / "bairros_aliases.csv"

# Manual aliases for the 4 names that don't match by case-fold alone.
# Direction: IDEB-canonical-name -> geom-canonical-name (as found in bairros.geojson).
# Verified in session 1 cross-check.
MANUAL_ALIASES_IDEB_TO_GEOM = {
    "freguesia (ilha do governador)": "Freguesia (Ilha)",
    "oswaldo cruz": "Osvaldo Cruz",  # IDEB uses 'w', IPP geom uses 'v'
    "parque columbia": "Parque Colúmbia",
    "turiaçu": "Turiaçú",
}


def normalize(name: str) -> str:
    """Lowercase + strip accents + strip whitespace. For matching only."""
    if name is None:
        return ""
    s = name.strip().lower()
    s = "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )
    return s


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--resolution", type=int, default=8, help="H3 resolution (default 8)")
    return p.parse_args()


def load_bairros() -> gpd.GeoDataFrame:
    """Load bairros, drop noisy columns, set CRS."""
    gdf = gpd.read_file(BAIRROS_GEOJSON)
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    # Strip padding from string fields
    for col in ("nome", "regiao_adm", "rp", "link"):
        if col in gdf.columns:
            gdf[col] = gdf[col].astype(str).str.strip()
    return gdf


def generate_h3_cells(rio_polygon, resolution: int) -> list[str]:
    """Generate H3 cells whose centers fall inside the city polygon."""
    geom = mapping(rio_polygon)
    h3shape = h3.geo_to_h3shape(geom)
    cells = h3.h3shape_to_cells(h3shape, resolution)
    return list(cells)


def hex_to_polygon(hex_id: str) -> Polygon:
    boundary = h3.cell_to_boundary(hex_id)  # list of (lat, lng) tuples
    # GeoJSON / shapely use (lng, lat)
    return Polygon([(lng, lat) for lat, lng in boundary])


def main() -> int:
    args = parse_args()
    res = args.resolution

    print(f"loading {BAIRROS_GEOJSON.relative_to(ROOT)}")
    bairros = load_bairros()
    print(f"  {len(bairros)} features, CRS={bairros.crs}")

    # Build normalization tables
    geom_names = bairros["nome"].tolist()
    geom_norm_to_name = {normalize(n): n for n in geom_names}

    # Cross-check IDEB names + build alias table
    ideb_df = pd.read_csv(IDEB_CSV)
    ideb_names = sorted(set(ideb_df["bairro"].dropna().astype(str).str.strip()))

    aliases_rows: list[dict] = []
    unmatched_ideb: list[str] = []
    for n in ideb_names:
        nn = normalize(n)
        if nn in geom_norm_to_name:
            geom_n = geom_norm_to_name[nn]
            if geom_n != n:
                aliases_rows.append({"ideb_name": n, "geom_name": geom_n, "match": "case_fold"})
        elif n.lower() in MANUAL_ALIASES_IDEB_TO_GEOM:
            target = MANUAL_ALIASES_IDEB_TO_GEOM[n.lower()]
            if normalize(target) in geom_norm_to_name:
                geom_n = geom_norm_to_name[normalize(target)]
                aliases_rows.append({"ideb_name": n, "geom_name": geom_n, "match": "manual"})
            else:
                unmatched_ideb.append(n)
        else:
            unmatched_ideb.append(n)

    print(f"\nname matching: {len(ideb_names)} ideb names")
    print(f"  matched: {len(ideb_names) - len(unmatched_ideb)}")
    print(f"  unmatched: {unmatched_ideb}")

    # City-wide polygon (union of all bairros) — used as the H3 mask.
    rio_polygon = unary_union(bairros.geometry)
    print(f"\nbuilding H3 res-{res} grid over union of {len(bairros)} polygons")
    cells = generate_h3_cells(rio_polygon, res)
    print(f"  {len(cells)} cells generated")

    # Build a GeoDataFrame of hex polygons
    hex_geoms = [hex_to_polygon(c) for c in cells]
    hexes = gpd.GeoDataFrame(
        {"hex_id": cells},
        geometry=hex_geoms,
        crs="EPSG:4326",
    )

    # Spatial join: each hex centroid → bairro (polygon containing the centroid).
    # Compute centroids in a projected CRS (UTM 23S = SIRGAS 2000 / 31983) to
    # avoid the warning + tiny error from doing it on geographic coords.
    # Reproject back to 4326 for the join with bairros.
    hex_proj = hexes.to_crs(31983)
    hex_pts = gpd.GeoDataFrame(
        {"hex_id": hexes["hex_id"]},
        geometry=hex_proj.geometry.centroid,
        crs=31983,
    ).to_crs(4326)

    joined = gpd.sjoin(
        hex_pts,
        bairros[["nome", "codbairro", "codra", "regiao_adm", "rp", "cod_rp", "area_plane", "geometry"]],
        how="left",
        predicate="within",
    )

    # Some hex centroids may sit on a boundary and be assigned to multiple
    # polygons by sjoin → keep first assignment per hex_id.
    joined = joined.drop_duplicates(subset="hex_id", keep="first")

    # Build geom_name → ideb_name reverse map for joining downstream
    geom_to_ideb = {}
    for r in aliases_rows:
        geom_to_ideb[r["geom_name"]] = r["ideb_name"]
    # And direct case-fold matches that didn't need an alias entry
    for ideb_n in ideb_names:
        nn = normalize(ideb_n)
        if nn in geom_norm_to_name:
            geom_n = geom_norm_to_name[nn]
            geom_to_ideb.setdefault(geom_n, ideb_n)

    joined["ideb_bairro"] = joined["nome"].map(geom_to_ideb).fillna(joined["nome"])

    n_assigned = joined["nome"].notna().sum()
    print(f"\nspatial join: {n_assigned}/{len(hexes)} hexes assigned to a bairro")

    # Distinct bairros covered by hexes
    bairros_covered = joined["nome"].dropna().nunique()
    print(f"  distinct bairros covered: {bairros_covered} (of {len(bairros)} polygons)")

    # Write hex grid as GeoJSON (re-attach hex polygons)
    out_grid = hexes.merge(
        joined.drop(columns="geometry")[
            ["hex_id", "nome", "codbairro", "codra", "rp", "cod_rp", "area_plane", "ideb_bairro"]
        ],
        on="hex_id",
        how="left",
    )
    out_grid.to_file(OUT_GRID, driver="GeoJSON")
    print(f"\nwrote {OUT_GRID.relative_to(ROOT)} ({OUT_GRID.stat().st_size / 1024:.0f} KiB)")

    # Lookup CSV (lightweight, easy to join in any tool)
    OUT_LOOKUP.parent.mkdir(parents=True, exist_ok=True)
    cols = ["hex_id", "ideb_bairro", "nome", "codbairro", "codra", "rp", "cod_rp", "area_plane"]
    out_grid[cols].to_csv(OUT_LOOKUP, index=False)
    print(f"wrote {OUT_LOOKUP.relative_to(ROOT)} ({len(out_grid)} rows)")

    # Aliases CSV
    if aliases_rows:
        with OUT_ALIASES.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["ideb_name", "geom_name", "match"])
            w.writeheader()
            w.writerows(aliases_rows)
        print(f"wrote {OUT_ALIASES.relative_to(ROOT)} ({len(aliases_rows)} aliases)")

    if unmatched_ideb:
        print(f"\n!!! unmatched IDEB names ({len(unmatched_ideb)}): {unmatched_ideb}")
        print("   These bairros from IDEB have no polygon match. Will appear as missing on maps.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
