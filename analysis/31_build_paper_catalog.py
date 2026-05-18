"""Validates `data/papers_catalog.yml` and builds the paper × data mapping.

Outputs:
  - `data/processed/paper_data_mapping.csv` — long-format paper × requirement
    × data.rio item × status. One row per requirement per paper.
  - `data/processed/papers_catalog_summary.json` — counts by area, status,
    brazil_specific, replication_status. Used by the docs page.

Validações (falha hard se quebrar):
  - id único, kebab-case
  - ano numérico e plausível (1900-2030)
  - replication_status ∈ {full, partial, pending, unfeasible}
  - data_rio_coverage.status ∈ {available, partial, external, missing}
  - se replication_status ∈ {full, partial}, deve ter ≥1 report_id

Uso:
  python3 analysis/31_build_paper_catalog.py
  python3 analysis/31_build_paper_catalog.py --strict   # falha em warnings
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
OPENALEX_JSON = ROOT / "data" / "processed" / "openalex_citations.json"
OUT_MAPPING = ROOT / "data" / "processed" / "paper_data_mapping.csv"
OUT_SUMMARY = ROOT / "data" / "processed" / "papers_catalog_summary.json"

VALID_REPL = {"full", "partial", "pending", "unfeasible"}
VALID_STATUS = {"available", "partial", "external", "missing"}
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_taxonomy() -> dict[str, str]:
    """Returns mapping {alias_lower → category_id} from requirements_taxonomy.yml.

    Empty dict if taxonomy file absent — backward-compat (free-text strings OK).
    """
    if not TAXONOMY_YML.exists():
        return {}
    data = yaml.safe_load(TAXONOMY_YML.read_text(encoding="utf-8")) or {}
    alias_to_cat: dict[str, str] = {}
    for cat in data.get("categories", []):
        cid = cat.get("id", "")
        for alias in cat.get("aliases", []) or []:
            alias_to_cat[alias.strip().lower()] = cid
    return alias_to_cat


def check_taxonomy(papers: list[dict], alias_to_cat: dict[str, str]) -> list[str]:
    """Warnings (not errors) for `data_requirements` strings outside the taxonomy."""
    if not alias_to_cat:
        return []
    warns: list[str] = []
    for p in papers:
        pid = p.get("id", "?")
        for req in p.get("data_requirements") or []:
            key = (req or "").strip().lower()
            if key and key not in alias_to_cat:
                warns.append(f"paper '{pid}': requirement '{req}' not in taxonomy")
    return warns


def validate(papers: list[dict]) -> list[str]:
    errs: list[str] = []
    seen_ids: set[str] = set()
    for i, p in enumerate(papers):
        loc = f"paper[{i}] {p.get('id', '?')}"
        for req_field in ("id", "authors", "year", "title", "venue",
                          "doi_or_url", "area", "method", "brazil_specific",
                          "data_requirements", "replication_status"):
            if req_field not in p:
                errs.append(f"{loc}: missing '{req_field}'")
        pid = p.get("id", "")
        if not isinstance(pid, str) or not KEBAB_RE.match(pid):
            errs.append(f"{loc}: id '{pid}' not kebab-case")
        if pid in seen_ids:
            errs.append(f"{loc}: duplicate id '{pid}'")
        seen_ids.add(pid)
        yr = p.get("year")
        if not isinstance(yr, int) or not (1900 <= yr <= 2030):
            errs.append(f"{loc}: year={yr} out of range")
        repl = p.get("replication_status")
        if repl not in VALID_REPL:
            errs.append(f"{loc}: replication_status='{repl}' not in {VALID_REPL}")
        for cov in p.get("data_rio_coverage", []) or []:
            st = cov.get("status")
            if st not in VALID_STATUS:
                errs.append(f"{loc}: coverage.status='{st}' not in {VALID_STATUS}")
        if repl in {"full", "partial"}:
            if not p.get("report_ids"):
                errs.append(f"{loc}: status={repl} but no report_ids")
    return errs


def build_mapping(papers: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for p in papers:
        pid = p["id"]
        coverage = {c["requirement"]: c for c in (p.get("data_rio_coverage") or [])}
        for req in p.get("data_requirements", []):
            cov = coverage.get(req)
            rows.append({
                "paper_id": pid,
                "year": p["year"],
                "title": p["title"],
                "requirement": req,
                "data_rio_item_id": (cov or {}).get("item_id") or "",
                "status": (cov or {}).get("status") or "missing",
                "replication_status": p["replication_status"],
            })
    return rows


def build_summary(papers: list[dict], mapping: list[dict]) -> dict:
    by_status = Counter(p["replication_status"] for p in papers)
    by_brazil = Counter("brazil" if p.get("brazil_specific") else "global" for p in papers)
    by_area = Counter()
    for p in papers:
        for a in p.get("area", []):
            by_area[a] += 1
    cov_status = Counter(m["status"] for m in mapping)

    # Per-paper coverage: how many requirements are satisfiable from data.rio?
    paper_coverage: list[dict] = []
    by_pid: dict[str, list[dict]] = {}
    for m in mapping:
        by_pid.setdefault(m["paper_id"], []).append(m)
    for pid, rows in by_pid.items():
        n = len(rows)
        n_avail = sum(1 for r in rows if r["status"] == "available")
        n_partial = sum(1 for r in rows if r["status"] == "partial")
        paper_coverage.append({
            "paper_id": pid,
            "n_requirements": n,
            "n_available": n_avail,
            "n_partial": n_partial,
            "coverage_share": (n_avail + 0.5 * n_partial) / n if n else 0.0,
        })
    paper_coverage.sort(key=lambda r: r["coverage_share"], reverse=True)

    # OpenAlex enrichment, if present
    openalex_present = False
    n_with_citations = 0
    if OPENALEX_JSON.exists():
        openalex_present = True
        data = json.loads(OPENALEX_JSON.read_text(encoding="utf-8"))
        n_with_citations = sum(
            1 for v in data.values()
            if v.get("citations_openalex") is not None
        )

    # Taxonomy coverage — share of (paper × requirement) pairs mapping to a
    # known category in requirements_taxonomy.yml.
    alias_to_cat = load_taxonomy()
    n_pairs = 0
    n_mapped = 0
    by_category: Counter = Counter()
    for p in papers:
        for req in p.get("data_requirements") or []:
            n_pairs += 1
            key = (req or "").strip().lower()
            if key in alias_to_cat:
                n_mapped += 1
                by_category[alias_to_cat[key]] += 1
    taxonomy_summary = {
        "loaded": bool(alias_to_cat),
        "n_categories": len({v for v in alias_to_cat.values()}) if alias_to_cat else 0,
        "n_aliases": len(alias_to_cat),
        "requirements_total": n_pairs,
        "requirements_mapped": n_mapped,
        "requirements_unmapped": n_pairs - n_mapped,
        "by_category_top": dict(by_category.most_common(15)),
    }

    return {
        "n_papers": len(papers),
        "by_replication_status": dict(by_status),
        "by_brazil_specific": dict(by_brazil),
        "by_area_top": dict(by_area.most_common(15)),
        "coverage_status_counts": dict(cov_status),
        "papers_with_full_coverage": sum(
            1 for r in paper_coverage if r["coverage_share"] == 1.0
        ),
        "papers_with_zero_coverage": sum(
            1 for r in paper_coverage if r["coverage_share"] == 0.0
        ),
        "openalex_snapshot_present": openalex_present,
        "openalex_n_with_citations": n_with_citations,
        "taxonomy": taxonomy_summary,
        "top_5_by_coverage": paper_coverage[:5],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    if not CATALOG_YML.exists():
        print(f"missing {CATALOG_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1

    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8"))
    papers = catalog.get("papers", [])
    print(f"loaded {len(papers)} papers from catalog")

    errs = validate(papers)
    if errs:
        for e in errs:
            print(f"  [error] {e}", file=sys.stderr)
        print(f"\n{len(errs)} validation errors", file=sys.stderr)
        return 2
    print("  validation: ok")

    alias_to_cat = load_taxonomy()
    taxonomy_warns: list[str] = []
    if alias_to_cat:
        taxonomy_warns = check_taxonomy(papers, alias_to_cat)
        if taxonomy_warns:
            for w in taxonomy_warns:
                print(f"  [warn] {w}", file=sys.stderr)
            print(
                f"  taxonomy: {len(taxonomy_warns)} requirements outside "
                f"`data/requirements_taxonomy.yml` (see warnings)",
                file=sys.stderr,
            )
        else:
            print("  taxonomy: all data_requirements map to a known category")
        if args.strict and taxonomy_warns:
            print("\nstrict mode: failing due to taxonomy warnings", file=sys.stderr)
            return 3
    else:
        print("  taxonomy: `data/requirements_taxonomy.yml` not found, skipping check")

    mapping = build_mapping(papers)
    OUT_MAPPING.parent.mkdir(parents=True, exist_ok=True)
    with OUT_MAPPING.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "paper_id", "year", "title", "requirement",
            "data_rio_item_id", "status", "replication_status",
        ])
        writer.writeheader()
        for row in mapping:
            writer.writerow(row)
    print(f"wrote {OUT_MAPPING.relative_to(ROOT)} ({len(mapping)} rows)")

    summary = build_summary(papers, mapping)
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_SUMMARY.relative_to(ROOT)}")

    print("\n=== headline ===")
    print(f"  total: {summary['n_papers']} papers")
    print(f"  by status: {summary['by_replication_status']}")
    print(f"  brazil-specific: {summary['by_brazil_specific'].get('brazil', 0)}")
    print(f"  data.rio coverage: {summary['coverage_status_counts']}")
    print(f"  full-coverage papers (replicable now): {summary['papers_with_full_coverage']}")
    if summary["openalex_snapshot_present"]:
        print(f"  openalex snapshot: {summary['openalex_n_with_citations']} papers enriched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
