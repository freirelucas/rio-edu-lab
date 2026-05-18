"""VULN-EDU — figuras Plotly para o relatório 15 + página-produto.

Gera:
  - vuln_edu_scatter.json     Scatter IDS × IDEB por bairro (colored by AP).
  - vuln_edu_map.json         Choropleth de bairros por quadrante VULN.
  - vuln_edu_top.json         Bar horizontal dos 15 bairros mais vulneráveis.

Inputs:
  - data/processed/vuln_edu_bairros.csv
  - data/processed/vuln_edu_summary.json
  - data/raw/geo/bairros.geojson

Uso:
  python3 analysis/30_vuln_edu_charts.py
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
VULN_CSV = ROOT / "data" / "processed" / "vuln_edu_bairros.csv"
VULN_SUMMARY = ROOT / "data" / "processed" / "vuln_edu_summary.json"
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"

OUT_DIR = ROOT / "docs" / "_assets" / "charts"

QUADRANT_COLORS = {
    "Q1: alto IDS · alto IDEB": "#2166ac",
    "Q2: baixo IDS · alto IDEB (resiliente)": "#67a9cf",
    "Q3: alto IDS · baixo IDEB (sub-performance)": "#fddbc7",
    "Q4: baixo IDS · baixo IDEB (vulnerável)": "#b2182b",
}
QUADRANT_ORDER = list(QUADRANT_COLORS.keys())

AP_COLORS = {
    "Área de Planejamento 1": "#7570b3",
    "Área de Planejamento 2": "#1b9e77",
    "Área de Planejamento 3": "#d95f02",
    "Área de Planejamento 4": "#e7298a",
    "Área de Planejamento 5": "#66a61e",
}


def write(name: str, fig: go.Figure) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = fig.to_json()
    raw = re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group(0)):.5f}", raw)
    (OUT_DIR / f"{name}.json").write_text(raw, encoding="utf-8")
    print(f"  wrote {OUT_DIR.relative_to(ROOT) / (name + '.json')}")


def build_scatter(df: pd.DataFrame, summary: dict) -> None:
    print("building vuln_edu_scatter …")
    ids_med = summary["quadrants"]["ids_median_threshold"]
    ideb_med = summary["quadrants"]["ideb_median_threshold"]
    ols = summary["ols_ideb_on_ids"]

    fig = go.Figure()

    # Quadrant background shading (Q4 = vulnerable highlighted)
    fig.add_shape(
        type="rect", xref="x", yref="y",
        x0=df["ids_median"].min() - 0.02, x1=ids_med,
        y0=df["ideb"].min() - 0.1, y1=ideb_med,
        fillcolor="#b2182b", opacity=0.06, line_width=0,
    )

    # OLS regression line
    x_line = np.linspace(df["ids_median"].min(), df["ids_median"].max(), 50)
    y_line = ols["intercept"] + ols["slope"] * x_line
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line, mode="lines",
        line={"color": "#555", "width": 2, "dash": "dash"},
        name=f"OLS: IDEB = {ols['intercept']:.2f} + {ols['slope']:.2f}·IDS (R²={ols['r2']:.2f})",
        hoverinfo="skip",
        showlegend=True,
    ))

    # One trace per AP for clear legend grouping
    for ap, color in AP_COLORS.items():
        sub = df[df["ap"] == ap]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["ids_median"], y=sub["ideb"],
            mode="markers",
            name=ap.replace("Área de Planejamento ", "AP "),
            marker={"color": color, "size": 9, "line": {"width": 0.5, "color": "white"}},
            text=sub["bairro"],
            customdata=np.stack([sub["ra"], sub["vuln_score"], sub["quadrante"]], axis=-1),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "RA: %{customdata[0]}<br>"
                "IDS (mediana setores): %{x:.3f}<br>"
                "IDEB séries iniciais 2023: %{y:.2f}<br>"
                "VULN score: %{customdata[1]:+.2f}<br>"
                "%{customdata[2]}<extra></extra>"
            ),
        ))

    # Median crosshairs
    fig.add_vline(x=ids_med, line_color="#888", line_width=1, line_dash="dot",
                  annotation_text=f"mediana IDS = {ids_med:.2f}", annotation_position="top")
    fig.add_hline(y=ideb_med, line_color="#888", line_width=1, line_dash="dot",
                  annotation_text=f"mediana IDEB = {ideb_med:.2f}", annotation_position="right")

    # Quadrant labels
    label_specs = [
        ("Q4 vulnerável", df["ids_median"].min() + 0.02, df["ideb"].min() + 0.1),
        ("Q1 privilegiado", df["ids_median"].max() - 0.02, df["ideb"].max() - 0.1),
        ("Q2 resiliente", df["ids_median"].min() + 0.02, df["ideb"].max() - 0.1),
        ("Q3 sub-performance", df["ids_median"].max() - 0.02, df["ideb"].min() + 0.1),
    ]
    for txt, x, y in label_specs:
        fig.add_annotation(x=x, y=y, text=f"<b>{txt}</b>", showarrow=False,
                           font={"size": 11, "color": "#444"}, opacity=0.7)

    fig.update_layout(
        title=("VULN-EDU — IDS (Censo 2010) × IDEB séries iniciais 2023, por bairro · "
               f"n = {len(df)}"),
        xaxis_title="IDS mediana dos setores censitários (0–1)",
        yaxis_title="IDEB séries iniciais 2023",
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 70, "r": 30, "t": 80, "b": 60},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.22,
                "xanchor": "center", "x": 0.5},
    )
    fig.update_xaxes(gridcolor="#eee", zeroline=False)
    fig.update_yaxes(gridcolor="#eee", zeroline=False)
    write("vuln_edu_scatter", fig)


def build_map(df: pd.DataFrame) -> None:
    print("building vuln_edu_map …")
    bairros = gpd.read_file(BAIRROS_GEOJSON).to_crs(4326)
    bairros["nome"] = bairros["nome"].astype(str).str.strip()
    bairros["geometry"] = bairros.geometry.simplify(0.0002, preserve_topology=True)

    df = df.copy()
    df["bairro_norm"] = df["bairro"].str.strip()
    merged = bairros.merge(df, left_on="nome", right_on="bairro_norm", how="left")

    # Numeric code for quadrante (for color mapping)
    quad_to_code = {q: i for i, q in enumerate(QUADRANT_ORDER)}
    merged["quad_code"] = merged["quadrante"].map(quad_to_code)

    geo = json.loads(merged[["nome", "geometry"]].to_json())

    fig = go.Figure(go.Choropleth(
        geojson=geo,
        locations=merged["nome"],
        featureidkey="properties.nome",
        z=merged["quad_code"],
        zmin=-0.5, zmax=3.5,
        colorscale=[
            [0.00, QUADRANT_COLORS[QUADRANT_ORDER[0]]],
            [0.25, QUADRANT_COLORS[QUADRANT_ORDER[0]]],
            [0.25, QUADRANT_COLORS[QUADRANT_ORDER[1]]],
            [0.50, QUADRANT_COLORS[QUADRANT_ORDER[1]]],
            [0.50, QUADRANT_COLORS[QUADRANT_ORDER[2]]],
            [0.75, QUADRANT_COLORS[QUADRANT_ORDER[2]]],
            [0.75, QUADRANT_COLORS[QUADRANT_ORDER[3]]],
            [1.00, QUADRANT_COLORS[QUADRANT_ORDER[3]]],
        ],
        marker_line_color="white", marker_line_width=0.4,
        showscale=False,
        text=merged["nome"],
        customdata=np.stack([
            merged["quadrante"].fillna("(sem cruzamento)"),
            merged["ids_median"].fillna(np.nan),
            merged["ideb"].fillna(np.nan),
            merged["vuln_score"].fillna(np.nan),
        ], axis=-1),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "%{customdata[0]}<br>"
            "IDS: %{customdata[1]:.3f}<br>"
            "IDEB 2023: %{customdata[2]:.2f}<br>"
            "VULN: %{customdata[3]:+.2f}<extra></extra>"
        ),
    ))

    # Legend via dummy traces
    for q, color in QUADRANT_COLORS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker={"color": color, "size": 12, "symbol": "square"},
            name=q,
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
        title="VULN-EDU — bairros por quadrante (IDS × IDEB)",
        height=540,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 0, "r": 0, "t": 60, "b": 0},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.05,
                "xanchor": "center", "x": 0.5, "font": {"size": 10}},
    )
    write("vuln_edu_map", fig)


def build_top_bar(df: pd.DataFrame, n: int = 15) -> None:
    print("building vuln_edu_top …")
    top = df.nlargest(n, "vuln_score").iloc[::-1]  # reverse for horizontal bar
    bot = df.nsmallest(n, "vuln_score")            # least vulnerable

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(f"{n} bairros mais vulneráveis",
                        f"{n} bairros menos vulneráveis"),
        horizontal_spacing=0.30,
    )

    fig.add_trace(go.Bar(
        y=top["bairro"],
        x=top["vuln_score"],
        orientation="h",
        marker={"color": QUADRANT_COLORS["Q4: baixo IDS · baixo IDEB (vulnerável)"]},
        text=[f"IDS {ids:.2f} · IDEB {ideb:.1f}"
              for ids, ideb in zip(top["ids_median"], top["ideb"])],
        textposition="inside",
        textfont={"color": "white", "size": 10},
        hovertemplate="<b>%{y}</b><br>VULN score: %{x:+.2f}<br>%{text}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=bot["bairro"],
        x=bot["vuln_score"],
        orientation="h",
        marker={"color": QUADRANT_COLORS["Q1: alto IDS · alto IDEB"]},
        text=[f"IDS {ids:.2f} · IDEB {ideb:.1f}"
              for ids, ideb in zip(bot["ids_median"], bot["ideb"])],
        textposition="inside",
        textfont={"color": "white", "size": 10},
        hovertemplate="<b>%{y}</b><br>VULN score: %{x:+.2f}<br>%{text}<extra></extra>",
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        height=540,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 30, "r": 30, "t": 60, "b": 60},
    )
    fig.update_xaxes(title_text="VULN score (+ = mais vulnerável)", row=1, col=1, gridcolor="#eee")
    fig.update_xaxes(title_text="VULN score (− = mais privilegiado)", row=1, col=2, gridcolor="#eee")
    write("vuln_edu_top", fig)


def main() -> int:
    if not (VULN_CSV.exists() and BAIRROS_GEOJSON.exists() and VULN_SUMMARY.exists()):
        print("missing inputs; run sessions 11 + 29 first")
        return 1

    df = pd.read_csv(VULN_CSV)
    summary = json.loads(VULN_SUMMARY.read_text(encoding="utf-8"))
    print(f"loaded {len(df)} bairros from {VULN_CSV.relative_to(ROOT)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_scatter(df, summary)
    build_map(df)
    build_top_bar(df)
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
