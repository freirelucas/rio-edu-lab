"""Stage 2 do funil — extração semi-automática de requisitos de dados.

Para cada candidato em `data/papers_funnel.yml` sem `suggested_requirements`,
tokeniza `title + " " + abstract` e pontua contra `aliases + aliases_en` das
10 categorias em `data/requirements_taxonomy.yml`. Escreve top-K (default 3)
sugestões com score.

**Pré-filtro (v0.7.5):** candidato deve mentar >= 2 tokens de `EDU_KEYWORDS`
(education/school/teacher/student/etc. em EN e PT) no title+abstract antes
de ser scoreado. Papers fora do domínio (médicos, COVID, infra) recebem
`suggested_requirements: []` direto.

**Notes excluídas do scoring (v0.7.5):** o campo `notes` da taxonomia contém
metadados ("Feature Service", "INEP per-school", "data.rio") que poluíam o
token set e geravam falsos positivos. 46 chama `category_keywords` com
`include_notes=False`.

Idempotente: candidatos com sugestões já preenchidas são pulados, a menos
que `--force` seja passada (recomputa tudo). Primeira run pós-v0.7.5 sobre
funnel pré-existente: use `--force` para re-scorear sob novos thresholds.

Uso:
  python3 analysis/46_extract_requirements.py
  python3 analysis/46_extract_requirements.py --top-k 5
  python3 analysis/46_extract_requirements.py --force         # recomputa tudo
  python3 analysis/46_extract_requirements.py --min-score 2.0 # cutoff mais permissivo
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
    build_idf_index,
    candidate_text,
    domain_signal,
    load_taxonomy,
    tokenize_bigrams,
    weighted_score,
)

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"

DEFAULT_TOP_K = 3
DEFAULT_MIN_SCORE = 3.0  # IDF-weighted score (see _match)
DEFAULT_EDU_MIN = 2


def write_funnel(candidates: list[dict]) -> None:
    """Preserve header comments, rewrite candidates block."""
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
    ap.add_argument("--top-k", type=int, default=DEFAULT_TOP_K,
                    help=f"Top-K suggestions per candidate (default {DEFAULT_TOP_K})")
    ap.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE,
                    help=f"Minimum score to include (default {DEFAULT_MIN_SCORE})")
    ap.add_argument("--edu-min", type=int, default=DEFAULT_EDU_MIN,
                    help=f"Minimum domain_signal (edu+policy) hits for paper to be scored (default {DEFAULT_EDU_MIN})")
    ap.add_argument("--greedy", action="store_true",
                    help="v0.19 — capturar greedy: relax domain_signal threshold para 1 "
                         "(default 2). Coleta mais candidates edu-adjacente; o inbox + "
                         "comunidade filtram depois via curatoria. Use quando ser exaustivo "
                         "importa mais que precisão por-candidate.")
    ap.add_argument("--force", action="store_true",
                    help="Recompute suggestions even when already present")
    args = ap.parse_args()

    # v0.19 — greedy mode overrides edu_min pra 1 (mais permissivo)
    if args.greedy:
        args.edu_min = 1
        print("[greedy] domain_signal threshold reduzido pra 1 — capturando mais candidates",
              file=sys.stderr)

    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML.relative_to(ROOT)} — run 45 first", file=sys.stderr)
        return 1
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    print(f"loaded {len(candidates)} candidates from funnel")

    cats, _ = load_taxonomy(TAXONOMY_YML)
    if not cats:
        print(f"missing taxonomy {TAXONOMY_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1
    if not MANIFEST_JSON.exists():
        print(f"missing {MANIFEST_JSON.relative_to(ROOT)}", file=sys.stderr)
        return 1
    items = json.loads(MANIFEST_JSON.read_text(encoding="utf-8")).get("items", [])
    print(f"loaded {len(cats)} taxonomy categories, {len(items)} manifest items")

    # IDF over taxonomy categories + manifest items + candidate abstracts.
    cand_tokens = [tokenize_bigrams(candidate_text(c)) for c in candidates]
    idf, cat_tokens, _ = build_idf_index(cats, items, extra_docs=cand_tokens)

    n_scored = 0
    n_skipped = 0
    n_empty = 0
    n_off_topic = 0
    for i, c in enumerate(candidates):
        if c.get("suggested_requirements") and not args.force:
            n_skipped += 1
            continue
        if domain_signal(candidate_text(c)) < args.edu_min:
            c["suggested_requirements"] = []
            n_off_topic += 1
            continue
        scored = [
            (cid, weighted_score(cand_tokens[i], cat_tokens[cid], idf))
            for cid in cats
        ]
        kept = [
            {"category_id": cid, "score": round(s, 2)}
            for cid, s in sorted(scored, key=lambda x: -x[1])
            if s >= args.min_score
        ][: args.top_k]
        c["suggested_requirements"] = kept
        if kept:
            n_scored += 1
        else:
            n_empty += 1

    print("\n=== summary ===")
    print(f"  scored: {n_scored}")
    print(f"  empty (passed edu-filter, no category above min-score): {n_empty}")
    print(f"  off-topic (domain_signal < {args.edu_min}): {n_off_topic}")
    print(f"  skipped (already had suggestions): {n_skipped}")

    if n_scored == 0 and n_empty == 0:
        print("nothing to do; pass --force to recompute")
        return 0

    write_funnel(candidates)
    print(f"wrote {FUNNEL_YML.relative_to(ROOT)}")

    # Headline: distribution by top-1 category
    by_top1: dict[str, int] = {}
    for c in candidates:
        sugg = c.get("suggested_requirements") or []
        if sugg:
            top1 = sugg[0]["category_id"]
            by_top1[top1] = by_top1.get(top1, 0) + 1
    if by_top1:
        print("\ntop-1 category distribution:")
        for cid, n in sorted(by_top1.items(), key=lambda x: -x[1]):
            print(f"  {cid}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
