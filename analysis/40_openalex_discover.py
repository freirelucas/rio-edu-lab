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
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
OUT_CSV = ROOT / "data" / "processed" / "openalex_candidates.csv"

USER_AGENT = "rio-edu-lab/0.8 (https://github.com/freirelucas/rio-edu-lab; mailto:none)"
TIMEOUT = 20
THROTTLE_S = 1.0
PER_PAGE = 25


def fetch(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [warn] {e}", file=sys.stderr)
        return None


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


def build_query_url(
    query: str,
    concept_id: str | None,
    year_from: int | None,
    year_to: int | None,
    min_citations: int,
    page: int,
) -> str:
    filters: list[str] = []
    if concept_id:
        filters.append(f"concepts.id:{concept_id}")
    if year_from:
        filters.append(f"from_publication_year:{year_from}")
    if year_to:
        filters.append(f"to_publication_year:{year_to}")
    if min_citations:
        filters.append(f"cited_by_count:>{min_citations}")
    parts: list[str] = []
    if query:
        parts.append(f"search={urllib.parse.quote_plus(query)}")
    if filters:
        parts.append("filter=" + ",".join(filters))
    parts.append("sort=cited_by_count:desc")
    parts.append(f"per-page={PER_PAGE}")
    parts.append(f"page={page}")
    return "https://api.openalex.org/works?" + "&".join(parts)


def authors_summary(authorships: list[dict]) -> str:
    names: list[str] = []
    for a in authorships[:3]:
        au = a.get("author") or {}
        n = au.get("display_name")
        if n:
            names.append(n)
    suffix = " et al." if len(authorships) > 3 else ""
    return ", ".join(names) + suffix


def concepts_top3(concepts: list[dict]) -> str:
    return "; ".join(c.get("display_name", "") for c in concepts[:3])


def reconstruct_abstract(inverted: dict | None, max_chars: int = 500) -> str:
    """OpenAlex returns abstract as a position → word inverted index."""
    if not inverted:
        return ""
    positions: dict[int, str] = {}
    for word, locs in inverted.items():
        for loc in locs:
            positions[loc] = word
    ordered = [positions[i] for i in sorted(positions)]
    text = " ".join(ordered)
    if len(text) > max_chars:
        return text[: max_chars - 1] + "…"
    return text


def doi_from_work(work: dict) -> str:
    doi = (work.get("doi") or "").strip()
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    return doi


def pdf_oa_url(work: dict) -> str:
    oa = work.get("open_access") or {}
    return oa.get("oa_url") or ""


def venue_display(work: dict) -> str:
    pl = work.get("primary_location") or {}
    src = pl.get("source") or {}
    return src.get("display_name") or ""


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

    rows: list[dict] = []
    seen: set[str] = set()
    page = 1
    while len(rows) < args.top:
        url = build_query_url(
            args.query, args.concept, args.year_from, args.year_to,
            args.min_citations, page,
        )
        print(f"  page {page}: {url[:160]}")
        data = fetch(url)
        if not data or "results" not in data:
            print("    [warn] empty results, stopping")
            break
        results = data["results"]
        if not results:
            print("    [info] no more results")
            break
        for w in results:
            oid = w.get("id", "")
            if oid in seen:
                continue
            seen.add(oid)
            doi = doi_from_work(w)
            row = {
                "openalex_id": oid,
                "doi": doi,
                "title": w.get("title") or "",
                "authors": authors_summary(w.get("authorships") or []),
                "year": w.get("publication_year") or "",
                "venue": venue_display(w),
                "cited_by_count": w.get("cited_by_count") or 0,
                "concepts_top3": concepts_top3(w.get("concepts") or []),
                "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
                "pdf_url_oa": pdf_oa_url(w),
                "already_in_catalog": doi.lower() in known if doi else False,
            }
            rows.append(row)
            if len(rows) >= args.top:
                break
        page += 1
        time.sleep(THROTTLE_S)

    # Sort once more (defensive — OpenAlex already sorts by cited_by_count desc)
    rows.sort(key=lambda r: -int(r.get("cited_by_count") or 0))
    rows = rows[: args.top]

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
