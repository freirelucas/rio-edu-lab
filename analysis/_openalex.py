"""OpenAlex API helpers shared by 40 (interactive discovery) and 45 (bulk).

Promoted out of `40_openalex_discover.py` so the bulk-discovery script in the
funnel can iterate a curated concept list and reuse the same query / throttle
/ parsing logic without duplication.

Polite usage: User-Agent + 1 req/s throttle (THROTTLE_S). Silent fail per
page (warn to stderr, continue). Stdlib only.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request

USER_AGENT = "rio-edu-lab/0.8 (https://github.com/freirelucas/rio-edu-lab)"
OPENALEX_MAILTO = "rio-edu-lab@example.com"  # polite-pool identifier; OpenAlex docs recommend including mailto


def _with_mailto(url: str) -> str:
    """Append mailto= query param so OpenAlex routes us to the polite pool."""
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}mailto={OPENALEX_MAILTO}"
TIMEOUT = 20
THROTTLE_S = 1.0
PER_PAGE = 25


def fetch(url: str) -> dict | None:
    polite_url = _with_mailto(url) if "api.openalex.org" in url else url
    req = urllib.request.Request(polite_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [warn] {e}", file=sys.stderr)
        return None


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
    if year_from or year_to:
        lo = str(year_from) if year_from else ""
        hi = str(year_to) if year_to else ""
        filters.append(f"publication_year:{lo}-{hi}")
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
    """OpenAlex returns the abstract as a position → word inverted index."""
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


def parse_work(work: dict) -> dict:
    """Convert a raw OpenAlex /works result into the lab's flat row shape."""
    return {
        "openalex_id": work.get("id", ""),
        "doi": doi_from_work(work),
        "title": work.get("title") or "",
        "authors": authors_summary(work.get("authorships") or []),
        "year": work.get("publication_year") or "",
        "venue": venue_display(work),
        "cited_by_count": work.get("cited_by_count") or 0,
        "concepts_top3": concepts_top3(work.get("concepts") or []),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "pdf_url_oa": pdf_oa_url(work),
    }


def iterate_works(
    query: str = "",
    concept_id: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    min_citations: int = 0,
    top: int = 50,
    verbose: bool = True,
) -> list[dict]:
    """Paginate `/works` for the given filters and return parsed rows.

    Caller handles dedup against external state. Pages are walked until
    `top` results collected or the API returns no more. Sleeps 1s between
    pages to respect OpenAlex's polite policy. Truncates to `top` results
    sorted by cited_by_count desc (defensive — the API already sorts).
    """
    rows: list[dict] = []
    seen: set[str] = set()
    page = 1
    while len(rows) < top:
        url = build_query_url(query, concept_id, year_from, year_to, min_citations, page)
        if verbose:
            print(f"  page {page}: {url[:160]}", file=sys.stderr)
        data = fetch(url)
        if not data or "results" not in data:
            break
        results = data["results"]
        if not results:
            break
        for w in results:
            oid = w.get("id", "")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            rows.append(parse_work(w))
            if len(rows) >= top:
                break
        page += 1
        time.sleep(THROTTLE_S)
    rows.sort(key=lambda r: -int(r.get("cited_by_count") or 0))
    return rows[:top]


def _normalize_id(openalex_id: str) -> str:
    """Strip the URL prefix so callers can pass either form."""
    s = (openalex_id or "").strip()
    if s.startswith("https://openalex.org/"):
        s = s[len("https://openalex.org/"):]
    return s


def fetch_work_by_id(openalex_id: str, verbose: bool = True) -> dict | None:
    """GET /works/{id} → full Work dict including `referenced_works`.

    Caller picks fields; we don't pre-parse so the full snowball structure
    (referenced_works, cited_by_count, abstract_inverted_index, etc.) stays
    available. Throttles once per call.
    """
    wid = _normalize_id(openalex_id)
    if not wid:
        return None
    url = f"https://api.openalex.org/works/{wid}"
    if verbose:
        print(f"  fetch_work_by_id: {wid}", file=sys.stderr)
    data = fetch(url)
    time.sleep(THROTTLE_S)
    return data


def fetch_works_batch(
    openalex_ids: list[str],
    chunk: int = 50,
    verbose: bool = True,
) -> list[dict]:
    """Batch-fetch many works via `?filter=openalex_id:W1|W2|...`.

    Reduces N individual fetches to N/50 calls (OpenAlex per-page max 200,
    but the filter-id syntax tolerates ≤50 OR'd ids safely). Returns the
    raw Work dicts (NOT parsed). Order not guaranteed; caller dedupes via
    `work['id']`. Skips ids that OpenAlex doesn't return (silently dropped
    by the API for invalid/withdrawn works).
    """
    out: list[dict] = []
    ids_clean = [_normalize_id(x) for x in openalex_ids if x]
    ids_clean = [x for x in ids_clean if x.startswith("W")]
    if not ids_clean:
        return []
    for i in range(0, len(ids_clean), chunk):
        batch = ids_clean[i:i + chunk]
        filt = "openalex_id:" + "|".join(batch)
        url = (
            "https://api.openalex.org/works?"
            f"filter={urllib.parse.quote(filt, safe=':|')}"
            f"&per-page={len(batch)}&page=1"
        )
        if verbose:
            print(
                f"  fetch_works_batch chunk {i // chunk + 1}: {len(batch)} ids",
                file=sys.stderr,
            )
        data = fetch(url)
        if data and "results" in data:
            got = data["results"]
            out.extend(got)
            if verbose and len(got) < len(batch):
                missing = len(batch) - len(got)
                print(f"  [warn] {missing} ids not returned by API", file=sys.stderr)
        time.sleep(THROTTLE_S)
    return out


def iterate_cites(
    seed_openalex_id: str,
    top: int = 50,
    min_citations: int = 0,
    max_citations: int | None = None,
    verbose: bool = True,
) -> list[dict]:
    """Paginate `/works?filter=cites:W{id}` → forward snowball.

    Returns parsed rows (via parse_work) sorted by cited_by_count desc,
    capped at `top`. `min_citations`/`max_citations` apply as inline
    filters so the API does the pruning. Mirrors iterate_works pagination
    and throttling.
    """
    wid = _normalize_id(seed_openalex_id)
    if not wid:
        return []
    rows: list[dict] = []
    seen: set[str] = set()
    page = 1
    while len(rows) < top:
        filters = [f"cites:{wid}"]
        if min_citations:
            filters.append(f"cited_by_count:>{min_citations}")
        if max_citations:
            filters.append(f"cited_by_count:<{max_citations}")
        url = (
            "https://api.openalex.org/works?"
            f"filter={','.join(filters)}"
            f"&sort=cited_by_count:desc&per-page={PER_PAGE}&page={page}"
        )
        if verbose:
            print(f"  iterate_cites {wid} page {page}", file=sys.stderr)
        data = fetch(url)
        if not data or "results" not in data:
            break
        results = data["results"]
        if not results:
            break
        for w in results:
            oid = w.get("id", "")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            rows.append(parse_work(w))
            if len(rows) >= top:
                break
        page += 1
        time.sleep(THROTTLE_S)
    rows.sort(key=lambda r: -int(r.get("cited_by_count") or 0))
    return rows[:top]


__all__ = [
    "USER_AGENT", "TIMEOUT", "THROTTLE_S", "PER_PAGE",
    "fetch", "build_query_url",
    "authors_summary", "concepts_top3", "reconstruct_abstract",
    "doi_from_work", "pdf_oa_url", "venue_display",
    "parse_work", "iterate_works",
    "fetch_work_by_id", "fetch_works_batch", "iterate_cites",
]
