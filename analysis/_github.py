"""GitHub Code Search adapter — proxy paper↔code via DOI lookup.

Stage 3 do funil precisa de um sinal cru pra "este paper tem replicação pública
no GitHub?". O melhor proxy gratuito é procurar o DOI do paper em código/READMEs
indexados pelo GitHub Code Search (REST /search/code).

Limites honestos do sinal:
- Não distingue "menção" (paper aparece numa lista bibliográfica) de "replicação
  real" (repo implementa o método). Trata o `n_hits` como triagem grosseira; valida
  por inspecção humana antes de prometer "this paper has code".
- Code Search só indexa default branch + repos públicos com < ~700KB por arquivo.
  Repos privados, notebooks gigantes ou monorepos grandes ficam invisíveis.
- Search hits são por arquivo — colapsamos pra repos únicos.

Auth: GITHUB_TOKEN (Bearer) — recomendado, 30 req/min.
Sem auth o /search/code retorna 403; o caller (45b_code_signal) sai cedo com
mensagem clara.

Cache: filesystem JSON por DOI em data/cache/github/, TTL 30d. Cache hit é
servido sem network. `--refresh` força bypass no caller.
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
CACHE_DIR = ROOT / "data" / "cache" / "github"
USER_AGENT = "rio-edu-lab/0.14 (https://github.com/freirelucas/rio-edu-lab)"
TIMEOUT = 20
THROTTLE_S = 2.0  # ~30 req/min — dentro do limit autenticado
CACHE_TTL_DAYS = 30
_RETRY_DELAYS = (2.0, 4.0, 8.0, 16.0)


def _get_token() -> str | None:
    """Read GITHUB_TOKEN (preferred) or GH_TOKEN from env."""
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    return tok.strip() if tok else None


def _safe_filename(s: str) -> str:
    """DOIs contain '/', ':' — sanitize for filesystem."""
    return s.replace("/", "_").replace(":", "_").replace("\\", "_")


def _cache_path(doi: str) -> Path:
    return CACHE_DIR / f"{_safe_filename(doi)}.json"


def _cache_get(doi: str) -> dict | None:
    p = _cache_path(doi)
    if not p.exists():
        return None
    if time.time() - p.stat().st_mtime > CACHE_TTL_DAYS * 86400:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_set(doi: str, payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(doi).write_text(json.dumps(payload), encoding="utf-8")


def _http_get(url: str, token: str | None) -> tuple[dict | None, str | None]:
    """Returns (json, error_tag). error_tag in {"auth_required","fetch_failed",None}."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    last_err: Exception | None = None
    for delay in (0.0, *_RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            status = e.code
            if status == 401 or status == 403:
                # 403 from /search/code without auth → caller deve parar.
                # 403 com auth → secondary rate limit ou abuse detection (retry).
                if not token:
                    return None, "auth_required"
                print(f"    [gh-retry] HTTP {status} (auth, secondary RL?)", file=sys.stderr)
                last_err = e
                continue
            if status in (429, 500, 502, 503, 504):
                print(f"    [gh-retry] HTTP {status}", file=sys.stderr)
                last_err = e
                continue
            return None, "fetch_failed"
        except Exception as e:
            last_err = e
            continue
    if last_err:
        print(f"    [warn] github giveup: {last_err}", file=sys.stderr)
    return None, "fetch_failed"


def search_code_by_doi(doi: str, max_results: int = 5) -> dict:
    """Search GitHub indexed code for the DOI as a literal string.

    Returns dict:
      {n_hits: int, repos: [{full_name, html_url, stars}], doi, queried_at,
       error: optional str ("auth_required", "fetch_failed", "no_doi")}.

    Hits are colapsados a unique repositórios; ranked por order que a API devolve
    (default = relevance + indexed_at). Cache hit é servido sem network.
    """
    if not doi:
        return {"n_hits": 0, "repos": [], "doi": None, "queried_at": None, "error": "no_doi"}

    cached = _cache_get(doi)
    if cached is not None:
        return cached

    token = _get_token()
    q = urllib.parse.quote(f'"{doi}"')
    url = f"https://api.github.com/search/code?q={q}&per_page={max_results * 3}"
    data, err = _http_get(url, token)

    if data is None:
        result = {
            "n_hits": 0,
            "repos": [],
            "doi": doi,
            "queried_at": time.time(),
            "error": err or "fetch_failed",
        }
        # Não cache auth_required (token pode ser adicionado depois)
        if err != "auth_required":
            _cache_set(doi, result)
        return result

    items = data.get("items", []) or []
    seen: set[str] = set()
    repos: list[dict] = []
    for it in items:
        r = it.get("repository") or {}
        full = r.get("full_name")
        if not full or full in seen:
            continue
        seen.add(full)
        repos.append({
            "full_name": full,
            "html_url": r.get("html_url"),
            "stars": (r.get("stargazers_count") or 0),
        })
        if len(repos) >= max_results:
            break

    result = {
        "n_hits": int(data.get("total_count") or 0),
        "repos": repos,
        "doi": doi,
        "queried_at": time.time(),
    }
    _cache_set(doi, result)
    time.sleep(THROTTLE_S)
    return result
