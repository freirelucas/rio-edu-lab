"""Stage 1 do funil — descoberta em lote no OpenAlex.

Itera `data/openalex_concepts.yml` (themes curados), consulta o OpenAlex
para cada theme via `_openalex.iterate_works`, deduplica por openalex_id e
faz **upsert** em `data/papers_funnel.yml`:

  - candidatos novos → inseridos com decision/suggested_requirements/coverage
    vazios
  - candidatos já presentes → discovered_via é unido (set), citations e
    abstract são atualizados, MAS `decision`, `decision_reason`,
    `suggested_requirements`, e `coverage` são preservados intactos.

Isso garante idempotência: re-rodar 45 com os mesmos themes nunca perde
trabalho do curador.

Uso:
  python3 analysis/45_bulk_discover.py                      # todos os themes
  python3 analysis/45_bulk_discover.py --concepts ID1,ID2   # subset
  python3 analysis/45_bulk_discover.py --dry-run            # sem escrever
  python3 analysis/45_bulk_discover.py --top 10             # cap por theme

Rede: OpenAlex public API, 1 req/s. ~30s por theme com top=50.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _openalex import iterate_works  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS_YML = ROOT / "data" / "openalex_concepts.yml"
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"

DEFAULT_TOP = 30
DEFAULT_MIN_CITATIONS = 200


def load_themes() -> list[dict]:
    if not CONCEPTS_YML.exists():
        print(f"missing {CONCEPTS_YML.relative_to(ROOT)}", file=sys.stderr)
        sys.exit(1)
    data = yaml.safe_load(CONCEPTS_YML.read_text(encoding="utf-8")) or {}
    return [t for t in (data.get("themes") or []) if t.get("enabled", True)]


def load_funnel() -> tuple[dict, dict[str, dict]]:
    """Returns (full_yaml_doc, candidates_by_openalex_id)."""
    if not FUNNEL_YML.exists():
        return {"version": 1, "candidates": []}, {}
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    cands = doc.get("candidates") or []
    by_id = {c["openalex_id"]: c for c in cands if c.get("openalex_id")}
    return doc, by_id


def write_funnel(doc: dict, candidates: list[dict]) -> None:
    """Write funnel.yml preserving header comments; serialize candidates only."""
    doc["candidates"] = candidates
    # Re-read header (lines before "candidates:") to preserve schema comment.
    header_lines: list[str] = []
    if FUNNEL_YML.exists():
        for line in FUNNEL_YML.read_text(encoding="utf-8").splitlines():
            if line.startswith("candidates:"):
                break
            header_lines.append(line)
    yaml_body = yaml.safe_dump(
        {"candidates": candidates},
        allow_unicode=True,
        sort_keys=False,
        width=120,
        default_flow_style=False,
    )
    full = "\n".join(header_lines).rstrip() + "\n\n" + yaml_body
    FUNNEL_YML.write_text(full, encoding="utf-8")


def merge_candidate(existing: dict, new: dict, theme_id: str) -> dict:
    """Upsert: refresh metadata + union discovered_via; preserve curator state."""
    discovered = set(existing.get("discovered_via") or [])
    discovered.add(theme_id)
    return {
        "openalex_id": existing["openalex_id"],
        "doi": new.get("doi") or existing.get("doi") or "",
        "title": new.get("title") or existing.get("title") or "",
        "authors": new.get("authors") or existing.get("authors") or "",
        "year": new.get("year") or existing.get("year") or "",
        "venue": new.get("venue") or existing.get("venue") or "",
        "citations": int(new.get("cited_by_count") or existing.get("citations") or 0),
        "abstract": new.get("abstract") or existing.get("abstract") or "",
        "pdf_url_oa": new.get("pdf_url_oa") or existing.get("pdf_url_oa") or "",
        "concepts_top3": new.get("concepts_top3") or existing.get("concepts_top3") or "",
        "discovered_via": sorted(discovered),
        # Preserved exactly:
        "suggested_requirements": existing.get("suggested_requirements") or [],
        "coverage": existing.get("coverage") or [],
        "decision": existing.get("decision") or "",
        "decision_reason": existing.get("decision_reason") or "",
    }


def new_candidate(work: dict, theme_id: str) -> dict:
    return {
        "openalex_id": work["openalex_id"],
        "doi": work.get("doi") or "",
        "title": work.get("title") or "",
        "authors": work.get("authors") or "",
        "year": work.get("year") or "",
        "venue": work.get("venue") or "",
        "citations": int(work.get("cited_by_count") or 0),
        "abstract": work.get("abstract") or "",
        "pdf_url_oa": work.get("pdf_url_oa") or "",
        "concepts_top3": work.get("concepts_top3") or "",
        "discovered_via": [theme_id],
        "suggested_requirements": [],
        "coverage": [],
        "decision": "",
        "decision_reason": "",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--concepts", help="Comma-separated theme ids (default: all)")
    ap.add_argument("--top", type=int, help="Override per-theme top (default from yml)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print summary without writing funnel.yml")
    args = ap.parse_args()

    themes = load_themes()
    if args.concepts:
        wanted = {x.strip() for x in args.concepts.split(",") if x.strip()}
        themes = [t for t in themes if t.get("id") in wanted]
    if not themes:
        print("no enabled themes to run", file=sys.stderr)
        return 1
    print(f"running discovery for {len(themes)} themes")

    doc, by_id = load_funnel()
    n_existing = len(by_id)
    print(f"funnel has {n_existing} existing candidates")

    n_new = 0
    n_updated = 0
    for theme in themes:
        tid = theme["id"]
        per_theme_top = args.top or theme.get("top") or DEFAULT_TOP
        min_cits = theme.get("min_citations") or DEFAULT_MIN_CITATIONS
        print(f"\n[{tid}] query='{theme.get('query', '')}' "
              f"concept={theme.get('concept_id', '-')} "
              f"year>={theme.get('year_from', '-')} "
              f"min_cit>{min_cits} top={per_theme_top}")
        works = iterate_works(
            query=theme.get("query", "") or "",
            concept_id=theme.get("concept_id"),
            year_from=theme.get("year_from"),
            year_to=theme.get("year_to"),
            min_citations=min_cits,
            top=per_theme_top,
        )
        print(f"  → got {len(works)} works")
        for w in works:
            oid = w.get("openalex_id")
            if not oid:
                continue
            if oid in by_id:
                by_id[oid] = merge_candidate(by_id[oid], w, tid)
                n_updated += 1
            else:
                by_id[oid] = new_candidate(w, tid)
                n_new += 1

    candidates = sorted(
        by_id.values(),
        key=lambda c: (-int(c.get("citations") or 0), c.get("year") or 0),
    )

    print(f"\n=== summary ===")
    print(f"  themes processed: {len(themes)}")
    print(f"  new candidates added: {n_new}")
    print(f"  existing refreshed: {n_updated}")
    print(f"  total in funnel: {len(candidates)}")
    if candidates:
        top1 = candidates[0]
        print(f"  top by citations: {top1.get('title', '')[:70]} ({top1.get('year', '?')}) — "
              f"{top1.get('citations', 0):,} cit")

    if args.dry_run:
        print("\n[dry-run] not writing funnel.yml")
        return 0

    write_funnel(doc, candidates)
    print(f"wrote {FUNNEL_YML.relative_to(ROOT)} ({len(candidates)} candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
