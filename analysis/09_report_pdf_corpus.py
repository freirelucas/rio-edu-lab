"""Renderiza docs/reports/05_pdf_corpus.md a partir do catálogo PDF."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "processed" / "pdf_catalog.csv"
REPORT = ROOT / "docs" / "reports" / "05_pdf_corpus.md"


def md_table(headers, rows, aligns=None):
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


def main() -> None:
    rows = list(csv.DictReader(CATALOG.open(encoding="utf-8")))
    n = len(rows)
    total_bytes = sum(int(r["file_bytes"]) for r in rows)
    total_pages = sum(int(r["n_pages"] or 0) for r in rows)
    n_with_text = sum(1 for r in rows if r["has_text_layer"] == "True")
    n_encrypted = sum(1 for r in rows if r["is_encrypted"] == "True")
    n_errors = sum(1 for r in rows if r["parse_error"])

    cols = Counter(r["colecao"] for r in rows)

    years = [int(r["issue_year"]) for r in rows if r["issue_year"]]

    pages = sorted(int(r["n_pages"] or 0) for r in rows)
    p50 = pages[len(pages) // 2] if pages else 0
    p90 = pages[int(len(pages) * 0.9)] if pages else 0

    by_col_views = Counter()
    by_col_pages = Counter()
    for r in rows:
        c = r["colecao"]
        by_col_views[c] += int(r["num_views"] or 0)
        by_col_pages[c] += int(r["n_pages"] or 0)

    out: list[str] = []
    out.append("# 05 — Corpus dos PDFs (Estudos Cariocas et al.)\n")
    out.append(
        "Os 35 PDFs do Grupo Educação são publicações do IPP (Instituto Pereira Passos) "
        "em quatro coleções editoriais distintas. Este relatório lê o conteúdo real de "
        "cada arquivo (texto da 1ª página + total de páginas) e classifica por coleção.\n"
    )

    out.append("## Visão geral\n")
    out.append(md_table(
        ["Métrica", "Valor"],
        [
            ["Arquivos", n],
            ["Tamanho total em disco", f"{total_bytes / 1024**2:.1f} MiB"],
            ["Páginas totais", fmt_int(total_pages)],
            ["Páginas por arquivo (p50 / p90)", f"{p50} / {p90}"],
            ["Com camada de texto extraível", f"{n_with_text}/{n} ({n_with_text / n:.0%})"],
            ["Criptografados", n_encrypted],
            ["Erros de parse", n_errors],
        ],
    ))
    out.append("")

    out.append("## Distribuição por coleção\n")
    rows_table = []
    for c, count in cols.most_common():
        rows_table.append([
            c, count, fmt_int(by_col_views[c]), fmt_int(by_col_pages[c])
        ])
    out.append(md_table(
        ["Coleção", "Arquivos", "Views totais", "Páginas totais"],
        rows_table,
        ["left", "right", "right", "right"],
    ))
    out.append("")

    if years:
        out.append(
            f"## Janela temporal das publicações\n\n"
            f"Anos detectados (no título ou na 1ª página): "
            f"**{min(years)}–{max(years)}** ({len(years)} de {n} PDFs com ano detectável)\n"
        )

    # Top by views
    top = sorted(rows, key=lambda r: int(r["num_views"] or 0), reverse=True)[:10]
    out.append("## Top 10 por visualizações\n")
    out.append(md_table(
        ["Views", "Páginas", "Coleção", "Ano", "Título"],
        [
            [
                fmt_int(r["num_views"]),
                r["n_pages"] or "—",
                r["colecao"],
                r["issue_year"] or "—",
                (r["title"] or "")[:55],
            ]
            for r in top
        ],
        ["right", "right", "left", "right", "left"],
    ))
    out.append("")

    # Skipped/error files
    bad = [r for r in rows if r["parse_error"] or r["has_text_layer"] != "True"]
    if bad:
        out.append("## Arquivos com problema (sem texto extraível ou erro)\n")
        out.append(md_table(
            ["Páginas", "Erro / motivo", "Título"],
            [
                [
                    r["n_pages"] or "—",
                    r["parse_error"] or "(sem camada de texto — provável scanned image)",
                    (r["title"] or "")[:60],
                ]
                for r in bad
            ],
            ["right", "left", "left"],
        ))
        out.append("")

    out.append("## Reprodutibilidade\n")
    out.append(
        "```bash\n"
        "pip install pypdf\n"
        "python3 analysis/07_download_pdfs.py    # baixa data/raw/pdf/*.pdf (~100 MiB)\n"
        "python3 analysis/08_pdf_corpus.py       # gera CSV + textos da 1ª página\n"
        "python3 analysis/09_report_pdf_corpus.py\n"
        "```\n"
    )
    out.append(
        "Textos completos da 1ª página de cada PDF ficam em `data/raw/pdf/_first_pages/{id}.txt` "
        "(gitignored, mas reproduzíveis), úteis para grep manual quando precisar achar uma "
        "metodologia citada.\n"
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
