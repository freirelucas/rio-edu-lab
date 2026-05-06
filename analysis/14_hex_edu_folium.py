"""HEX-EDU interativo (Folium): seletor de ano + tooltips por hex.

Constrói um mapa Folium com:
  - 1 camada por ano de IDEB disponível (2007, 2009, ..., 2023)
  - LayerControl para alternar entre anos
  - Tooltips: bairro, IDEB do ano, RA, AP
  - Camada base de bordas dos bairros (sempre visível)
  - Tile dark/light claro neutro

Saída: HTML standalone embebível em iframe no MkDocs.

Uso:
  python3 analysis/14_hex_edu_folium.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
from branca.colormap import LinearColormap

ROOT = Path(__file__).resolve().parent.parent
HEX_GEOJSON = ROOT / "data" / "processed" / "h3_grid.geojson"
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"
IDEB_CSV = ROOT / "data" / "processed" / "ideb_bairros.csv"

OUT_HTML = ROOT / "docs" / "reports" / "_assets" / "08_hex_edu_interactive.html"
OUT_REPORT = ROOT / "docs" / "reports" / "08_hex_edu_interactive.md"

# IDEB years actually available in the source file (every 2 years)
YEARS = [2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023]
# Default visible (most recent)
DEFAULT_YEAR = 2023

# Same divergent palette as the static map for consistency
PALETTE_STEPS = ["#b2182b", "#ef8a62", "#fddbc7", "#f7f7f7", "#d1e5f0", "#67a9cf", "#2166ac"]
VMIN, VMAX = 4.5, 7.5

# Rio centroid + zoom that fits the city
RIO_CENTER = (-22.92, -43.45)
RIO_ZOOM = 11


def load_data() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame]:
    hexes = gpd.read_file(HEX_GEOJSON).to_crs(4326)
    bairros = gpd.read_file(BAIRROS_GEOJSON).to_crs(4326)
    bairros["nome"] = bairros["nome"].astype(str).str.strip()
    ideb = pd.read_csv(IDEB_CSV)
    ideb["bairro"] = ideb["bairro"].astype(str).str.strip()
    return hexes, bairros, ideb


def round_geom_coords(geojson_str: str, ndigits: int = 5) -> str:
    """Round all numeric coordinates in a GeoJSON to ndigits.

    For H3 res 8 (~0.7 km²), 5 decimals (~1.1 m) is more than enough.
    Cuts file size ~3-4x without visible precision loss.
    """
    import re
    return re.sub(
        r"-?\d+\.\d+",
        lambda m: f"{float(m.group(0)):.{ndigits}f}",
        geojson_str,
    )


def build_year_layer(
    hexes: gpd.GeoDataFrame,
    ideb: pd.DataFrame,
    year: int,
    cmap: LinearColormap,
    show: bool,
) -> folium.FeatureGroup:
    lookup = {row["bairro"]: row["ideb"] for _, row in ideb[ideb["year"] == year].iterrows()}

    # Strip down to just the columns we render in tooltips, reduces JSON size 2-3x.
    hexes_y = hexes[["hex_id", "ideb_bairro", "rp", "area_plane", "geometry"]].copy()
    hexes_y["ideb"] = [lookup.get(str(b).strip()) for b in hexes_y["ideb_bairro"]]

    fg = folium.FeatureGroup(name=f"IDEB {year}", overlay=False, show=show)

    plotted = hexes_y[hexes_y["ideb"].notna()].copy()
    no_data = hexes_y[hexes_y["ideb"].isna()].copy()

    # Plotted hexes: color-coded by IDEB
    def style_with_data(feat):
        v = feat["properties"]["ideb"]
        return {
            "fillColor": cmap(v),
            "color": "white",
            "weight": 0.3,
            "fillOpacity": 0.85,
        }

    folium.GeoJson(
        round_geom_coords(plotted.to_json()),
        style_function=style_with_data,
        tooltip=folium.GeoJsonTooltip(
            fields=["ideb_bairro", "ideb", "rp", "area_plane"],
            aliases=["Bairro:", f"IDEB {year}:", "Região planejam.:", "AP:"],
            localize=True,
            sticky=False,
            labels=True,
            style="background-color: #ffffff; color: #111; font-family: sans-serif;",
        ),
        highlight_function=lambda x: {"weight": 1.5, "color": "#000"},
        smooth_factor=0.3,
    ).add_to(fg)

    if len(no_data):
        folium.GeoJson(
            round_geom_coords(no_data.to_json()),
            style_function=lambda f: {
                "fillColor": "#dddddd",
                "color": "white",
                "weight": 0.2,
                "fillOpacity": 0.5,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["ideb_bairro"],
                aliases=[f"Bairro (sem IDEB {year}):"],
                style="background-color: #f4f4f4; color: #555; font-family: sans-serif;",
            ),
            smooth_factor=0.3,
        ).add_to(fg)

    return fg


def build_bairros_borders(bairros: gpd.GeoDataFrame) -> folium.GeoJson:
    # Simplify polygons (~50m tolerance in degrees) — borders only, full
    # precision wastes ~3 MiB on jagged coastlines.
    simplified = bairros[["nome", "regiao_adm", "rp", "geometry"]].copy()
    simplified["geometry"] = simplified.geometry.simplify(0.0005, preserve_topology=True)
    return folium.GeoJson(
        round_geom_coords(simplified.to_json()),
        name="Bordas de bairros",
        style_function=lambda f: {
            "color": "#333",
            "weight": 0.6,
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["nome", "regiao_adm", "rp"],
            aliases=["Bairro:", "Região Adm.:", "RP:"],
        ),
        control=True,
        show=True,
    )


def build_map(hexes: gpd.GeoDataFrame, bairros: gpd.GeoDataFrame, ideb: pd.DataFrame) -> folium.Map:
    cmap = LinearColormap(
        colors=PALETTE_STEPS,
        vmin=VMIN, vmax=VMAX,
        caption="IDEB séries iniciais (rede municipal)",
    )

    m = folium.Map(
        location=RIO_CENTER,
        zoom_start=RIO_ZOOM,
        tiles="cartodbpositron",  # neutral, light, doesn't compete with the data
        control_scale=True,
    )

    # One feature group per year — only DEFAULT_YEAR is visible at start
    for y in YEARS:
        layer = build_year_layer(hexes, ideb, y, cmap, show=(y == DEFAULT_YEAR))
        layer.add_to(m)

    # Always-on bairro borders
    build_bairros_borders(bairros).add_to(m)

    cmap.add_to(m)
    folium.LayerControl(collapsed=False, position="topright").add_to(m)

    # Add a small explanatory caption
    title_html = """
        <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                    z-index: 9999; background: rgba(255,255,255,.92); padding: 8px 14px;
                    border-radius: 6px; font-family: sans-serif; font-size: 13px;
                    box-shadow: 0 2px 6px rgba(0,0,0,.12);">
            <strong>HEX-EDU</strong> · IDEB séries iniciais por hex H3 res 8 ·
            selecione um ano à direita
        </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    return m


def write_report() -> None:
    out = []
    out.append("# 08 — HEX-EDU interativo\n")
    out.append(
        "Mesmo conteúdo do [Relatório 07](07_hex_edu_static.md), mas em formato "
        "interativo: panning, zoom, tooltip por hex, e seletor de ano (toggle entre os "
        "9 IDEBs disponíveis, 2007–2023).\n"
    )
    out.append(
        '<iframe src="_assets/08_hex_edu_interactive.html" '
        'width="100%" height="640" style="border:1px solid #ddd; border-radius:4px;">'
        "</iframe>\n"
    )
    out.append("## Como usar\n")
    out.append(
        "- **Painel direito**: alterne entre os anos disponíveis. Camada `Bordas de bairros` é always-on.\n"
        "- **Hover sobre um hex**: mostra bairro, IDEB do ano selecionado, RP e AP.\n"
        "- **Zoom**: scroll do mouse. Clique-arraste para mover.\n"
        "- **Hexes cinza**: bairro sem IDEB municipal naquele ano.\n"
    )
    out.append("## Limites técnicos\n")
    out.append(
        "- HTML standalone com 9 camadas pré-renderizadas (~1593 features cada). "
        "Tamanho: ~1–2 MiB. Carrega de uma vez; não há lazy-loading.\n"
        "- Não funciona offline (depende dos tiles `cartodbpositron`).\n"
        "- Versão hospedada Streamlit (com slider contínuo, filtros por faixa de IDEB, "
        "pesos por matrícula) fica no roadmap pós-v0.1.\n"
    )
    out.append("## Reprodutibilidade\n")
    out.append(
        "```bash\n"
        "pip install -r requirements.txt   # inclui folium e branca\n"
        "python3 analysis/14_hex_edu_folium.py\n"
        "```\n"
    )

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


def main() -> int:
    hexes, bairros, ideb = load_data()
    print(f"loaded: {len(hexes)} hexes, {len(bairros)} bairros, {len(ideb)} IDEB rows")

    m = build_map(hexes, bairros, ideb)

    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT_HTML))
    print(f"wrote {OUT_HTML.relative_to(ROOT)} ({OUT_HTML.stat().st_size / 1024:.0f} KiB)")

    write_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
