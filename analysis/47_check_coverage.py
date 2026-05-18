"""Stage 3 do funil — coverage check vs data.rio.

Para cada `suggested_requirement` de cada candidato em
`data/papers_funnel.yml`, encontra o item do manifest data.rio mais similar
(reusa `_match.score_item` + `category_keywords`). Grava top-1 hit por
categoria com `status` derivado do score:

  status         critério
  ─────────      ──────────────────────────────────────────────
  available      score ≥ AVAILABLE_THRESHOLD (default 5.0)
  partial        0 < score < AVAILABLE_THRESHOLD
  missing        score == 0 (nenhum item bate keywords)

Categorias marcadas em `requirements_taxonomy.yml` com level=`individual` ou
level=`meta` mas notes explicitando "Não disponível no data.rio" são sempre
gravadas como `external` (não testa contra manifest — overhead inútil).

Idempotente: re-rodar atualiza coverage sem perder decisões do curador.
`--force` recomputa tudo (use após manifest.json atualizar).

Uso:
  python3 analysis/47_check_coverage.py
  python3 analysis/47_check_coverage.py --threshold 8.0  # mais estrito
  python3 analysis/47_check_coverage.py --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _match import category_keywords, load_taxonomy, score_item  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"

DEFAULT_AVAILABLE_THRESHOLD = 5.0

# Categorias cujos dados notoriamente vivem fora do data.rio (microdado INEP,
# PNAD, RAIS, OSM). Marcamos `external` sem rodar matching.
EXTERNAL_LEVELS = {"individual"}
EXTERNAL_IDS = {"travel-network"}


def is_external_category(cat: dict) -> bool:
    if cat.get("level") in EXTERNAL_LEVELS:
        return True
    if cat.get("id") in EXTERNAL_IDS:
        return True
    notes = (cat.get("notes") or "").lower()
    if "não disponível no data.rio" in notes or "nao disponivel no data.rio" in notes:
        return True
    return False


def status_from_score(score: float, threshold: float) -> str:
    if score >= threshold:
        return "available"
    if score > 0:
        return "partial"
    return "missing"


def write_funnel(candidates: list[dict]) -> None:
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
    ap.add_argument("--threshold", type=float, default=DEFAULT_AVAILABLE_THRESHOLD,
                    help=f"Score ≥ threshold → available (default {DEFAULT_AVAILABLE_THRESHOLD})")
    ap.add_argument("--force", action="store_true",
                    help="Recompute coverage even when already present")
    args = ap.parse_args()

    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML.relative_to(ROOT)} — run 45+46 first", file=sys.stderr)
        return 1
    if not MANIFEST_JSON.exists():
        print(f"missing {MANIFEST_JSON.relative_to(ROOT)}", file=sys.stderr)
        return 1

    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    cats, _ = load_taxonomy(TAXONOMY_YML)
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    items = manifest.get("items", [])
    print(f"loaded {len(candidates)} candidates, {len(items)} manifest items, "
          f"{len(cats)} taxonomy categories")

    # Pre-compute top manifest item per category (avoids quadratic scan).
    # include_notes=False evita poluir o token set com metadados (root cause
    # PoSWID #3: notes tipo "Feature Service" matchavam manifest items
    # genéricos, inflando scores e nunca emitindo `partial`/`missing`).
    cat_top: dict[str, dict] = {}
    for cid, cat in cats.items():
        if is_external_category(cat):
            continue
        kws = category_keywords(cat, include_notes=False)
        scored = [(score_item(it, kws), it) for it in items]
        scored = [(s, it) for s, it in scored if s > 0]
        scored.sort(key=lambda x: -x[0])
        if scored:
            cat_top[cid] = {"score": scored[0][0], "item": scored[0][1]}

    n_processed = 0
    n_skipped = 0
    n_no_suggestions = 0
    for c in candidates:
        sugg = c.get("suggested_requirements") or []
        if not sugg:
            n_no_suggestions += 1
            continue
        if c.get("coverage") and not args.force:
            n_skipped += 1
            continue

        coverage_rows: list[dict] = []
        for s in sugg:
            cid = s["category_id"]
            cat = cats.get(cid, {})
            if is_external_category(cat):
                coverage_rows.append({
                    "category_id": cid,
                    "manifest_item_id": None,
                    "manifest_title": "(fora do data.rio — fonte externa)",
                    "score": 0.0,
                    "status": "external",
                })
                continue
            top = cat_top.get(cid)
            if not top:
                coverage_rows.append({
                    "category_id": cid,
                    "manifest_item_id": None,
                    "manifest_title": "(nenhum item bate a categoria)",
                    "score": 0.0,
                    "status": "missing",
                })
                continue
            it = top["item"]
            score = top["score"]
            coverage_rows.append({
                "category_id": cid,
                "manifest_item_id": it.get("id"),
                "manifest_title": it.get("title", ""),
                "score": round(score, 1),
                "status": status_from_score(score, args.threshold),
            })
        c["coverage"] = coverage_rows
        n_processed += 1

    print(f"\n=== summary ===")
    print(f"  candidates processed: {n_processed}")
    print(f"  skipped (already had coverage): {n_skipped}")
    print(f"  no suggestions to check: {n_no_suggestions}")

    if n_processed > 0 or args.force:
        write_funnel(candidates)
        print(f"wrote {FUNNEL_YML.relative_to(ROOT)}")

    # Headline: status distribution
    by_status: dict[str, int] = {}
    for c in candidates:
        for cov in c.get("coverage") or []:
            st = cov["status"]
            by_status[st] = by_status.get(st, 0) + 1
    if by_status:
        print("\ncoverage status distribution (across all requirements):")
        for st, n in sorted(by_status.items(), key=lambda x: -x[1]):
            print(f"  {st}: {n}")

    n_replicable = sum(
        1 for c in candidates
        if c.get("coverage")
        and all(
            cov["status"] in ("available", "partial")
            for cov in c["coverage"]
        )
    )
    print(f"\n  candidates with ALL requirements covered: {n_replicable}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
