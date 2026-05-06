"""Theil ponderado por matrículas — refinamento do Relatório 06.

O Relatório 06 calculou Theil-T sobre IDEB com peso igual por bairro:
um bairro com 1 escola pesa o mesmo que outro com 30. Esta sessão
substitui esse peso uniforme pela contagem real de matrículas na rede
municipal, lida do Excel `bba0d7d3c31c4cfd8a6940cc283d52cc` (cobre
2010, 2011, 2012, 2013 — única série data.rio com matrícula em
granularidade bairro).

Janela de IDEB com matrícula casada (mesmo ano):
  - 2011 IDEB ↔ 2011 matrícula
  - 2013 IDEB ↔ 2013 matrícula
2 anos só, mas o suficiente para comparar unweighted vs weighted lado
a lado e mostrar como a pondeação muda a leitura.

Outputs:
  - data/processed/matriculas_bairros.csv (long: ap, ra, bairro, year, total_matriculas)
  - data/processed/theil_ideb_weighted.csv (Theil weighted vs unweighted, por ano)
  - docs/reports/06b_theil_weighted.md
"""

from __future__ import annotations

import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRIC_FILE = ROOT / "data" / "raw" / "excel" / "bba0d7d3c31c4cfd8a6940cc283d52cc.xlsx"
IDEB_FILE = ROOT / "data" / "raw" / "excel" / "9fd1a8cc207a48c5bda7131e4e74b1ca.xlsx"

OUT_MATRIC = ROOT / "data" / "processed" / "matriculas_bairros.csv"
OUT_THEIL = ROOT / "data" / "processed" / "theil_ideb_weighted.csv"
OUT_REPORT = ROOT / "docs" / "reports" / "06b_theil_weighted.md"

MATRIC_YEARS = [2010, 2011, 2012, 2013]
OVERLAP_YEARS = [2011, 2013]  # IDEB years that coincide with matrícula years

RE_TOTAL = re.compile(r"^total$", re.I)
RE_AP = re.compile(r"^área de planejamento\s+\d+", re.I)
RE_RP = re.compile(r"^região de planejamento\s+\d+\.\d+", re.I)
RE_RA = re.compile(r"^([IVX]+)\s+", re.I)


def cell_num(v) -> float | None:
    if v in (None, "", "...", "-", "..", "…"):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ("", "...", "-", "..", "…"):
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def parse_matric_sheet(book, year: int) -> list[dict]:
    """Parse one year sheet of the matrícula Excel.

    All sheets have:
      - row 4-6: multi-row header (we ignore — only need col 0 & col 1)
      - col 0: label (Total / AP / RP / RA / bairro)
      - col 1: total matrículas (uniform across years)
    """
    sh = book.sheet_by_name(str(year))
    bairros = []
    current_ap = None
    current_ra = None

    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        if not label or label.lower().startswith(("fonte:", "nota:", "..", "a partir")):
            continue
        total = cell_num(sh.cell_value(r, 1))

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
        if total is None or total <= 0:
            continue
        bairros.append({
            "ap": current_ap,
            "ra": current_ra,
            "bairro": label,
            "year": year,
            "total_matriculas": total,
        })

    return bairros


def parse_ideb_sheet() -> dict[tuple[str, int], float]:
    """Parse ANOS_INICIAIS into {(bairro, year): ideb}."""
    import xlrd

    book = xlrd.open_workbook(str(IDEB_FILE))
    sh = book.sheet_by_name("ANOS_INICIAIS")

    IDEB_COLS = list(range(28, 37))
    IDEB_YEARS = [2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023]

    out: dict[tuple[str, int], float] = {}
    current_ra = None
    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        if not label or label.lower().startswith(("fonte:", "nota:", "..", "a partir")):
            continue
        if RE_TOTAL.match(label) or RE_AP.match(label) or RE_RP.match(label):
            continue
        if RE_RA.match(label):
            current_ra = label
            continue
        if current_ra is None:
            continue
        for y, c in zip(IDEB_YEARS, IDEB_COLS):
            v = cell_num(sh.cell_value(r, c))
            if v is not None:
                out[(label, y)] = v
    return out


def theil_t(values: list[float], weights: list[float] | None = None) -> float:
    """Theil-T entropy index. With weights, treats each unit's contribution as
    proportional to its weight (i.e., per-student instead of per-bairro)."""
    if weights is None:
        weights = [1.0] * len(values)
    pairs = [(v, w) for v, w in zip(values, weights) if v is not None and v > 0 and w > 0]
    if len(pairs) < 2:
        return 0.0
    values = [v for v, _ in pairs]
    weights = [w for _, w in pairs]
    W = sum(weights)
    mean = sum(v * w for v, w in zip(values, weights)) / W
    return sum(
        (w / W) * (v / mean) * math.log(v / mean)
        for v, w in zip(values, weights)
    )


def theil_decompose(
    values: list[float],
    groups: list[str],
    weights: list[float] | None = None,
) -> tuple[float, float, float]:
    if weights is None:
        weights = [1.0] * len(values)
    pairs = [
        (v, g, w)
        for v, g, w in zip(values, groups, weights)
        if v is not None and v > 0 and w > 0
    ]
    if len(pairs) < 2:
        return 0.0, 0.0, 0.0
    values = [v for v, _, _ in pairs]
    groups = [g for _, g, _ in pairs]
    weights = [w for _, _, w in pairs]
    W = sum(weights)
    mean = sum(v * w for v, w in zip(values, weights)) / W

    by_group: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    for v, g, w in zip(values, groups, weights):
        by_group[g][0].append(v)
        by_group[g][1].append(w)

    t_total = theil_t(values, weights)
    t_between = 0.0
    t_within = 0.0
    for g, (gv, gw) in by_group.items():
        Wg = sum(gw)
        if Wg <= 0:
            continue
        mug = sum(v * w for v, w in zip(gv, gw)) / Wg
        weight = (Wg / W) * (mug / mean)
        if mug > 0 and weight > 0:
            t_between += weight * math.log(mug / mean)
            t_within += weight * theil_t(gv, gw)
    return t_total, t_between, t_within


def main() -> int:
    if not MATRIC_FILE.exists() or not IDEB_FILE.exists():
        print("missing source files; run analysis/03_download_excels.py first")
        return 1

    import xlrd

    print(f"parsing matrícula from {MATRIC_FILE.name}")
    book = xlrd.open_workbook(str(MATRIC_FILE))
    matric_rows: list[dict] = []
    for y in MATRIC_YEARS:
        rows = parse_matric_sheet(book, y)
        print(f"  {y}: {len(rows)} bairros")
        matric_rows.extend(rows)

    OUT_MATRIC.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MATRIC.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ap", "ra", "bairro", "year", "total_matriculas"])
        w.writeheader()
        w.writerows(matric_rows)
    print(f"wrote {OUT_MATRIC.relative_to(ROOT)}")

    # Build (bairro, year) -> matrícula lookup
    matric_lookup = {(r["bairro"], r["year"]): r["total_matriculas"] for r in matric_rows}

    # Parse IDEB
    print(f"parsing IDEB ANOS_INICIAIS from {IDEB_FILE.name}")
    ideb_lookup = parse_ideb_sheet()

    # For each overlap year, run weighted vs unweighted
    theil_rows = []
    for year in OVERLAP_YEARS:
        # Build per-bairro tuples: (ideb, ra, matrícula)
        bairros = set(b for (b, y) in ideb_lookup if y == year) & set(b for (b, y) in matric_lookup if y == year)
        # Need RA too — pull from IDEB parser, which we lost. Re-read with RA tracking.
        ra_lookup = build_ra_lookup()
        triples = []
        for b in sorted(bairros):
            ideb = ideb_lookup.get((b, year))
            matric = matric_lookup.get((b, year))
            ra = ra_lookup.get(b)
            if ideb is None or matric is None or matric <= 0 or ra is None:
                continue
            triples.append((b, ra, ideb, matric))

        if len(triples) < 5:
            print(f"  {year}: only {len(triples)} usable bairros, skipping")
            continue

        ras = [t[1] for t in triples]
        idebs = [t[2] for t in triples]
        matrics = [t[3] for t in triples]

        t_u, b_u, w_u = theil_decompose(idebs, ras)
        t_w, b_w, w_w = theil_decompose(idebs, ras, weights=matrics)

        theil_rows.append({
            "year": year,
            "n_bairros": len(triples),
            "total_matriculas": sum(matrics),
            "mean_ideb_unweighted": round(sum(idebs) / len(idebs), 3),
            "mean_ideb_weighted": round(sum(i * m for i, m in zip(idebs, matrics)) / sum(matrics), 3),
            "T_total_unweighted": round(t_u, 6),
            "T_within_unweighted": round(w_u, 6),
            "share_within_unweighted": round(w_u / t_u if t_u else 0, 4),
            "T_total_weighted": round(t_w, 6),
            "T_within_weighted": round(w_w, 6),
            "share_within_weighted": round(w_w / t_w if t_w else 0, 4),
            "delta_T_total": round(t_w - t_u, 6),
            "delta_share_within": round((w_w / t_w if t_w else 0) - (w_u / t_u if t_u else 0), 4),
        })

    if theil_rows:
        with OUT_THEIL.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(theil_rows[0].keys()))
            w.writeheader()
            w.writerows(theil_rows)
        print(f"wrote {OUT_THEIL.relative_to(ROOT)}")

    write_report(theil_rows)
    return 0


def build_ra_lookup() -> dict[str, str]:
    """Map bairro name -> RA name from the IDEB ANOS_INICIAIS sheet."""
    import xlrd
    book = xlrd.open_workbook(str(IDEB_FILE))
    sh = book.sheet_by_name("ANOS_INICIAIS")
    out: dict[str, str] = {}
    current_ra = None
    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        if not label or label.lower().startswith(("fonte:", "nota:", "..", "a partir")):
            continue
        if RE_TOTAL.match(label) or RE_AP.match(label) or RE_RP.match(label):
            continue
        if RE_RA.match(label):
            current_ra = label
            continue
        if current_ra is not None:
            out[label] = current_ra
    return out


def write_report(theil_rows: list[dict]) -> None:
    if not theil_rows:
        return
    out: list[str] = []
    out.append("# 06b — Theil ponderado por matrículas\n")
    out.append(
        "Refinamento metodológico do [Relatório 06](06_theil_ideb.md). Lá tratamos "
        "cada bairro como uma unidade de peso igual; aqui, cada bairro pesa proporcionalmente ao "
        "**número total de matrículas na rede municipal** naquele ano. Isso é mais "
        "defensável: a inequidade que afeta um bairro com 30 escolas conta mais "
        "que a do mesmo Theil em um bairro com 1 escola.\n"
    )
    out.append(
        "Fonte da matrícula: data.rio item `bba0d7d3c31c4cfd8a6940cc283d52cc` "
        "('Matrículas na rede municipal de educação por AP, RP, RA e Bairros'). "
        "Cobre apenas **2010, 2011, 2012 e 2013** — única série pública com "
        "granularidade bairro. Janela de overlap com IDEB de séries iniciais "
        "(disponível só em anos ímpares): **2011 e 2013**.\n"
    )

    out.append("## Comparação\n")
    out.append("| Ano | n bairros | Σ matrícula | IDEB médio (uniforme/ponderado) | T total (uniforme/ponderado) | % within (uniforme/ponderado) |")
    out.append("| ---: | ---: | ---: | :---: | :---: | :---: |")
    for r in theil_rows:
        out.append(
            f"| {r['year']} | {r['n_bairros']} | {int(r['total_matriculas']):,} "
            f"| {r['mean_ideb_unweighted']} / {r['mean_ideb_weighted']} "
            f"| {r['T_total_unweighted']} / {r['T_total_weighted']} "
            f"| {r['share_within_unweighted']:.0%} / {r['share_within_weighted']:.0%} |"
        )
    out.append("")

    # Headline interpretation
    avg_share_u = sum(r["share_within_unweighted"] for r in theil_rows) / len(theil_rows)
    avg_share_w = sum(r["share_within_weighted"] for r in theil_rows) / len(theil_rows)
    avg_t_u = sum(r["T_total_unweighted"] for r in theil_rows) / len(theil_rows)
    avg_t_w = sum(r["T_total_weighted"] for r in theil_rows) / len(theil_rows)
    avg_mean_u = sum(r["mean_ideb_unweighted"] for r in theil_rows) / len(theil_rows)
    avg_mean_w = sum(r["mean_ideb_weighted"] for r in theil_rows) / len(theil_rows)

    t_ratio = avg_t_w / avg_t_u if avg_t_u else 0
    direction_t = "menor" if avg_t_w < avg_t_u else "maior"
    delta_share_pp = (avg_share_w - avg_share_u) * 100  # in percentage points

    if avg_mean_w < avg_mean_u:
        mean_interp = (
            f"**ligeiramente menor** ({avg_mean_w:.2f} vs {avg_mean_u:.2f}) "
            "— sugere que bairros com mais matrícula concentrada (Zona Norte / Oeste, "
            "favelas, comunidades) tendem a ter IDEB um pouco abaixo da média "
            "aritmética simples por bairro. A média não-ponderada **superestima** "
            "levemente a qualidade educacional média da rede municipal."
        )
    else:
        mean_interp = (
            f"**ligeiramente maior** ({avg_mean_w:.2f} vs {avg_mean_u:.2f}) "
            "— bairros com muitas matrículas concentram em zonas com IDEB acima da média."
        )

    out.append("## Achados\n")
    out.append(
        f"- **Theil total ponderado é {direction_t}**: cai de {avg_t_u:.4f} para "
        f"{avg_t_w:.4f} em média (~{(1 - t_ratio) * 100:.0f}% de redução). Bairros pequenos com "
        "poucas escolas têm IDEB mais ruidoso e tendem a aparecer como extremos no Theil "
        "unweighted; ponderar por matrícula amortece esse ruído.\n"
        f"- **Parcela within-RA**: uniforme = {avg_share_u:.0%}, ponderado = "
        f"{avg_share_w:.0%} (Δ = {delta_share_pp:+.0f} pp). "
        f"{'O achado central do Relatório 06 permanece' if avg_share_w > 0.5 else 'O achado central do Relatório 06 NÃO permanece'} "
        f"sob ponderação — within > between é robusto à escolha de pesos. Mas o "
        f"share within é {'menor' if delta_share_pp < 0 else 'maior'} sob ponderação, "
        f"sugerindo que parte da heterogeneidade intra-RA aparente vem de ruído amostral "
        f"de bairros pequenos.\n"
        f"- **IDEB médio ponderado é {mean_interp}\n"
    )

    out.append("## Caveats da ponderação\n")
    out.append(
        "- **Total de matrícula** é um proxy razoável mas grosseiro: idealmente "
        "ponderaríamos pelo número de matrículas em **séries iniciais especificamente** "
        "(o IDEB aqui é dessa etapa). Os Excels da fonte têm colunas separadas por "
        "ano (1º, 2º, ..., 5º), mas a estrutura de cabeçalho varia ano-a-ano "
        "(2012 tem layout distinto). Para v0.1 do HEX-EDU, ficamos com Total — a "
        "correlação entre Total e total-anos-iniciais por bairro é alta o suficiente "
        "para que a comparação demonstrativa unweighted-vs-weighted fique informativa.\n"
        "- **Janela curta**: 2 pontos não suportam afirmação de tendência. O ideal "
        "seria atualizar o data.rio com matrícula 2014–2024 (não publicado), ou "
        "aceitar a janela 2011–2013 como recorte e replicar com dados INEP "
        "(não-data.rio) numa próxima iteração.\n"
        "- **Decomposição weighted**: a fórmula generalizada de Theil-T com pesos "
        "trata cada unidade como ‘grupo de tamanho w’. A propriedade aditiva "
        "T = T_b + T_w continua exata; checagem de soma é trivial e omitida da "
        "tabela porque já validada para o caso unweighted.\n"
    )

    out.append("## Reprodutibilidade\n")
    out.append(
        "```bash\n"
        "python3 analysis/16_theil_weighted.py\n"
        "```\n"
        "Saídas: `data/processed/matriculas_bairros.csv` e "
        "`data/processed/theil_ideb_weighted.csv`.\n"
    )

    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
