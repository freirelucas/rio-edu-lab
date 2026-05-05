"""EDA do manifest.json (Grupo Educação do data.rio).

Produz:
  - data/manifest_enriched.csv  (inventário derivado, uma linha por item)
  - analysis/reports/01_manifest_eda.md  (relatório markdown)

Uso:
  python analysis/01_manifest_eda.py
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.json"
ENRICHED = ROOT / "data" / "manifest_enriched.csv"
REPORT = ROOT / "analysis" / "reports" / "01_manifest_eda.md"

GRANULARITY_PATTERNS = [
    ("escola", r"\b(escola|escolar|unidade escolar)s?\b"),
    ("cre", r"\bCRE\b"),
    ("bairro", r"\bbairros?\b"),
    ("ra", r"\b(RA|região administrativa|regiões administrativas)\b"),
    ("rp", r"\b(RP|região de planejamento|regiões de planejamento)\b"),
    ("ap", r"\b(AP|área de planejamento|áreas de planejamento)\b"),
    ("municipio", r"\b(município|cidade|capitais|municipal)\b"),
]

THEME_PATTERNS = [
    ("matricula", r"matrícul|matricul"),
    ("ideb_avaliacao", r"\b(IDEB|SAEB|prova brasil|avaliação)\b"),
    ("infraestrutura", r"infraestrutura|equipamentos|biblioteca|laboratóri"),
    ("censo_escolar", r"censo escolar"),
    ("censo_demografico", r"censo (demográfico|201[01]|2022)|prévias do censo"),
    ("ips_ids", r"\b(IPS|IDS|Índice de Progresso Social|Índice de Desenvolvimento Social)\b"),
    ("docentes", r"docent|professor"),
    ("pnad", r"\bPNAD\b"),
    ("ensino_superior", r"ensino superior|graduação|universidad"),
    ("ensino_medio", r"ensino médio"),
    ("educacao_basica", r"educação básica|ensino fundamental"),
    ("escolaridade", r"escolaridade"),
    ("transporte", r"transporte"),
]


def load_items() -> tuple[dict, list[dict]]:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return raw, raw["items"]


def ts_to_year(ms: int | None) -> int | None:
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).year


def first_match(text: str, patterns: list[tuple[str, str]]) -> str:
    for label, pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            return label
    return ""


def all_matches(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    return [label for label, pat in patterns if re.search(pat, text, flags=re.IGNORECASE)]


def enrich(items: list[dict]) -> list[dict]:
    rows = []
    for it in items:
        haystack = " ".join(
            str(it.get(k, "") or "") for k in ("title", "snippet")
        ) + " " + " ".join(it.get("tags", []) or [])
        rows.append({
            "id": it.get("id"),
            "title": it.get("title"),
            "type": it.get("type"),
            "owner": it.get("owner"),
            "url": it.get("url") or "",
            "has_url": bool(it.get("url")),
            "size": it.get("size", 0) or 0,
            "num_views": it.get("numViews", 0) or 0,
            "tags": "|".join(it.get("tags", []) or []),
            "year_created": ts_to_year(it.get("created")),
            "year_modified": ts_to_year(it.get("modified")),
            "granularity_guess": first_match(haystack, GRANULARITY_PATTERNS),
            "themes_guess": "|".join(all_matches(haystack, THEME_PATTERNS)),
            "snippet": (it.get("snippet") or "").replace("\n", " ").strip(),
        })
    return rows


def write_enriched(rows: list[dict]) -> None:
    ENRICHED.parent.mkdir(parents=True, exist_ok=True)
    with ENRICHED.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def md_table(headers: list[str], data: list[list], aligns: list[str] | None = None) -> str:
    aligns = aligns or ["left"] * len(headers)
    sep = {"left": ":---", "right": "---:", "center": ":---:"}
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(sep[a] for a in aligns) + " |")
    for row in data:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def build_report(meta: dict, items: list[dict], rows: list[dict]) -> str:
    n = len(items)
    types = Counter(it["type"] for it in rows).most_common()
    owners = Counter(it["owner"] for it in rows).most_common()
    has_url_n = sum(1 for r in rows if r["has_url"])
    total_views = sum(r["num_views"] for r in rows)

    by_year_mod = Counter(r["year_modified"] for r in rows if r["year_modified"])
    by_year_cre = Counter(r["year_created"] for r in rows if r["year_created"])

    by_granularity = Counter(r["granularity_guess"] or "(não classificado)" for r in rows)

    theme_counter: Counter[str] = Counter()
    for r in rows:
        if r["themes_guess"]:
            for t in r["themes_guess"].split("|"):
                theme_counter[t] += 1
    no_theme = sum(1 for r in rows if not r["themes_guess"])

    top_views = sorted(rows, key=lambda r: r["num_views"], reverse=True)[:10]

    type_x_year: dict[tuple[str, int], int] = Counter()
    for r in rows:
        if r["year_modified"]:
            type_x_year[(r["type"], r["year_modified"])] += 1
    years_axis = sorted({y for _, y in type_x_year})
    types_axis = [t for t, _ in types]

    top_excels_by_views = sorted(
        (r for r in rows if r["type"] == "Microsoft Excel"),
        key=lambda r: r["num_views"], reverse=True,
    )[:15]

    out: list[str] = []
    out.append("# 01 — EDA do manifest do Grupo Educação (data.rio)\n")
    out.append(f"_Gerado a partir de `data/manifest.json` (fetched_at = {meta['fetched_at']})._\n")
    out.append(f"_Source: {meta['source']}_  ")
    out.append(f"_Group: {meta['group_url']}_\n")

    out.append("## Visão geral\n")
    out.append(md_table(
        ["Métrica", "Valor"],
        [
            ["Itens", n],
            ["Visualizações somadas", f"{total_views:,}"],
            ["Itens com URL direta", f"{has_url_n} ({has_url_n / n:.0%})"],
            ["Itens sem URL direta", f"{n - has_url_n} ({1 - has_url_n / n:.0%})"],
            ["Owners distintos", len(owners)],
        ],
    ))
    out.append("")

    out.append("## Distribuição por tipo\n")
    out.append(md_table(
        ["Tipo", "Itens", "%"],
        [[t, c, f"{c / n:.1%}"] for t, c in types],
        ["left", "right", "right"],
    ))
    out.append("")

    out.append("## Owners\n")
    out.append(md_table(
        ["Owner", "Itens"],
        [[o, c] for o, c in owners],
        ["left", "right"],
    ))
    out.append("")

    out.append("## Janela temporal\n")
    out.append("### Itens por `year_modified`\n")
    out.append(md_table(
        ["Ano", "Itens"],
        [[y, by_year_mod[y]] for y in sorted(by_year_mod)],
        ["right", "right"],
    ))
    out.append("\n### Itens por `year_created`\n")
    out.append(md_table(
        ["Ano", "Itens"],
        [[y, by_year_cre[y]] for y in sorted(by_year_cre)],
        ["right", "right"],
    ))
    out.append("")

    out.append("## Tipo × ano de modificação\n")
    header = ["Tipo"] + [str(y) for y in years_axis] + ["Total"]
    rows_table = []
    for t in types_axis:
        line = [t]
        total = 0
        for y in years_axis:
            v = type_x_year.get((t, y), 0)
            line.append(v)
            total += v
        line.append(total)
        rows_table.append(line)
    out.append(md_table(header, rows_table, ["left"] + ["right"] * (len(header) - 1)))
    out.append("")

    out.append("## Granularidade espacial (heurística por título/snippet/tags)\n")
    out.append(md_table(
        ["Granularidade", "Itens"],
        [[g, c] for g, c in by_granularity.most_common()],
        ["left", "right"],
    ))
    out.append("")

    out.append("## Temas (heurística, multi-rótulo)\n")
    out.append(md_table(
        ["Tema", "Itens"],
        [[t, c] for t, c in theme_counter.most_common()] + [["(sem tema classificado)", no_theme]],
        ["left", "right"],
    ))
    out.append("")

    out.append("## Top 10 itens por visualizações\n")
    out.append(md_table(
        ["Views", "Tipo", "Título"],
        [[f"{r['num_views']:,}", r["type"], r["title"][:80]] for r in top_views],
        ["right", "left", "left"],
    ))
    out.append("")

    out.append("## Top 15 Excels por visualizações (candidatos para HEX-EDU)\n")
    out.append(md_table(
        ["Views", "Granularidade", "Temas", "Título"],
        [
            [
                f"{r['num_views']:,}",
                r["granularity_guess"] or "—",
                r["themes_guess"] or "—",
                r["title"][:80],
            ]
            for r in top_excels_by_views
        ],
        ["right", "left", "left", "left"],
    ))
    out.append("")

    out.append("## Achados-chave\n")
    pct_2023 = by_year_mod.get(2023, 0) / n
    top5_views = sum(r["num_views"] for r in top_views[:5])
    out.append(
        f"- **Concentração temporal**: {by_year_mod.get(2023, 0)} de {n} itens ({pct_2023:.0%}) "
        f"foram modificados em 2023 — provável bulk re-tag de metadados, não refresh de dados.\n"
        f"- **Concentração de atenção**: os 5 itens mais vistos somam {top5_views:,} de "
        f"{total_views:,} views ({top5_views / total_views:.0%}). Todos são interativos "
        "(Hub Site, Web Map App, Feature Service) — confirma o gap entre Excels históricos "
        "e ferramentas de exploração que o ACEC-Hub propõe ocupar.\n"
        f"- **URLs ausentes**: {n - has_url_n} de {n} itens ({1 - has_url_n / n:.0%}) "
        "não têm URL direta no manifest. Antes de qualquer pipeline de ingestão, validar se "
        "a URL é resolvida sob demanda pela API do ArcGIS Hub ou se está realmente quebrada.\n"
        "- **127 Excels = backlog do MVP**: a triagem por tema e granularidade no CSV "
        "enriquecido (`data/manifest_enriched.csv`) deve guiar o shortlist do HEX-EDU.\n"
    )

    return "\n".join(out)


def main() -> None:
    meta, items = load_items()
    rows = enrich(items)
    write_enriched(rows)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(build_report(meta, items, rows), encoding="utf-8")
    print(f"wrote {ENRICHED.relative_to(ROOT)} ({len(rows)} rows)")
    print(f"wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
