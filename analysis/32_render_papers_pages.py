"""Renderiza páginas Markdown a partir de `data/papers_catalog.yml`.

Para cada paper, escreve `docs/papers/<id>.md` com cabeçalho bibliográfico,
abstract, requisitos de dados, cobertura no data.rio e (se replicado)
links para relatórios + insight para gestores. Também atualiza a tabela
do catálogo em `docs/papers/index.md`.

Determinístico: o output depende exclusivamente do YAML + opcionalmente do
snapshot `openalex_citations.json`. Pode rodar em CI.

Uso:
  python3 analysis/32_render_papers_pages.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
OPENALEX_JSON = ROOT / "data" / "processed" / "openalex_citations.json"
OUT_DIR = ROOT / "docs" / "papers"
OUT_INDEX = OUT_DIR / "index.md"

STATUS_BADGES = {
    "full": ("Replicado", "#1a9850"),
    "partial": ("Replicação parcial", "#fee08b"),
    "pending": ("Catalogado", "#abd9e9"),
    "unfeasible": ("Dados indisponíveis", "#d73027"),
}

COVERAGE_BADGES = {
    "available": ("✅", "disponível no data.rio"),
    "partial": ("◐", "cobertura parcial"),
    "external": ("⚠️", "dado externo necessário"),
    "missing": ("✗", "não disponível"),
}


def fmt_authors(authors: list[str]) -> str:
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} & {authors[1]}"
    return f"{authors[0]} et al."


def fmt_authors_full(authors: list[str]) -> str:
    return ", ".join(authors)


REPORTS_DIR = ROOT / "docs" / "reports"


def _resolve_report_link(report_id: int) -> str:
    """Find docs/reports/NN_*.md and return relative link from docs/papers/."""
    prefix = f"{report_id:02d}_"
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.glob(f"{prefix}*.md"):
            return f"../reports/{f.stem}.md"
    return f"../reports/{prefix}.md"


def render_paper_page(p: dict, openalex: dict | None) -> str:
    pid = p["id"]
    status = p["replication_status"]
    badge_label, _ = STATUS_BADGES[status]

    lines = [
        "---",
        f"title: \"{fmt_authors(p['authors'])} ({p['year']}) — {p['title'][:80]}\"",
        f"description: \"{(p.get('abstract') or '').strip()[:160]}\"",
        "---",
        "",
        f"# {fmt_authors(p['authors'])} ({p['year']})",
        "",
        f"**{p['title']}**",
        "",
        f"_{p['venue']}_",
        "",
        f"<a href=\"{p['doi_or_url']}\" target=\"_blank\">{p['doi_or_url']}</a>",
        "",
    ]

    # OpenAlex citation snapshot
    if openalex and pid in openalex:
        oa = openalex[pid]
        if oa.get("citations_openalex") is not None:
            cit_pt = f"{oa['citations_openalex']:,}".replace(",", ".")
            lines += [
                f"**Citações (OpenAlex, {oa['fetched_at']}):** {cit_pt}",
                "",
            ]

    lines += [
        f"**Status:** _{badge_label}_",
        "",
        "## Resumo",
        "",
        (p.get("abstract") or "_(resumo a redigir)_").strip(),
        "",
        "## Categorias",
        "",
        f"- **Área:** {', '.join(p.get('area', []))}",
        f"- **Método:** {', '.join(p.get('method', []))}",
        f"- **Brasil-específico:** {'sim' if p.get('brazil_specific') else 'não'}",
        "",
        "## Requisitos de dados × cobertura no data.rio",
        "",
        "| Requisito | Status | Item data.rio |",
        "|---|---|---|",
    ]
    coverage = {c["requirement"]: c for c in (p.get("data_rio_coverage") or [])}
    for req in p.get("data_requirements", []):
        cov = coverage.get(req, {"status": "missing", "item_id": None})
        icon, label = COVERAGE_BADGES.get(cov["status"], ("?", cov["status"]))
        item = cov.get("item_id") or "—"
        lines.append(f"| {req} | {icon} {label} | `{item}` |")
    lines.append("")

    if status in ("full", "partial"):
        lines += ["## Replicação no lab", ""]
        if p.get("product"):
            lines.append(f"- **Produto associado:** {p['product']}")
        if p.get("report_ids"):
            ids = ", ".join(f"[{i}]({_resolve_report_link(i)})" for i in p["report_ids"])
            lines.append(f"- **Relatórios:** {ids}")
        if p.get("scripts"):
            ids = ", ".join(f"`analysis/{i:02d}_*.py`" for i in p["scripts"])
            lines.append(f"- **Scripts:** {ids}")
        lines.append("")
        if p.get("policy_insight"):
            lines += [
                "## Para gestores públicos",
                "",
                f"> {p['policy_insight'].strip()}",
                "",
            ]
    elif status == "pending":
        lines += [
            "## Status no lab",
            "",
            "Catalogado, replicação leve planejada para release próxima. "
            "Dados básicos cobertos no data.rio.",
            "",
        ]
    elif status == "unfeasible":
        lines += [
            "## Status no lab",
            "",
            "Catalogado para referência. Requer dados não disponíveis no data.rio "
            "(ex.: microdado individual, painel longitudinal) — replicação "
            "exigiria fontes externas.",
            "",
        ]

    lines += [
        "## Referência completa",
        "",
        f"{fmt_authors_full(p['authors'])} ({p['year']}). _{p['title']}_. {p['venue']}.",
        "",
        "[← Voltar ao catálogo](index.md)",
        "",
    ]
    return "\n".join(lines)


def render_index(papers: list[dict], openalex: dict | None) -> str:
    """Renders the searchable catalog landing page."""
    by_status: dict[str, list[dict]] = {k: [] for k in STATUS_BADGES}
    for p in papers:
        by_status[p["replication_status"]].append(p)

    lines = [
        "---",
        "title: \"Catálogo de papers — rio-edu-lab\"",
        "description: \"Papers em educação aplicados ao Rio: status de replicação + cobertura no data.rio.\"",
        "---",
        "",
        "# 📚 Catálogo de papers",
        "",
        f"O laboratório opera um catálogo aberto de **papers em educação aplicados ao Rio**, "
        f"cruzados com os dados do data.rio. Cada entrada indica o status de replicação no "
        f"lab e a cobertura dos requisitos de dados.",
        "",
        f"**Estado atual:** {len(papers)} papers catalogados — "
        f"{len(by_status['full'])} totalmente replicados, "
        f"{len(by_status['partial'])} em replicação parcial, "
        f"{len(by_status['pending'])} catalogados pendentes, "
        f"{len(by_status['unfeasible'])} indisponíveis por dados.",
        "",
        "> **Roadmap pós-v0.7:** ampliar para os 100 papers mais influentes. A v0.7 "
        "entrega o framework + 12 papers seed (3 já replicados + 5 alvo de novas "
        "replicações + 4 metodológicos).",
        "",
        "## Replicados (operacionalizados em produtos do lab)",
        "",
        _render_table(by_status["full"] + by_status["partial"], openalex),
        "",
        "## Catalogados — replicação leve planejada",
        "",
        _render_table(by_status["pending"], openalex),
        "",
        "## Catalogados — dados não disponíveis no data.rio",
        "",
        _render_table(by_status["unfeasible"], openalex),
        "",
        "## Sobre a curadoria",
        "",
        "- **Critério de inclusão:** papers seminais em educação (top-citados em economia, "
        "sociologia, política educacional) + papers brasileiros relevantes + metodológicos canônicos.",
        "- **Fonte de citações:** [OpenAlex](https://openalex.org), snapshot na curadoria. "
        "Atualizado periodicamente por `analysis/34_fetch_openalex.py`.",
        "- **Catálogo versionado:** edits ao YAML são auditáveis via git diff.",
        "- **Não é ranking objetivo:** é lista justificada por curadoria.",
        "",
        "## Reproduzir",
        "",
        "```bash",
        "pip install -r requirements.txt",
        "python3 analysis/34_fetch_openalex.py     # opcional: refresh de citações",
        "python3 analysis/31_build_paper_catalog.py",
        "python3 analysis/32_render_papers_pages.py",
        "```",
        "",
    ]
    return "\n".join(lines)


def _render_table(papers: list[dict], openalex: dict | None) -> str:
    if not papers:
        return "_(vazio)_"
    rows = [
        "| Paper | Ano | Área | Brasil? | Citações | Cobertura data.rio |",
        "|---|---|---|---|---|---|",
    ]
    for p in sorted(papers, key=lambda x: x["year"]):
        oa_cit = ""
        if openalex and p["id"] in openalex:
            c = openalex[p["id"]].get("citations_openalex")
            if c is not None:
                oa_cit = f"{c:,}".replace(",", ".")
        area = (p.get("area") or ["—"])[0]
        cov = p.get("data_rio_coverage") or []
        n_avail = sum(1 for c in cov if c.get("status") in {"available", "partial"})
        n_req = len(p.get("data_requirements", []))
        cov_str = f"{n_avail}/{n_req}" if n_req else "—"
        brazil = "🇧🇷" if p.get("brazil_specific") else ""
        link = f"[{fmt_authors(p['authors'])} ({p['year']})]({p['id']}.md)"
        rows.append(f"| {link} | {p['year']} | {area} | {brazil} | {oa_cit} | {cov_str} |")
    return "\n".join(rows)


def main() -> int:
    if not CATALOG_YML.exists():
        print(f"missing {CATALOG_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1
    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8"))
    papers = catalog.get("papers", [])

    openalex = None
    if OPENALEX_JSON.exists():
        openalex = json.loads(OPENALEX_JSON.read_text(encoding="utf-8"))
        print(f"loaded OpenAlex snapshot ({len(openalex)} entries)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in papers:
        path = OUT_DIR / f"{p['id']}.md"
        path.write_text(render_paper_page(p, openalex), encoding="utf-8")
    print(f"wrote {len(papers)} paper pages to {OUT_DIR.relative_to(ROOT)}")

    OUT_INDEX.write_text(render_index(papers, openalex), encoding="utf-8")
    print(f"wrote {OUT_INDEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
