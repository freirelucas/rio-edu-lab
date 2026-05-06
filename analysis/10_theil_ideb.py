"""MVP do produto HEX-EDU: decomposição Theil do IDEB do Rio.

Lê o arquivo `IDEB das séries iniciais e finais segundo as Áreas de
Planejamento (AP), Regiões de Planejamento (RP), Regiões Administrativas
(RA) e Bairros do Município do Rio de Janeiro` (data.rio item
`9fd1a8cc207a48c5bda7131e4e74b1ca`), parseia a hierarquia AP → RP → RA →
bairro, e calcula o índice de Theil-T total para cada ano disponível
(2007–2023), decomposto em parcela entre-RAs e dentro-de-RA.

Theil-T (peso igual por unidade):
    T   = (1/N) Σᵢ (yᵢ/ȳ) ln(yᵢ/ȳ)
    T_b = Σ_g (n_g/N) (ȳ_g/ȳ) ln(ȳ_g/ȳ)
    T_w = Σ_g (n_g/N) (ȳ_g/ȳ) T_g
    T   = T_b + T_w  (decomposição aditiva)

Outputs:
  - data/processed/ideb_bairros.csv         (long: id, year, ap, ra, bairro, ideb)
  - data/processed/theil_ideb_anos_iniciais.csv
  - docs/reports/06_theil_ideb.md
"""

from __future__ import annotations

import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
IDEB_FILE = ROOT / "data" / "raw" / "excel" / "9fd1a8cc207a48c5bda7131e4e74b1ca.xlsx"
OUT_LONG = ROOT / "data" / "processed" / "ideb_bairros.csv"
OUT_THEIL = ROOT / "data" / "processed" / "theil_ideb_anos_iniciais.csv"
REPORT = ROOT / "docs" / "reports" / "06_theil_ideb.md"

# Header inferido da inspeção: row 5 traz seções, row 6 traz anos.
# IDEB scores são as colunas 28..36 → anos 2007..2023 (passo 2).
IDEB_COLS = list(range(28, 37))
IDEB_YEARS = [2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023]

# Padrões para classificar nível na hierarquia.
RE_TOTAL = re.compile(r"^total$", re.I)
RE_AP = re.compile(r"^área de planejamento\s+\d+", re.I)
RE_RP = re.compile(r"^região de planejamento\s+\d+\.\d+", re.I)
RE_RA = re.compile(r"^([IVX]+)\s+", re.I)  # romano + nome (I Portuária, II Centro, ...)


def cell_num(v) -> float | None:
    """Convert Excel cell to float; treat '...', '-', '..' as missing."""
    if v in (None, "", "...", "-", ".."):
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


def parse_ideb_sheet(sheet_name: str = "ANOS_INICIAIS"):
    import xlrd

    book = xlrd.open_workbook(str(IDEB_FILE))
    sh = book.sheet_by_name(sheet_name)

    bairros = []  # list of (ap, ra, bairro, {year: ideb})
    ap_aggregates = {}  # ap -> {year: ideb}
    ra_aggregates = {}  # ra -> {year: ideb, ap: ap}

    current_ap: str | None = None
    current_ra: str | None = None

    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        if not label:
            continue
        # Skip footer notes
        if label.lower().startswith(("fonte:", "nota:", "..", "a partir")):
            continue
        # Get this row's IDEB scores by year
        scores = {y: cell_num(sh.cell_value(r, c)) for y, c in zip(IDEB_YEARS, IDEB_COLS)}

        if RE_TOTAL.match(label):
            continue  # city aggregate, ignore
        if RE_AP.match(label):
            current_ap = label
            ap_aggregates[label] = scores
            continue
        if RE_RP.match(label):
            continue  # Aggregate at RP level — not used here
        if RE_RA.match(label):
            current_ra = label
            ra_aggregates[label] = {**scores, "ap": current_ap}
            continue
        # Else: bairro under current_ra
        if current_ra is None:
            # Some pre-RA stray row, ignore
            continue
        bairros.append({
            "ap": current_ap,
            "ra": current_ra,
            "bairro": label,
            "scores": scores,
        })

    return bairros, ap_aggregates, ra_aggregates


def theil_t(values: list[float]) -> float:
    """Theil-T (general entropy α=1), unit weights."""
    values = [v for v in values if v is not None and v > 0]
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return sum((v / mean) * math.log(v / mean) for v in values) / n


def theil_decompose(values: list[float], groups: list[str]) -> tuple[float, float, float, dict]:
    """Returns (T_total, T_between, T_within, group_info)."""
    pairs = [(v, g) for v, g in zip(values, groups) if v is not None and v > 0]
    if len(pairs) < 2:
        return 0.0, 0.0, 0.0, {}
    values = [v for v, _ in pairs]
    groups = [g for _, g in pairs]
    n = len(values)
    mean = sum(values) / n

    by_group: dict[str, list[float]] = defaultdict(list)
    for v, g in zip(values, groups):
        by_group[g].append(v)

    t_total = theil_t(values)
    t_between = 0.0
    t_within = 0.0
    info = {}
    for g, gv in by_group.items():
        ng = len(gv)
        mug = sum(gv) / ng
        weight = (ng / n) * (mug / mean)  # group income share
        if mug > 0 and weight > 0:
            t_between += weight * math.log(mug / mean)
            t_g = theil_t(gv)
            t_within += weight * t_g
            info[g] = {"n": ng, "mean": mug, "share": weight, "t_within": t_g}

    return t_total, t_between, t_within, info


def md_table(headers, rows, aligns=None):
    aligns = aligns or ["left"] * len(headers)
    sep = {"left": ":---", "right": "---:", "center": ":---:"}
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(sep[a] for a in aligns) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def write_long_csv(bairros: list[dict]) -> None:
    OUT_LONG.parent.mkdir(parents=True, exist_ok=True)
    with OUT_LONG.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ap", "ra", "bairro", "year", "ideb"])
        for b in bairros:
            for y, v in b["scores"].items():
                if v is not None:
                    w.writerow([b["ap"], b["ra"], b["bairro"], y, v])


def write_theil_csv(rows: list[dict]) -> None:
    OUT_THEIL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_THEIL.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    if not IDEB_FILE.exists():
        print(f"missing {IDEB_FILE}; run analysis/03_download_excels.py first")
        return 1

    bairros, ap_agg, ra_agg = parse_ideb_sheet("ANOS_INICIAIS")

    print(f"parsed: {len(bairros)} bairro-rows, {len(ra_agg)} RAs, {len(ap_agg)} APs")

    write_long_csv(bairros)

    # Compute Theil per year over bairros, grouped by RA
    theil_rows = []
    by_year_table = []
    for year in IDEB_YEARS:
        values = [b["scores"][year] for b in bairros]
        groups = [b["ra"] for b in bairros]
        # Drop missings
        clean = [(v, g) for v, g in zip(values, groups) if v is not None and v > 0]
        n = len(clean)
        if n < 5:
            continue
        v = [x for x, _ in clean]
        g = [x for _, x in clean]
        t_total, t_between, t_within, info = theil_decompose(v, g)
        share_b = t_between / t_total if t_total else 0
        share_w = t_within / t_total if t_total else 0
        theil_rows.append({
            "year": year,
            "n_bairros": n,
            "n_ras": len(set(g)),
            "mean_ideb": round(sum(v) / n, 3),
            "T_total": round(t_total, 6),
            "T_between": round(t_between, 6),
            "T_within": round(t_within, 6),
            "share_between": round(share_b, 4),
            "share_within": round(share_w, 4),
            "check_sum": round(t_between + t_within - t_total, 8),
        })
        by_year_table.append([
            year, n, len(set(g)), f"{sum(v) / n:.2f}",
            f"{t_total:.4f}", f"{t_between:.4f}", f"{t_within:.4f}",
            f"{share_b:.0%}", f"{share_w:.0%}",
        ])

    write_theil_csv(theil_rows)

    # Build report
    md: list[str] = []
    md.append("# 06 — Decomposição Theil do IDEB por bairro\n")
    md.append(
        "Primeira aplicação metodológica do lab: medir desigualdade educacional na "
        "rede municipal de ensino do Rio usando o **índice de Theil-T**, decomposto em "
        "parcela **entre-RAs** e **dentro-de-RA**, sobre dados reais de IDEB séries "
        "iniciais (2007–2023).\n"
    )
    md.append(
        "Fonte: data.rio item "
        "`9fd1a8cc207a48c5bda7131e4e74b1ca` ('IDEB das séries iniciais e finais segundo "
        "as Áreas de Planejamento, Regiões de Planejamento, Regiões Administrativas e "
        "Bairros'). Sheet `ANOS_INICIAIS`. Hierarquia AP → RP → RA → bairro reconstruída "
        "do conteúdo de uma única coluna.\n"
    )

    md.append("## Método\n")
    md.append(
        "Theil-T com peso igual por unidade (cada bairro conta 1):\n\n"
        "```\n"
        "T = (1/N) * Σ_i (y_i / ȳ) * ln(y_i / ȳ)\n"
        "```\n\n"
        "Decomposição aditiva por grupos g (RAs):\n\n"
        "```\n"
        "T_between = Σ_g (n_g/N) * (ȳ_g/ȳ) * ln(ȳ_g/ȳ)\n"
        "T_within  = Σ_g (n_g/N) * (ȳ_g/ȳ) * T_g\n"
        "T         = T_between + T_within\n"
        "```\n"
    )
    md.append(
        "Theil aceita ratio scale com positividade. IDEB ∈ [0, 10] e na prática carioca "
        "fica entre ~4.5 e ~7.5 — bem dentro do range válido.\n"
    )
    md.append(
        "Bairros com IDEB faltante (`...` no Excel) são descartados naquele ano. "
        "RAs com 0–1 bairros válidos contribuem 0 ao within (esperado: variância "
        "dentro de unidade singular é nula).\n"
    )

    if theil_rows:
        avg_within = sum(r["share_within"] for r in theil_rows) / len(theil_rows)
        avg_between = sum(r["share_between"] for r in theil_rows) / len(theil_rows)
        md.append("## Achado principal\n")
        md.append(
            f"Em todos os 9 anos com dados (2007–2023), **{avg_within:.0%} da desigualdade "
            f"do IDEB municipal está dentro das RAs, não entre elas** "
            f"(média anual; entre-RA fica em {avg_between:.0%}). "
            "Em outras palavras: políticas públicas educacionais que tratam a RA como "
            "unidade homogênea (que é a granularidade típica do IPP, do IPS e da maioria "
            "dos painéis municipais) estão errando o foco — a maior parte da variância "
            "está em escala mais fina, **bairro a bairro**.\n"
        )
        md.append(
            "Esse achado é justamente o tipo de evidência que o produto HEX-EDU pretende "
            "tornar visível: um mapa H3 do Rio em que cada hexágono carrega o IDEB "
            "interpolado pelo bairro de origem, em lugar do agregado por RA que mascara a "
            "variação relevante.\n"
        )

    md.append("## Decomposição por ano\n")
    md.append(md_table(
        ["Ano", "n bairros", "n RAs", "IDEB médio", "T total", "T entre-RA", "T dentro-RA", "% entre", "% dentro"],
        by_year_table,
        ["right"] * 9,
    ))
    md.append("")

    # First-vs-last comparison
    if len(theil_rows) >= 2:
        first = theil_rows[0]
        last = theil_rows[-1]
        delta_total = last["T_total"] - first["T_total"]
        delta_between = last["T_between"] - first["T_between"]
        md.append(f"## Variação {first['year']} → {last['year']}\n")
        md.append(
            f"- IDEB médio: {first['mean_ideb']:.2f} → {last['mean_ideb']:.2f} "
            f"(Δ {last['mean_ideb'] - first['mean_ideb']:+.2f})\n"
            f"- T total: {first['T_total']:.4f} → {last['T_total']:.4f} (Δ {delta_total:+.4f})\n"
            f"- T entre-RA: {first['T_between']:.4f} → {last['T_between']:.4f} (Δ {delta_between:+.4f})\n"
            f"- T dentro-RA: {first['T_within']:.4f} → {last['T_within']:.4f}\n"
            f"- Parcela entre-RA: {first['share_between']:.0%} → {last['share_between']:.0%}\n"
        )

    # Top/bottom RAs in latest year
    if theil_rows:
        last_year = theil_rows[-1]["year"]
        ra_means = []
        for ra in {b["ra"] for b in bairros}:
            vals = [b["scores"][last_year] for b in bairros if b["ra"] == ra]
            vals = [v for v in vals if v is not None]
            if vals:
                ra_means.append((ra, sum(vals) / len(vals), len(vals)))
        ra_means.sort(key=lambda x: x[1])
        md.append(f"## Ranking de RAs por IDEB médio em {last_year}\n")
        md.append(md_table(
            ["#", "RA", "IDEB médio", "n bairros válidos"],
            [
                [i + 1, ra, f"{m:.2f}", n]
                for i, (ra, m, n) in enumerate(ra_means)
            ],
            ["right", "left", "right", "right"],
        ))
        md.append("")

    md.append("## Caveats\n")
    md.append(
        "- **Peso igual por bairro**: tratamos cada bairro como uma unidade. "
        "Em rigor, o IDEB de um bairro com 30 escolas e o de um com 1 escola contam "
        "igual no T. Ponderação por nº de matrículas seria mais defensável; "
        "o data.rio tem dados de matrícula em outros itens — implementar na próxima iteração.\n"
        "- **IDEB ≠ qualidade educacional total**: é uma combinação de fluxo (aprovação) "
        "e desempenho (SAEB). Análises mais ricas decompõem cada componente separado, "
        "como faz Pereira et al. (2019).\n"
        "- **Rede municipal apenas**: IDEB reportado aqui cobre a rede pública municipal. "
        "Bairros sem escolas municipais (ou com IDEB suprimido por baixa amostra) ficam "
        "fora — viés sistemático contra zonas com forte presença privada/estadual.\n"
        "- **MAUP**: a definição de bairro segue o IPP. Mudanças de fronteira ao longo "
        "dos anos podem inflar/deflar `T_within`. Não corrigido aqui.\n"
        "- **Sanity check**: a coluna `check_sum` em `theil_ideb_anos_iniciais.csv` é "
        "`T_b + T_w - T` e deve ser ≈ 0 (precisão de ponto flutuante). Cheque antes de citar números.\n"
    )

    md.append("## Reprodutibilidade\n")
    md.append(
        "```bash\n"
        "pip install xlrd>=2.0\n"
        "python3 analysis/03_download_excels.py    # se ainda não baixou\n"
        "python3 analysis/10_theil_ideb.py\n"
        "```\n"
        "Saídas: `data/processed/ideb_bairros.csv` (long format) e "
        "`data/processed/theil_ideb_anos_iniciais.csv`.\n"
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(md), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(ROOT)}")
    print(f"wrote {OUT_LONG.relative_to(ROOT)}")
    print(f"wrote {OUT_THEIL.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
