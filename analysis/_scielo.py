"""SciELO adapter — fonte BR aberto de papers educacionais.

Sprint v0.19.b — multi-source greedy. OpenAlex tem boa cobertura global mas
papers BR em português pré-2010 ficam sub-indexados. SciELO (Scientific
Electronic Library Online) é o repositório principal de open access BR.

API: ArticleMeta v1 (https://articlemeta.scielo.org/) — REST JSON, sem auth.
Cobertura: ~1.5M papers de ~1.500 journals BR + LATAM em open access.

Shape espelha `_openalex.py` (cache filesystem TTL 30d, retry backoff,
polite throttle 0.5s/req).

Uso:
  from _scielo import search_articles_edu, fetch_article_by_pid
  articles = search_articles_edu(year_min=2010, max_results=50)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "cache" / "scielo"
USER_AGENT = "rio-edu-lab/0.19 (https://github.com/freirelucas/rio-edu-lab)"
TIMEOUT_S = 30
THROTTLE_S = 0.5
CACHE_TTL_DAYS = 30
_RETRY_DELAYS = (2.0, 4.0, 8.0)

# Base URLs
ARTICLEMETA_BASE = "https://articlemeta.scielo.org/api/v1"

# Subject codes pra educação na taxonomia SciELO (CNPq)
# Ref: https://docs.scielo.org/projects/scielo-pc-programs/en/latest/
EDU_SUBJECT_CODES = ["education", "educação", "educacao", "educational sciences"]


def _get_email() -> str:
    return os.environ.get("SCIELO_EMAIL", os.environ.get("OPENALEX_EMAIL", "")).strip()


def _safe_filename(s: str) -> str:
    return s.replace("/", "_").replace(":", "_").replace("\\", "_")


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{_safe_filename(key)}.json"


def _cache_get(key: str) -> dict | None:
    p = _cache_path(key)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > CACHE_TTL_DAYS * 86400:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_set(key: str, payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(key).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _http_get(url: str) -> dict | None:
    """GET JSON com retry backoff exponencial. None em giveup."""
    email = _get_email()
    ua = USER_AGENT + (f" (mailto:{email})" if email else "")
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "application/json"})
    last_err: Exception | None = None
    for delay in (0.0, *_RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                print(f"    [scielo-retry] HTTP {e.code}", file=sys.stderr)
                last_err = e
                continue
            if e.code == 404:
                return None  # not found — não retry
            last_err = e
            return None
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    if last_err:
        print(f"    [scielo-warn] giveup: {last_err}", file=sys.stderr)
    return None


def fetch_article_by_pid(collection: str, pid: str) -> dict | None:
    """Fetch single article by SciELO PID (S0101-73302007000300016 style).

    Returns raw ArticleMeta JSON. Cache hit serves immediately.
    """
    if not pid:
        return None
    cache_key = f"article_{collection}_{pid}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    url = f"{ARTICLEMETA_BASE}/article/?collection={collection}&code={pid}&format=json"
    data = _http_get(url)
    if data is not None:
        _cache_set(cache_key, data)
        time.sleep(THROTTLE_S)
    return data


def list_article_identifiers(collection: str = "scl", offset: int = 0,
                              limit: int = 50, from_date: str | None = None) -> list[dict]:
    """Lista PIDs paginados de uma coleção SciELO.

    Args:
        collection: 'scl' (Brasil), 'col' (Colômbia), 'arg' (Argentina), etc.
        offset: pagination offset
        limit: results per page (max ~1000)
        from_date: "YYYY-MM-DD" ou None pra todos

    Returns: list of {code, collection, processing_date}
    """
    cache_key = f"identifiers_{collection}_{offset}_{limit}_{from_date or 'all'}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached.get("identifiers") or []
    url = f"{ARTICLEMETA_BASE}/article/identifiers/?collection={collection}&offset={offset}&limit={limit}"
    if from_date:
        url += f"&from={from_date}"
    data = _http_get(url)
    if data is None:
        return []
    identifiers = data.get("objects") or data.get("identifiers") or []
    _cache_set(cache_key, {"identifiers": identifiers})
    time.sleep(THROTTLE_S)
    return identifiers


def parse_article(article: dict) -> dict:
    """Normalize ArticleMeta JSON → rio-edu-lab candidate shape.

    Subset mimicking _openalex.parse_work pra que 45_bulk_discover possa
    consumir sem branching extra.
    """
    if not article:
        return {}

    # ArticleMeta returns nested 'article' key sometimes
    art = article.get("article", article) if isinstance(article, dict) else {}

    pid = art.get("code") or art.get("v880", [{}])[0].get("_", "")
    title_v = art.get("v12") or []
    title = title_v[0].get("_") if title_v else ""

    abstract_v = art.get("v83") or []
    abstract = abstract_v[0].get("_", "") if abstract_v else ""

    year_v = art.get("v65") or []
    year_raw = year_v[0].get("_", "") if year_v else ""
    try:
        year = int(year_raw[:4]) if year_raw else None
    except (ValueError, TypeError):
        year = None

    doi_v = art.get("v237") or []
    doi = doi_v[0].get("_", "") if doi_v else ""

    # Authors (v10 is per-author array)
    authors_raw = art.get("v10") or []
    authors = []
    for a in authors_raw:
        surname = a.get("s", "")
        given = a.get("n", "")
        if surname:
            authors.append(f"{surname}, {given}".strip(", "))

    # SciELO BR is implicitly Brazilian (collection=scl)
    collection = art.get("collection", "scl")

    return {
        "scielo_pid": pid,
        "scielo_collection": collection,
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "year": year,
        "authors": authors,
        "is_brazilian": collection == "scl",
        "discovered_via": ["scielo"],
        "_source": "scielo",
    }


def search_articles_edu(year_min: int = 2010, max_results: int = 100,
                         collection: str = "scl") -> list[dict]:
    """Convenience: lista identifiers + parsea cada article.

    Greedy edu filter aplicado no caller (Stage 2). Aqui só harvestamos.

    Returns list of parsed candidate dicts.
    """
    results = []
    offset = 0
    batch_size = 50

    while len(results) < max_results:
        identifiers = list_article_identifiers(
            collection=collection, offset=offset, limit=batch_size,
            from_date=f"{year_min}-01-01",
        )
        if not identifiers:
            break
        for ident in identifiers[: max_results - len(results)]:
            pid = ident.get("code")
            if not pid:
                continue
            article = fetch_article_by_pid(collection, pid)
            if article:
                results.append(parse_article(article))
        offset += batch_size
        if len(identifiers) < batch_size:
            break  # last page

    return results


__all__ = [
    "ARTICLEMETA_BASE",
    "EDU_SUBJECT_CODES",
    "fetch_article_by_pid",
    "list_article_identifiers",
    "parse_article",
    "search_articles_edu",
]
