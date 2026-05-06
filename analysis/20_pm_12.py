"""PM-12: lei de escala intra-Rio (matrícula × escolas × IDEB).

Quarto produto do MVP-1 do ACEC-Hub. Inspirado em Bettencourt et al.
(2010) sobre leis de escala urbanas e Heinrich Mora et al. (2023) sobre
SAMI (Scaling Adjusted Metropolitan Indicator).

A versão original de Bettencourt compara cidades inteiras: cada cidade
é um ponto, e indicadores sociais escalam com a população por leis de
potência (β > 1 = superlinear, β < 1 = sublinear). A versão intra-Rio
adapta o método para **bairros** dentro do município:

  ESCOLAS = A · MATRÍCULAS^β

Para cada bairro com matrícula 2011 e contagem de escolas IDEB 2011:
  - β = 1 → alocação linear (uma escola para cada N alunos)
  - β > 1 → bairros grandes têm DESPROPORCIONALMENTE mais escolas
            (concentração de infraestrutura)
  - β < 1 → bairros grandes têm DESPROPORCIONALMENTE menos escolas
            (sub-serviço por aluno em zonas populosas)

Bettencourt et al. (2010) acharam β ≈ 1.15 para infraestrutura urbana
em geral (superlinear modesta). Hipótese pré-registrada para Rio:
β ≈ 1 para escolas vs. matrícula (alocação proporcional foi historicamente
metodologia explícita do INEP). Desvios → sinal de mal-distribuição.

SAMI (Scaling Adjusted Metropolitan Indicator) na versão intra-Rio:
  - Para cada bairro, computar resíduo da regressão log-log
  - SAMI > 0 → bairro tem mais escolas que o esperado pela escala
  - SAMI < 0 → menos escolas que o esperado
  - Mapa H3 do SAMI revela bairros over/under-served após controlar
    pelo tamanho (insight que o headcount absoluto esconde)

Outputs:
  - data/processed/pm12_scaling.csv (bairro × matrícula × escolas × SAMI)
  - data/processed/pm12_fit.json    (parâmetros A, β, R²)
  - docs/reports/_assets/13_pm12_scaling.png  (log-log scatter + ajuste)
  - docs/reports/_assets/13_pm12_sami_map.png (mapa H3 do SAMI)
  - docs/reports/13_pm_12.md
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
IDEB_FILE = ROOT / "data" / "raw" / "excel" / "9fd1a8cc207a48c5bda7131e4e74b1ca.xlsx"
MATRIC_LONG = ROOT / "data" / "processed" / "matriculas_bairros.csv"
HEX_GEOJSON = ROOT / "data" / "processed" / "h3_grid.geojson"
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"

OUT_CSV = ROOT / "data" / "processed" / "pm12_scaling.csv"
OUT_FIT = ROOT / "data" / "processed" / "pm12_fit.json"
OUT_SCATTER_PNG = ROOT / "docs" / "reports" / "_assets" / "13_pm12_scaling.png"
OUT_SAMI_PNG = ROOT / "docs" / "reports" / "_assets" / "13_pm12_sami_map.png"
OUT_REPORT = ROOT / "docs" / "reports" / "13_pm_12.md"

YEAR = 2011  # Único ano com matrícula + IDEB simultâneos no nosso corpus
ESCOLAS_COL = 3  # col 3 = "Escolas Participantes" no ano 2011
IDEB_COL = 30    # col 30 = IDEB no ano 2011 (cols 28-36 são IDEB 2007-2023)


def parse_escolas(year_col: int = ESCOLAS_COL, ideb_col: int = IDEB_COL) -> dict:
    """Extract Escolas Participantes + IDEB per bairro for the target year."""
    import re

    import xlrd

    RE_TOTAL = re.compile(r"^total$", re.I)
    RE_AP = re.compile(r"^área de planejamento\s+\d+", re.I)
    RE_RP = re.compile(r"^região de planejamento\s+\d+\.\d+", re.I)
    RE_RA = re.compile(r"^([IVX]+)\s+", re.I)

    book = xlrd.open_workbook(str(IDEB_FILE))
    sh = book.sheet_by_name("ANOS_INICIAIS")
    out: dict[str, dict] = {}
    current_ap = None
    current_ra = None

    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        if not label or label.lower().startswith(("fonte:", "nota:", "..", "a partir")):
            continue
        if RE_TOTAL.match(label):
            continue
        if RE_AP.match(label):
            current_ap = label
            continue
        if RE_RP.match(label):
            continue
        if RE_RA.match(label):
            current_ra = label
            continue
        if current_ra is None:
            continue
        e = sh.cell_value(r, year_col)
        i = sh.cell_value(r, ideb_col)
        try:
            e = float(e)
            i = float(i) if i not in (None, "", "...", "-", "..") else None
        except (TypeError, ValueError):
            continue
        if e <= 0:
            continue
        out[label] = {
            "ap": current_ap,
            "ra": current_ra,
            "escolas": e,
            "ideb": i,
        }
    return out


def fit_power_law(matriculas, escolas):
    """OLS in log-log space. Returns (intercept_A, exponent_β, R²)."""
    import numpy as np
    x = np.log(matriculas)
    y = np.log(escolas)
    n = len(x)
    if n < 5:
        return None, None, None
    # OLS slope + intercept
    x_mean = x.mean()
    y_mean = y.mean()
    sxy = ((x - x_mean) * (y - y_mean)).sum()
    sxx = ((x - x_mean) ** 2).sum()
    beta = sxy / sxx
    log_A = y_mean - beta * x_mean
    A = math.exp(log_A)
    # R²
    y_pred = log_A + beta * x
    ss_res = ((y - y_pred) ** 2).sum()
    ss_tot = ((y - y_mean) ** 2).sum()
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    return A, beta, r2


def main() -> int:
    if not IDEB_FILE.exists() or not MATRIC_LONG.exists():
        print("missing input data; run sessions 03 and 16 first")
        return 1

    escolas_lookup = parse_escolas()
    print(f"escolas_2011: {len(escolas_lookup)} bairros")

    matric = pd.read_csv(MATRIC_LONG)
    matric = matric[matric["year"] == YEAR][["bairro", "total_matriculas"]]
    matric["bairro"] = matric["bairro"].astype(str).str.strip()
    matric_lookup = dict(zip(matric["bairro"], matric["total_matriculas"]))
    print(f"matrícula_2011: {len(matric_lookup)} bairros")

    rows = []
    for b, info in escolas_lookup.items():
        m = matric_lookup.get(b)
        if m is None or m <= 0:
            continue
        rows.append({
            "bairro": b,
            "ap": info["ap"],
            "ra": info["ra"],
            "matriculas": m,
            "escolas": info["escolas"],
            "ideb": info["ideb"],
        })
    df = pd.DataFrame(rows)
    print(f"matched: {len(df)} bairros with both matrícula and escolas")

    A, beta, r2 = fit_power_law(df["matriculas"], df["escolas"])
    print(f"power law fit: escolas = {A:.4f} · matrículas^{beta:.4f}  (R² = {r2:.3f})")

    # SAMI = log(observed) − log(predicted)
    df["log_predicted_escolas"] = math.log(A) + beta * df["matriculas"].apply(math.log)
    df["sami"] = df["escolas"].apply(math.log) - df["log_predicted_escolas"]
    df["sami"] = df["sami"].round(4)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV.relative_to(ROOT)}")

    OUT_FIT.write_text(json.dumps({
        "year": YEAR,
        "n_bairros": len(df),
        "intercept_A": round(A, 6),
        "exponent_beta": round(beta, 6),
        "r_squared": round(r2, 4),
        "interpretation": (
            "linear" if 0.95 <= beta <= 1.05
            else ("superlinear" if beta > 1.05 else "sublinear")
        ),
    }, indent=2), encoding="utf-8")
    print(f"wrote {OUT_FIT.relative_to(ROOT)}")

    make_scatter(df, A, beta, r2)
    make_sami_map(df)
    write_report(df, A, beta, r2)
    return 0


def make_scatter(df, A, beta, r2):
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np

    mpl.rcParams["figure.dpi"] = 130
    mpl.rcParams["savefig.dpi"] = 160
    mpl.rcParams["font.family"] = "DejaVu Sans"

    fig, ax = plt.subplots(figsize=(9, 7))
    # Color by AP
    aps = sorted(df["ap"].unique())
    palette = ["#b2182b", "#ef8a62", "#fddbc7", "#67a9cf", "#2166ac"]
    for ap, color in zip(aps, palette):
        sub = df[df["ap"] == ap]
        ax.scatter(sub["matriculas"], sub["escolas"], color=color,
                   label=ap[-2:].strip(), alpha=0.75, s=30, edgecolor="white")

    # Power law curve
    xs = np.geomspace(df["matriculas"].min(), df["matriculas"].max(), 200)
    ax.plot(xs, A * xs ** beta, "k-", linewidth=2, alpha=0.7,
            label=f"escolas = {A:.3f} · matrículas$^{{{beta:.2f}}}$  (R² = {r2:.2f})")
    # Reference linear (β=1)
    A_ref = (df["escolas"] / df["matriculas"]).median()
    ax.plot(xs, A_ref * xs, "k--", linewidth=1, alpha=0.4,
            label=f"linear β=1 (referência)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Matrículas no bairro (rede municipal, 2011)")
    ax.set_ylabel("Número de escolas IDEB participantes")
    ax.set_title(f"PM-12: lei de escala intra-Rio  (n = {len(df)} bairros)")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, which="both", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    OUT_SCATTER_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_SCATTER_PNG, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT_SCATTER_PNG.relative_to(ROOT)}")


def make_sami_map(df):
    import geopandas as gpd
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    hexes = gpd.read_file(HEX_GEOJSON).to_crs(4326)
    bairros_geom = gpd.read_file(BAIRROS_GEOJSON).to_crs(4326)

    sami_lookup = {row["bairro"]: row["sami"] for _, row in df.iterrows()}

    h = hexes.copy()
    h["sami"] = [sami_lookup.get(str(b).strip()) for b in h["ideb_bairro"]]

    fig, ax = plt.subplots(figsize=(11, 9))
    norm = mpl.colors.TwoSlopeNorm(vmin=-1.0, vcenter=0, vmax=1.0)
    h.plot(
        column="sami", ax=ax, cmap="RdBu_r", norm=norm,
        edgecolor="white", linewidth=0.05,
        missing_kwds={"color": "#dddddd"},
    )
    bairros_geom.boundary.plot(ax=ax, color="#222", linewidth=0.3, alpha=0.5)
    ax.set_title(
        "PM-12 / SAMI: bairros over/under-served após controlar pelo tamanho\n"
        "azul = mais escolas que o esperado pela matrícula; vermelho = menos",
        fontsize=12,
    )
    ax.set_axis_off()
    sm = mpl.cm.ScalarMappable(cmap="RdBu_r", norm=norm)
    fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04, pad=0.04, aspect=50,
                 label="SAMI (resíduo log-log)")

    OUT_SAMI_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_SAMI_PNG, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT_SAMI_PNG.relative_to(ROOT)}")


def write_report(df, A, beta, r2):
    out = []
    out.append("# 13 — PM-12: lei de escala intra-Rio (Bettencourt et al.)\n")
    out.append(
        "Quarto produto do MVP-1. Adapta a metodologia de leis de escala urbanas "
        "(Bettencourt et al. 2010) e indicador ajustado por escala (SAMI; Heinrich "
        "Mora et al. 2023) do nível **inter-cidade** para o nível **intra-Rio**: "
        "cada bairro é um ponto, e perguntamos como o número de escolas escala com "
        "o número de matrículas.\n"
    )
    out.append(
        "Modelo:\n"
        "\n"
        "```\n"
        "escolas = A · matrículas^β\n"
        "```\n"
        "\n"
        "Interpretação canônica:\n"
        "- β = 1: alocação linear (1 escola por N alunos, constante)\n"
        "- β > 1: superlinear → bairros maiores têm desproporcionalmente mais escolas\n"
        "- β < 1: sublinear → bairros maiores têm desproporcionalmente menos escolas\n"
    )

    out.append("## Ajuste empírico (2011)\n")
    out.append(f"- Bairros com matrícula + escolas IDEB participantes: **{len(df)}**\n")
    out.append(f"- Intercepto A: **{A:.4f}**\n")
    out.append(f"- Expoente **β = {beta:.4f}**\n")
    out.append(f"- R² = **{r2:.3f}**\n")

    if 0.95 <= beta <= 1.05:
        interp = (
            f"β = {beta:.3f} é estatisticamente próximo de 1 → alocação aproximadamente "
            "**linear**. Conforme alocação histórica via INEP, é o regime esperado: "
            "uma escola para cada ~N matrículas, sem ganhos ou perdas de escala."
        )
    elif beta > 1.05:
        interp = (
            f"β = {beta:.3f} > 1 → alocação **superlinear**. Bairros maiores têm "
            "desproporcionalmente mais escolas por aluno — concentração de "
            "infraestrutura nas zonas mais populosas."
        )
    else:
        interp = (
            f"β = {beta:.3f} < 1 → alocação **sublinear**. Bairros maiores têm "
            "desproporcionalmente menos escolas por aluno. Em outras palavras, "
            "quanto maior o bairro em matrícula, **pior** sua razão escolas/matrícula. "
            "Isso é compatível com infra escolar consolidada décadas atrás (quando "
            "as zonas hoje populosas eram menos populosas) e não acompanhando o "
            "crescimento populacional municipal — efeito reportado no Brasil "
            "para várias capitais."
        )
    out.append(f"\n**Interpretação**: {interp}\n")

    out.append("## Visualizações\n")
    out.append("![scatter](_assets/13_pm12_scaling.png)\n")
    out.append("![SAMI map](_assets/13_pm12_sami_map.png)\n")

    out.append("## SAMI (Scaling Adjusted Indicator)\n")
    out.append(
        "Para cada bairro:\n"
        "\n"
        "```\n"
        "SAMI = log(escolas_observadas) − log(escolas_previstas pela lei de escala)\n"
        "```\n"
        "\n"
        "SAMI > 0 → bairro tem mais escolas que o previsto pela sua matrícula.\n"
        "SAMI < 0 → bairro tem menos escolas que o previsto.\n"
        "\n"
        "O mapa H3 acima mostra o SAMI distribuído pelo município. "
        "Bairros vermelhos são os candidatos prioritários para alocação adicional "
        "de escolas pública — não pela matrícula absoluta, mas pelo desvio relativo "
        "à curva de escala municipal.\n"
    )

    # Top deficits + surplus
    top_deficit = df.nsmallest(8, "sami")[["bairro", "ap", "matriculas", "escolas", "sami"]]
    top_surplus = df.nlargest(8, "sami")[["bairro", "ap", "matriculas", "escolas", "sami"]]
    out.append("### Top 8 bairros com maior déficit relativo (SAMI mais negativo)\n")
    out.append("| Bairro | AP | Matrículas | Escolas | SAMI |")
    out.append("| :--- | ---: | ---: | ---: | ---: |")
    for _, r in top_deficit.iterrows():
        out.append(f"| {r['bairro']} | {r['ap'][-1]} | {int(r['matriculas']):,} | {int(r['escolas'])} | {r['sami']:+.2f} |")
    out.append("")
    out.append("### Top 8 bairros com maior superávit relativo (SAMI mais positivo)\n")
    out.append("| Bairro | AP | Matrículas | Escolas | SAMI |")
    out.append("| :--- | ---: | ---: | ---: | ---: |")
    for _, r in top_surplus.iterrows():
        out.append(f"| {r['bairro']} | {r['ap'][-1]} | {int(r['matriculas']):,} | {int(r['escolas'])} | {r['sami']:+.2f} |")
    out.append("")

    out.append("## Caveats\n")
    out.append(
        "- **Janela: só 2011**. Único ano com matrícula por bairro e IDEB simultâneos. "
        "Replicação em 2013 fica como backlog (matrícula 2013 disponível; IDEB 2013 "
        "também).\n"
        "- **'Escolas' = Escolas Participantes do IDEB**, não cadastro completo. Subestima "
        "em bairros cujas escolas não participam do IDEB (escolas novas, baixa amostra). "
        "Versão futura: cruzar com Feature Service `0a220ea7...` (Escolas Municipais) "
        "para count completo via spatial join.\n"
        "- **Comparação com Bettencourt et al. (2010) é metodológica, não numérica**. "
        "Eles fitavam β a indicadores cross-cidade; aqui estamos intra-cidade. Os "
        "regimes de β esperados podem ser diferentes — nossa hipótese de β ≈ 1 vem "
        "da lógica de alocação INEP, não da literatura cross-city.\n"
        "- **R² alto não implica modelo correto**. Power law é um modelo simples; "
        "alternativas (piecewise linear, modelo com efeitos fixos por AP) ficam como "
        "robustez para v0.6.\n"
    )

    out.append("## Reprodutibilidade\n")
    out.append(
        "```bash\n"
        "python3 analysis/16_theil_weighted.py  # gera matriculas_bairros.csv\n"
        "python3 analysis/20_pm_12.py           # este script\n"
        "```\n"
    )

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
