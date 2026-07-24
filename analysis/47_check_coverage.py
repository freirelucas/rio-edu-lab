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

Ranker primário (v0.22): a seleção do item por categoria usa um score
*blended* — `rank = lexical + w · (composite − neutral)` — onde `lexical` é o
IDF + `code_book_bonus` (relevância TÓPICA, inalterada) e `composite ∈ [0,10]`
vem de `match_detail` (fit ESTRUTURAL: domínio/granularidade/temporal/schema/
api). Centrar em `neutral` (composite de um item sem `code_book` = 5.0) garante
que items legacy contribuam delta 0 e mantenham o ranking lexical idêntico
(zero regressão nos ~9820 items sem code_book); items enriquecidos passam a
COMPETIR pelo topo (`cat_top`) via seu fit estrutural. O gate `lex > 0`
preserva a semântica `missing` — item sem relevância tópica nunca é elegível,
então um item off-topic mas enriquecido não consegue roubar o slot. `status`
continua ancorado no score lexical (decisão conservadora: fit estrutural
refina QUAL item, mas `available` exige match tópico real). `--composite-weight
0` reproduz exatamente o ranker puro-lexical legacy.

Idempotente: re-rodar atualiza coverage sem perder decisões do curador.
`--force` recomputa tudo (use após manifest.json atualizar).

Uso:
  python3 analysis/47_check_coverage.py
  python3 analysis/47_check_coverage.py --threshold 8.0        # mais estrito
  python3 analysis/47_check_coverage.py --composite-weight 0   # legacy lexical
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
from _match import (  # noqa: E402
    MATCH_DETAIL_WEIGHTS,
    build_idf_index,
    candidate_text,
    code_book_bonus,
    load_taxonomy,
    match_detail,
    tokenize_bigrams,
    weighted_score,
)

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"

DEFAULT_AVAILABLE_THRESHOLD = 5.0
DEFAULT_PARTIAL_THRESHOLD = 2.0
DEFAULT_COMPOSITE_WEIGHT = 1.0

# Composite de um item SEM code_book: todos os 5 sub-scores caem no neutral 0.5,
# logo composite = 0.5 · Σ(pesos). Centrar o booster estrutural aqui faz items
# legacy contribuírem delta 0 (rank == lexical) → ranking idêntico ao legacy.
# Derivado dos pesos (não hard-coded) pra continuar correto se eles mudarem.
NEUTRAL_COMPOSITE = 0.5 * sum(MATCH_DETAIL_WEIGHTS.values())

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


def status_from_score(score: float, threshold: float, partial_threshold: float) -> str:
    if score >= threshold:
        return "available"
    if score >= partial_threshold:
        return "partial"
    return "missing"


def select_cat_top(
    cats: dict[str, dict],
    items: list[dict],
    idf: dict[str, float],
    cat_tokens: dict[str, set],
    item_tokens: list[set],
    composite_weight: float = DEFAULT_COMPOSITE_WEIGHT,
) -> tuple[dict[str, dict], int]:
    """Best-matching manifest item per (non-external) category, by blended rank.

    Ranker primário (v0.22):
        rank = lexical + composite_weight · (composite − NEUTRAL_COMPOSITE)
    com o gate `lexical > 0` (item precisa de relevância tópica pra ser
    elegível — preserva a semântica `missing`). `lexical` = IDF + code_book_bonus
    (relevância TÓPICA); `composite ∈ [0,10]` = match_detail (fit ESTRUTURAL).
    Centrar em NEUTRAL_COMPOSITE (5.0) faz items SEM code_book contribuírem
    delta 0 → rank == lexical → seleção idêntica ao legacy (zero regressão);
    items enriquecidos competem pelo topo via fit estrutural. `code_book_bonus`
    e `composite` intencionalmente se sobrepõem em domínio/granularidade —
    concordância dos dois sinais reforça a escolha.

    Retorna `(cat_top, n_composite_flips)` onde
        cat_top[cid] = {"score": <lexical do vencedor>,
                        "rank_score": <rank do vencedor>,
                        "item": <manifest item>}
    e `n_composite_flips` conta categorias em que o vencedor difere do argmax
    puro-lexical (ou seja, o composite promoveu um item enriquecido).
    """
    cat_top: dict[str, dict] = {}
    n_composite_flips = 0
    for cid, cat in cats.items():
        if is_external_category(cat):
            continue
        best_rank, best_lex, best_item, have_pick = 0.0, 0.0, None, False
        lex_only_best, lex_only_item = 0.0, None
        for k, it in enumerate(items):
            # Lexical IDF score + code-book alignment nudge (0 unless both the
            # item's `code_book` and the category's `expects` are populated).
            lex = weighted_score(item_tokens[k], cat_tokens[cid], idf) + code_book_bonus(it, cat)
            if lex <= 0:
                continue  # sem relevância tópica → não elegível (preserva 'missing')
            # Booster estrutural só entra pra items enriquecidos; legacy → delta 0.
            rank = lex
            if it.get("code_book"):
                composite = match_detail(it, cat)["composite"]
                rank = lex + composite_weight * (composite - NEUTRAL_COMPOSITE)
            if not have_pick or rank > best_rank:
                best_rank, best_lex, best_item, have_pick = rank, lex, it, True
            if lex > lex_only_best:
                lex_only_best, lex_only_item = lex, it
        if best_item is not None:
            cat_top[cid] = {"score": best_lex, "rank_score": best_rank, "item": best_item}
            if lex_only_item is not None and lex_only_item.get("id") != best_item.get("id"):
                n_composite_flips += 1
    return cat_top, n_composite_flips


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
    ap.add_argument("--partial-threshold", type=float, default=DEFAULT_PARTIAL_THRESHOLD,
                    help=f"Score ≥ this (but < threshold) → partial (default {DEFAULT_PARTIAL_THRESHOLD})")
    ap.add_argument("--composite-weight", type=float, default=DEFAULT_COMPOSITE_WEIGHT,
                    help=f"Peso do booster estrutural (composite−neutral) no ranker primário "
                         f"(default {DEFAULT_COMPOSITE_WEIGHT}; 0 = ranker puro-lexical legacy)")
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

    # IDF over taxonomy categories + manifest items + candidate abstracts
    # (same corpus as Stage 2 in 46, so scores are comparable across stages).
    cand_tokens = [tokenize_bigrams(candidate_text(c)) for c in candidates]
    idf, cat_tokens, item_tokens = build_idf_index(cats, items, extra_docs=cand_tokens)

    # Best-matching manifest item per category via ranker primário blended
    # (lexical + composite booster). Ver docstring de `select_cat_top`. External
    # categories são puladas lá dentro — seus dados vivem fora do data.rio.
    cat_top, n_composite_flips = select_cat_top(
        cats, items, idf, cat_tokens, item_tokens, args.composite_weight
    )

    n_processed = 0
    n_skipped = 0
    n_no_suggestions = 0
    n_cleared = 0
    for c in candidates:
        sugg = c.get("suggested_requirements") or []
        if not sugg:
            # No suggestions → no coverage. Clear any stale rows left from a
            # previous scoring run (keeps derived state consistent).
            if c.get("coverage"):
                c["coverage"] = []
                n_cleared += 1
            else:
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
            row = {
                "category_id": cid,
                "manifest_item_id": it.get("id"),
                "manifest_title": it.get("title", ""),
                "score": round(score, 2),
                "rank_score": round(top["rank_score"], 2),
                "status": status_from_score(score, args.threshold, args.partial_threshold),
            }
            # v0.15: enriched match_detail (5 normalized sub-scores + composite).
            # v0.22: o composite agora É o ranker primário — entra em `rank_score`
            # (que seleciona QUAL item vence `cat_top`). `score` continua sendo o
            # lexical do item vencedor e dirige o `status`; `rank_score ≥ score`
            # quando o fit estrutural elevou um item enriquecido.
            row["match_detail"] = match_detail(it, cat)
            coverage_rows.append(row)
        c["coverage"] = coverage_rows
        n_processed += 1

    print("\n=== summary ===")
    print(f"  candidates processed: {n_processed}")
    print(f"  skipped (already had coverage): {n_skipped}")
    print(f"  stale coverage cleared (no suggestions): {n_cleared}")
    print(f"  no suggestions to check: {n_no_suggestions}")
    print(f"  cat_top flips (enriquecido ganhou do argmax lexical, w={args.composite_weight}): "
          f"{n_composite_flips}")

    if n_processed > 0 or n_cleared > 0 or args.force:
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
