"""H3 grid generation + bairro spatial join.

Promoted from `rio-edu-lab/analysis/12_h3_grid.py`. Generates an H3
hexagonal grid covering a city polygon and links each cell to the
bairro of its centroid (in projected CRS for accuracy).

Usage:
    import geopandas as gpd
    from acec.geo.h3_grid import generate_grid

    bairros = gpd.read_file("bairros.geojson").to_crs(4326)
    grid = generate_grid(bairros, resolution=8, projected_epsg=31983)
    grid.to_file("h3_grid.geojson", driver="GeoJSON")
"""

from __future__ import annotations

from typing import Any


def generate_grid(
    bairros: Any,  # GeoDataFrame (avoid import at module top)
    resolution: int = 8,
    projected_epsg: int = 31983,  # SIRGAS 2000 / UTM 23S — Rio appropriate
):
    """Generate H3 cells covering the union of bairro polygons + spatial join.

    Args:
      bairros: GeoDataFrame with at least `geometry` and ideally `nome`,
               `codbairro`, `codra`, `rp`, `cod_rp`, `area_plane`.
               Must be in EPSG:4326.
      resolution: H3 resolution. 8 ≈ 0.7 km², 9 ≈ 0.1 km² for Rio.
      projected_epsg: CRS used for centroid computation (avoids the
                      geographic-CRS warning + tiny error). 31983 is
                      SIRGAS 2000 / UTM 23S, standard for Rio.

    Returns:
      GeoDataFrame in EPSG:4326 with one row per hex, columns:
        - hex_id (str): the H3 cell index
        - geometry (Polygon): hex shape
        - all bairro attributes from sjoin (nome, codbairro, ...)

    Raises:
      ValueError: if input is not in EPSG:4326.
    """
    import geopandas as gpd
    import h3
    from shapely.geometry import Polygon, mapping
    from shapely.ops import unary_union

    if bairros.crs is None or bairros.crs.to_epsg() != 4326:
        raise ValueError(
            f"bairros must be in EPSG:4326, got {bairros.crs}"
        )

    rio = unary_union(bairros.geometry)
    h3shape = h3.geo_to_h3shape(mapping(rio))
    cells = list(h3.h3shape_to_cells(h3shape, resolution))

    def _hex_polygon(hex_id: str) -> Polygon:
        boundary = h3.cell_to_boundary(hex_id)
        # H3 returns (lat, lng); shapely expects (lng, lat)
        return Polygon([(lng, lat) for lat, lng in boundary])

    hexes = gpd.GeoDataFrame(
        {"hex_id": cells},
        geometry=[_hex_polygon(c) for c in cells],
        crs="EPSG:4326",
    )

    # Compute centroids in projected CRS for sjoin accuracy.
    hex_proj = hexes.to_crs(projected_epsg)
    hex_pts = gpd.GeoDataFrame(
        {"hex_id": hexes["hex_id"]},
        geometry=hex_proj.geometry.centroid,
        crs=projected_epsg,
    ).to_crs(4326)

    joined = gpd.sjoin(hex_pts, bairros, how="left", predicate="within")
    joined = joined.drop_duplicates(subset="hex_id", keep="first")

    # Re-attach hex polygons + drop sjoin index column.
    out = hexes.merge(
        joined.drop(columns=["geometry", "index_right"], errors="ignore"),
        on="hex_id",
        how="left",
    )
    return out


__all__ = ["generate_grid"]
