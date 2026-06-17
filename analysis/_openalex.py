"""OpenAlex API helpers compartilhados por 40 (interactive) e 45 (bulk snowball).

v2 (eficiente + rico):
- Polite-pool email via `OPENALEX_EMAIL` env (fallback placeholder pra dev)
- Optional `OPENALEX_API_KEY` header pra premium tier
- Per-paper JSON cache em `data/cache/openalex/work/` (TTL 30d)
- Retry exponencial em 429/500 (4 attempts: 2s, 4s, 8s, 16s)
- `parse_work` persiste **12 fields ricos novos** (sem quebrar callers):
    concepts (structured), topics, primary_topic, keywords, institutions,
    is_brazilian, related_works, referenced_works, best_oa_pdf_url, fwci, counts_by_year,
    is_retracted, mesh, sdg
- `reconstruct_abstract` SEM truncation (era 500 chars → agora full)
- `concepts_top3: str` preservado pra backward-compat (48_promote_funnel.py usa)

Stdlib + json + urllib. Sem deps externas.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER_AGENT = "rio-edu-lab/0.14 (https://github.com/freirelucas/rio-edu-lab)"
DEFAULT_EMAIL = "rio-edu-lab@example.com"  # fallback se OPENALEX_EMAIL não setado

TIMEOUT = 20
THROTTLE_S = 1.0
PER_PAGE = 25

# ─── Cache layer ───────────────────────────────────────────────────────────
# Per-paper JSON em data/cache/openalex/work/{W12345}.json (TTL configurável).
# Cache speedup: re-rodar 45_bulk_discover.py com cache populado fica < 30s.

_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "openalex"
CACHE_TTL_DAYS = 30


def _get_email() -> str:
    return os.environ.get("OPENALEX_EMAIL", DEFAULT_EMAIL).strip() or DEFAULT_EMAIL


def _get_api_key() -> str | None:
    key = os.environ.get("OPENALEX_API_KEY", "").strip()
    return key or None


def _with_mailto(url: str) -> str:
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}mailto={_get_email()}"


def _cache_path(kind: str, key: str) -> Path:
    return _CACHE_DIR / kind / f"{key}.json"


def _cache_get(kind: str, key: str, ttl_days: int = CACHE_TTL_DAYS) -> dict | None:
    p = _cache_path(kind, key)
    if not p.exists():
        return None
    try:
        age = datetime.now(timezone.utc) - datetime.fromtimestamp(
            p.stat().st_mtime, tz=timezone.utc
        )
        if age > timedelta(days=ttl_days):
            return None  # expirou
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _cache_set(kind: str, key: str, data: dict) -> None:
    p = _cache_path(kind, key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


# ─── HTTP fetch com retry ──────────────────────────────────────────────────
_RETRY_DELAYS = (2.0, 4.0, 8.0, 16.0)  # backoff exponencial em 429/5xx


def fetch(url: str) -> dict | None:
    """GET JSON com polite-pool (mailto + optional Bearer) + retry em 429/5xx."""
    polite_url = _with_mailto(url) if "api.openalex.org" in url else url
    headers = {"User-Agent": USER_AGENT}
    api_key = _get_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    for attempt in range(len(_RETRY_DELAYS) + 1):
        try:
            req = urllib.request.Request(polite_url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                print(f"  [retry] HTTP {e.code} → wait {delay}s", file=sys.stderr)
                time.sleep(delay)
                continue
            print(f"  [warn] HTTP {e.code} {url[:80]}", file=sys.stderr)
            return None
        except Exception as e:  # noqa: BLE001 — silent fail for non-HTTP
            if attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                print(f"  [retry] {e} → wait {delay}s", file=sys.stderr)
                time.sleep(delay)
                continue
            print(f"  [warn] {e}", file=sys.stderr)
            return None
    return None


# ─── Query builders ────────────────────────────────────────────────────────

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


# ─── Extractors (parse_work helpers) ───────────────────────────────────────

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
    """Legacy — string usada por 48_promote_funnel.py.derive_areas."""
    return "; ".join(c.get("display_name", "") for c in concepts[:3])


def concepts_structured(concepts: list[dict]) -> list[dict]:
    """v2: top-5 concepts como lista estruturada (id + level + score)."""
    return [
        {
            "id": c.get("id"),
            "level": c.get("level"),
            "score": c.get("score"),
            "display_name": c.get("display_name"),
        }
        for c in concepts[:5]
    ]


def topics_structured(topics: list[dict]) -> list[dict]:
    """OpenAlex Topics: hierarquia domain → field → subfield → topic."""
    return [
        {
            "id": t.get("id"),
            "display_name": t.get("display_name"),
            "score": t.get("score"),
            "subfield": (t.get("subfield") or {}).get("display_name"),
            "field": (t.get("field") or {}).get("display_name"),
            "domain": (t.get("domain") or {}).get("display_name"),
        }
        for t in topics[:5]
    ]


def primary_topic_dict(work: dict) -> dict | None:
    pt = work.get("primary_topic")
    if not pt:
        return None
    return {
        "id": pt.get("id"),
        "display_name": pt.get("display_name"),
        "score": pt.get("score"),
        "subfield": (pt.get("subfield") or {}).get("display_name"),
        "field": (pt.get("field") or {}).get("display_name"),
    }


def reconstruct_abstract(inverted: dict | None) -> str:
    """OpenAlex retorna `abstract_inverted_index` (word → posições).
    v2: sem truncation (era 500 chars). Caller trunca se quiser."""
    if not inverted:
        return ""
    positions: dict[int, str] = {}
    for word, locs in inverted.items():
        for loc in locs:
            positions[loc] = word
    return " ".join(positions[i] for i in sorted(positions))


def doi_from_work(work: dict) -> str:
    doi = (work.get("doi") or "").strip()
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    return doi


def pdf_oa_url(work: dict) -> str:
    oa = work.get("open_access") or {}
    return oa.get("oa_url") or ""


def best_oa_pdf_url(work: dict) -> str:
    """Fallback PDF URL quando open_access.oa_url é None."""
    loc = work.get("best_oa_location") or {}
    return loc.get("pdf_url") or ""


def venue_display(work: dict) -> str:
    pl = work.get("primary_location") or {}
    src = pl.get("source") or {}
    return src.get("display_name") or ""


def is_brazilian(authorships: list[dict]) -> bool:
    """True se ≥1 autor tem ≥1 instituição com country_code=BR."""
    for a in authorships:
        for inst in a.get("institutions") or []:
            if (inst.get("country_code") or "").upper() == "BR":
                return True
    return False


def institutions_summary(authorships: list[dict]) -> list[dict]:
    """Flatten authorships → lista de instituições únicas (por ror ou nome)."""
    seen: set[str] = set()
    out: list[dict] = []
    for a in authorships:
        for inst in a.get("institutions") or []:
            key = inst.get("ror") or inst.get("display_name") or ""
            if not key or key in seen:
                continue
            seen.add(key)
            out.append({
                "ror": inst.get("ror"),
                "display_name": inst.get("display_name"),
                "country_code": inst.get("country_code"),
                "type": inst.get("type"),
            })
    return out


def parse_work(work: dict) -> dict:
    """Raw OpenAlex Work → flat lab row. v2: rico (12+ fields novos)."""
    authorships = work.get("authorships") or []
    return {
        # Legacy fields (preservados — callers existentes não quebram):
        "openalex_id": work.get("id", ""),
        "doi": doi_from_work(work),
        "title": work.get("title") or "",
        "authors": authors_summary(authorships),
        "year": work.get("publication_year") or "",
        "venue": venue_display(work),
        "cited_by_count": work.get("cited_by_count") or 0,
        "concepts_top3": concepts_top3(work.get("concepts") or []),
        "abstract": reconstruct_abstract(work.get("abstract_inverted_index")),
        "pdf_url_oa": pdf_oa_url(work),
        # v2 rich fields:
        "concepts": concepts_structured(work.get("concepts") or []),
        "topics": topics_structured(work.get("topics") or []),
        "primary_topic": primary_topic_dict(work),
        "keywords": [
            k.get("display_name") for k in (work.get("keywords") or [])
            if k.get("display_name")
        ],
        "institutions": institutions_summary(authorships),
        "is_brazilian": is_brazilian(authorships),
        # v0.17 — top-level OpenAlex type (article|dataset|book-chapter|paratext|dissertation|...).
        # Útil pra filtrar `referenced_works` por tipo: papers que CITAM um
        # work tipo `dataset` provavelmente o usam como input — paper↔dataset
        # linkage declarativo. Recomendação dos 5 agentes (v0.16 audit).
        "type": work.get("type"),
        # v0.16 bug fix: separar related_works (similaridade do OpenAlex —
        # papers RELACIONADOS por similarity model) de referenced_works
        # (citações REAIS feitas pelo paper). Antes só capturávamos
        # related_works, enviesando ranqueamento downstream.
        "related_works": work.get("related_works") or [],
        "referenced_works": work.get("referenced_works") or [],
        "best_oa_pdf_url": best_oa_pdf_url(work),
        "fwci": work.get("fwci"),
        "counts_by_year": work.get("counts_by_year") or [],
        "is_retracted": bool(work.get("is_retracted")),
        "mesh": [
            m.get("descriptor_name") for m in (work.get("mesh") or [])
            if m.get("descriptor_name")
        ],
        "sdg": [
            s.get("display_name") for s in (work.get("sustainable_development_goals") or [])
            if s.get("display_name")
        ],
    }


# ─── Helpers de ID + iteradores (com cache) ────────────────────────────────

def _normalize_id(openalex_id: str) -> str:
    s = (openalex_id or "").strip()
    if s.startswith("https://openalex.org/"):
        s = s[len("https://openalex.org/"):]
    return s


def fetch_work_by_id(
    openalex_id: str, verbose: bool = True, use_cache: bool = True,
) -> dict | None:
    """GET /works/{id}. v2: usa cache (data/cache/openalex/work/{W}.json)."""
    wid = _normalize_id(openalex_id)
    if not wid:
        return None
    if use_cache:
        cached = _cache_get("work", wid)
        if cached is not None:
            if verbose:
                print(f"  fetch_work_by_id: {wid} (cache)", file=sys.stderr)
            return cached
    url = f"https://api.openalex.org/works/{wid}"
    if verbose:
        print(f"  fetch_work_by_id: {wid}", file=sys.stderr)
    data = fetch(url)
    if data and use_cache:
        _cache_set("work", wid, data)
    time.sleep(THROTTLE_S)
    return data


def fetch_works_batch(
    openalex_ids: list[str], chunk: int = 50,
    verbose: bool = True, use_cache: bool = True,
) -> list[dict]:
    """Batch-fetch via filter=openalex_id:W1|W2|…
    v2: checa cache per-id antes de buscar; só busca os missing em batch."""
    ids_clean = [_normalize_id(x) for x in openalex_ids if x]
    ids_clean = [x for x in ids_clean if x.startswith("W")]
    if not ids_clean:
        return []

    cached_results: list[dict] = []
    missing_ids: list[str] = []
    if use_cache:
        for wid in ids_clean:
            c = _cache_get("work", wid)
            if c is not None:
                cached_results.append(c)
            else:
                missing_ids.append(wid)
        if verbose and cached_results:
            print(
                f"  fetch_works_batch: {len(cached_results)} cache hits, "
                f"{len(missing_ids)} to fetch",
                file=sys.stderr,
            )
    else:
        missing_ids = list(ids_clean)

    fetched: list[dict] = []
    for i in range(0, len(missing_ids), chunk):
        batch = missing_ids[i:i + chunk]
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
            fetched.extend(got)
            if use_cache:
                for w in got:
                    wid_norm = _normalize_id(w.get("id", ""))
                    if wid_norm:
                        _cache_set("work", wid_norm, w)
            if verbose and len(got) < len(batch):
                print(f"  [warn] {len(batch) - len(got)} ids not returned", file=sys.stderr)
        time.sleep(THROTTLE_S)

    return cached_results + fetched


def iterate_works(
    query: str = "", concept_id: str | None = None,
    year_from: int | None = None, year_to: int | None = None,
    min_citations: int = 0, top: int = 50, verbose: bool = True,
) -> list[dict]:
    """Paginate /works → list de rows parseados (sem cache; query é volátil)."""
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


def iterate_cites(
    seed_openalex_id: str, top: int = 50, min_citations: int = 0,
    max_citations: int | None = None, verbose: bool = True,
) -> list[dict]:
    """Forward snowball via /works?filter=cites:W{id}."""
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
    "CACHE_TTL_DAYS",
    "fetch", "build_query_url",
    "authors_summary", "concepts_top3", "concepts_structured",
    "topics_structured", "primary_topic_dict",
    "reconstruct_abstract",
    "doi_from_work", "pdf_oa_url", "best_oa_pdf_url", "venue_display",
    "is_brazilian", "institutions_summary",
    "parse_work",
    "iterate_works", "fetch_work_by_id", "fetch_works_batch", "iterate_cites",
]
