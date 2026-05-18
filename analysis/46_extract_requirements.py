"""Stage 2 do funil — extração semi-automática de requisitos de dados.

Para cada candidato em `data/papers_funnel.yml` sem `suggested_requirements`,
tokeniza `title + " " + abstract` e pontua contra os aliases das 10 categorias
em `data/requirements_taxonomy.yml`. Escreve top-K (default 3) sugestões com
score (= número de aliases que aparecem no texto).

Idempotente: candidatos com sugestões já preenchidas são pulados, a menos
que `--force` seja passada (recomputa tudo).

Curador revisa em `papers_funnel.yml` e pode editar à mão antes de aceitar
no estágio 4. Sem sugestões acima do threshold → lista vazia (curador
preenche manualmente).

Uso:
  python3 analysis/46_extract_requirements.py
  python3 analysis/46_extract_requirements.py --top-k 5
  python3 analysis/46_extract_requirements.py --force         # recomputa tudo
  python3 analysis/46_extract_requirements.py --min-score 2.0 # cutoff mais alto
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _match import load_taxonomy, score_against_categories  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"

DEFAULT_TOP_K = 3
DEFAULT_MIN_SCORE = 1.0


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
    ap.add_argument("--force", action="store_true",
                    help="Recompute suggestions even when already present")
    args = ap.parse_args()

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
    print(f"loaded {len(cats)} taxonomy categories")

    n_scored = 0
    n_skipped = 0
    n_empty = 0
    for c in candidates:
        if c.get("suggested_requirements") and not args.force:
            n_skipped += 1
            continue
        text = (c.get("title") or "") + " " + (c.get("abstract") or "")
        ranked = score_against_categories(text, cats)
        # Filter by score threshold and take top-K
        kept = [
            {"category_id": cid, "score": round(s, 1)}
            for cid, s in ranked
            if s >= args.min_score
        ][: args.top_k]
        c["suggested_requirements"] = kept
        if kept:
            n_scored += 1
        else:
            n_empty += 1

    print(f"\n=== summary ===")
    print(f"  scored: {n_scored}")
    print(f"  empty (no category above min-score): {n_empty}")
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
