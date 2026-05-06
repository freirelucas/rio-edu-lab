"""FUN-Rio: trajetórias de pseudocoortes 5º → 9º ano.

Terceiro produto do MVP-1 do ACEC-Hub. Inspirado em Mare (1980) sobre
transições educacionais e Reardon & Owens (2014) sobre segregação no
percurso escolar.

A pergunta: a turma que faz o IDEB 5º ano em ano T volta a ser medida
como IDEB 9º ano em ano T+4 (mesma coorte estimada). Quanto cada bairro
melhora ou piora ao longo do ensino fundamental II?

Definição operacional:
    delta[bairro, base_year] = IDEB_9º[bairro, base_year + 4]
                             − IDEB_5º[bairro, base_year]

Com IDEB de 2 em 2 anos, temos 7 pseudocoortes:
    2007→2011, 2009→2013, 2011→2015, 2013→2017,
    2015→2019, 2017→2021, 2019→2023.

Pre-registered hypotheses:
1. Em média, delta < 0 (literatura: IDEB 9º é tipicamente menor que 5º).
2. Distribuição de delta tem cauda esquerda gorda — alguns bairros
   "afundam" muito mais que outros, indicando perda de qualidade
   educacional concentrada em zonas específicas.
3. Bairros de IDEB 5º acima da média municipal mantêm vantagem;
   bairros abaixo afundam mais rápido (efeito de concentração).

Outputs:
  - data/processed/fun_rio_transitions.csv (long: bairro, base_year, delta, ideb_5, ideb_9)
  - data/processed/fun_rio_summary.csv     (por base_year: dist statistics)
  - docs/reports/_assets/12_fun_rio_dist.png   (histograma + scatter ideb5 vs delta)
  - docs/reports/_assets/12_fun_rio_map.png    (mapa H3 do delta médio por bairro)
  - docs/reports/12_fun_rio.md
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INI_LONG = ROOT / "data" / "processed" / "ideb_bairros.csv"
FIN_LONG = ROOT / "data" / "processed" / "ideb_anos_finais.csv"
HEX_GEOJSON = ROOT / "data" / "processed" / "h3_grid.geojson"
BAIRROS_GEOJSON = ROOT / "data" / "raw" / "geo" / "bairros.geojson"

OUT_TRANS = ROOT / "data" / "processed" / "fun_rio_transitions.csv"
OUT_SUMMARY = ROOT / "data" / "processed" / "fun_rio_summary.csv"
OUT_DIST_PNG = ROOT / "docs" / "reports" / "_assets" / "12_fun_rio_dist.png"
OUT_MAP_PNG = ROOT / "docs" / "reports" / "_assets" / "12_fun_rio_map.png"
OUT_REPORT = ROOT / "docs" / "reports" / "12_fun_rio.md"

PSEUDO_COHORTS = [(2007, 2011), (2009, 2013), (2011, 2015), (2013, 2017),
                  (2015, 2019), (2017, 2021), (2019, 2023)]


def main() -> int:
    if not INI_LONG.exists() or not FIN_LONG.exists():
        print("missing input CSVs; run analysis/10_theil_ideb.py and 15_anos_finais.py first")
        return 1

    ini = pd.read_csv(INI_LONG)
    fin = pd.read_csv(FIN_LONG)
    print(f"loaded: 5º ano = {len(ini)} rows, 9º ano = {len(fin)} rows")

    ini["bairro"] = ini["bairro"].astype(str).str.strip()
    fin["bairro"] = fin["bairro"].astype(str).str.strip()

    transitions: list[dict] = []
    for y5, y9 in PSEUDO_COHORTS:
        s5 = ini[ini["year"] == y5][["bairro", "ra", "ap", "ideb"]].rename(columns={"ideb": "ideb_5"})
        s9 = fin[fin["year"] == y9][["bairro", "ideb"]].rename(columns={"ideb": "ideb_9"})
        merged = s5.merge(s9, on="bairro", how="inner")
        merged["delta"] = merged["ideb_9"] - merged["ideb_5"]
        merged["base_year"] = y5
        merged["target_year"] = y9
        transitions.extend(merged[["base_year", "target_year", "ap", "ra", "bairro",
                                    "ideb_5", "ideb_9", "delta"]].to_dict(orient="records"))
        print(f"  cohort {y5}→{y9}: {len(merged)} bairros matched")

    OUT_TRANS.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(transitions).to_csv(OUT_TRANS, index=False)
    print(f"wrote {OUT_TRANS.relative_to(ROOT)} ({len(transitions)} rows)")

    df = pd.DataFrame(transitions)

    # Summary by base_year
    summary = df.groupby("base_year").agg(
        n=("bairro", "count"),
        mean_delta=("delta", "mean"),
        median_delta=("delta", "median"),
        std_delta=("delta", "std"),
        p10_delta=("delta", lambda s: s.quantile(0.10)),
        p90_delta=("delta", lambda s: s.quantile(0.90)),
        min_delta=("delta", "min"),
        max_delta=("delta", "max"),
    ).round(3).reset_index()
    summary.to_csv(OUT_SUMMARY, index=False)
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")

    make_dist_plot(df)
    make_map(df)
    write_report(df, summary)
    return 0


def make_dist_plot(df: pd.DataFrame) -> None:
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    mpl.rcParams["figure.dpi"] = 130
    mpl.rcParams["savefig.dpi"] = 160
    mpl.rcParams["font.family"] = "DejaVu Sans"

    fig, (ax_h, ax_s) = plt.subplots(1, 2, figsize=(13, 5))

    # Histogram of all transitions
    ax_h.hist(df["delta"], bins=40, color="#4575b4", edgecolor="white", alpha=0.85)
    ax_h.axvline(0, color="black", linewidth=0.8, linestyle="--", label="sem mudança (Δ=0)")
    ax_h.axvline(df["delta"].mean(), color="#d73027", linewidth=2,
                 label=f"média = {df['delta'].mean():.2f}")
    ax_h.set_xlabel("Δ IDEB (9º − 5º), pseudocoortes 2007–2023")
    ax_h.set_ylabel("Bairro-coortes")
    ax_h.set_title(f"Distribuição de Δ ({len(df)} pseudocoortes)")
    ax_h.legend(loc="upper right", fontsize=9)
    ax_h.spines["top"].set_visible(False)
    ax_h.spines["right"].set_visible(False)

    # Scatter ideb_5 vs delta
    ax_s.scatter(df["ideb_5"], df["delta"], alpha=0.4, s=14, color="#4575b4",
                 edgecolor="none")
    ax_s.axhline(0, color="black", linewidth=0.8, linestyle="--")
    # Trend line
    import numpy as np
    z = np.polyfit(df["ideb_5"], df["delta"], 1)
    xs = np.linspace(df["ideb_5"].min(), df["ideb_5"].max(), 100)
    ax_s.plot(xs, z[0] * xs + z[1], color="#d73027", linewidth=2,
              label=f"slope = {z[0]:+.2f}")
    ax_s.set_xlabel("IDEB 5º (base_year)")
    ax_s.set_ylabel("Δ IDEB (9º − 5º)")
    ax_s.set_title("Trajetória vs ponto de partida")
    ax_s.legend(loc="upper right", fontsize=9)
    ax_s.spines["top"].set_visible(False)
    ax_s.spines["right"].set_visible(False)

    fig.suptitle("FUN-Rio: trajetórias 5º → 9º ano por bairro-coorte",
                 fontsize=13, y=1.02)
    OUT_DIST_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_DIST_PNG, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT_DIST_PNG.relative_to(ROOT)}")


def make_map(df: pd.DataFrame) -> None:
    """Map of mean delta per bairro across all cohorts."""
    import geopandas as gpd
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    hexes = gpd.read_file(HEX_GEOJSON).to_crs(4326)
    bairros_geom = gpd.read_file(BAIRROS_GEOJSON).to_crs(4326)

    mean_delta = df.groupby("bairro")["delta"].mean().to_dict()

    h = hexes.copy()
    h["delta"] = [mean_delta.get(str(b).strip()) for b in h["ideb_bairro"]]

    fig, ax = plt.subplots(figsize=(11, 9))
    norm = mpl.colors.TwoSlopeNorm(vmin=-1.5, vcenter=0, vmax=1.5)
    h.plot(
        column="delta", ax=ax, cmap="RdBu", norm=norm,
        edgecolor="white", linewidth=0.05,
        missing_kwds={"color": "#dddddd"},
    )
    bairros_geom.boundary.plot(ax=ax, color="#222", linewidth=0.3, alpha=0.5)
    ax.set_title(
        "FUN-Rio: Δ IDEB médio (9º − 5º) por bairro\n"
        "média de até 7 pseudocoortes (2007→2011 a 2019→2023)",
        fontsize=12,
    )
    ax.set_axis_off()

    sm = mpl.cm.ScalarMappable(cmap="RdBu", norm=norm)
    fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.04, pad=0.04, aspect=50,
                 label="Δ IDEB médio (9º − 5º)")

    OUT_MAP_PNG.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_MAP_PNG, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {OUT_MAP_PNG.relative_to(ROOT)}")


def write_report(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    mean_delta = df["delta"].mean()
    median_delta = df["delta"].median()
    pct_negative = (df["delta"] < 0).mean()

    # Slope of delta vs ideb_5
    import numpy as np
    z = np.polyfit(df["ideb_5"], df["delta"], 1)

    out = []
    out.append("# 12 — FUN-Rio: trajetórias 5º → 9º ano por pseudocoorte\n")
    out.append(
        "Terceiro produto do MVP-1 do ACEC-Hub. Inspirado em Mare (1980) sobre "
        "transições educacionais e Reardon & Owens (2014) sobre segregação no "
        "percurso escolar.\n"
    )
    out.append(
        "**Definição operacional**: a turma que faz IDEB 5º ano no ano T volta a "
        "ser medida como IDEB 9º ano em T+4 (mesma coorte estimada). Para cada "
        "bairro com dados em ambos:\n"
        "\n"
        "```\n"
        "Δ[bairro, T] = IDEB_9º[bairro, T+4] − IDEB_5º[bairro, T]\n"
        "```\n"
        "\n"
        "Com IDEB bienal, há 7 pseudocoortes possíveis (2007→2011 a 2019→2023).\n"
    )

    out.append("## Visualizações\n")
    out.append("![distribuição](_assets/12_fun_rio_dist.png)\n")
    out.append("![mapa Δ médio](_assets/12_fun_rio_map.png)\n")

    out.append("## Achados (números reais)\n")
    out.append(
        f"- **{len(df)} pseudocoortes** observadas (bairro × base_year), "
        f"~{df['bairro'].nunique()} bairros distintos.\n"
        f"- **Δ médio** = {mean_delta:+.2f} (mediana = {median_delta:+.2f}). "
        + ("**A maioria das coortes piora** ao avançar de 5º para 9º "
           f"({pct_negative:.0%} têm Δ < 0)." if pct_negative > 0.5
           else f"A maioria mantém ou melhora ({1-pct_negative:.0%} com Δ ≥ 0).")
        + "\n"
        f"- **Slope Δ vs IDEB-5º base** = {z[0]:+.2f}. "
        + ("Bairros que começam com IDEB 5º mais alto **caem mais** ao chegar no 9º — "
           "indício de regressão à média ou perda diferencial nas zonas mais bem "
           "servidas (alunos mudando para rede privada ao avançar o ciclo escolar)."
           if z[0] < 0 else
           "Bairros melhores no 5º mantêm/ampliam vantagem no 9º — "
           "consistente com efeito Mateus de concentração de oportunidade.")
        + "\n"
    )

    out.append("## Distribuição por base_year\n")
    out.append("| Base | n | Δ médio | Δ p10 | Δ p90 |")
    out.append("| ---: | ---: | ---: | ---: | ---: |")
    for _, r in summary.iterrows():
        out.append(
            f"| {int(r['base_year'])} | {int(r['n'])} | {r['mean_delta']:+.2f} "
            f"| {r['p10_delta']:+.2f} | {r['p90_delta']:+.2f} |"
        )
    out.append("")

    # Top 10 worst trajectories
    worst = df.nsmallest(10, "delta")[["base_year", "ap", "bairro", "ideb_5", "ideb_9", "delta"]]
    out.append("## Top 10 quedas (5º → 9º)\n")
    out.append("| Base | AP | Bairro | IDEB 5º | IDEB 9º | Δ |")
    out.append("| ---: | :--- | :--- | ---: | ---: | ---: |")
    for _, r in worst.iterrows():
        out.append(
            f"| {int(r['base_year'])} | {r['ap'][-1]} | {r['bairro']} | "
            f"{r['ideb_5']:.2f} | {r['ideb_9']:.2f} | {r['delta']:+.2f} |"
        )
    out.append("")

    out.append("## Caveats\n")
    out.append(
        "- **Pseudocoorte ≠ coorte real**: o 5º ano de 2007 não é estritamente o "
        "mesmo grupo de alunos do 9º de 2011 (perdas, transferências, repetências). "
        "Com microdado INEP por escola seria possível seguir a coorte real; com "
        "dado agregado por bairro, é uma proxy.\n"
        "- **Mudança de rede**: alunos de 5º que migram para escola privada antes "
        "do 9º **saem** da nossa amostra municipal. Se eles eram tipicamente os de "
        "IDEB mais alto, isso enviesa Δ para baixo nas zonas onde a migração para "
        "privada é mais comum (Zona Sul, Barra). Esse é o sinal econômico real, "
        "mas não pode ser separado do efeito puramente educacional sem dado de "
        "matrícula privada por bairro.\n"
        "- **Pseudocoorte usa anos pares**: 2007→2011 mistura 2 ciclos de avaliação. "
        "Versão futura poderia usar microdados anuais quando disponíveis.\n"
    )

    out.append("## Reprodutibilidade\n")
    out.append(
        "```bash\n"
        "python3 analysis/10_theil_ideb.py     # gera ideb_bairros.csv\n"
        "python3 analysis/15_anos_finais.py    # gera ideb_anos_finais.csv\n"
        "python3 analysis/19_fun_rio.py        # este script\n"
        "```\n"
    )

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
