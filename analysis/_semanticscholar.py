"""Semantic Scholar Graph API wrapper — fallback pra abstracts vazios da OpenAlex.

v2 design: chamado pelo `45_bulk_discover.py` SÓ quando OpenAlex devolve
`abstract == ""` mas o candidate tem DOI. Não duplica calls — OpenAlex
sempre vai primeiro; SS é a rede de segurança.

Endpoints usados:
- POST /graph/v1/paper/batch (até 500 IDs por call; mais eficiente)
- GET  /graph/v1/paper/DOI:{doi} (single, pra debug/testes)

Rate limit free tier: 100 req/5min (~20 req/min). Throttle interno: 0.5s
entre calls (≈ 2 req/s instantâneo mas com janela de 5min, bem dentro).
Authenticated via `SEMANTIC_SCHOLAR_API_KEY` → mais headroom.

Cache filesystem em `data/cache/semscholar/{doi_safe}.json` (TTL 30d).

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

API_BASE = "https://api.semanticscholar.org/graph/v1"
USER_AGENT = "rio-edu-lab/0.14 (https://github.com/freirelucas/rio-edu-lab)"
TIMEOUT = 20
THROTTLE_S = 0.5  # free tier: ~20 req/min; buffer
BATCH_CHUNK = 500
RETURN_FIELDS = "abstract,title,year,citationCount,externalIds"

_CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "semscholar"
CACHE_TTL_DAYS = 30

_RETRY_DELAYS = (2.0, 4.0, 8.0, 16.0)


def _get_api_key() -> str | None:
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY", "").strip()
    return key or None


def _safe_doi_key(doi: str) -> str:
    """DOI → filesystem-safe key (replace `/` e `:` por `_`)."""
    return doi.replace("/", "_").replace(":", "_").replace("\\", "_")


def _cache_path(doi: str) -> Path:
    return _CACHE_DIR / f"{_safe_doi_key(doi)}.json"


def _cache_get(doi: str, ttl_days: int = CACHE_TTL_DAYS) -> dict | None:
    p = _cache_path(doi)
    if not p.exists():
        return None
    try:
        age = datetime.now(timezone.utc) - datetime.fromtimestamp(
            p.stat().st_mtime, tz=timezone.utc
        )
        if age > timedelta(days=ttl_days):
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _cache_set(doi: str, data: dict) -> None:
    p = _cache_path(doi)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _fetch_with_retry(
    url: str, method: str = "GET", body: dict | None = None,
) -> dict | list | None:
    """HTTP com retry exponencial em 429/5xx. Silent on 404."""
    headers = {"User-Agent": USER_AGENT}
    api_key = _get_api_key()
    if api_key:
        headers["x-api-key"] = api_key
    data_bytes: bytes | None = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data_bytes = json.dumps(body).encode("utf-8")

    for attempt in range(len(_RETRY_DELAYS) + 1):
        try:
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                print(f"  [ss-retry] HTTP {e.code} → wait {delay}s", file=sys.stderr)
                time.sleep(delay)
                continue
            if e.code == 404:
                return None  # paper não está no SS → silent
            print(f"  [ss-warn] HTTP {e.code} {url[:80]}", file=sys.stderr)
            return None
        except Exception as e:  # noqa: BLE001 — silent for non-HTTP
            if attempt < len(_RETRY_DELAYS):
                delay = _RETRY_DELAYS[attempt]
                print(f"  [ss-retry] {e} → wait {delay}s", file=sys.stderr)
                time.sleep(delay)
                continue
            print(f"  [ss-warn] {e}", file=sys.stderr)
            return None
    return None


def fetch_paper_by_doi(
    doi: str, use_cache: bool = True, verbose: bool = True,
) -> dict | None:
    """GET /paper/DOI:{doi} (single)."""
    if not doi:
        return None
    if use_cache:
        cached = _cache_get(doi)
        if cached is not None:
            if verbose:
                print(f"  ss fetch_paper_by_doi: {doi} (cache)", file=sys.stderr)
            return cached
    encoded = urllib.parse.quote(doi, safe="")
    url = f"{API_BASE}/paper/DOI:{encoded}?fields={RETURN_FIELDS}"
    if verbose:
        print(f"  ss fetch_paper_by_doi: {doi}", file=sys.stderr)
    data = _fetch_with_retry(url)
    if isinstance(data, dict) and use_cache:
        _cache_set(doi, data)
    time.sleep(THROTTLE_S)
    return data if isinstance(data, dict) else None


def fetch_papers_batch(
    dois: list[str], use_cache: bool = True, verbose: bool = True,
) -> dict[str, dict]:
    """POST /paper/batch (até 500 DOIs por call) → {doi_lower: paper_dict}.

    Cache-aware: checa cache antes; busca só os missing em batches.
    SS batch endpoint retorna list ordenada matching input ids; null se não achou.
    """
    if not dois:
        return {}

    results: dict[str, dict] = {}
    missing: list[str] = []

    if use_cache:
        for doi in dois:
            c = _cache_get(doi)
            if c is not None:
                results[doi.lower()] = c
            else:
                missing.append(doi)
        if verbose and (results or missing):
            print(
                f"  ss batch: {len(results)} cache hits, {len(missing)} to fetch",
                file=sys.stderr,
            )
    else:
        missing = list(dois)

    for i in range(0, len(missing), BATCH_CHUNK):
        chunk = missing[i:i + BATCH_CHUNK]
        body = {"ids": [f"DOI:{d}" for d in chunk]}
        url = f"{API_BASE}/paper/batch?fields={RETURN_FIELDS}"
        if verbose:
            print(
                f"  ss batch chunk {i // BATCH_CHUNK + 1}: {len(chunk)} DOIs",
                file=sys.stderr,
            )
        data = _fetch_with_retry(url, method="POST", body=body)
        if isinstance(data, list):
            for doi, paper in zip(chunk, data, strict=False):
                if isinstance(paper, dict):
                    results[doi.lower()] = paper
                    if use_cache:
                        _cache_set(doi, paper)
        time.sleep(THROTTLE_S)

    return results


def get_abstract(doi: str, **kwargs) -> str:
    """High-level helper: DOI → abstract string ("" se ausente)."""
    paper = fetch_paper_by_doi(doi, **kwargs)
    if not paper:
        return ""
    return paper.get("abstract") or ""


__all__ = [
    "API_BASE", "USER_AGENT", "TIMEOUT", "THROTTLE_S", "CACHE_TTL_DAYS",
    "BATCH_CHUNK", "RETURN_FIELDS",
    "fetch_paper_by_doi", "fetch_papers_batch", "get_abstract",
]
