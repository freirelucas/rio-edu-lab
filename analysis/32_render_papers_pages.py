"""Renderiza páginas Markdown a partir de `data/papers_catalog.yml`.

Para cada paper, escreve `docs/papers/<id>.md` com cabeçalho bibliográfico,
abstract, requisitos de dados, cobertura no data.rio e (se replicado)
links para relatórios + insight para gestores. Também atualiza o catálogo
em `docs/papers/index.md` (com tabs internas e cards Pudding-style para
replicados).

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

STATUS_HERO = {
    "full": {
        "icon": "✓",
        "label": "Replicado",
        "headline": "Operacionalizado em produto do lab.",
    },
    "partial": {
        "icon": "◐",
        "label": "Replicação parcial",
        "headline": "Replicação parcial — núcleo do método entregue; extensões em andamento.",
    },
    "pending": {
        "icon": "⏳",
        "label": "Catalogado — pendente",
        "headline": "Replicação leve planejada para release próxima; dados básicos cobertos no data.rio.",
    },
    "unfeasible": {
        "icon": "⚠",
        "label": "Sem cobertura no data.rio",
        "headline": "Catalogado para referência. Replicação exige fontes externas (microdado individual, painel longitudinal).",
    },
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


def _resolve_report_link(report_id: int, raw_html: bool = False) -> str:
    """Return link from docs/papers/<id>.md to docs/reports/NN_*.md.

    raw_html=False (default) returns the markdown form `../reports/NN_slug.md`
    that MkDocs rewrites at build time to the proper directory URL.
    raw_html=True returns the rendered directory URL form
    `../../reports/NN_slug/` for use inside raw <a href=...>, since MkDocs
    does not rewrite .md links inside raw HTML. Note the double `..`:
    from page URL `/papers/<id>/`, two levels up reaches site root.
    """
    prefix = f"{report_id:02d}_"
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.glob(f"{prefix}*.md"):
            if raw_html:
                return f"../../reports/{f.stem}/"
            return f"../reports/{f.stem}.md"
    return f"../../reports/{prefix}/" if raw_html else f"../reports/{prefix}.md"


def _status_hero_block(p: dict) -> str:
    """Visual hero card at top of paper mini-page reflecting replication maturity."""
    status = p["replication_status"]
    cfg = STATUS_HERO[status]
    headline = cfg["headline"]

    if status in ("full", "partial") and p.get("product"):
        product_slug = p["product"].lower().replace("-", "_").replace(" ", "_")
        link = f'<a href="../../produtos/{product_slug}/">{p["product"]}</a>'
        headline = f"Operacionalizado no produto {link}."
        if p.get("report_ids"):
            r_id = p["report_ids"][0]
            r_link = _resolve_report_link(r_id, raw_html=True)
            headline += f' Ver <a href="{r_link}">relatório {r_id:02d}</a>.'

    return (
        f'<div class="status-hero status-{status}" '
        f'aria-label="Status no lab: {cfg["label"]}">\n'
        f'  <span class="icon" aria-hidden="true">{cfg["icon"]}</span>\n'
        f'  <div class="text">\n'
        f'    <span class="label">{cfg["label"]}</span>\n'
        f'    <span class="headline">{headline}</span>\n'
        f'  </div>\n'
        f'</div>\n'
    )


def _policy_callout(insight: str, p: dict) -> str:
    """Render policy_insight as visual .policy-callout component."""
    insight = insight.strip()
    audit_link = ""
    if p.get("report_ids"):
        r_id = p["report_ids"][0]
        r_link = _resolve_report_link(r_id, raw_html=True)
        audit_link = f'  <footer><a href="{r_link}">Como auditar: relatório {r_id:02d} →</a></footer>\n'

    return (
        f'<div class="policy-callout">\n'
        f'  <header>\n'
        f'    <span class="icon" aria-hidden="true">🏛️</span>\n'
        f'    <h3>Para gestores públicos</h3>\n'
        f'  </header>\n'
        f'  <div class="body">\n'
        f'    <div class="cell"><strong>Achado</strong>{insight}</div>\n'
        f'  </div>\n'
        f'{audit_link}'
        f'</div>\n'
    )


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
        _status_hero_block(p),
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
                _policy_callout(": " + p["policy_insight"], p),
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


def _render_card(p: dict, openalex: dict | None) -> str:
    """Pudding-style card for replicated papers."""
    status = p["replication_status"]
    first_letter = (p["authors"][0] if p["authors"] else "?")[0].upper()
    authors_str = fmt_authors(p["authors"])
    year = p["year"]

    oa_cit = ""
    if openalex and p["id"] in openalex:
        c = openalex[p["id"]].get("citations_openalex")
        if c is not None:
            oa_cit = f"{c:,}".replace(",", ".") + " citações"

    area = (p.get("area") or [""])[0]
    flag = "🇧🇷 " if p.get("brazil_specific") else ""
    meta_parts = [x for x in [oa_cit, area, flag.strip()] if x]
    meta = " · ".join(meta_parts)

    insight = p.get("policy_insight") or p.get("abstract") or ""
    insight = insight.strip().replace("\n", " ")
    if len(insight) > 140:
        insight = insight[:137] + "…"

    cta = {
        "full": "Replicado →",
        "partial": "Replicação parcial →",
        "pending": "Próxima leitura →",
        "unfeasible": "Sem cobertura →",
    }[status]

    return (
        f'<a class="paper-card status-{status}" href="{p["id"]}/">\n'
        f'  <span class="drop-cap" aria-hidden="true">{first_letter}</span>\n'
        f'  <h4>{authors_str} ({year})</h4>\n'
        f'  <p class="meta">{meta}</p>\n'
        f'  <p class="insight">{insight}</p>\n'
        f'  <span class="cta">{cta}</span>\n'
        f'</a>\n'
    )


def _render_card_grid(papers: list[dict], openalex: dict | None) -> str:
    if not papers:
        return "_(vazio)_"
    cards = "\n".join(_render_card(p, openalex) for p in sorted(papers, key=lambda x: x["year"]))
    return f'<div class="paper-grid">\n{cards}</div>'


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


def render_index(papers: list[dict], openalex: dict | None) -> str:
    """Renders the searchable catalog landing page with status sections."""
    by_status: dict[str, list[dict]] = {k: [] for k in STATUS_BADGES}
    for p in papers:
        by_status[p["replication_status"]].append(p)

    n_repl = len(by_status["full"]) + len(by_status["partial"])
    n_pend = len(by_status["pending"])
    n_unf = len(by_status["unfeasible"])

    lines = [
        "---",
        "title: \"Catálogo de papers — rio-edu-lab\"",
        "description: \"Papers em educação aplicados ao Rio: status de replicação + cobertura no data.rio.\"",
        "---",
        "",
        "# Catálogo de papers",
        "",
        "Cada entrada do catálogo é um paper em educação cruzado com o **data.rio**. O lab declara o status de replicação, "
        "lista os requisitos de dados, mostra a cobertura no portal e (quando aplicável) aponta o insight para gestores públicos.",
        "",
        '<div class="how-to-read" markdown>',
        "### Como ler este catálogo",
        "",
        "O catálogo está organizado em três faixas. **Replicados** são papers já operacionalizados em produtos do lab. "
        "**Catalogados** são alvos das próximas releases — os dados básicos já estão cobertos no data.rio. "
        "**Sem cobertura** são papers seminais que ficam aqui para referência teórica — replicação exigiria fontes externas.",
        "</div>",
        "",
        '<div class="big-num-grid">',
        f'  <div class="big-num"><span class="num">{len(papers)}</span><span class="label">papers no catálogo seed (v0.7)</span></div>',
        f'  <div class="big-num"><span class="num">{n_repl}</span><span class="label">replicados ou em replicação parcial</span></div>',
        f'  <div class="big-num"><span class="num">{n_pend}</span><span class="label">catalogados — próxima leitura</span></div>',
        f'  <div class="big-num"><span class="num">{n_unf}</span><span class="label">sem cobertura no data.rio</span></div>',
        "</div>",
        "",
        "> **Roadmap pós-v0.7:** ampliar para os 100 papers mais influentes. A v0.7 entrega o framework + 12 papers seed "
        "(3 já replicados + 5 alvo de novas replicações + 4 metodológicos canônicos).",
        "",
        f"## Replicados ({n_repl})",
        "",
        "Papers operacionalizados em produtos do lab — HEX-EDU, VULN-EDU. Cada card linka para a mini-page do paper "
        "com o cruzamento de dados, link para o relatório técnico e insight para gestores.",
        "",
        _render_card_grid(by_status["full"] + by_status["partial"], openalex),
        "",
        f"## Catalogados — próxima leitura ({n_pend})",
        "",
        "Dados básicos cobertos no data.rio; replicação leve planejada para release próxima.",
        "",
        _render_card_grid(by_status["pending"], openalex),
        "",
        f"## Sem cobertura no data.rio ({n_unf})",
        "",
        "Papers seminais que pedem dados não cobertos no data.rio (microdado individual, painel longitudinal). "
        "Catalogados para referência teórica.",
        "",
        _render_table(by_status["unfeasible"], openalex),
        "",
        "## Sobre a curadoria",
        "",
        "- **Critério de inclusão:** papers seminais em educação (top-citados em economia, sociologia, política educacional) "
        "+ papers brasileiros relevantes + metodológicos canônicos.",
        "- **Fonte de citações:** [OpenAlex](https://openalex.org), snapshot na curadoria. Atualizado periodicamente por "
        "`analysis/34_fetch_openalex.py`.",
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
