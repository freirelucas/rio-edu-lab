"""Generate the Plotly figure JSONs consumed by the new UX pages.

Each chart is materialized as `docs/_assets/charts/<id>.json` ready to
be loaded by `docs/javascripts/charts.js` via `<div data-chart="...">`.

Charts produced:

  hero_toggle.json
    Side-by-side Plotly choropleth (RA vs H3) with a dropdown to
    toggle scenes. Drives the landing page hero.

  tour_slide_1.json   RA-only choropleth (the "antes").
  tour_slide_2.json   H3-only choropleth (the "depois").
  tour_slide_3.json   Robustness panel: share_within over 9 years for
                      ANOS_INICIAIS, ANOS_FINAIS, weighted, Aprovação,
                      SAEB, IDEB.
  tour_slide_4.json   Combined PM-12 scaling + FUN-Rio Δ histogram.
  tour_slide_5.json   Top priority bairros bar chart (ranked).

Usage:
  python3 analysis/21_build_tour_charts.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"
HEX_GEOJSON = ROOT / "data" / "processed" / "h3_grid.geojson"
IDEB_LONG = ROOT / "data" / "processed" / "ideb_bairros.csv"
THEIL_INI = ROOT / "data" / "processed" / "theil_ideb_anos_iniciais.csv"
THEIL_FIN = ROOT / "data" / "processed" / "theil_ideb_anos_finais.csv"
THEIL_WEIGHTED = ROOT / "data" / "processed" / "theil_ideb_weighted.csv"
THEIL_COMP = ROOT / "data" / "processed" / "theil_components.csv"
PM12_CSV = ROOT / "data" / "processed" / "pm12_scaling.csv"
PM12_FIT = ROOT / "data" / "processed" / "pm12_fit.json"
FUN_TRANS = ROOT / "data" / "processed" / "fun_rio_transitions.csv"

OUT_DIR = ROOT / "docs" / "_assets" / "charts"

# Same divergent palette anchored at IDEB = 6.0 used in static maps + reports.
IDEB_COLORSCALE = "RdBu"
IDEB_VMIN, IDEB_VMID, IDEB_VMAX = 4.5, 6.0, 7.5

PALETTE = {
    "teal": "#008572",
    "red": "#b2182b",
    "blue": "#2166ac",
    "gray": "#6c757d",
    "soft_red": "#ef8a62",
    "soft_blue": "#67a9cf",
}


def normalize(name: str) -> str:
    s = (name or "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def ra_key(s: str) -> str:
    """Strip the leading roman numeral so IDEB 'I Portuária' matches geom 'PORTUARIA'."""
    s = re.sub(r"^[IVX]+\s+", "", str(s).strip())
    return normalize(s).upper()


def write(name: str, fig: go.Figure) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.loads(fig.to_json())
    raw = json.dumps(payload, ensure_ascii=False)
    # Round coordinates to 5 decimals (~1.1m) — saves ~3-4x on inline GeoJSON
    # without visible loss at the zoom levels we render.
    raw = re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group(0)):.5f}", raw)
    (OUT_DIR / f"{name}.json").write_text(raw, encoding="utf-8")
    print(f"  wrote {OUT_DIR.relative_to(ROOT) / (name + '.json')}")


def load_geo_data():
    bairros = gpd.read_file(BAIRROS_GEOJSON).to_crs(4326)
    bairros["nome"] = bairros["nome"].astype(str).str.strip()
    bairros["regiao_adm"] = bairros["regiao_adm"].astype(str).str.strip()
    bairros["ra_match"] = bairros["regiao_adm"].apply(lambda s: normalize(s).upper())

    hexes = gpd.read_file(HEX_GEOJSON).to_crs(4326)
    hexes["ideb_bairro"] = hexes["ideb_bairro"].astype(str).str.strip()

    ideb = pd.read_csv(IDEB_LONG)
    ideb["bairro"] = ideb["bairro"].astype(str).str.strip()
    ideb["ra_match"] = ideb["ra"].apply(ra_key)
    return bairros, hexes, ideb


def _simplify(gdf: gpd.GeoDataFrame, tolerance_deg: float) -> gpd.GeoDataFrame:
    out = gdf.copy()
    out["geometry"] = out.geometry.simplify(tolerance_deg, preserve_topology=True)
    return out


def ra_choropleth(bairros: gpd.GeoDataFrame, ideb: pd.DataFrame, year: int) -> go.Choropleth:
    """RA-level choropleth: dissolve bairros into RAs, color by mean IDEB."""
    bairros["regiao_adm"] = bairros["regiao_adm"].astype(str).str.strip()
    ras = bairros.dissolve(by="regiao_adm", aggfunc="first").reset_index()
    ras["ra_match"] = ras["regiao_adm"].apply(lambda s: normalize(s).upper())
    # ~30m tolerance — RA polygons are huge; we don't need coastline detail.
    ras = _simplify(ras, 0.0003)

    means = ideb[ideb["year"] == year].groupby("ra_match")["ideb"].mean()
    ras["ideb"] = ras["ra_match"].map(means)

    geo = json.loads(ras[["ra_match", "geometry"]].to_json())
    return go.Choropleth(
        geojson=geo,
        locations=ras["ra_match"],
        featureidkey="properties.ra_match",
        z=ras["ideb"],
        zmin=IDEB_VMIN, zmax=IDEB_VMAX, zmid=IDEB_VMID,
        colorscale=IDEB_COLORSCALE,
        marker_line_color="white", marker_line_width=0.5,
        colorbar_title=f"IDEB {year}",
        text=ras["regiao_adm"],
        hovertemplate="<b>%{text}</b><br>IDEB: %{z:.2f}<extra></extra>",
    )


def hex_choropleth(hexes: gpd.GeoDataFrame, ideb: pd.DataFrame, year: int) -> go.Choropleth:
    lookup = {row["bairro"]: row["ideb"] for _, row in ideb[ideb["year"] == year].iterrows()}
    h = hexes.copy()
    h["ideb"] = [lookup.get(b) for b in h["ideb_bairro"]]
    # Hex polygons are already small (6 vertices each); a tiny simplify still
    # trims the inlined string a bit by collapsing collinear-ish points.
    h = _simplify(h, 0.0001)

    geo = json.loads(h[["hex_id", "geometry"]].to_json())
    return go.Choropleth(
        geojson=geo,
        locations=h["hex_id"],
        featureidkey="properties.hex_id",
        z=h["ideb"],
        zmin=IDEB_VMIN, zmax=IDEB_VMAX, zmid=IDEB_VMID,
        colorscale=IDEB_COLORSCALE,
        marker_line_color="white", marker_line_width=0.05,
        colorbar_title=f"IDEB {year}",
        text=h["ideb_bairro"],
        hovertemplate="<b>%{text}</b><br>IDEB: %{z:.2f}<extra></extra>",
    )


def map_layout(title: str | None = None) -> dict[str, Any]:
    return {
        "geo": {
            "fitbounds": "locations",
            "visible": False,
            "projection_type": "mercator",
            "showcoastlines": False,
            "showframe": False,
            "bgcolor": "rgba(0,0,0,0)",
        },
        "margin": {"l": 0, "r": 0, "t": 30 if title else 0, "b": 0},
        "title": title,
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
    }


def build_hero_toggle(bairros, hexes, ideb) -> None:
    """Hero chart: 2 traces (RA + H3) with a button toggling visibility."""
    print("building hero_toggle …")
    year = 2023
    fig = go.Figure()
    ra_trace = ra_choropleth(bairros, ideb, year)
    hex_trace = hex_choropleth(hexes, ideb, year)
    ra_trace.update(visible=True)
    hex_trace.update(visible=False)
    fig.add_trace(ra_trace)
    fig.add_trace(hex_trace)

    fig.update_layout(
        **map_layout(),
        height=420,
        updatemenus=[{
            "type": "buttons",
            "direction": "right",
            "x": 0.5, "y": 1.06,
            "xanchor": "center",
            "showactive": True,
            "buttons": [
                {
                    "label": "Por RA (33)",
                    "method": "update",
                    "args": [{"visible": [True, False]}],
                },
                {
                    "label": "Por bairro (H3)",
                    "method": "update",
                    "args": [{"visible": [False, True]}],
                },
            ],
        }],
        annotations=[{
            "text": f"IDEB {year} · clique para alternar a granularidade",
            "showarrow": False, "x": 0.5, "y": -0.04, "xref": "paper", "yref": "paper",
            "font": {"size": 11, "color": PALETTE["gray"]},
        }],
    )
    write("hero_toggle", fig)


def build_tour_slide_1(bairros, ideb) -> None:
    print("building tour_slide_1 …")
    fig = go.Figure(ra_choropleth(bairros, ideb, 2023))
    fig.update_layout(**map_layout("Por RA (33 unidades) — média do IDEB 2023"))
    fig.update_layout(height=460)
    write("tour_slide_1", fig)


def build_tour_slide_2(hexes, ideb) -> None:
    print("building tour_slide_2 …")
    fig = go.Figure(hex_choropleth(hexes, ideb, 2023))
    fig.update_layout(**map_layout("Por bairro (1593 hex H3) — IDEB 2023"))
    fig.update_layout(height=460)
    write("tour_slide_2", fig)


def build_tour_slide_3() -> None:
    """Robustness panel: share_within across 6 series."""
    print("building tour_slide_3 …")
    ini = pd.read_csv(THEIL_INI)
    fin = pd.read_csv(THEIL_FIN)
    weighted = pd.read_csv(THEIL_WEIGHTED)
    comp = pd.read_csv(THEIL_COMP)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ini["year"], y=ini["share_within"] * 100,
        mode="lines+markers", name="IDEB 5º (base)",
        line={"color": PALETTE["teal"], "width": 3}, marker={"size": 9},
    ))
    fig.add_trace(go.Scatter(
        x=fin["year"], y=fin["share_within"] * 100,
        mode="lines+markers", name="IDEB 9º",
        line={"color": PALETTE["red"], "width": 2.5, "dash": "dash"}, marker={"size": 7},
    ))
    fig.add_trace(go.Scatter(
        x=weighted["year"], y=weighted["share_within_weighted"] * 100,
        mode="markers", name="IDEB 5º ponderado por matrícula",
        marker={"size": 14, "color": PALETTE["blue"], "symbol": "diamond"},
    ))
    for component, color in [("aprovacao", PALETTE["soft_red"]), ("saeb", PALETTE["soft_blue"])]:
        sub = comp[comp["component"] == component].sort_values("year")
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["share_within"] * 100,
            mode="lines+markers",
            name="Aprovação" if component == "aprovacao" else "SAEB",
            line={"color": color, "width": 1.5, "dash": "dot"}, marker={"size": 6},
        ))

    fig.add_hline(y=50, line_dash="dot", line_color=PALETTE["gray"],
                  annotation_text="50% (linha de paridade)",
                  annotation_position="bottom right",
                  annotation_font_size=10)
    fig.update_layout(
        title="Parcela <b>within-RA</b> da desigualdade — robusto em 6 séries",
        xaxis_title="Ano",
        yaxis_title="% da desigualdade que está dentro das RAs",
        yaxis={"range": [40, 90], "ticksuffix": "%"},
        hovermode="x unified",
        height=440,
        margin={"l": 60, "r": 30, "t": 60, "b": 50},
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.32, "xanchor": "center", "x": 0.5},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(0,0,0,0.1)")
    write("tour_slide_3", fig)


def build_tour_slide_4() -> None:
    """Two-panel: PM-12 scaling scatter + FUN-Rio Δ histogram."""
    print("building tour_slide_4 …")
    pm = pd.read_csv(PM12_CSV)
    fit = json.loads(PM12_FIT.read_text(encoding="utf-8"))
    fun = pd.read_csv(FUN_TRANS)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f"PM-12: escolas vs matrícula (β = {fit['exponent_beta']:.2f}, sublinear)",
            f"FUN-Rio: Δ IDEB 9º−5º (média {fun['delta'].mean():+.2f})",
        ),
        horizontal_spacing=0.12,
    )

    # left scatter
    fig.add_trace(
        go.Scatter(
            x=pm["matriculas"], y=pm["escolas"],
            mode="markers",
            marker={"size": 7, "color": PALETTE["teal"], "opacity": 0.65},
            name="bairros",
            hovertemplate="<b>%{text}</b><br>matrículas: %{x:,}<br>escolas: %{y}<extra></extra>",
            text=pm["bairro"],
            showlegend=False,
        ),
        row=1, col=1,
    )
    xs = np.geomspace(pm["matriculas"].min(), pm["matriculas"].max(), 100)
    A, beta = fit["intercept_A"], fit["exponent_beta"]
    fig.add_trace(
        go.Scatter(
            x=xs, y=A * xs**beta, mode="lines",
            name=f"escolas = {A:.3f}·m^{beta:.2f}",
            line={"color": PALETTE["red"], "width": 2.5},
            hoverinfo="skip",
        ),
        row=1, col=1,
    )
    fig.update_xaxes(type="log", title_text="matrículas (log)", row=1, col=1)
    fig.update_yaxes(type="log", title_text="escolas (log)", row=1, col=1)

    # right histogram
    fig.add_trace(
        go.Histogram(
            x=fun["delta"], nbinsx=40,
            marker={"color": PALETTE["soft_blue"], "line": {"color": "white", "width": 1}},
            showlegend=False,
            hovertemplate="Δ ∈ %{x}<br>n = %{y}<extra></extra>",
        ),
        row=1, col=2,
    )
    fig.add_vline(x=0, line_dash="dash", line_color="black", row=1, col=2)
    fig.add_vline(
        x=fun["delta"].mean(), line_color=PALETTE["red"], line_width=2,
        annotation_text=f"média {fun['delta'].mean():+.2f}",
        annotation_position="top right", row=1, col=2,
    )
    fig.update_xaxes(title_text="Δ IDEB (9º − 5º)", row=1, col=2)
    fig.update_yaxes(title_text="bairro-coortes", row=1, col=2)

    fig.update_layout(
        height=440,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 60, "r": 30, "t": 60, "b": 50},
    )
    write("tour_slide_4", fig)


def build_tour_slide_5() -> None:
    """Top-15 priority bairros (combined SAMI + ΔFUN)."""
    print("building tour_slide_5 …")
    pm = pd.read_csv(PM12_CSV)[["bairro", "ap", "sami"]]
    fun = pd.read_csv(FUN_TRANS)
    fun_mean = (
        fun.groupby("bairro", as_index=False)["delta"]
        .mean()
        .rename(columns={"delta": "delta_mean"})
    )
    merged = pm.merge(fun_mean, on="bairro", how="inner").dropna()

    # Combined priority score: lower SAMI + lower delta = higher priority.
    # Z-score each, sum, then negate so that higher = more priority.
    merged["sami_z"] = (merged["sami"] - merged["sami"].mean()) / merged["sami"].std()
    merged["delta_z"] = (merged["delta_mean"] - merged["delta_mean"].mean()) / merged["delta_mean"].std()
    merged["priority"] = -(merged["sami_z"] + merged["delta_z"])

    top = merged.nlargest(15, "priority").iloc[::-1]  # reverse for top-down bar order

    fig = go.Figure(go.Bar(
        x=top["priority"],
        y=top["bairro"] + "  (AP " + top["ap"].str[-1] + ")",
        orientation="h",
        marker={
            "color": top["priority"],
            "colorscale": [[0, PALETTE["soft_blue"]], [1, PALETTE["red"]]],
            "line": {"color": "white", "width": 1},
        },
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Δ IDEB médio (FUN-Rio): %{customdata[0]:+.2f}<br>"
            "SAMI (PM-12): %{customdata[1]:+.2f}<br>"
            "Score combinado: %{x:.2f}<extra></extra>"
        ),
        customdata=top[["delta_mean", "sami"]].values,
    ))
    fig.update_layout(
        title="<b>Top 15 bairros prioritários</b><br>"
              "<sub>Combinando déficit de escolas (SAMI &lt; 0) + queda 5º→9º (Δ &lt; 0)</sub>",
        xaxis_title="Score de prioridade (z combinado)",
        yaxis={"automargin": True},
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 220, "r": 40, "t": 70, "b": 50},
    )
    fig.update_xaxes(gridcolor="rgba(0,0,0,0.08)")
    write("tour_slide_5", fig)


def main() -> int:
    bairros, hexes, ideb = load_geo_data()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    build_hero_toggle(bairros, hexes, ideb)
    build_tour_slide_1(bairros, ideb)
    build_tour_slide_2(hexes, ideb)
    build_tour_slide_3()
    build_tour_slide_4()
    build_tour_slide_5()

    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
