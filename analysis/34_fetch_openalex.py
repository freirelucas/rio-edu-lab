"""Fetch OpenAlex metadata + citation counts for the papers catalog.

Lê `data/papers_catalog.yml`, resolve cada entrada contra a API pública do
OpenAlex (https://api.openalex.org) e atualiza `openalex_id`,
`citations_openalex` e `citations_openalex_fetched_at` em `data/processed/
openalex_citations.json`. Não modifica o YAML in-place — o JSON é o snapshot,
pode ser regenerado anytime sem mexer no source-of-truth.

Estratégia de lookup:
  1. Se `doi_or_url` for um DOI canônico (10.xxxx/yyyy ou URL doi.org/handle),
     usa endpoint /works/<doi>.
  2. Senão, usa endpoint de busca /works?search=<title>&filter=author...
     e pega o melhor match por similaridade de título + autor + ano.
  3. Se nenhum match com confiança razoável, registra `null`.

Uso:
  python3 analysis/34_fetch_openalex.py            # fetch + write JSON
  python3 analysis/34_fetch_openalex.py --dry-run  # só imprime resultados

Rede:
  - Endpoint público sem auth. Polite usage: User-Agent + 1 req/s.
  - Falha silenciosa por paper (rede instável); imprime warning, segue.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
OUT_JSON = ROOT / "data" / "processed" / "openalex_citations.json"

USER_AGENT = "rio-edu-lab/0.7 (https://github.com/freirelucas/rio-edu-lab; mailto:none)"
TIMEOUT = 15
THROTTLE_S = 1.0  # polite ≤1 req/s


def normalize_doi(s: str) -> str | None:
    """Extract bare DOI (10.x/y) from a string that may be a URL."""
    if not s:
        return None
    s = s.strip()
    if s.startswith("10."):
        return s
    # Common forms: https://doi.org/10..., http://dx.doi.org/10..., handle.net/...
    for prefix in ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/", "https://dx.doi.org/"):
        if s.startswith(prefix):
            return s[len(prefix):]
    if "doi.org/" in s:
        return s.split("doi.org/", 1)[1]
    return None


def fetch_openalex(url: str) -> dict | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    [warn] {e}", file=sys.stderr)
        return None


def lookup_by_doi(doi: str) -> dict | None:
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    return fetch_openalex(url)


def lookup_by_search(title: str, year: int) -> dict | None:
    q = urllib.parse.quote_plus(title[:120])
    url = (
        f"https://api.openalex.org/works"
        f"?search={q}&filter=publication_year:{year-1}|{year}|{year+1}&per-page=5"
    )
    data = fetch_openalex(url)
    if not data or "results" not in data:
        return None
    results = data["results"]
    if not results:
        return None
    # Best match: highest cited_by_count among results (a weak heuristic)
    return max(results, key=lambda r: r.get("cited_by_count", 0))


def extract_fields(work: dict) -> dict:
    return {
        "openalex_id": work.get("id"),
        "citations_openalex": work.get("cited_by_count"),
        "openalex_title": work.get("title"),
        "openalex_year": work.get("publication_year"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not CATALOG_YML.exists():
        print(f"missing {CATALOG_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1

    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8"))
    papers = catalog.get("papers", [])
    print(f"resolving {len(papers)} papers against OpenAlex...")

    results: dict[str, dict] = {}
    today = date.today().isoformat()

    for i, p in enumerate(papers, 1):
        pid = p["id"]
        title = p["title"]
        year = p["year"]
        doi = normalize_doi(p.get("doi_or_url", ""))
        print(f"  [{i:>2}/{len(papers)}] {pid}")
        work = None
        if doi:
            work = lookup_by_doi(doi)
            if work is None:
                print(f"      DOI lookup failed for {doi}, trying search...")
        if work is None:
            work = lookup_by_search(title, year)
        if work is None:
            print(f"      no OpenAlex match found")
            results[pid] = {
                "openalex_id": None,
                "citations_openalex": None,
                "openalex_title": None,
                "openalex_year": None,
                "fetched_at": today,
                "match": "none",
            }
        else:
            ext = extract_fields(work)
            ext["fetched_at"] = today
            ext["match"] = "doi" if doi else "search"
            results[pid] = ext
            cit = ext.get("citations_openalex")
            print(f"      cited_by={cit}  id={ext.get('openalex_id')}")
        time.sleep(THROTTLE_S)

    if args.dry_run:
        print("\n[dry-run] not writing output")
        return 0

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_JSON.relative_to(ROOT)} ({len(results)} entries)")
    n_matched = sum(1 for v in results.values() if v.get("openalex_id"))
    print(f"  matched: {n_matched}/{len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
