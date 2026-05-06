"""Mapa estático HEX-EDU: IDEB por hex H3 vs por RA, lado-a-lado.

Argumento visual do achado central do projeto (Relatório 06):
60–70% da desigualdade do IDEB municipal está DENTRO das RAs, não entre.
Política em granularidade de RA (a default do IPP) mascara variação real.
Este mapa expõe isso: mesmo dado, duas resoluções, conclusões diferentes.

Para os anos 2007, 2013, 2019, 2023 (snapshots cobrindo o período inteiro):
  - Esquerda: choropleth dos polígonos das RAs, IDEB médio por RA
  - Direita: choropleth dos hexes H3 res 8, IDEB do bairro do centroide

Outputs:
  - data/processed/hex_ideb_panel.csv
  - docs/reports/_assets/07_hex_edu_panel.png
  - docs/reports/_assets/07_hex_edu_2023.png   (zoom no ano mais recente)
  - docs/reports/07_hex_edu_static.md

Uso:
  python3 analysis/13_hex_edu_static.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

mpl.rcParams["figure.dpi"] = 130
mpl.rcParams["savefig.dpi"] = 160
mpl.rcParams["font.family"] = "DejaVu Sans"

ROOT = Path(__file__).resolve().parent.parent
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"
HEX_GEOJSON = ROOT / "data" / "processed" / "h3_grid.geojson"
HEX_LOOKUP = ROOT / "data" / "processed" / "hex_to_bairro.csv"
IDEB_CSV = ROOT / "data" / "processed" / "ideb_bairros.csv"

OUT_PANEL_PNG = ROOT / "docs" / "reports" / "_assets" / "07_hex_edu_panel.png"
OUT_2023_PNG = ROOT / "docs" / "reports" / "_assets" / "07_hex_edu_2023.png"
OUT_PANEL_CSV = ROOT / "data" / "processed" / "hex_ideb_panel.csv"
OUT_REPORT = ROOT / "docs" / "reports" / "07_hex_edu_static.md"

YEARS_PANEL = [2007, 2013, 2019, 2023]

# Divergent palette anchored at the city-wide IDEB mean (~6.0).
# Below = red, near = white, above = blue.
PALETTE = "RdBu"
VMIN, VCENTER, VMAX = 4.5, 6.0, 7.5


def load_data() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame]:
    bairros = gpd.read_file(BAIRROS_GEOJSON)
    if bairros.crs is None or bairros.crs.to_epsg() != 4326:
        bairros = bairros.set_crs(4326) if bairros.crs is None else bairros.to_crs(4326)
    bairros["nome"] = bairros["nome"].astype(str).str.strip()

    hexes = gpd.read_file(HEX_GEOJSON)
    if hexes.crs is None or hexes.crs.to_epsg() != 4326:
        hexes = hexes.set_crs(4326) if hexes.crs is None else hexes.to_crs(4326)

    ideb = pd.read_csv(IDEB_CSV)
    return bairros, hexes, ideb


def aggregate_ideb_by_ra(ideb: pd.DataFrame, year: int) -> pd.Series:
    yr = ideb[ideb["year"] == year]
    return yr.groupby("ra")["ideb"].mean()


def build_panel_df(hexes: gpd.GeoDataFrame, ideb: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    ideb_lookup = {(r["bairro"].strip(), int(r["year"])): r["ideb"] for _, r in ideb.iterrows()}
    for _, h in hexes.iterrows():
        for y in YEARS_PANEL:
            v = ideb_lookup.get((str(h["ideb_bairro"]).strip(), y))
            rows.append({
                "hex_id": h["hex_id"],
                "year": y,
                "ideb_bairro": h["ideb_bairro"],
                "ideb": v,
            })
    return pd.DataFrame(rows)


def add_norm_kwargs() -> dict:
    return {
        "cmap": PALETTE,
        "norm": mpl.colors.TwoSlopeNorm(vmin=VMIN, vcenter=VCENTER, vmax=VMAX),
    }


def plot_panel(
    bairros: gpd.GeoDataFrame,
    hexes: gpd.GeoDataFrame,
    ideb: pd.DataFrame,
    out_path: Path,
) -> None:
    """4 anos × 2 colunas (RA-choropleth, H3-choropleth)."""
    fig, axes = plt.subplots(
        nrows=len(YEARS_PANEL), ncols=2, figsize=(12, 4 * len(YEARS_PANEL))
    )

    # Lookup ideb by bairro x year for hex coloring (bairro names are normalized)
    ideb_lookup = {(r["bairro"].strip(), int(r["year"])): r["ideb"] for _, r in ideb.iterrows()}

    # We need a polygon per RA — derive from bairros by dissolving on regiao_adm
    bairros["regiao_adm"] = bairros["regiao_adm"].astype(str).str.strip()
    ras = bairros.dissolve(by="regiao_adm", aggfunc="first").reset_index()

    norm_kwargs = add_norm_kwargs()

    # Map IDEB-csv "ra" (e.g. "I Portuária") to geom "regiao_adm" (e.g. "PORTUARIA")
    # The IDEB ra is "[romano] Nome", geom regiao_adm is upper-case name only.
    # Build a normalization helper: remove leading roman+space, uppercase, strip.
    import re, unicodedata
    def ra_norm(s: str) -> str:
        s = re.sub(r"^[IVX]+\s+", "", str(s).strip())
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return s.upper()

    ras["ra_match"] = ras["regiao_adm"].apply(ra_norm)
    ideb["ra_match"] = ideb["ra"].apply(ra_norm)

    for row_idx, year in enumerate(YEARS_PANEL):
        # ---- left: RA choropleth
        ra_means = ideb[ideb["year"] == year].groupby("ra_match")["ideb"].mean()
        ras_y = ras.merge(ra_means.rename("ideb"), left_on="ra_match", right_index=True, how="left")

        ax_l = axes[row_idx, 0]
        ras_y.plot(
            column="ideb",
            ax=ax_l,
            edgecolor="white",
            linewidth=0.4,
            missing_kwds={"color": "#dddddd", "label": "sem dado"},
            **norm_kwargs,
        )
        ax_l.set_title(f"{year} — IDEB médio por RA", fontsize=11)
        ax_l.set_axis_off()

        # ---- right: H3 choropleth
        hexes_y = hexes.copy()
        hexes_y["ideb"] = [
            ideb_lookup.get((str(b).strip(), year))
            for b in hexes_y["ideb_bairro"]
        ]

        ax_r = axes[row_idx, 1]
        hexes_y.plot(
            column="ideb",
            ax=ax_r,
            edgecolor="white",
            linewidth=0.05,
            missing_kwds={"color": "#dddddd", "label": "sem dado"},
            **norm_kwargs,
        )
        # Bairros borders on top, light, for orientation
        bairros.boundary.plot(ax=ax_r, color="#222222", linewidth=0.3, alpha=0.5)
        ax_r.set_title(f"{year} — IDEB por H3 (bairro)", fontsize=11)
        ax_r.set_axis_off()

    # One shared colorbar
    sm = mpl.cm.ScalarMappable(cmap=PALETTE, norm=norm_kwargs["norm"])
    cbar = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.025, pad=0.03, aspect=50)
    cbar.set_label("IDEB séries iniciais (rede municipal)")

    fig.suptitle(
        "HEX-EDU: IDEB por RA vs por bairro (H3 res 8)\n"
        "esquerda mascara variação intra-RA; direita preserva.",
        fontsize=13,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(ROOT)}")


def plot_2023_zoom(
    bairros: gpd.GeoDataFrame,
    hexes: gpd.GeoDataFrame,
    ideb: pd.DataFrame,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))

    ideb_lookup = {(r["bairro"].strip(), int(r["year"])): r["ideb"] for _, r in ideb.iterrows()}
    bairros["regiao_adm"] = bairros["regiao_adm"].astype(str).str.strip()
    ras = bairros.dissolve(by="regiao_adm", aggfunc="first").reset_index()

    import re, unicodedata
    def ra_norm(s: str) -> str:
        s = re.sub(r"^[IVX]+\s+", "", str(s).strip())
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return s.upper()

    ras["ra_match"] = ras["regiao_adm"].apply(ra_norm)
    ideb["ra_match"] = ideb["ra"].apply(ra_norm)
    norm_kwargs = add_norm_kwargs()

    ra_means = ideb[ideb["year"] == 2023].groupby("ra_match")["ideb"].mean()
    ras_y = ras.merge(ra_means.rename("ideb"), left_on="ra_match", right_index=True, how="left")
    ras_y.plot(
        column="ideb", ax=axes[0],
        edgecolor="white", linewidth=0.5,
        missing_kwds={"color": "#dddddd"},
        **norm_kwargs,
    )
    axes[0].set_title("2023 — IDEB médio por RA (33 unidades)", fontsize=12)
    axes[0].set_axis_off()

    hexes_y = hexes.copy()
    hexes_y["ideb"] = [
        ideb_lookup.get((str(b).strip(), 2023))
        for b in hexes_y["ideb_bairro"]
    ]
    hexes_y.plot(
        column="ideb", ax=axes[1],
        edgecolor="white", linewidth=0.05,
        missing_kwds={"color": "#dddddd"},
        **norm_kwargs,
    )
    bairros.boundary.plot(ax=axes[1], color="#222222", linewidth=0.3, alpha=0.5)
    axes[1].set_title("2023 — IDEB por hex H3 res 8 (1593 unidades)", fontsize=12)
    axes[1].set_axis_off()

    sm = mpl.cm.ScalarMappable(cmap=PALETTE, norm=norm_kwargs["norm"])
    cbar = fig.colorbar(sm, ax=axes, orientation="horizontal", fraction=0.04, pad=0.05, aspect=50)
    cbar.set_label("IDEB séries iniciais 2023")

    fig.suptitle(
        "HEX-EDU 2023: o que o coroplético por RA esconde",
        fontsize=14, y=0.95,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out_path.relative_to(ROOT)}")


def write_report(panel_df: pd.DataFrame, hexes: gpd.GeoDataFrame) -> None:
    n_hexes = len(hexes)
    coverage = panel_df.groupby("year")["ideb"].apply(lambda s: s.notna().sum())
    n_with_data_2023 = int(coverage.get(2023, 0))

    lines: list[str] = []
    lines.append("# 07 — HEX-EDU estático: o que o coroplético por RA esconde\n")
    lines.append(
        "Primeiro entregável visual do produto **HEX-EDU**. Apresenta lado-a-lado o "
        "mesmo dado de IDEB séries iniciais em duas resoluções espaciais: agregado por "
        "**Região Administrativa** (33 unidades, padrão IPP) e por **hex H3 res 8** "
        f"(1593 unidades, herdando o IDEB do bairro do centroide).\n"
    )
    lines.append(
        "Justificativa metodológica direta no [Relatório 06](06_theil_ideb.md): "
        "60–70% da desigualdade do IDEB municipal está dentro das RAs em todos os "
        "9 anos disponíveis. O mapa da esquerda mascara essa variação. O da direita "
        "a preserva."
    )

    lines.append("## Mapa principal — 2023\n")
    lines.append("![HEX-EDU 2023](_assets/07_hex_edu_2023.png)\n")
    lines.append(
        f"_{n_hexes} hexes H3 ao todo; {n_with_data_2023} carregam IDEB de 2023 do "
        "bairro do seu centroide. Hexes em cinza: bairro sem IDEB municipal naquele "
        "ano (rede privada/estadual dominante, escolas suprimidas por baixa amostra, "
        "ou bairros sem escolas básicas reportadas)._\n"
    )

    lines.append("## Painel temporal — 4 snapshots de 2007 a 2023\n")
    lines.append("![HEX-EDU painel](_assets/07_hex_edu_panel.png)\n")

    lines.append("## Cobertura por ano\n")
    lines.append("| Ano | Hexes com IDEB | % cobertura |")
    lines.append("| ---: | ---: | ---: |")
    for y in YEARS_PANEL:
        c = int(coverage.get(y, 0))
        lines.append(f"| {y} | {c} | {c / n_hexes:.0%} |")
    lines.append("")

    lines.append("## Como ler\n")
    lines.append(
        "- **Paleta divergente** ancorada em IDEB = 6.0 (≈ média municipal). "
        "Vermelho = abaixo da média, azul = acima.\n"
        "- **Range fixado** em [4.5, 7.5] para que diferentes anos sejam comparáveis "
        "lado-a-lado. IDEB municipal raramente sai desse intervalo na prática.\n"
        "- **Linhas pretas finas** no mapa H3 são os limites de bairro do IPP — "
        "ajudam a identificar regiões.\n"
        "- **Cinza claro**: sem dado naquele ano. Comum em 2007 (ano inicial do IDEB) "
        "e em bairros pequenos sem escolas municipais.\n"
    )

    lines.append("## Caveats herdados\n")
    lines.append(
        "Tudo do Relatório 06 continua válido — peso igual por bairro, IDEB ≠ qualidade "
        "total, rede municipal apenas, MAUP. Aqui, dois novos:\n"
        "- **7 bairros não têm hex centroide em res 8** (Abolição, Argentino, Bancários, "
        "Cocotá, Jabour, Lapa, Saúde — todos pequenos). Aparecem em branco mesmo quando "
        "têm IDEB. Subir para res 9 (~12k hexes) cobriria todos, ao custo de mais ruído visual.\n"
        "- **O hex herda o IDEB do bairro inteiro**: dentro de bairros grandes (Santa Cruz, "
        "Campo Grande, Jacarepaguá), todos os hexes são uniformes. A real variância "
        "intra-bairro só apareceria com dado por escola, que o data.rio não publica.\n"
    )

    lines.append("## Reprodutibilidade\n")
    lines.append(
        "```bash\n"
        "pip install -r requirements.txt\n"
        "python3 analysis/11_fetch_bairros.py    # se ainda não fez\n"
        "python3 analysis/12_h3_grid.py\n"
        "python3 analysis/13_hex_edu_static.py\n"
        "```\n"
        "Saídas: `data/processed/hex_ideb_panel.csv`, e os PNGs em "
        "`docs/reports/_assets/`.\n"
    )

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


def main() -> int:
    bairros, hexes, ideb = load_data()
    print(f"loaded: {len(bairros)} bairros, {len(hexes)} hexes, {len(ideb)} IDEB rows")

    panel_df = build_panel_df(hexes, ideb)
    OUT_PANEL_CSV.parent.mkdir(parents=True, exist_ok=True)
    panel_df.to_csv(OUT_PANEL_CSV, index=False)
    print(f"wrote {OUT_PANEL_CSV.relative_to(ROOT)} ({len(panel_df)} rows)")

    plot_panel(bairros, hexes, ideb, OUT_PANEL_PNG)
    plot_2023_zoom(bairros, hexes, ideb, OUT_2023_PNG)
    write_report(panel_df, hexes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
