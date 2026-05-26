"""Matching: requisito de paper × item do manifest data.rio + link reverso.

Para cada `data_requirement` do catálogo (canonicalizado via taxonomia em
`data/requirements_taxonomy.yml`), procura itens do manifest data.rio que
provavelmente o satisfazem. Algoritmo: scoring IDF-weighted sobre unigrams +
bigrams (ver `_match.py`).

Output é sugestão para o curador, não atribuição final. O curador valida
e edita `data_rio_coverage` em `data/papers_catalog.yml` manualmente.

Também produz o **link reverso**: para cada item do data.rio JÁ referenciado
pelo catálogo, lista quais papers o utilizam e que requisito ele atende.

Outputs:
  - data/processed/data_rio_match_suggestions.csv
      Linhas: paper_id × requirement × candidate_item_id × score.
      Top-K candidates por requirement (default K=5).
  - data/processed/data_rio_reverse_links.json
      Mapa item_id → {item_title, papers: [{paper_id, requirement}]}
  - docs/papers-by-data-rio.md
      Tabela markdown auto-gerada do link reverso.

Determinístico (sem rede). Roda em CI quando catalog OR manifest mudam.

Uso:
  python3 analysis/41_match_requirements.py
  python3 analysis/41_match_requirements.py --top-k 10  # mais candidatos
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Import shared tokenizer/scorer from sibling module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _match import (  # noqa: E402
    build_idf_index,
    load_taxonomy,
    weighted_score,
)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"
OUT_SUGGESTIONS = ROOT / "data" / "processed" / "data_rio_match_suggestions.csv"
OUT_REVERSE = ROOT / "data" / "processed" / "data_rio_reverse_links.json"
OUT_DOC = ROOT / "docs" / "papers-by-data-rio.md"


def build_suggestions(
    papers: list[dict],
    items: list[dict],
    cats: dict[str, dict],
    alias_to_cat: dict[str, str],
    top_k: int,
) -> list[dict]:
    """For each (paper, requirement) pair, top-K candidate manifest items."""
    # IDF-weighted scoring over taxonomy categories + manifest items.
    idf, cat_tokens, item_tokens = build_idf_index(cats, items)
    cat_candidates: dict[str, list[tuple[float, dict]]] = {}
    for cid in cats:
        scored = [
            (weighted_score(item_tokens[k], cat_tokens[cid], idf), it)
            for k, it in enumerate(items)
        ]
        scored = [(s, it) for s, it in scored if s > 0]
        scored.sort(key=lambda x: -x[0])
        cat_candidates[cid] = scored[:top_k]

    rows: list[dict] = []
    for p in papers:
        pid = p["id"]
        coverage = {c["requirement"]: c for c in (p.get("data_rio_coverage") or [])}
        for req in p.get("data_requirements") or []:
            key = (req or "").strip().lower()
            cid = alias_to_cat.get(key, "")
            current = coverage.get(req, {})
            candidates = cat_candidates.get(cid, [])
            if not candidates:
                rows.append({
                    "paper_id": pid,
                    "requirement": req,
                    "category_id": cid or "(unmapped)",
                    "rank": 0,
                    "score": 0.0,
                    "candidate_item_id": "",
                    "candidate_title": "(no candidates — category not in taxonomy or no match)",
                    "currently_assigned": current.get("item_id") or "",
                    "current_status": current.get("status") or "",
                })
                continue
            for rank, (score, it) in enumerate(candidates, start=1):
                rows.append({
                    "paper_id": pid,
                    "requirement": req,
                    "category_id": cid,
                    "rank": rank,
                    "score": round(score, 2),
                    "candidate_item_id": it.get("id", ""),
                    "candidate_title": it.get("title", ""),
                    "currently_assigned": current.get("item_id") or "",
                    "current_status": current.get("status") or "",
                })
    return rows


def build_reverse_links(papers: list[dict], items: list[dict]) -> dict:
    """item_id → {item_title, type, papers: [{paper_id, requirement}]}."""
    item_by_id = {it["id"]: it for it in items}
    reverse: dict[str, dict] = {}
    for p in papers:
        pid = p["id"]
        for cov in p.get("data_rio_coverage") or []:
            iid = cov.get("item_id")
            if not iid:
                continue
            it = item_by_id.get(iid)
            if iid not in reverse:
                reverse[iid] = {
                    "item_id": iid,
                    "item_title": (it or {}).get("title", "(unknown — not in manifest)"),
                    "item_type": (it or {}).get("type", ""),
                    "papers": [],
                }
            reverse[iid]["papers"].append({
                "paper_id": pid,
                "requirement": cov.get("requirement", ""),
                "status": cov.get("status", ""),
            })
    return reverse


def fmt_authors(authors: list[str]) -> str:
    if not authors:
        return "?"
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} & {authors[1]}"
    return f"{authors[0]} et al."


def render_reverse_doc(reverse: dict, papers: list[dict]) -> str:
    """Markdown table of {item_id → papers using it}, ordered by # of papers desc."""
    paper_by_id = {p["id"]: p for p in papers}
    rows = sorted(
        reverse.values(),
        key=lambda r: (-len(r["papers"]), r["item_title"]),
    )
    lines = [
        "---",
        "title: Papers por item do data.rio",
        "description: Link reverso auto-gerado — para cada item do manifest data.rio referenciado pelo catálogo de papers, quais papers o utilizam e que requisito atende.",
        "---",
        "",
        "# Papers por item do data.rio",
        "",
        "Auto-gerado por `analysis/41_match_requirements.py` a partir de "
        "`data/papers_catalog.yml` + `data/manifest.json`. Para cada item do "
        "data.rio referenciado por algum paper do catálogo, lista quais papers "
        "o utilizam e que requisito ele atende.",
        "",
        f"**Estado atual:** {len(rows)} itens do data.rio referenciados por "
        f"{len(papers)} papers no catálogo.",
        "",
        "| Item ID | Título | Tipo | # papers | Papers (requisito atendido) |",
        "|---|---|---|---:|---|",
    ]
    for r in rows:
        used_by = []
        for ref in r["papers"]:
            p = paper_by_id.get(ref["paper_id"], {})
            who = f"{fmt_authors(p.get('authors', []))} ({p.get('year', '?')})"
            req = ref["requirement"]
            used_by.append(f"{who} — _{req}_")
        used_str = "<br>".join(used_by)
        iid_code = f"`{r['item_id']}`" if r["item_id"] else "—"
        title = r["item_title"].replace("|", "\\|")
        lines.append(
            f"| {iid_code} | {title} | {r['item_type']} | "
            f"{len(r['papers'])} | {used_str} |"
        )
    lines.append("")
    lines.append("## Como reproduzir")
    lines.append("")
    lines.append("```bash")
    lines.append("python3 analysis/41_match_requirements.py")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top-k", type=int, default=5,
                    help="Top-K candidate items per requirement (default 5)")
    args = ap.parse_args()

    if not CATALOG_YML.exists():
        print(f"missing {CATALOG_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not MANIFEST_JSON.exists():
        print(f"missing {MANIFEST_JSON.relative_to(ROOT)}", file=sys.stderr)
        return 1

    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8"))
    papers = catalog.get("papers", [])
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    items = manifest.get("items", [])
    cats, alias_to_cat = load_taxonomy(TAXONOMY_YML)
    print(f"loaded: {len(papers)} papers, {len(items)} manifest items, "
          f"{len(cats)} taxonomy categories")

    suggestions = build_suggestions(papers, items, cats, alias_to_cat, args.top_k)
    OUT_SUGGESTIONS.parent.mkdir(parents=True, exist_ok=True)
    with OUT_SUGGESTIONS.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "paper_id", "requirement", "category_id", "rank", "score",
            "candidate_item_id", "candidate_title",
            "currently_assigned", "current_status",
        ])
        writer.writeheader()
        for row in suggestions:
            writer.writerow(row)
    print(f"wrote {OUT_SUGGESTIONS.relative_to(ROOT)} ({len(suggestions)} rows)")

    reverse = build_reverse_links(papers, items)
    OUT_REVERSE.write_text(
        json.dumps(reverse, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote {OUT_REVERSE.relative_to(ROOT)} ({len(reverse)} items)")

    doc_md = render_reverse_doc(reverse, papers)
    OUT_DOC.write_text(doc_md, encoding="utf-8")
    print(f"wrote {OUT_DOC.relative_to(ROOT)}")

    # Headline
    n_unmapped = sum(1 for s in suggestions
                     if s["category_id"] == "(unmapped)" and s["rank"] == 0)
    n_with_candidates = sum(
        1 for s in suggestions if s["rank"] == 1 and s["score"] > 0
    )
    print("\n=== headline ===")
    print(f"  taxonomy categories: {len(cats)}")
    print(f"  requirements scanned: {sum(len(p.get('data_requirements') or []) for p in papers)}")
    print(f"  data.rio items referenced by catalog: {len(reverse)}")
    print(f"  unmapped requirements (no taxonomy match): {n_unmapped}")
    print(f"  requirements with at least 1 manifest candidate: {n_with_candidates}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
