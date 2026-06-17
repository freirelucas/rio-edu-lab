"""TOP Guidelines scorecard generator (rio-edu-lab v0.16+).

Implements the **Transparency and Openness Promotion (TOP) Guidelines** from
the Center for Open Science (cos.io/initiatives/top-guidelines).

TOP defines **8 standards** for research transparency, each at 4 levels:
  0 — Not implemented
  1 — Disclosed (statement made; not necessarily shared)
  2 — Required (data/code shared + cited)
  3 — Verified (independent replication confirms)

The 8 standards:
  1. Citation Standards          — data + code + materials cited as primary
                                   research products
  2. Data Transparency           — data available in trusted repository
  3. Analytic Methods Transp.    — code available + executable
  4. Research Materials Transp.  — instruments, protocols, stimuli available
  5. Design + Analysis Transp.   — pre-specified design + analysis plan
  6. Study Preregistration       — design pre-registered before observation
  7. Analysis Plan Preregistration — analysis pre-registered before analysis
  8. Replication                 — replication encouraged + valued

For rio-edu-lab (a REPLICATION lab, not original-research), we score the
LAB's compliance per paper: did *we* (replicators) hit the TOP level for
each standard?

Heuristics (computed from papers_catalog.yml fields populated v0.16+):
  S1 Citation: doi_or_url + OpenAlex ID + references in CITATION.cff
  S2 Data:     data_availability_statement.summary == public + sources[]
  S3 Code:     scripts[] populated + commit references
  S4 Material: report_ids[] (mini-pages with figures/tables)
  S5 D+A:      data_requirements[] + method[] + controlled_randomness
  S6 Study:    preregistration.type ∈ {prospective}  (impossible for
                                       retrospective replications → cap at 1)
  S7 Plan:     preregistration.type == retrospective_replication_recipe + osf_url
  S8 Repl:     replication_status ∈ {full, partial}

Outputs:
  data/processed/top_scorecard.csv  — wide table per (paper, standard)
  data/processed/top_scorecard.md   — human-readable Markdown
  docs/top-scorecard.md             — renderable in mkdocs site
  data/processed/top_summary.json   — aggregate stats

Drift check no CI: re-roda este script e diffa.
"""

from __future__ import annotations

import csv
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
OUT_CSV = ROOT / "data" / "processed" / "top_scorecard.csv"
OUT_MD = ROOT / "data" / "processed" / "top_scorecard.md"
OUT_DOCS = ROOT / "docs" / "top-scorecard.md"
OUT_JSON = ROOT / "data" / "processed" / "top_summary.json"

# Os 8 standards do TOP — labels canônicos
STANDARDS = [
    ("S1", "Citation Standards"),
    ("S2", "Data Transparency"),
    ("S3", "Code Transparency"),
    ("S4", "Materials Transparency"),
    ("S5", "Design + Analysis Transparency"),
    ("S6", "Study Preregistration"),
    ("S7", "Analysis Plan Preregistration"),
    ("S8", "Replication"),
]


def score_s1_citation(p: dict) -> int:
    """Citation Standards. doi/url + OpenAlex enriched = level 2."""
    has_doi = bool(p.get("doi_or_url"))
    has_openalex = bool(p.get("openalex_id"))
    if has_doi and has_openalex:
        return 2
    if has_doi or has_openalex:
        return 1
    return 0


def score_s2_data(p: dict) -> int:
    """Data Transparency. DAS public + sources[] cited = level 2."""
    das = p.get("data_availability_statement") or {}
    if not das:
        # Fallback pra data_rio_coverage (legacy)
        if p.get("data_rio_coverage"):
            return 1
        return 0
    summary = das.get("summary")
    sources = das.get("sources") or []
    if summary == "public" and len(sources) >= 1:
        return 2
    if summary in ("public", "restricted"):
        return 1
    return 0


def score_s3_code(p: dict) -> int:
    """Code Transparency. scripts[] populated + can verify in repo = level 2."""
    scripts = p.get("scripts") or []
    status = p.get("replication_status")
    if scripts and status in ("full", "partial"):
        return 2
    if scripts:
        return 1
    return 0


def score_s4_materials(p: dict) -> int:
    """Research Materials Transparency. report_ids[] = mini-pages available."""
    reports = p.get("report_ids") or []
    if reports:
        return 1  # docs/reports rendered = materials disclosed
    return 0


def score_s5_design(p: dict) -> int:
    """Design + Analysis Transparency.

    data_requirements + method + (optional) controlled_randomness.
    Level 2 quando DAS public + controlled_randomness.seeds (mesmo que vazio
    pra deterministic) explicitamente declarado.
    """
    has_requirements = bool(p.get("data_requirements"))
    has_method = bool(p.get("method"))
    has_randomness = p.get("controlled_randomness") is not None
    if has_requirements and has_method and has_randomness:
        return 2
    if has_requirements and has_method:
        return 1
    return 0


def score_s6_study_prereg(p: dict) -> int:
    """Study Preregistration. Retrospective replications cap at 1
    (impossível pre-registrar antes da observação se paper já existe).
    Level 2 só se prospective."""
    prereg = p.get("preregistration") or {}
    ptype = prereg.get("type")
    osf = prereg.get("osf_url")
    if ptype == "prospective" and osf:
        return 2
    if ptype in ("prospective", "retrospective_replication_recipe"):
        return 1
    return 0


def score_s7_analysis_plan(p: dict) -> int:
    """Analysis Plan Preregistration. OSF Replication Recipe + osf_url = level 2."""
    prereg = p.get("preregistration") or {}
    ptype = prereg.get("type")
    osf = prereg.get("osf_url")
    if ptype == "retrospective_replication_recipe" and osf:
        return 2
    if ptype:
        return 1
    return 0


def score_s8_replication(p: dict) -> int:
    """Replication standard. Level 2 if full, 1 if partial."""
    status = p.get("replication_status")
    if status == "full":
        return 2
    if status == "partial":
        return 1
    return 0


SCORERS = {
    "S1": score_s1_citation,
    "S2": score_s2_data,
    "S3": score_s3_code,
    "S4": score_s4_materials,
    "S5": score_s5_design,
    "S6": score_s6_study_prereg,
    "S7": score_s7_analysis_plan,
    "S8": score_s8_replication,
}


def compute_scorecard(papers: list[dict]) -> list[dict]:
    """Returns list of {id, S1..S8, total} per paper."""
    out = []
    for p in papers:
        row = {"id": p["id"], "replication_status": p.get("replication_status", "?")}
        total = 0
        for code, _label in STANDARDS:
            level = SCORERS[code](p)
            row[code] = level
            total += level
        row["total"] = total
        row["max_possible"] = len(STANDARDS) * 2  # cap por standard
        out.append(row)
    return out


def render_markdown(scorecard: list[dict], papers_by_id: dict[str, dict]) -> str:
    """Renderiza tabela Markdown legível."""
    lines = []
    lines.append("# TOP Guidelines Scorecard")
    lines.append("")
    lines.append("Auto-gerado por `analysis/60_top_scorecard.py` a partir de `data/papers_catalog.yml`.")
    lines.append("")
    lines.append("**TOP Guidelines** (Center for Open Science) define 8 padrões de transparência, cada um em 4 níveis:")
    lines.append("")
    lines.append("- **0** — Not implemented")
    lines.append("- **1** — Disclosed (declarado)")
    lines.append("- **2** — Required (dados/código compartilhados + citados)")
    lines.append("- **3** — Verified (replicação independente confirmou)")
    lines.append("")
    lines.append("Score do rio-edu-lab por paper:")
    lines.append("")

    # Header
    header = ["paper", "status"] + [c for c, _ in STANDARDS] + ["total", "%"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")

    for row in scorecard:
        pct = int(100 * row["total"] / row["max_possible"])
        cells = [row["id"], row["replication_status"]]
        cells.extend(str(row[c]) for c, _ in STANDARDS)
        cells.append(str(row["total"]))
        cells.append(f"{pct}%")
        lines.append("| " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Legenda dos standards")
    lines.append("")
    for code, label in STANDARDS:
        lines.append(f"- **{code}** — {label}")
    lines.append("")
    lines.append("## Heurísticas de scoring")
    lines.append("")
    lines.append("Veja docstring em `analysis/60_top_scorecard.py` pra fórmulas exatas. Em resumo:")
    lines.append("")
    lines.append("- S1 (Citation): DOI + OpenAlex ID populados")
    lines.append("- S2 (Data): `data_availability_statement.summary == public` + sources[]")
    lines.append("- S3 (Code): `scripts[]` + replication_status ∈ {full, partial}")
    lines.append("- S4 (Materials): `report_ids[]` populated (mini-pages renderizados)")
    lines.append("- S5 (Design+Analysis): data_requirements + method + controlled_randomness declarados")
    lines.append("- S6 (Study Prereg): cap em 1 pra retrospective replications (impossível pre-registrar paper já publicado)")
    lines.append("- S7 (Analysis Plan): `preregistration.osf_url` populated")
    lines.append("- S8 (Replication): full=2, partial=1")
    lines.append("")
    lines.append(f"**Total possível**: {len(STANDARDS)} standards × 2 levels = {len(STANDARDS) * 2}")
    lines.append("")
    return "\n".join(lines)


def render_docs_page(md_body: str) -> str:
    """Wrap pro mkdocs com front-matter."""
    return (
        "---\n"
        "title: TOP Guidelines Scorecard\n"
        "description: Scorecard de transparência (Center for Open Science TOP Guidelines) por paper do catálogo. Auto-gerado.\n"
        "---\n\n"
    ) + md_body


def main() -> int:
    if not CATALOG_YML.exists():
        print(f"missing {CATALOG_YML}", file=sys.stderr)
        return 1
    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8")) or {}
    papers = catalog.get("papers") or []
    print(f"loaded {len(papers)} papers from catalog")

    scorecard = compute_scorecard(papers)
    papers_by_id = {p["id"]: p for p in papers}

    # CSV
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    cols = ["id", "replication_status"] + [c for c, _ in STANDARDS] + ["total", "max_possible"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in scorecard:
            writer.writerow({k: row[k] for k in cols})
    print(f"wrote {OUT_CSV.relative_to(ROOT)}")

    # Markdown
    md_body = render_markdown(scorecard, papers_by_id)
    OUT_MD.write_text(md_body, encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")

    # Docs page
    OUT_DOCS.write_text(render_docs_page(md_body), encoding="utf-8")
    print(f"wrote {OUT_DOCS.relative_to(ROOT)}")

    # Summary JSON
    summary = {
        "n_papers": len(scorecard),
        "by_status": {
            status: sum(1 for r in scorecard if r["replication_status"] == status)
            for status in ("full", "partial", "pending", "unfeasible")
        },
        "mean_total_score": (
            sum(r["total"] for r in scorecard) / len(scorecard) if scorecard else 0
        ),
        "max_possible": len(STANDARDS) * 2,
        "by_standard_mean": {
            code: round(
                sum(r[code] for r in scorecard) / len(scorecard) if scorecard else 0,
                2,
            )
            for code, _ in STANDARDS
        },
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")

    print("\n=== headline ===")
    print(f"  papers: {len(scorecard)}")
    print(f"  mean total score: {summary['mean_total_score']:.1f}/{summary['max_possible']}")
    print(f"  by standard mean: {summary['by_standard_mean']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
