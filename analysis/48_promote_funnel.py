"""Stage 4 do funil — promover candidatos aceitos ao catálogo canônico.

Filtra `data/papers_funnel.yml` por `decision: accept` e, para cada candidato,
gera uma entrada válida no schema de `data/papers_catalog.yml` (validado por
`analysis/31_build_paper_catalog.py`). Anexa ao final do catalog YAML
preservando comentários do arquivo (não re-serializa via PyYAML).

Derivações automáticas:
  id                 slug(first_author + year + first_word_of_title); collisions → -2, -3…
  authors            split de "Smith, Doe et al." em lista
  data_requirements  label_pt da taxonomia para cada suggested category_id
  data_rio_coverage  cada coverage row → {requirement, item_id, status}
  replication_status all coverage in {available,partial} → pending
                     senão                                → unfeasible
  brazil_specific    heurística: títulos/abstract/venue mencionando Brasil
  area               dos concepts_top3 do OpenAlex (lowercase, split "; ")
  method             [] vazio (curador preenche depois)

Aborta sem alterações se algum id derivado já existe no catálogo (curador
resolve à mão antes de re-rodar). Use --dry-run para inspecionar primeiro.

Após rodar, executar pipeline existente:
  python3 analysis/31_build_paper_catalog.py      # valida
  python3 analysis/32_render_papers_pages.py      # gera mini-pages
  python3 analysis/41_match_requirements.py       # atualiza link reverso
  python3 analysis/34_fetch_openalex.py           # snapshot citations

Uso:
  python3 analysis/48_promote_funnel.py
  python3 analysis/48_promote_funnel.py --dry-run    # imprime sem escrever
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _match import load_taxonomy, strip_accents  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"

# Seção marker para anexação idempotente no catalog YAML.
SECTION_MARKER = "# DESCOBERTOS VIA FUNIL (auto-promovidos por 48_promote_funnel.py)"

STOP_TITLE = {
    "the", "a", "an", "of", "in", "on", "by", "to", "and", "or", "for", "with",
    "into", "from", "is", "are", "was", "were", "be", "been", "do", "does",
    "did", "this", "that", "these", "those", "as", "at", "but", "if", "then",
    "than", "what", "how", "why", "when", "where", "which",
    "o", "a", "os", "as", "um", "uma", "de", "da", "do", "das", "dos",
    "no", "na", "nos", "nas", "por", "para", "em", "com", "sem",
}

BRAZIL_MARKERS = {
    "brazil", "brasil", "brazilian", "rio", "ipea", "inep", "ibge",
    "sao paulo", "são paulo", "salvador", "fortaleza", "recife",
    "belo horizonte", "porto alegre", "curitiba", "manaus",
}


def title_first_word(title: str) -> str:
    norm = strip_accents(title.lower())
    for tok in re.split(r"[^a-z0-9]+", norm):
        if len(tok) >= 4 and tok not in STOP_TITLE:
            return tok
    return "paper"


def first_author_surname(authors: str) -> str:
    """Best-effort surname from 'Smith, Doe et al.' or 'Name Surname, ...'."""
    if not authors:
        return "anon"
    first = authors.split(",")[0].strip()
    first = first.replace(" et al.", "").replace(" et al", "").strip()
    if not first:
        return "anon"
    parts = [p for p in first.split() if p]
    surname = parts[-1] if parts else "anon"
    norm = strip_accents(surname.lower())
    norm = re.sub(r"[^a-z0-9]+", "", norm)
    return norm or "anon"


def make_slug(authors: str, year: int, title: str, existing: set[str]) -> str:
    surname = first_author_surname(authors)
    first = title_first_word(title)
    base = f"{surname}-{year}-{first}"
    slug = base
    n = 2
    while slug in existing:
        slug = f"{base}-{n}"
        n += 1
    return slug


def parse_authors_list(authors: str) -> list[str]:
    """Convert 'Smith, Doe et al.' → ['Smith', 'Doe'] (last names)."""
    if not authors:
        return []
    cleaned = authors.replace(" et al.", "").replace(" et al", "")
    out: list[str] = []
    for chunk in cleaned.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p for p in chunk.split() if p]
        if parts:
            out.append(parts[-1])
    return out


def detect_brazil(c: dict) -> bool:
    blob = " ".join([
        c.get("title", ""),
        c.get("abstract", ""),
        c.get("venue", ""),
        c.get("authors", ""),
    ]).lower()
    blob_norm = strip_accents(blob)
    return any(m in blob_norm for m in BRAZIL_MARKERS)


def derive_areas(concepts_top3: str) -> list[str]:
    if not concepts_top3:
        return []
    chunks = [c.strip().lower() for c in concepts_top3.split(";") if c.strip()]
    return chunks[:3]


def derive_doi_or_url(c: dict) -> str:
    doi = (c.get("doi") or "").strip()
    if doi:
        return f"https://doi.org/{doi}"
    return c.get("pdf_url_oa") or ""


def derive_replication_status(coverage: list[dict]) -> str:
    if not coverage:
        return "unfeasible"
    statuses = {cov["status"] for cov in coverage}
    if statuses <= {"available", "partial"}:
        return "pending"
    return "unfeasible"


def render_catalog_entry(c: dict, slug: str, cats: dict[str, dict]) -> str:
    """Format a single catalog entry as YAML text (matching existing style)."""
    authors_list = parse_authors_list(c.get("authors", ""))
    year = int(c.get("year") or 0)
    title = (c.get("title") or "").replace('"', '\\"')
    venue = (c.get("venue") or "?").replace('"', '\\"')
    doi_url = derive_doi_or_url(c)
    abstract = (c.get("abstract") or "").strip()
    if not abstract:
        abstract = "(abstract não disponível no OpenAlex)"
    area = derive_areas(c.get("concepts_top3", ""))
    brazil = detect_brazil(c)

    suggestions = c.get("suggested_requirements") or []
    coverage_rows = c.get("coverage") or []
    cov_by_cat = {cov["category_id"]: cov for cov in coverage_rows}

    requirement_labels: list[str] = []
    coverage_entries: list[tuple[str, str | None, str]] = []
    for s in suggestions:
        cid = s["category_id"]
        cat = cats.get(cid, {})
        # Use first alias (canonical taxonomy lookup string); falls back to
        # label_pt or category_id if aliases missing.
        aliases = cat.get("aliases") or []
        label = aliases[0] if aliases else (cat.get("label_pt") or cid)
        requirement_labels.append(label)
        cov = cov_by_cat.get(cid)
        if cov:
            coverage_entries.append((label, cov.get("manifest_item_id"), cov["status"]))
        else:
            coverage_entries.append((label, None, "missing"))

    status = derive_replication_status(coverage_rows)

    lines: list[str] = []
    lines.append(f"  - id: {slug}")
    if authors_list:
        lines.append("    authors: [" + ", ".join(authors_list) + "]")
    else:
        lines.append("    authors: []")
    lines.append(f"    year: {year}")
    lines.append(f'    title: "{title}"')
    lines.append(f'    venue: "{venue}"')
    lines.append(f'    doi_or_url: "{doi_url}"')
    if c.get("pdf_url_oa"):
        lines.append(f'    pdf_url: "{c["pdf_url_oa"]}"')
    if c.get("openalex_id"):
        lines.append(f'    openalex_id: "{c["openalex_id"]}"')
    if c.get("citations") is not None:
        lines.append(f"    citations_openalex: {int(c['citations'])}")
    lines.append("    abstract: >")
    for chunk in _wrap(abstract, width=80):
        lines.append("      " + chunk)
    if area:
        lines.append("    area: [" + ", ".join(_yaml_str(a) for a in area) + "]")
    else:
        lines.append("    area: []")
    lines.append("    method: []")
    lines.append(f"    brazil_specific: {'true' if brazil else 'false'}")
    if requirement_labels:
        lines.append("    data_requirements:")
        for r in requirement_labels:
            lines.append(f'      - "{r}"')
    else:
        lines.append("    data_requirements: []")
    if coverage_entries:
        lines.append("    data_rio_coverage:")
        for req, iid, st in coverage_entries:
            lines.append(f'      - requirement: "{req}"')
            if iid:
                lines.append(f'        item_id: "{iid}"')
            else:
                lines.append("        item_id: null")
            lines.append(f"        status: {st}")
    else:
        lines.append("    data_rio_coverage: []")
    lines.append(f"    replication_status: {status}")
    lines.append("    policy_insight: null")
    return "\n".join(lines)


def _yaml_str(s: str) -> str:
    """Quote a string for inline YAML list.

    JSON strings are a subset of YAML flow scalars — always safe, always
    quoted correctly even for parens/colons/special chars. Prevents the
    document-end marker bug from `yaml.safe_dump(scalar, flow_style=True)`.
    """
    return json.dumps(s, ensure_ascii=False)


def _wrap(text: str, width: int) -> list[str]:
    out: list[str] = []
    line = ""
    for word in text.split():
        if len(line) + len(word) + 1 > width and line:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return out or [""]


def append_to_catalog(blocks: list[str]) -> None:
    """Append new entries after the section marker (or at end with marker)."""
    text = CATALOG_YML.read_text(encoding="utf-8").rstrip() + "\n"
    if SECTION_MARKER in text:
        # Append blocks after current end of file (marker already present).
        text += "\n" + "\n\n".join(blocks) + "\n"
    else:
        text += "\n  # ============================================================\n"
        text += f"  {SECTION_MARKER}\n"
        text += "  # ============================================================\n\n"
        text += "\n\n".join(blocks) + "\n"
    CATALOG_YML.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Print generated YAML without writing to catalog")
    args = ap.parse_args()

    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not CATALOG_YML.exists():
        print(f"missing {CATALOG_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1

    funnel = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = funnel.get("candidates") or []
    accepted = [c for c in candidates if c.get("decision") == "accept"]
    print(f"funnel: {len(candidates)} total, {len(accepted)} accepted for promotion")

    if not accepted:
        print("nothing to promote")
        return 0

    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8")) or {}
    existing_ids = {p["id"] for p in catalog.get("papers") or [] if p.get("id")}
    print(f"catalog: {len(existing_ids)} existing papers")

    cats, _ = load_taxonomy(TAXONOMY_YML)

    blocks: list[str] = []
    new_ids: list[str] = []
    for c in accepted:
        slug = make_slug(
            c.get("authors", ""),
            int(c.get("year") or 0),
            c.get("title", ""),
            existing_ids | set(new_ids),
        )
        new_ids.append(slug)
        block = render_catalog_entry(c, slug, cats)
        blocks.append(block)
        print(f"  promote: {slug} ← {c.get('title', '')[:60]}…")

    if args.dry_run:
        print("\n=== dry-run output (not written) ===\n")
        for b in blocks:
            print(b)
            print()
        return 0

    append_to_catalog(blocks)
    print(f"\nappended {len(blocks)} entries to {CATALOG_YML.relative_to(ROOT)}")
    print("next steps:")
    print("  python3 analysis/31_build_paper_catalog.py")
    print("  python3 analysis/32_render_papers_pages.py")
    print("  python3 analysis/41_match_requirements.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
