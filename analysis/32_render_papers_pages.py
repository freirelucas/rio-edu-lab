"""Renderiza páginas Markdown a partir de `data/papers_catalog.yml`.

Para cada paper, escreve `docs/papers/<id>.md` com template story-driven:
finding-first quando há `applied_finding_*` no YAML, paper-first quando
pending, what-is-missing quando unfeasible. Também escreve o index do
catálogo em `docs/papers/index.md` organizado por TEMA (não por status).

Determinístico: output depende exclusivamente do YAML + opcionalmente do
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

# Mapping de áreas (do YAML) pra temas de alto nível. Ordem importa:
# o primeiro tema com match em qualquer área do paper define o tema do paper.
THEMES = [
    (
        "Desigualdade & equidade",
        {"desigualdade", "equidade", "equidade espacial", "segregação escolar",
         "SES e desempenho", "teoria da informação"},
    ),
    (
        "Acessibilidade & geografia escolar",
        {"acessibilidade", "geografia urbana"},
    ),
    (
        "Sociologia & efeito-escola",
        {"sociologia educacional", "efeito-escola", "tendências longitudinais"},
    ),
    (
        "Política educacional & avaliação",
        {"política educacional", "avaliação", "school choice", "competição"},
    ),
    (
        "Economia da educação",
        {"economia da educação", "função-produção", "retornos da educação",
         "teoria do capital humano", "primeira infância", "ciclo de vida",
         "qualidade docente"},
    ),
]
DEFAULT_THEME = "Outros"


def assign_theme(p: dict) -> str:
    areas = set(p.get("area") or [])
    for theme, tags in THEMES:
        if areas & tags:
            return theme
    return DEFAULT_THEME


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
    """Render policy_insight as visual .policy-callout component.

    Stance: replication-first. Header is "Insight da replicação aplicado ao Rio";
    body is a single cell with the literal paper × Rio finding. No advocacy,
    no policy recommendations, no "Ações" lists.
    """
    insight = insight.strip()
    audit_link = ""
    if p.get("report_ids"):
        r_id = p["report_ids"][0]
        r_link = _resolve_report_link(r_id, raw_html=True)
        audit_link = f'  <footer><a href="{r_link}">Como auditar: relatório {r_id:02d} →</a></footer>\n'

    return (
        f'<div class="policy-callout">\n'
        f'  <header>\n'
        f'    <span class="icon" aria-hidden="true">🔬</span>\n'
        f'    <h3>Insight da replicação aplicado ao Rio</h3>\n'
        f'  </header>\n'
        f'  <div class="body">\n'
        f'    <div class="cell"><strong>Achado replicado</strong>{insight}</div>\n'
        f'  </div>\n'
        f'{audit_link}'
        f'</div>\n'
    )


def _frontmatter(p: dict, title: str) -> list[str]:
    desc = (p.get("applied_finding_lede") or p.get("abstract") or "").strip()[:200]
    desc = " ".join(desc.split())
    return [
        "---",
        f"title: \"{title}\"",
        f"description: \"{desc}\"",
        "---",
        "",
    ]


def _provenance_block(p: dict, openalex: dict | None) -> list[str]:
    """Compact provenance: bibliography + DOI + citations + cobertura."""
    pid = p["id"]
    lines = ["## Provenance", ""]
    lines.append(f"**{p['title']}**")
    lines.append("")
    lines.append(f"_{fmt_authors_full(p['authors'])} ({p['year']}). {p['venue']}._")
    lines.append("")
    lines.append(f"<a href=\"{p['doi_or_url']}\" target=\"_blank\">{p['doi_or_url']}</a>")
    lines.append("")

    if openalex and pid in openalex:
        oa = openalex[pid]
        if oa.get("citations_openalex") is not None:
            cit_pt = f"{oa['citations_openalex']:,}".replace(",", ".")
            lines.append(f"**Citações (OpenAlex, {oa['fetched_at']}):** {cit_pt}")
            lines.append("")

    lines.append(f"**Área:** {', '.join(p.get('area', []))}")
    lines.append("")
    lines.append(f"**Método:** {', '.join(p.get('method', []))}")
    lines.append("")
    if p.get("brazil_specific"):
        lines.append("**🇧🇷 Brasil-específico.**")
        lines.append("")

    lines += [
        "### Requisitos de dados × cobertura no data.rio",
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

    if p.get("scripts"):
        sids = ", ".join(f"`analysis/{i:02d}_*.py`" for i in p["scripts"])
        lines.append(f"**Código:** {sids}")
        lines.append("")

    return lines


def _render_full_or_partial(p: dict, openalex: dict | None) -> str:
    """Story-driven template for replicated papers (full or partial)."""
    question = (
        p.get("applied_finding_question")
        or f"{fmt_authors(p['authors'])} ({p['year']}) aplicado ao Rio"
    )
    headline = p.get("applied_finding_headline") or ""
    lede = (p.get("applied_finding_lede") or p.get("policy_insight") or "").strip()
    status = p["replication_status"]

    title = f"{fmt_authors(p['authors'])} ({p['year']}) — {question}"

    lines = _frontmatter(p, title)
    lines += [
        f"# {question}",
        "",
    ]

    if headline:
        lines += [f"**{headline}**", ""]

    if lede:
        lines += [lede, ""]

    lines.append(_status_hero_block(p))
    lines.append("")

    abstract = (p.get("abstract") or "").strip()
    if abstract:
        lines += [
            "## O que esse paper diz",
            "",
            abstract,
            "",
        ]

    lines += ["## Aplicado ao Rio", ""]
    rio_para = []
    if p.get("policy_insight"):
        rio_para.append(p["policy_insight"].strip())
    if p.get("product"):
        rio_para.append(
            f"Operacionalizado no produto **{p['product']}** "
            f"([detalhe técnico](../produtos/{p['product'].lower().replace('-', '_')}.md))."
        )
    if rio_para:
        lines.append(" ".join(rio_para))
        lines.append("")

    if p.get("report_ids"):
        lines.append("**Como auditar:**")
        lines.append("")
        for r_id in p["report_ids"]:
            r_link = _resolve_report_link(r_id)
            lines.append(f"- [Relatório {r_id:02d}]({r_link})")
        lines.append("")

    lines += _provenance_block(p, openalex)
    lines += ["[← Voltar aos papers](index.md)", ""]
    return "\n".join(lines)


def _render_pending(p: dict, openalex: dict | None) -> str:
    """Template for pending papers: 'what would this say about Rio if we ran it'."""
    question = (
        p.get("applied_finding_question")
        or f"{fmt_authors(p['authors'])} ({p['year']}) — replicação pendente"
    )
    title = f"{fmt_authors(p['authors'])} ({p['year']}) — {question}"

    lines = _frontmatter(p, title)
    lines += [
        f"# {question}",
        "",
        f"**Dados básicos cobertos no data.rio. Replicação pendente — {fmt_authors(p['authors'])} ({p['year']}) está na fila.**",
        "",
    ]

    lines.append(_status_hero_block(p))
    lines.append("")

    abstract = (p.get("abstract") or "").strip()
    if abstract:
        lines += [
            "## O que esse paper faz",
            "",
            abstract,
            "",
        ]

    lines += ["## Por que dá pra rodar no Rio", ""]
    coverage = p.get("data_rio_coverage") or []
    n_avail = sum(1 for c in coverage if c.get("status") in {"available", "partial"})
    n_req = len(p.get("data_requirements") or [])
    lines.append(
        f"Dos {n_req} requisitos de dados do paper, **{n_avail} têm cobertura no data.rio**. "
        f"Detalhe abaixo em Provenance."
    )
    lines.append("")

    lines += _provenance_block(p, openalex)
    lines += ["[← Voltar aos papers](index.md)", ""]
    return "\n".join(lines)


def _render_unfeasible(p: dict, openalex: dict | None) -> str:
    """Template for unfeasible papers: 'what's missing to run this in Rio'."""
    question = (
        p.get("applied_finding_question")
        or f"{fmt_authors(p['authors'])} ({p['year']}) — dados ausentes"
    )
    title = f"{fmt_authors(p['authors'])} ({p['year']}) — {question}"

    coverage = p.get("data_rio_coverage") or []
    missing_reqs = [
        c["requirement"] for c in coverage if c.get("status") in {"external", "missing"}
    ]

    lines = _frontmatter(p, title)
    lines += [
        f"# {question}",
        "",
    ]

    if missing_reqs:
        lines += [
            f"**Falta dado essencial no data.rio:** {', '.join(missing_reqs)}.",
            "",
        ]
    else:
        lines += [
            "**Replicação no Rio inviável com o data.rio atual.**",
            "",
        ]

    lines.append(_status_hero_block(p))
    lines.append("")

    abstract = (p.get("abstract") or "").strip()
    if abstract:
        lines += [
            "## O paper",
            "",
            abstract,
            "",
        ]

    lines += [
        "## O que precisaria pra rodar no Rio",
        "",
        "Os requisitos abaixo não são cobertos pelo data.rio. Tipicamente envolvem "
        "microdado individual (INEP nominal não publicado), painel longitudinal "
        "(RAIS/INEP coorte) ou domicílios (PNAD anual). Se isso mudar, o paper sai "
        "automaticamente desta seção via re-run do funil.",
        "",
    ]

    lines += _provenance_block(p, openalex)
    lines += ["[← Voltar aos papers](index.md)", ""]
    return "\n".join(lines)


def render_paper_page(p: dict, openalex: dict | None) -> str:
    status = p["replication_status"]
    if status in ("full", "partial"):
        return _render_full_or_partial(p, openalex)
    if status == "pending":
        return _render_pending(p, openalex)
    if status == "unfeasible":
        return _render_unfeasible(p, openalex)
    raise ValueError(f"unknown status: {status}")


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
    """Renders the catalog landing organized by theme (not status)."""
    by_theme: dict[str, list[dict]] = {}
    for p in papers:
        by_theme.setdefault(assign_theme(p), []).append(p)

    n_full = sum(1 for p in papers if p["replication_status"] == "full")
    n_partial = sum(1 for p in papers if p["replication_status"] == "partial")
    n_pend = sum(1 for p in papers if p["replication_status"] == "pending")
    n_unf = sum(1 for p in papers if p["replication_status"] == "unfeasible")
    n_repl = n_full + n_partial

    lines = [
        "---",
        "title: \"Papers — rio-edu-lab\"",
        "description: \"12 papers acadêmicos sobre educação. Organizados por tema. Cada um cruzado contra os 9.855 itens do data.rio.\"",
        "---",
        "",
        "# Papers",
        "",
        f"**{len(papers)} papers acadêmicos sobre educação.** Organizados por tema. Cada um cruzado contra os "
        "**9.855 itens do data.rio**. Status de replicação + cobertura de dados + achado quando aplicável.",
        "",
        "O catálogo é o **estágio 4 do funil**: o que sobreviveu à curadoria depois do snowball bibliométrico, "
        "filtro temático e checagem de cobertura. [Ver o funil completo →](../index.md#como-o-funil-funciona)",
        "",
        '<div class="big-num-grid">',
        f'  <div class="big-num"><span class="num">{len(papers)}</span><span class="label">papers no catálogo</span></div>',
        f'  <div class="big-num"><span class="num">{n_repl}</span><span class="label">replicados (full + partial)</span></div>',
        f'  <div class="big-num"><span class="num">{n_pend}</span><span class="label">prontos pra replicar</span></div>',
        f'  <div class="big-num"><span class="num">{n_unf}</span><span class="label">faltam dados externos</span></div>',
        "</div>",
        "",
        "**Legenda de status:** ✓ replicado · ◐ replicação parcial · ⏳ catalogado pendente · ⚠ dados ausentes",
        "",
    ]

    theme_order = [t for t, _ in THEMES] + [DEFAULT_THEME]
    for theme in theme_order:
        ps = by_theme.get(theme, [])
        if not ps:
            continue
        # Sort: replicados first, then pending, then unfeasible; by year within
        status_rank = {"full": 0, "partial": 1, "pending": 2, "unfeasible": 3}
        ps_sorted = sorted(ps, key=lambda x: (status_rank[x["replication_status"]], x["year"]))
        lines += [
            f"## {theme} ({len(ps)})",
            "",
            _render_card_grid(ps_sorted, openalex),
            "",
        ]

    lines += [
        "## Sobre a curadoria",
        "",
        "- **Critério de inclusão:** papers seminais em educação (top-citados em economia, sociologia, política educacional) "
        "+ papers brasileiros relevantes + metodológicos canônicos.",
        "- **Fonte de citações:** [OpenAlex](https://openalex.org), snapshot na curadoria. Atualizado periodicamente por "
        "`analysis/34_fetch_openalex.py`.",
        "- **Catálogo versionado:** edits ao YAML são auditáveis via git diff.",
        "- **Não é ranking objetivo:** é lista justificada por curadoria.",
        "- **Não é destino do funil:** novos papers entram pela curadoria de candidatos do "
        "[funil de descoberta](../index.md#como-o-funil-funciona) (253 candidatos no Stage 1 hoje).",
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
