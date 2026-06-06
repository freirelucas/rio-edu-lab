"""Compara LLM extraction (v3) vs bag-of-words IDF (v2) sobre mesmo funil.

Sprint v3.B. Pra cada candidate em papers_funnel.yml que tem AMBOS:
- `suggested_requirements` (v2, do `46_extract_requirements.py`)
- `llm_suggested_requirements` (v3, do `55_llm_extract_requirements.py`)

Computa:
- **Agreement top-1**: bow top-1 == llm top-1?
- **Agreement set**: Jaccard das categorias top-3 de cada método
- **Confusion matrix**: bow_top1 × llm_top1 (descobre confusões sistemáticas)
- **Taxonomy-gap rate**: % de candidates que LLM marcou como gap
- **Disagreement examples**: top-20 cases onde bow ≠ llm (por citation desc)
- **Quando gold-set labeled** (data/match_quality_gold.yml com is_correct
  preenchido): P/R per categoria pros dois métodos sobre o mesmo eval set.
  Decisão empírica "trocar inferência principal?"

Outputs:
- `data/processed/llm_vs_bow_comparison.json` (machine; pro CI consumir)
- `docs/llm-vs-bow.md` (human, drift-checked; site-rendered)

Uso:
  python3 analysis/55_llm_extract_requirements.py --limit 30  # popular llm_*
  python3 analysis/56_llm_vs_bow_compare.py                    # compara
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
GOLD = ROOT / "data" / "match_quality_gold.yml"
SUMMARY_JSON = ROOT / "data" / "processed" / "llm_vs_bow_comparison.json"
REPORT_MD = ROOT / "docs" / "llm-vs-bow.md"


def _bow_top1(c: dict) -> str | None:
    """Top-1 category do bag-of-words (46_extract_requirements)."""
    sugg = c.get("suggested_requirements") or []
    if not sugg:
        return None
    top = max(sugg, key=lambda s: float(s.get("score") or 0))
    return top.get("category_id")


def _bow_set(c: dict) -> set[str]:
    return {s.get("category_id") for s in (c.get("suggested_requirements") or []) if s.get("category_id")}


def _llm_top1(c: dict) -> str | None:
    """Top-1 do LLM (highest confidence)."""
    sugg = c.get("llm_suggested_requirements") or []
    if not sugg:
        return None
    top = max(sugg, key=lambda s: float(s.get("confidence") or 0))
    return top.get("category_id")


def _llm_set(c: dict) -> set[str]:
    return {s.get("category_id") for s in (c.get("llm_suggested_requirements") or []) if s.get("category_id")}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def compute_comparison(candidates: list[dict]) -> dict:
    """Pure: candidates with both signals → comparison dict."""
    both: list[dict] = [
        c for c in candidates
        if c.get("suggested_requirements") and c.get("llm_suggested_requirements")
    ]
    n_with_bow = sum(1 for c in candidates if c.get("suggested_requirements"))
    n_with_llm = sum(1 for c in candidates if c.get("llm_suggested_requirements"))

    # Top-1 agreement + Jaccard
    n_top1_agree = 0
    jaccards: list[float] = []
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for c in both:
        bow1 = _bow_top1(c)
        llm1 = _llm_top1(c)
        if bow1 == llm1 and bow1 is not None:
            n_top1_agree += 1
        if bow1 and llm1:
            confusion[bow1][llm1] += 1
        jaccards.append(_jaccard(_bow_set(c), _llm_set(c)))

    # Taxonomy-gap rate
    n_gap = sum(1 for c in both if c.get("llm_taxonomy_gap"))
    gap_examples = [
        {
            "openalex_id": c.get("openalex_id"),
            "title": (c.get("title") or "")[:80],
            "gap_description": c.get("llm_gap_description"),
        }
        for c in both
        if c.get("llm_taxonomy_gap") and c.get("llm_gap_description")
    ][:15]

    # Disagreement examples (bow_top1 ≠ llm_top1), sorted by citation desc
    disagreements = [
        {
            "openalex_id": c.get("openalex_id"),
            "title": (c.get("title") or "")[:80],
            "citations": int(c.get("citations") or c.get("cited_by_count") or 0),
            "bow_top1": _bow_top1(c),
            "llm_top1": _llm_top1(c),
            "abstract_preview": (c.get("abstract") or "")[:120],
        }
        for c in both
        if _bow_top1(c) != _llm_top1(c) and _bow_top1(c) and _llm_top1(c)
    ]
    disagreements.sort(key=lambda r: -r["citations"])

    # Per-category usage rate by each method
    bow_top1_dist: Counter = Counter()
    llm_top1_dist: Counter = Counter()
    for c in both:
        if _bow_top1(c):
            bow_top1_dist[_bow_top1(c)] += 1
        if _llm_top1(c):
            llm_top1_dist[_llm_top1(c)] += 1

    return {
        "n_candidates_total": len(candidates),
        "n_with_bow": n_with_bow,
        "n_with_llm": n_with_llm,
        "n_with_both": len(both),
        "top1_agreement": {
            "n_agree": n_top1_agree,
            "rate": (n_top1_agree / len(both)) if both else None,
        },
        "jaccard": {
            "mean": (sum(jaccards) / len(jaccards)) if jaccards else None,
            "n": len(jaccards),
        },
        "taxonomy_gap": {
            "n_flagged": n_gap,
            "rate": (n_gap / len(both)) if both else None,
            "examples": gap_examples,
        },
        "bow_top1_distribution": dict(bow_top1_dist.most_common()),
        "llm_top1_distribution": dict(llm_top1_dist.most_common()),
        "confusion_matrix": {k: dict(v) for k, v in confusion.items()},
        "disagreement_examples": disagreements[:20],
    }


def compute_gold_set_eval(candidates: list[dict], gold_labels: list[dict]) -> dict | None:
    """Quando gold-set tem labels (is_correct preenchido), compara P por método.

    Pra cada label do gold-set:
    - Recupera o candidate pelo openalex_id
    - Vê se LLM top-1 == labeled true (se tiver) OU == predicted (se correct)

    Returns None se nenhum label decided OR nenhum candidate gold tem llm_*.
    """
    decided = [lbl for lbl in gold_labels if lbl.get("is_correct") in (True, False)]
    if not decided:
        return None

    by_oid = {c.get("openalex_id"): c for c in candidates}

    bow_tp = bow_fp = llm_tp = llm_fp = 0
    n_overlap = 0

    for lbl in decided:
        oid = lbl.get("openalex_id")
        c = by_oid.get(oid)
        if not c or not c.get("llm_suggested_requirements"):
            continue
        n_overlap += 1
        true_cat = lbl.get("true_category")
        predicted_bow = lbl.get("predicted_category")  # snapshot do bow no momento do sample
        is_correct = lbl.get("is_correct")

        # bow precision: how often the snapshot's predicted (from sample) matches truth
        if is_correct is True:
            bow_tp += 1
        elif is_correct is False:
            bow_fp += 1

        # llm precision: is llm top-1 correct?
        llm1 = _llm_top1(c)
        if true_cat:
            # If true_category provided, llm correct = llm top-1 == true_category
            if llm1 == true_cat:
                llm_tp += 1
            else:
                llm_fp += 1
        elif is_correct is True:
            # No true_category but bow was correct. LLM agrees with bow? credit.
            if llm1 == predicted_bow:
                llm_tp += 1
            else:
                llm_fp += 1
        else:  # is_correct False, no true_category
            llm_fp += 1  # conservative: we don't know what true was; count as wrong unless llm finds gap

    if not n_overlap:
        return None

    return {
        "n_gold_decided": len(decided),
        "n_overlap_with_llm": n_overlap,
        "bow_precision": bow_tp / (bow_tp + bow_fp) if (bow_tp + bow_fp) > 0 else None,
        "llm_precision": llm_tp / (llm_tp + llm_fp) if (llm_tp + llm_fp) > 0 else None,
        "bow_tp": bow_tp, "bow_fp": bow_fp,
        "llm_tp": llm_tp, "llm_fp": llm_fp,
    }


def render_report_md(summary: dict, gold_eval: dict | None) -> str:
    lines: list[str] = []
    lines.append("---\n")
    lines.append('title: "LLM vs bag-of-words: comparação"\n')
    lines.append('description: "Agreement, disagreement e taxonomy-gap rate entre o IDF lexical (v2) e o LLM extraction (v3) sobre o mesmo funil."\n')
    lines.append("---\n\n")
    lines.append("# LLM (v3) vs bag-of-words IDF (v2) — comparação\n\n")
    lines.append(
        "_Gerado por `analysis/56_llm_vs_bow_compare.py` sobre os candidatos do funil "
        "que têm ambos os signals (bow do `46` e llm do `55`)._\n\n"
    )

    n_both = summary["n_with_both"]
    n_bow = summary["n_with_bow"]
    n_llm = summary["n_with_llm"]
    n_total = summary["n_candidates_total"]

    lines.append("## Cobertura\n\n")
    lines.append(f"- **Total no funil:** {n_total}\n")
    lines.append(f"- **Com bow signal:** {n_bow}\n")
    lines.append(f"- **Com llm signal:** {n_llm}\n")
    lines.append(f"- **Com ambos (= sample da comparação):** {n_both}\n\n")

    if n_both == 0:
        lines.append("!!! note\n")
        lines.append("    Nenhum candidate tem ambos signals ainda. Rode `55_llm_extract_requirements.py` "
                     "pra popular llm_* em alguns candidates, depois re-rode este script.\n")
        return "".join(lines)

    agree = summary["top1_agreement"]
    rate = agree["rate"]
    lines.append("## Agreement\n\n")
    lines.append(f"- **Top-1 agreement:** {agree['n_agree']}/{n_both} ({rate:.0%})\n")
    j = summary["jaccard"]["mean"]
    lines.append(f"- **Jaccard set médio (top-K vs top-K):** {j:.2f} (1.0 = sets idênticos)\n\n")

    gap = summary["taxonomy_gap"]
    gap_rate = gap["rate"]
    lines.append("## Taxonomy gap\n\n")
    lines.append(f"- **LLM marcou como gap:** {gap['n_flagged']}/{n_both} ({gap_rate:.0%})\n")
    lines.append("- Indica papers cuja inferência precisa de dado fora das 10 categorias fechadas.\n\n")
    if gap["examples"]:
        lines.append("### Exemplos de gap (até 15)\n\n")
        for ex in gap["examples"]:
            desc = (ex.get("gap_description") or "")[:120]
            title = (ex.get("title") or "")[:60]
            lines.append(f"- **{title}** — {desc}\n")
        lines.append("\n")

    # Top-1 distribution by method
    lines.append("## Distribuição de top-1 por método\n\n")
    cats = sorted(set(summary["bow_top1_distribution"]) | set(summary["llm_top1_distribution"]))
    lines.append("| Categoria | bow top-1 | llm top-1 | Δ |\n")
    lines.append("|---|---:|---:|---:|\n")
    for cat in cats:
        bow_n = summary["bow_top1_distribution"].get(cat, 0)
        llm_n = summary["llm_top1_distribution"].get(cat, 0)
        delta = llm_n - bow_n
        lines.append(f"| `{cat}` | {bow_n} | {llm_n} | {delta:+d} |\n")
    lines.append("\n")

    # Confusion matrix (bow_top1 × llm_top1)
    cm = summary["confusion_matrix"]
    if cm:
        all_cats = sorted(set(cm.keys()) | {t for row in cm.values() for t in row.keys()})
        lines.append("## Confusion matrix (bow top-1 \\ llm top-1)\n\n")
        lines.append("| bow \\ llm | " + " | ".join(f"`{t}`" for t in all_cats) + " |\n")
        lines.append("|---|" + "---:|" * len(all_cats) + "\n")
        for bow_cat in all_cats:
            row = [str(cm.get(bow_cat, {}).get(t, 0)) for t in all_cats]
            lines.append(f"| `{bow_cat}` | " + " | ".join(row) + " |\n")
        lines.append("\n")
        lines.append("_Diagonal = agreement; off-diagonal = onde bow e llm discordam._\n\n")

    # Disagreement examples
    da = summary["disagreement_examples"]
    if da:
        lines.append(f"## Disagreement examples — top {min(len(da), 20)} (por citation)\n\n")
        lines.append("| bow | llm | Citations | Title | Abstract preview |\n")
        lines.append("|---|---|---:|---|---|\n")
        for ex in da[:20]:
            title = (ex.get("title") or "")[:55]
            preview = (ex.get("abstract_preview") or "")[:80].replace("|", "\\|")
            lines.append(
                f"| `{ex['bow_top1']}` | `{ex['llm_top1']}` | "
                f"{ex['citations']} | {title} | {preview} |\n"
            )
        lines.append("\n")

    # Gold-set eval
    if gold_eval:
        lines.append("## Precision contra gold-set labeled\n\n")
        lines.append(f"- **Labels decididos no gold-set:** {gold_eval['n_gold_decided']}\n")
        lines.append(f"- **Overlap com LLM-processados:** {gold_eval['n_overlap_with_llm']}\n\n")
        bp = gold_eval["bow_precision"]
        lp = gold_eval["llm_precision"]
        lines.append("| Método | TP | FP | Precision |\n")
        lines.append("|---|---:|---:|---:|\n")
        lines.append(f"| **bow** | {gold_eval['bow_tp']} | {gold_eval['bow_fp']} | "
                     f"{f'{bp:.0%}' if bp is not None else '—'} |\n")
        lines.append(f"| **llm** | {gold_eval['llm_tp']} | {gold_eval['llm_fp']} | "
                     f"{f'{lp:.0%}' if lp is not None else '—'} |\n")
        lines.append("\n")
        if bp is not None and lp is not None:
            if lp > bp + 0.05:
                lines.append(f"!!! tip\n    LLM precision excede bow em {(lp - bp) * 100:.0f}pp. "
                             "Considerar trocar inferência principal pra LLM.\n\n")
            elif bp > lp + 0.05:
                lines.append(f"!!! note\n    Bow precision excede LLM em {(bp - lp) * 100:.0f}pp. "
                             "Bag-of-words ainda é competitivo no escopo atual.\n\n")
            else:
                lines.append("!!! note\n    Métodos têm precision similar (Δ < 5pp); decisão "
                             "depende de outros fatores (custo, latência, taxonomy-gap detection).\n\n")
    else:
        lines.append("## Precision empírica\n\n")
        lines.append("!!! note\n    Gold-set vazio (sem labels decididos) ou sem overlap com LLM-"
                     "processados. Etiquete `data/match_quality_gold.yml` (preencha `is_correct`) "
                     "e rode `55_llm_extract_requirements.py` nos mesmos openalex_ids pra ativar "
                     "esta seção.\n\n")

    return "".join(lines)


def main() -> int:
    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    print(f"loaded {len(candidates)} candidates")

    summary = compute_comparison(candidates)
    summary["funnel_size"] = len(candidates)

    # Gold eval (opcional)
    gold_eval: dict | None = None
    if GOLD.exists():
        gold = yaml.safe_load(GOLD.read_text(encoding="utf-8")) or {}
        labels = gold.get("labels") or []
        gold_eval = compute_gold_set_eval(candidates, labels)

    summary["gold_set_eval"] = gold_eval

    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {SUMMARY_JSON.relative_to(ROOT)}")

    report = render_report_md(summary, gold_eval)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(report, encoding="utf-8")
    print(f"wrote {REPORT_MD.relative_to(ROOT)}")

    # Summary print
    print("\n=== summary ===")
    print(f"  n_with_both: {summary['n_with_both']}")
    if summary["top1_agreement"]["rate"] is not None:
        print(f"  top-1 agreement: {summary['top1_agreement']['rate']:.0%}")
        print(f"  jaccard mean:    {summary['jaccard']['mean']:.2f}")
        print(f"  taxonomy gap:    {summary['taxonomy_gap']['rate']:.0%}")
    if gold_eval and gold_eval["bow_precision"] is not None:
        print(f"  bow precision (gold): {gold_eval['bow_precision']:.0%}")
        print(f"  llm precision (gold): {gold_eval['llm_precision']:.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
