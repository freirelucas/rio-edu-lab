"""Discovery: lista top-cited papers do OpenAlex matching uma query / concept.

Para o curador: dada uma área temática ou concept-id do OpenAlex, lista
papers top-cited candidatos a entrar no catálogo do lab. Output é CSV com
todos os campos necessários para decisão humana (DOI, autores, ano, venue,
citações, top-3 concepts, link OA quando aberto, abstract).

Não toca o catálogo. O curador filtra o CSV e adiciona linhas manualmente
a `data/papers_catalog.yml`.

Marca em `already_in_catalog` os DOIs que já estão no catálogo, para o
curador não duplicar.

Uso:
  # Top 50 papers de "educational inequality" desde 2000 com 100+ citações
  python3 analysis/40_openalex_discover.py "educational inequality" \\
      --year-from 2000 --min-citations 100 --top 50

  # Top 100 papers de Education concept (C71924100), qualquer ano, 500+ citações
  python3 analysis/40_openalex_discover.py --concept C71924100 \\
      --min-citations 500 --top 100

Rede:
  - OpenAlex public API, no auth (throttle ≤1 req/s).
  - Falha silenciosa por página; segue.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Import shared OpenAlex helpers from sibling module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _openalex import iterate_works  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
OUT_CSV = ROOT / "data" / "processed" / "openalex_candidates.csv"


def existing_dois() -> set[str]:
    """Set of normalized DOI strings already in papers_catalog.yml.

    Used to flag duplicates so the curator can skip them.
    """
    if not CATALOG_YML.exists():
        return set()
    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8"))
    dois: set[str] = set()
    for p in catalog.get("papers", []):
        url = (p.get("doi_or_url") or "").strip()
        for prefix in (
            "https://doi.org/",
            "http://doi.org/",
            "http://dx.doi.org/",
            "https://dx.doi.org/",
        ):
            if url.startswith(prefix):
                url = url[len(prefix):]
                break
        if url:
            dois.add(url.lower())
    return dois


FIELDS = [
    "openalex_id",
    "doi",
    "title",
    "authors",
    "year",
    "venue",
    "cited_by_count",
    "concepts_top3",
    "abstract",
    "pdf_url_oa",
    "already_in_catalog",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Discover top-cited OpenAlex papers")
    ap.add_argument(
        "query",
        nargs="?",
        default="",
        help="Free-text search query (optional if --concept passed)",
    )
    ap.add_argument(
        "--concept",
        help="OpenAlex concept ID, e.g., C71924100 for 'Education'",
    )
    ap.add_argument("--year-from", type=int, dest="year_from")
    ap.add_argument("--year-to", type=int, dest="year_to")
    ap.add_argument("--min-citations", type=int, default=50)
    ap.add_argument("--top", type=int, default=50)
    ap.add_argument("--out", type=str, default=str(OUT_CSV))
    args = ap.parse_args()

    if not args.query and not args.concept:
        print("error: provide a query or --concept", file=sys.stderr)
        return 1

    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    known = existing_dois()
    print(f"  catalog has {len(known)} DOI/URLs (used to flag duplicates)")

    works = iterate_works(
        query=args.query,
        concept_id=args.concept,
        year_from=args.year_from,
        year_to=args.year_to,
        min_citations=args.min_citations,
        top=args.top,
    )
    rows = [
        {**w, "already_in_catalog": w["doi"].lower() in known if w.get("doi") else False}
        for w in works
    ]

    with out_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\nwrote {out_path.relative_to(ROOT)} ({len(rows)} rows)")
    n_dup = sum(1 for r in rows if r["already_in_catalog"])
    print(f"  already in catalog: {n_dup} / {len(rows)}")
    if rows:
        top1 = rows[0]
        print(f"  top: {top1['authors'][:50]} ({top1['year']}) — "
              f"{top1['cited_by_count']:,} cit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
