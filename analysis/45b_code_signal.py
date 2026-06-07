"""Enriquece candidates do funil com code_signal (paper↔código via GitHub).

Stage entre 45 (snowball) e 46 (data matching). Procura cada DOI no GitHub Code
Search e persiste `code_signal: {github_n_hits, github_repos, queried_at}` nos
candidates priorizados.

Prioridade (priority_pool):
  Tier 1: candidates com coverage TOTAL (all data.rio items available)
  Tier 2: candidates com coverage parcial (any data.rio item available)
  Tier 3: BR papers (is_brazilian=True) com qualquer coverage
Ordenados por citação dentro de cada tier; concatenados.

Cap padrão `--limit 100` (~3-5min com GITHUB_TOKEN, sem token sai cedo com 403).
Idempotente — pula candidates com code_signal setado (`--refresh` força).

Uso:
  GITHUB_TOKEN=ghp_... python3 analysis/45b_code_signal.py            # 100 prioritários
  GITHUB_TOKEN=ghp_... python3 analysis/45b_code_signal.py --limit 20 # smoke test
  python3 analysis/45b_code_signal.py --dry-run                       # sem network
  GITHUB_TOKEN=ghp_... python3 analysis/45b_code_signal.py --refresh  # re-query cache
  GITHUB_TOKEN=ghp_... python3 analysis/45b_code_signal.py --all      # todo o funil (todos com DOI)

Cache: data/cache/github/{doi_safe}.json — gitignored, TTL 30d.
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from _github import _get_token, search_code_by_doi  # noqa: E402

FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"


def priority_pool(candidates: list[dict]) -> list[int]:
    """Returns indices ordered by priority for code-signal enrichment.

    Tier 1: full coverage.   Tier 2: partial coverage.   Tier 3: BR + any coverage.
    Each tier sorted by citation desc.
    """
    tier1: list[int] = []
    tier2: list[int] = []
    tier3: list[int] = []
    for i, c in enumerate(candidates):
        cov = c.get("coverage") or []
        statuses = [(x or {}).get("status") for x in cov]
        has_any_available = any(s == "available" for s in statuses)
        all_available = bool(statuses) and all(s == "available" for s in statuses)
        if all_available:
            tier1.append(i)
        elif has_any_available:
            tier2.append(i)
        elif c.get("is_brazilian") and cov:
            tier3.append(i)
    key = lambda idx: -(candidates[idx].get("citations") or 0)  # noqa: E731
    tier1.sort(key=key)
    tier2.sort(key=key)
    tier3.sort(key=key)
    return tier1 + tier2 + tier3


def write_funnel(candidates: list[dict]) -> None:
    """Preserve header comments, rewrite candidates block (matches 46/47)."""
    header_lines: list[str] = []
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100,
                    help="cap number of DOIs to enrich (default 100)")
    ap.add_argument("--refresh", action="store_true",
                    help="re-query GitHub even if code_signal already populated")
    ap.add_argument("--dry-run", action="store_true",
                    help="show what would be queried without network calls")
    ap.add_argument("--all", action="store_true",
                    help="enrich every candidate with a DOI (ignores priority pool)")
    args = ap.parse_args()

    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML} — run 45 first", file=sys.stderr)
        return 1

    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    print(f"loaded {len(candidates)} candidates")

    has_token = bool(_get_token())
    if not has_token and not args.dry_run:
        print("[warn] GITHUB_TOKEN / GH_TOKEN not set — /search/code returns 403.")
        print("       Set token and re-run, OR use --dry-run to preview targets.", file=sys.stderr)
        return 2
    if not args.dry_run:
        print("github auth: token (30 req/min)")

    if args.all:
        pool = [i for i, c in enumerate(candidates) if c.get("doi")]
        pool.sort(key=lambda i: -(candidates[i].get("citations") or 0))
    else:
        pool = [i for i in priority_pool(candidates) if candidates[i].get("doi")]
    print(f"priority pool: {len(pool)} candidates with DOI")

    n_enriched = 0
    n_skipped = 0
    n_hits_total = 0
    n_papers_with_code = 0
    n_errors = 0

    targets = pool[: args.limit]
    for rank, i in enumerate(targets, 1):
        c = candidates[i]
        if c.get("code_signal") and not args.refresh:
            n_skipped += 1
            continue
        doi = c["doi"]
        title = (c.get("title") or "")[:55]
        if args.dry_run:
            print(f"  [{rank:>3}/{len(targets)}] [dry] {doi} — {title}")
            continue
        result = search_code_by_doi(doi)
        n_hits = int(result.get("n_hits") or 0)
        repos = [r["full_name"] for r in (result.get("repos") or [])]
        c["code_signal"] = {
            "github_n_hits": n_hits,
            "github_repos": repos,
            "queried_at": result.get("queried_at"),
        }
        err = result.get("error")
        if err:
            c["code_signal"]["error"] = err
            n_errors += 1
            print(f"  [{rank:>3}/{len(targets)}] ERROR {err} — {title}", file=sys.stderr)
            if err == "auth_required":
                print("       (token rejected; aborting)", file=sys.stderr)
                break
        else:
            n_hits_total += n_hits
            if n_hits > 0:
                n_papers_with_code += 1
                top3 = repos[:3]
                print(f"  [{rank:>3}/{len(targets)}] {n_hits:>4} hits — {title}")
                print(f"        repos: {top3}")
            else:
                print(f"  [{rank:>3}/{len(targets)}]    0 hits — {title}")
        n_enriched += 1

    if args.dry_run:
        print(f"\n[dry-run] would query {len(targets)} DOIs")
        return 0

    print("\n=== summary ===")
    print(f"  enriched: {n_enriched}")
    print(f"  skipped (already had code_signal): {n_skipped}")
    print(f"  papers with n_hits > 0: {n_papers_with_code}/{n_enriched}")
    print(f"  total github code hits: {n_hits_total}")
    print(f"  errors: {n_errors}")

    if n_enriched > 0:
        write_funnel(candidates)
        print(f"wrote {FUNNEL_YML.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
