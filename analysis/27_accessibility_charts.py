"""HEX-EDU acessibilidade — Plotly figures para o relatório 14 + páginas-produto.

Gera:
  - acessibilidade_map.json   Choropleth H3 por acesso_quality (Pereira-style).
  - acessibilidade_dist.json  Distribuição de acesso por AP + dist_min.

Inputs:
  - data/processed/hex_accessibility.csv
  - data/processed/h3_grid.geojson
  - data/raw/geo/escolas_municipais.geojson  (para sobrepor pontos no mapa)

Uso:
  python3 analysis/27_accessibility_charts.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent
HEX_GEOJSON = ROOT / "data" / "processed" / "h3_grid.geojson"
ACCESS_CSV = ROOT / "data" / "processed" / "hex_accessibility.csv"
ESCOLAS_GEOJSON = ROOT / "data" / "raw" / "geo" / "escolas_municipais.geojson"

OUT_DIR = ROOT / "docs" / "_assets" / "charts"
PALETTE = {
    "low": "#b2182b",
    "mid": "#fddbc7",
    "high": "#2166ac",
    "gray": "#888888",
    "green": "#1a9850",
}


def write(name: str, fig: go.Figure) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = fig.to_json()
    raw = re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group(0)):.5f}", raw)
    (OUT_DIR / f"{name}.json").write_text(raw, encoding="utf-8")
    print(f"  wrote {OUT_DIR.relative_to(ROOT) / (name + '.json')}")


def build_access_map() -> None:
    print("building acessibilidade_map …")
    hexes = gpd.read_file(HEX_GEOJSON).to_crs(4326)
    hexes["geometry"] = hexes.geometry.simplify(0.0001, preserve_topology=True)
    access = pd.read_csv(ACCESS_CSV)
    # Only join numeric metrics; the categorical attrs (bairro, area_plane, etc.)
    # already live on `hexes` from session 12.
    h = hexes.merge(
        access[["hex_id", "acesso_quality", "n_5km", "dist_min_km"]],
        on="hex_id", how="left",
    )

    geo = json.loads(h[["hex_id", "geometry"]].to_json())
    fig = go.Figure(go.Choropleth(
        geojson=geo,
        locations=h["hex_id"],
        featureidkey="properties.hex_id",
        z=h["acesso_quality"],
        zmin=0, zmax=200,
        colorscale=[
            [0, PALETTE["low"]],
            [0.25, PALETTE["mid"]],
            [0.6, PALETTE["high"]],
            [1.0, PALETTE["green"]],
        ],
        marker_line_color="white", marker_line_width=0.05,
        colorbar_title="acesso_quality",
        text=h["ideb_bairro"],
        customdata=np.stack([h["n_5km"], h["dist_min_km"], h["area_plane"].astype(str)], axis=-1),
        hovertemplate=(
            "<b>%{text}</b> · AP %{customdata[2]}<br>"
            "acesso_quality: %{z:.1f}<br>"
            "escolas em 5 km: %{customdata[0]}<br>"
            "dist min: %{customdata[1]:.2f} km<extra></extra>"
        ),
    ))
    fig.update_layout(
        geo={
            "fitbounds": "locations",
            "visible": False,
            "projection_type": "mercator",
            "showcoastlines": False,
            "showframe": False,
            "bgcolor": "rgba(0,0,0,0)",
        },
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        title="HEX-EDU — acessibilidade ponderada por IDEB (Pereira-style, v0.6)",
        height=540,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    write("acessibilidade_map", fig)


def build_dist_panel() -> None:
    print("building acessibilidade_dist …")
    df = pd.read_csv(ACCESS_CSV).dropna(subset=["acesso_quality"])
    df["AP"] = df["area_plane"].apply(lambda x: f"AP {int(x)}" if pd.notna(x) else "?")

    # Sort APs by ascending median
    ap_order = df.groupby("AP")["acesso_quality"].median().sort_values().index.tolist()

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "Distribuição de acesso_quality por AP",
            "Distância mínima a equipamento (escolas eleg.)",
        ),
        horizontal_spacing=0.14,
    )

    # Box-plot left
    palette = ["#b2182b", "#ef8a62", "#fddbc7", "#67a9cf", "#2166ac"]
    for i, ap in enumerate(ap_order):
        sub = df[df["AP"] == ap]
        fig.add_trace(
            go.Box(
                y=sub["acesso_quality"], name=ap,
                marker={"color": palette[i % len(palette)]},
                boxmean=True,
                showlegend=False,
            ),
            row=1, col=1,
        )
    fig.update_yaxes(title_text="acesso_quality (Pereira)", row=1, col=1)

    # Histogram of dist_min_km right
    fig.add_trace(
        go.Histogram(
            x=df["dist_min_km"].dropna(),
            nbinsx=40,
            marker={"color": "#67a9cf", "line": {"color": "white", "width": 1}},
            showlegend=False,
            hovertemplate="dist ∈ %{x:.2f} km<br>n = %{y}<extra></extra>",
        ),
        row=1, col=2,
    )
    fig.add_vline(
        x=df["dist_min_km"].median(),
        line_color=PALETTE["low"], line_width=2,
        annotation_text=f"mediana {df['dist_min_km'].median():.2f} km",
        annotation_position="top right", row=1, col=2,
    )
    fig.update_xaxes(title_text="distância à escola mais próxima (km)", row=1, col=2)
    fig.update_yaxes(title_text="hexes", row=1, col=2)

    fig.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 60, "r": 30, "t": 60, "b": 50},
    )
    write("acessibilidade_dist", fig)


def main() -> int:
    if not all(p.exists() for p in (HEX_GEOJSON, ACCESS_CSV)):
        print("missing inputs; run sessions 12 + 26 first")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_access_map()
    build_dist_panel()
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
