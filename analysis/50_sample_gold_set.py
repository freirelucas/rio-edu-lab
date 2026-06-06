"""Sample 50 (paper, predicted_top1_category) pairs from `data/papers_funnel.yml`,
stratified por categoria + banda de confidence, escreve `data/match_quality_gold.yml`
pra curador etiquetar.

Estratificação:
- **6 categorias data.rio-relevantes** (geometry-schools, geometry-neighborhoods,
  performance-aggregated, ses-aggregated, enrollment-counts, spatial-partition).
- **5 pairs por core cat** = 30: 2 top (top 25% de score na cat) + 2 mid (middle 50%) +
  1 borderline (score ≈ AVAILABLE_THRESHOLD=5.0).
- **+ 20 wild** = random dos demais (incl. cats `external` — detecta leak).

Idempotente: re-rodar sem `--reseed` é noop sobre o conjunto sampled (preserva labels
existentes); com `--reseed` regenera o sample preservando labels pelos `openalex_id` que
re-apareceram.

Uso:
  python3 analysis/50_sample_gold_set.py
  python3 analysis/50_sample_gold_set.py --reseed --seed 42
"""

from __future__ import annotations

import argparse
import random
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
FUNNEL = ROOT / "data" / "papers_funnel.yml"
GOLD = ROOT / "data" / "match_quality_gold.yml"

CORE_CATS = [
    "geometry-schools",
    "geometry-neighborhoods",
    "performance-aggregated",
    "ses-aggregated",
    "enrollment-counts",
    "spatial-partition",
]

AVAILABLE_THRESHOLD = 5.0   # mesma constante de 47_check_coverage.py
BORDERLINE_HALF = 1.0       # borderline = score em [THRESHOLD ± BORDERLINE_HALF]
N_CORE_PER_CAT = 5          # 2 top + 2 mid + 1 borderline
N_WILD = 20
N_TARGET = N_CORE_PER_CAT * len(CORE_CATS) + N_WILD  # 50

GOLD_HEADER = """# Gold-set para medir qualidade do match (paper → categoria).
# Gerado por `analysis/50_sample_gold_set.py`; rerodar é idempotente (preserva labels
# por openalex_id). Curador edita inline e commita.
#
# Schema por label:
#   openalex_id, title, predicted_category, score, sample_band: campos do sample (não editar)
#   is_correct: null | true | false | "unsure"   ← curador preenche
#   true_category: null | <category_id>          ← se is_correct=false e sabe a certa
#   notes: ""                                    ← rationale opcional (obrigatório se ambíguo)
#
# Heurística pra is_correct:
#   true  = a `predicted_category` É um dos data_requirements explícitos OU implícitos do paper
#           (na narrativa do abstract). Ex.: "estima IDEB por bairro" → performance-aggregated true.
#   false = não corresponde. Preencher `true_category` se souber qual seria.
#   unsure = não dá pra decidir do abstract sozinho. Exclui dos cálculos P/R mas conta
#            em "needs-second-opinion %".
#
# Bands (estratificação para garantir cobertura do regime de score):
#   top        = top-25% de score na categoria (sistema confiante)
#   mid        = middle-50% (sistema convicto)
#   borderline = score ∈ [4.0, 6.0] (zona de erro provável; está na borda do threshold available=5.0)
#   wild       = random de qualquer categoria fora das 6 core (incl. external — detecta leak)
"""


def _git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()[:12]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _build_rows(candidates: list[dict]) -> list[dict]:
    """Para cada candidate com suggested_requirements, extrai top-1 (paper, predicted_cat)."""
    rows = []
    for c in candidates:
        sugg = c.get("suggested_requirements") or []
        if not sugg:
            continue
        top = max(sugg, key=lambda s: float(s.get("score") or 0))
        rows.append({
            "openalex_id": c.get("openalex_id"),
            "title": (c.get("title") or "")[:120],
            "predicted_category": top.get("category_id"),
            "score": float(top.get("score") or 0),
        })
    return rows


def _stratify_cat(cat_rows: list[dict], rng: random.Random,
                  n_top: int = 2, n_mid: int = 2, n_border: int = 1) -> list[dict]:
    """Pra uma categoria, sample n_top + n_mid + n_border sem repetição entre bands."""
    if not cat_rows:
        return []
    sorted_rs = sorted(cat_rows, key=lambda r: -r["score"])
    n = len(sorted_rs)
    used: set[str] = set()
    out: list[dict] = []

    def pick(pool: list[dict], n_target: int, band: str) -> None:
        avail = [r for r in pool if r["openalex_id"] not in used]
        k = min(n_target, len(avail))
        for r in rng.sample(avail, k):
            used.add(r["openalex_id"])
            out.append({**r, "sample_band": band})

    top_pool = sorted_rs[:max(1, n // 4)]                       # top 25%
    mid_pool = sorted_rs[max(1, n // 4): max(2, 3 * n // 4)]    # middle 50%
    border_pool = [
        r for r in cat_rows
        if AVAILABLE_THRESHOLD - BORDERLINE_HALF <= r["score"] <= AVAILABLE_THRESHOLD + BORDERLINE_HALF
    ]
    pick(top_pool, n_top, "top")
    pick(mid_pool, n_mid, "mid")
    pick(border_pool, n_border, "borderline")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reseed", action="store_true",
                    help="Regenera sample (preserva labels já preenchidos por openalex_id)")
    ap.add_argument("--seed", type=int, default=42, help="Seed do RNG (default 42)")
    args = ap.parse_args()

    if not FUNNEL.exists():
        print(f"missing {FUNNEL.relative_to(ROOT)}", file=sys.stderr)
        return 1

    funnel = yaml.safe_load(FUNNEL.read_text(encoding="utf-8")) or {}
    candidates = funnel.get("candidates") or []
    rows = _build_rows(candidates)
    print(f"loaded {len(candidates)} candidates; {len(rows)} têm pelo menos 1 suggested_requirement")

    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r["predicted_category"], []).append(r)

    # Se já existe gold-set e --reseed não passou, é noop.
    if GOLD.exists() and not args.reseed:
        print(f"{GOLD.relative_to(ROOT)} já existe; --reseed pra regenerar (preserva labels).")
        return 0

    # Preserva labels existentes por openalex_id (em --reseed).
    existing_labels: dict[str, dict] = {}
    if GOLD.exists():
        existing = yaml.safe_load(GOLD.read_text(encoding="utf-8")) or {}
        for lbl in existing.get("labels") or []:
            existing_labels[lbl.get("openalex_id")] = lbl

    rng = random.Random(args.seed)
    sampled: list[dict] = []

    # Core: 6 cats × até 5 pairs
    for cat in CORE_CATS:
        sampled.extend(_stratify_cat(by_cat.get(cat, []), rng))

    # Wild: random N_TARGET - len(core) dos demais
    sampled_ids = {r["openalex_id"] for r in sampled}
    wild_pool = [r for r in rows if r["openalex_id"] not in sampled_ids]
    n_wild = min(N_TARGET - len(sampled), len(wild_pool))
    for r in rng.sample(wild_pool, n_wild):
        sampled.append({**r, "sample_band": "wild"})

    out: dict = {
        "version": 1,
        "sampled_from_funnel_commit": _git_commit(ROOT),
        "n_target": N_TARGET,
        "n_sampled": len(sampled),
        "labels": [],
    }
    for s in sampled:
        prev = existing_labels.get(s["openalex_id"], {})
        out["labels"].append({
            "openalex_id": s["openalex_id"],
            "title": s["title"],
            "predicted_category": s["predicted_category"],
            "score": round(s["score"], 2),
            "sample_band": s["sample_band"],
            "is_correct": prev.get("is_correct"),
            "true_category": prev.get("true_category"),
            "notes": prev.get("notes", ""),
        })

    yaml_body = yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=120, default_flow_style=False)
    GOLD.write_text(GOLD_HEADER + "\n" + yaml_body, encoding="utf-8")

    band_counts: dict[str, int] = {}
    for lbl in out["labels"]:
        band_counts[lbl["sample_band"]] = band_counts.get(lbl["sample_band"], 0) + 1
    n_filled = sum(1 for lbl in out["labels"] if lbl["is_correct"] is not None)

    print(f"wrote {GOLD.relative_to(ROOT)} ({len(out['labels'])} labels)")
    print(f"  by band: {band_counts}")
    print(f"  labels preenchidos preservados: {n_filled}/{len(out['labels'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
