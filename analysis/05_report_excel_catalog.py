"""Renderiza docs/reports/03_excel_catalog.md a partir do catálogo empírico.

Lê:
  - data/processed/excel_catalog.csv
  - data/processed/excel_sheets.csv
  - data/raw/excel/_index.json
  - data/manifest_enriched.csv (para cruzar com heurísticas anteriores)
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "processed" / "excel_catalog.csv"
SHEETS = ROOT / "data" / "processed" / "excel_sheets.csv"
DOWNLOAD_INDEX = ROOT / "data" / "raw" / "excel" / "_index.json"
ENRICHED = ROOT / "data" / "manifest_enriched.csv"
REPORT = ROOT / "docs" / "reports" / "03_excel_catalog.md"


def load_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def md_table(headers: list[str], rows: list[list], aligns: list[str] | None = None) -> str:
    aligns = aligns or ["left"] * len(headers)
    sep = {"left": ":---", "right": "---:", "center": ":---:"}
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(sep[a] for a in aligns) + " |")
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def fmt_int(n) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)


def percentile(values: list[int], p: float) -> int:
    s = sorted(values)
    if not s:
        return 0
    return s[min(len(s) - 1, int(len(s) * p))]


def granularity_bucket(n: int) -> str:
    if n == 0:
        return "0 (sem rótulos detectáveis)"
    if n <= 3:
        return "1–3 (totais agregados)"
    if n <= 6:
        return "4–6 (compatível com 5 APs)"
    if n <= 12:
        return "7–12 (compatível com 11 CREs)"
    if n <= 30:
        return "13–30 (compatível com RP / parcial RA)"
    if n <= 50:
        return "31–50 (compatível com 33 RAs)"
    if n <= 200:
        return "51–200 (compatível com ~163 bairros)"
    return "200+ (escola ou linha-por-observação)"


def main() -> None:
    catalog = load_csv(CATALOG)
    sheets = load_csv(SHEETS)
    download_idx = json.loads(DOWNLOAD_INDEX.read_text(encoding="utf-8"))
    enriched = load_csv(ENRICHED)

    n_files = len(catalog)
    n_sheets = len(sheets)
    total_bytes = sum(int(r["file_bytes"]) for r in catalog)

    fmt_counts = Counter(r["format"] for r in catalog)

    sizes = sorted(int(r["file_bytes"]) for r in catalog)
    p50, p90, p99 = percentile(sizes, 0.5), percentile(sizes, 0.9), percentile(sizes, 0.99)

    n_sheets_per_file = Counter(int(r["n_sheets"]) for r in catalog)

    # Year coverage
    have_years = [r for r in catalog if r["years_min"]]
    year_mins = [int(r["years_min"]) for r in have_years]
    year_maxs = [int(r["years_max"]) for r in have_years]
    spans = [int(r["years_max"]) - int(r["years_min"]) for r in have_years]

    span_buckets = Counter()
    for s in spans:
        if s == 0:
            span_buckets["0 anos (snapshot único)"] += 1
        elif s <= 5:
            span_buckets["1–5 anos"] += 1
        elif s <= 10:
            span_buckets["6–10 anos"] += 1
        elif s <= 20:
            span_buckets["11–20 anos"] += 1
        else:
            span_buckets["21+ anos"] += 1

    # Granularity from first column unique counts (max across sheets per file)
    gran_buckets = Counter(
        granularity_bucket(int(r["max_unique_first_col"])) for r in catalog
    )

    # Cross with prior heuristic (manifest_enriched)
    enriched_by_id = {r["id"]: r for r in enriched if r["type"] == "Microsoft Excel"}
    heur_vs_emp_year_disagreement = []
    for r in catalog:
        emp_min = int(r["years_min"])
        emp_max = int(r["years_max"])
        # The enriched CSV uses year_modified (last update on portal) as a temporal proxy;
        # compare with empirical content-derived years_max
        e = enriched_by_id.get(r["id"], {})
        ym = int(e["year_modified"]) if e.get("year_modified") else None
        if ym is not None and abs(ym - emp_max) >= 5:
            heur_vs_emp_year_disagreement.append((r, ym, emp_max))

    # Shortlist for HEX-EDU: long span, granularity 30+, reasonable size
    def is_shortlist(r: dict) -> bool:
        return (
            r["years_min"]
            and (int(r["years_max"]) - int(r["years_min"])) >= 5
            and int(r["max_unique_first_col"]) >= 30
        )

    shortlist = sorted(
        [r for r in catalog if is_shortlist(r)],
        key=lambda r: (
            int(r["years_max"]) - int(r["years_min"]),
            int(r["num_views"]),
        ),
        reverse=True,
    )[:20]

    # Top by views
    top_views = sorted(catalog, key=lambda r: int(r["num_views"]), reverse=True)[:10]

    # Build report
    out: list[str] = []
    out.append("# 03 — Catálogo empírico dos Excels\n")
    out.append(
        "Gerado a partir dos 127 arquivos do tipo `Microsoft Excel` baixados em "
        "`data/raw/excel/`. Diferente dos relatórios anteriores (que se apoiam em "
        "metadados do manifest e regex sobre títulos), este relatório lê o conteúdo "
        "real de cada arquivo via `xlrd`/`openpyxl`. Onde houver discrepância com as "
        "heurísticas anteriores, ela é apontada explicitamente.\n"
    )

    out.append("## Visão geral\n")
    out.append(md_table(
        ["Métrica", "Valor"],
        [
            ["Arquivos", fmt_int(n_files)],
            ["Sheets totais", fmt_int(n_sheets)],
            ["Tamanho total em disco", f"{total_bytes / 1024**2:.1f} MiB ({fmt_int(total_bytes)} B)"],
            ["Tamanho p50 / p90 / p99", f"{p50/1024:.0f} KiB / {p90/1024:.0f} KiB / {p99/1024:.0f} KiB"],
            ["Janela temporal global", f"{min(year_mins)}–{max(year_maxs)}"],
        ],
    ))
    out.append("")

    out.append("## Achado #1 — quase tudo é `.xls` legacy, não `.xlsx`\n")
    out.append(
        "Apesar do `type: Microsoft Excel` no manifest e do `Content-Type` "
        "`...spreadsheetml.sheet` reportado pela API (que sugere XLSX), o conteúdo "
        "real é majoritariamente o **formato binário pré-2007** (Composite Document, "
        "magic bytes `D0 CF 11 E0`):\n"
    )
    out.append(md_table(
        ["Formato real (magic bytes)", "Arquivos", "%"],
        [[k, v, f"{v / n_files:.1%}"] for k, v in fmt_counts.most_common()],
        ["left", "right", "right"],
    ))
    out.append(
        "\nImplicação prática: `pandas.read_excel(..., engine='openpyxl')` falha em "
        "126 dos 127 arquivos. É preciso usar `xlrd>=2.0` (que lê `.xls`) ou converter "
        "previamente. O probe da API (Relatório 02) reporta MIME XLSX porque o portal "
        "anota o type genericamente, sem sniffing real.\n"
    )

    out.append("## Achado #2 — sizes empíricos: 12.3 MiB total, não ~100 MiB\n")
    out.append(
        f"O total real é **{total_bytes / 1024**2:.1f} MiB** (média ~"
        f"{total_bytes / n_files / 1024:.0f} KiB/arquivo). A estimativa anterior "
        "neste lab (Relatório 02) era ~100 MiB, baseada em **uma única amostra** "
        "(o IPS, que é justamente o maior arquivo do corpus). É um caso clássico de "
        "extrapolar de outlier — sirva de aviso.\n"
    )
    out.append(
        f"\nDistribuição de tamanho (bytes): mediana **{p50:,}**, p90 **{p90:,}**, "
        f"p99 **{p99:,}**, máximo **{max(sizes):,}**.\n"
    )

    out.append("## Estrutura: sheets por arquivo\n")
    out.append(md_table(
        ["Sheets/arquivo", "Arquivos"],
        [[k, v] for k, v in sorted(n_sheets_per_file.items())],
        ["right", "right"],
    ))
    out.append(
        "\n44 arquivos (35%) têm sheet única; outros 9 têm 24 sheets cada — "
        "padrão de 'um sheet por ano' (provavelmente IDS / IPS por ano).\n"
    )

    out.append("## Cobertura temporal (lida do conteúdo)\n")
    out.append(
        "A detecção considera anos 4-dígitos em strings ou em células numéricas "
        "**dentro das primeiras 4 linhas** de cada sheet (cabeçalhos). Valores numéricos "
        "no corpo da tabela em range 1990–2030 são ignorados, porque há contagens "
        "(ex.: número de professores) que cairiam no range — corrigido após detectar "
        "células com `2070`, `2038` em meio a dados.\n"
    )
    out.append(md_table(
        ["Span", "Arquivos"],
        [[k, span_buckets[k]] for k in [
            "0 anos (snapshot único)", "1–5 anos", "6–10 anos", "11–20 anos", "21+ anos"
        ] if k in span_buckets],
        ["left", "right"],
    ))
    out.append("")

    out.append("## Granularidade espacial (heurística por unicos da 1ª coluna)\n")
    out.append(
        "O número de valores únicos na primeira coluna (descontadas as 3 primeiras "
        "linhas presumidas como cabeçalho) é cruzado com as quantidades conhecidas "
        "de unidades administrativas do Rio: **5 APs**, **11 CREs**, **33 RAs**, "
        "~**163 bairros**, milhares de escolas. É heurístico — pode haver sheet com "
        "múltiplas escalas misturadas — mas é a primeira aproximação empírica.\n"
    )
    out.append(md_table(
        ["Bucket", "Arquivos"],
        [[k, v] for k, v in sorted(gran_buckets.items(), key=lambda x: -x[1])],
        ["left", "right"],
    ))
    out.append("")

    out.append("## Top 10 por visualizações (cruzando com dados empíricos)\n")
    out.append(md_table(
        ["Views", "Format", "Sheets", "Linhas", "Anos", "Unq col 0", "Título"],
        [
            [
                fmt_int(r["num_views"]),
                r["format"],
                r["n_sheets"],
                r["total_rows"],
                f"{r['years_min']}–{r['years_max']}" if r["years_min"] else "—",
                r["max_unique_first_col"],
                r["title"][:60],
            ]
            for r in top_views
        ],
        ["right", "left", "right", "right", "left", "right", "left"],
    ))
    out.append("")

    out.append("## Shortlist preliminar para HEX-EDU\n")
    out.append(
        "Critério: span ≥ 5 anos **e** unicos da coluna 0 ≥ 30 (proxy para "
        "granularidade RA-ou-mais-fina). Ordenado por span (decrescente), depois "
        "views. Esta é a porta de entrada da próxima fase, **não** uma escolha "
        "metodológica — toda candidata aqui ainda precisa de auditoria manual de "
        "cabeçalhos antes de virar input para Theil.\n"
    )
    out.append(md_table(
        ["Anos", "Unq col 0", "Sheets", "Views", "Título", "ID"],
        [
            [
                f"{r['years_min']}–{r['years_max']}",
                r["max_unique_first_col"],
                r["n_sheets"],
                fmt_int(r["num_views"]),
                r["title"][:60],
                f"`{r['id']}`",
            ]
            for r in shortlist
        ],
        ["left", "right", "right", "right", "left", "left"],
    ))
    out.append("")

    out.append("## Discrepâncias com heurísticas anteriores\n")
    out.append(
        f"- **Tamanho total**: heurística (Relatório 02) projetava ~100 MiB; real = "
        f"**{total_bytes / 1024**2:.1f} MiB**. Erro de ~8×, causado por extrapolação "
        "a partir de um outlier.\n"
        f"- **Formato**: `Content-Type` HTTP afirma XLSX; conteúdo real é "
        f"**{fmt_counts.get('xls', 0)} XLS legacy + {fmt_counts.get('xlsx', 0)} XLSX**. "
        "O portal não faz sniffing.\n"
        f"- **Anos detectados**: {len(have_years)}/{n_files} têm cobertura temporal "
        "extraível do conteúdo. Antes da correção, 5 arquivos apareciam com `years_max=2030` "
        "porque células numéricas como `2030`, `2038`, `2070` (contagens de professores/alunos) "
        "eram interpretadas como anos. Detecção numérica restrita a cabeçalhos resolveu.\n"
        f"- **Heurística temática (Relatório 01)**: ainda é regex sobre `title` + `snippet`. "
        "Vale auditar contra os cabeçalhos reais agora disponíveis em `data/processed/excel_sheets.csv`.\n"
    )

    out.append("## Reprodutibilidade\n")
    out.append(
        "```bash\n"
        "pip install openpyxl xlrd>=2.0\n"
        "python3 analysis/03_download_excels.py    # ~92 s, 12.3 MiB\n"
        "python3 analysis/04_excel_catalog.py      # <1 s\n"
        "python3 analysis/05_report_excel_catalog.py\n"
        "```\n"
    )
    out.append(
        "Os binários em `data/raw/excel/` ficam gitignored (12.3 MiB cabe no repo "
        "tranquilamente, mas seria poluição — o catálogo derivado em "
        "`data/processed/` já condensa o que importa, com 2 CSVs leves).\n"
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
