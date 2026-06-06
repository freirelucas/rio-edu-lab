"""Compute precision/recall por categoria + confusion matrix + failure modes
sobre o gold set (`data/match_quality_gold.yml`).

Outputs:
  - `data/processed/match_quality_summary.json` — machine-readable digest.
  - `docs/match-quality.md` — site-rendered report (drift-checked no CI).

Compute_summary() é pure e testável (`tests/test_match_quality.py`).

Uso:
  python3 analysis/51_match_quality_report.py
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
GOLD = ROOT / "data" / "match_quality_gold.yml"
SUMMARY_JSON = ROOT / "data" / "processed" / "match_quality_summary.json"
REPORT_MD = ROOT / "docs" / "match-quality.md"

EXTERNAL_CATS = {
    "microdata-student", "microdata-household",
    "longitudinal-cohort", "travel-network",
}
SCORE_BANDS = [(5.0, 7.0), (7.0, 10.0), (10.0, 15.0), (15.0, 100.0)]


def metric(tp: int, fp: int, fn: int) -> tuple[float | None, float | None]:
    """Precision = TP/(TP+FP); Recall = TP/(TP+FN). None se denom = 0."""
    p = tp / (tp + fp) if (tp + fp) > 0 else None
    r = tp / (tp + fn) if (tp + fn) > 0 else None
    return p, r


def _failure_mode(predicted: str | None, true: str | None) -> str:
    """Tag de failure mode pra um FP."""
    if true is None:
        return "taxonomy-gap"
    if true in EXTERNAL_CATS and predicted not in EXTERNAL_CATS:
        return "cross-domain-leak"
    if predicted in EXTERNAL_CATS and true not in EXTERNAL_CATS:
        return "external-misclassified"
    if predicted and true and predicted.startswith(true.split("-")[0]):
        return "granularity-mismatch"  # ex: ses-aggregated vs performance-aggregated
    return "category-confusion"


def compute_summary(labels: list[dict]) -> dict:
    """Pure: gold labels → summary dict (precision/recall/confusion/bands/failures)."""
    n_correct = sum(1 for lbl in labels if lbl.get("is_correct") is True)
    n_wrong = sum(1 for lbl in labels if lbl.get("is_correct") is False)
    n_unsure = sum(1 for lbl in labels if lbl.get("is_correct") == "unsure")
    n_unlabeled = sum(1 for lbl in labels if lbl.get("is_correct") is None)
    n_decided = n_correct + n_wrong

    # Categorias mencionadas (em predicted OU true).
    all_cats = sorted({
        cat
        for lbl in labels
        for cat in (lbl.get("predicted_category"), lbl.get("true_category"))
        if cat
    })

    per_cat: dict[str, dict] = {}
    for cat in all_cats:
        tp = sum(1 for lbl in labels if lbl.get("predicted_category") == cat and lbl.get("is_correct") is True)
        fp = sum(1 for lbl in labels if lbl.get("predicted_category") == cat and lbl.get("is_correct") is False)
        fn = sum(
            1 for lbl in labels
            if lbl.get("predicted_category") != cat
            and lbl.get("true_category") == cat
            and lbl.get("is_correct") is False
        )
        n_predicted = sum(
            1 for lbl in labels
            if lbl.get("predicted_category") == cat and lbl.get("is_correct") in (True, False)
        )
        p, r = metric(tp, fp, fn)
        per_cat[cat] = {
            "n_predicted_labeled": n_predicted,
            "tp": tp, "fp": fp, "fn": fn,
            "precision": p, "recall": r,
        }

    # Confusion matrix: predito → true.
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for lbl in labels:
        pred = lbl.get("predicted_category")
        if lbl.get("is_correct") is True:
            confusion[pred][pred] += 1
        elif lbl.get("is_correct") is False:
            true = lbl.get("true_category") or "(unspecified)"
            confusion[pred][true] += 1
    confusion_serializable = {k: dict(v) for k, v in confusion.items()}

    # Score bands.
    score_bands: list[dict] = []
    for lo, hi in SCORE_BANDS:
        in_band = [
            lbl for lbl in labels
            if lbl.get("is_correct") in (True, False) and lo <= float(lbl.get("score") or 0) < hi
        ]
        n_c = sum(1 for lbl in in_band if lbl.get("is_correct") is True)
        n_w = sum(1 for lbl in in_band if lbl.get("is_correct") is False)
        score_bands.append({
            "band": f"{lo:g}-{hi:g}",
            "n_labeled": len(in_band),
            "n_correct": n_c,
            "n_wrong": n_w,
            "precision": (n_c / (n_c + n_w)) if (n_c + n_w) > 0 else None,
        })

    # Failure modes (tags por FP).
    fail_tag_counts: Counter = Counter()
    fail_examples: list[dict] = []
    for lbl in labels:
        if lbl.get("is_correct") is not False:
            continue
        tag = _failure_mode(lbl.get("predicted_category"), lbl.get("true_category"))
        fail_tag_counts[tag] += 1
        fail_examples.append({
            "openalex_id": lbl.get("openalex_id"),
            "title": lbl.get("title"),
            "predicted_category": lbl.get("predicted_category"),
            "true_category": lbl.get("true_category"),
            "score": lbl.get("score"),
            "tag": tag,
        })

    overall_precision = (n_correct / n_decided) if n_decided > 0 else None

    return {
        "n_labels": len(labels),
        "n_correct": n_correct,
        "n_wrong": n_wrong,
        "n_unsure": n_unsure,
        "n_unlabeled": n_unlabeled,
        "n_decided": n_decided,
        "overall_precision": overall_precision,
        "per_category": per_cat,
        "confusion_matrix": confusion_serializable,
        "score_bands": score_bands,
        "failure_modes": dict(fail_tag_counts),
        "failure_examples": fail_examples[:20],  # cap pra MD não estourar
    }


def render_report_md(summary: dict, sampled_from_commit: str | None) -> str:
    """Pure: summary → markdown report."""
    lines: list[str] = []
    lines.append("---\n")
    lines.append('title: "Qualidade do match"\n')
    lines.append('description: "Precision/recall por categoria + confusion matrix sobre gold-set de ~50 pairs etiquetados à mão."\n')
    lines.append("---\n\n")
    lines.append("# Qualidade do match (paper → categoria)\n\n")
    lines.append(
        f"_Relatório gerado por `analysis/51_match_quality_report.py` sobre "
        f"`data/match_quality_gold.yml` (sample do funnel commit `{sampled_from_commit}`)._\n\n"
    )

    n_total = summary["n_labels"]
    n_decided = summary["n_decided"]
    n_unsure = summary["n_unsure"]
    n_unlabeled = summary["n_unlabeled"]

    lines.append("## Cobertura do labeling\n\n")
    lines.append(f"- **Total de labels no sample:** {n_total}\n")
    lines.append(f"- **Decididos (correct + wrong):** {n_decided}\n")
    lines.append(f"- **Corretos:** {summary['n_correct']}\n")
    lines.append(f"- **Errados:** {summary['n_wrong']}\n")
    pct_unsure = (100 * n_unsure / n_total) if n_total else 0
    lines.append(f"- **Unsure:** {n_unsure} ({pct_unsure:.0f}% — needs-second-opinion)\n")
    lines.append(f"- **Não preenchidos:** {n_unlabeled}\n\n")

    if n_decided == 0:
        lines.append(
            "\n!!! note\n"
            "    Nenhum label decidido ainda — preencha `is_correct` em "
            "`data/match_quality_gold.yml` (true/false/\"unsure\") e rerode "
            "`python3 analysis/51_match_quality_report.py`.\n"
        )
        return "".join(lines)

    op = summary["overall_precision"]
    lines.append(f"### Precision geral\n\n**{op:.0%}** sobre {n_decided} labels decididos.\n\n")

    # Per-cat table
    lines.append("## Precision/recall por categoria\n\n")
    lines.append("| Categoria | N predicted | TP | FP | FN | Precision | Recall |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|\n")
    for cat, m in summary["per_category"].items():
        p = f"{m['precision']:.0%}" if m["precision"] is not None else "—"
        r = f"{m['recall']:.0%}" if m["recall"] is not None else "—"
        lines.append(f"| `{cat}` | {m['n_predicted_labeled']} | {m['tp']} | {m['fp']} | {m['fn']} | {p} | {r} |\n")
    lines.append("\n")

    # Score bands
    lines.append("## Confidence por band de score\n\n")
    lines.append("| Score band | N labeled | Correct | Wrong | Precision |\n")
    lines.append("|---|---:|---:|---:|---:|\n")
    for b in summary["score_bands"]:
        p = f"{b['precision']:.0%}" if b["precision"] is not None else "—"
        lines.append(f"| {b['band']} | {b['n_labeled']} | {b['n_correct']} | {b['n_wrong']} | {p} |\n")
    lines.append("\n")

    # Confusion matrix
    cm = summary["confusion_matrix"]
    if cm:
        all_in_cm = sorted({k for k in cm.keys()} | {t for row in cm.values() for t in row.keys()})
        lines.append("## Confusion matrix (predito \\ true)\n\n")
        lines.append("| predito \\ true | " + " | ".join(f"`{t}`" for t in all_in_cm) + " |\n")
        lines.append("|---|" + "---:|" * len(all_in_cm) + "\n")
        for pred in all_in_cm:
            row_cells = [str(cm.get(pred, {}).get(t, 0)) for t in all_in_cm]
            lines.append(f"| `{pred}` | " + " | ".join(row_cells) + " |\n")
        lines.append("\n")

    # Failure modes
    fm = summary["failure_modes"]
    if fm:
        lines.append("## Failure modes\n\n")
        for tag, n in sorted(fm.items(), key=lambda kv: -kv[1]):
            lines.append(f"- **`{tag}`**: {n}\n")
        lines.append("\n")

    fe = summary["failure_examples"]
    if fe:
        lines.append("### Exemplos (até 20)\n\n")
        lines.append("| Predicted | True | Score | Tag | Title |\n")
        lines.append("|---|---|---:|---|---|\n")
        for x in fe:
            t = (x.get("title") or "")[:60]
            lines.append(
                f"| `{x['predicted_category']}` | `{x.get('true_category') or '—'}` | "
                f"{x.get('score'):.1f} | `{x['tag']}` | {t} |\n"
            )
        lines.append("\n")

    return "".join(lines)


def main() -> int:
    if not GOLD.exists():
        print(f"missing {GOLD.relative_to(ROOT)} — rode 50_sample_gold_set.py primeiro", file=sys.stderr)
        return 1

    gold = yaml.safe_load(GOLD.read_text(encoding="utf-8")) or {}
    labels = gold.get("labels") or []
    print(f"loaded {len(labels)} labels from {GOLD.relative_to(ROOT)}")

    summary = compute_summary(labels)
    summary["sampled_from_funnel_commit"] = gold.get("sampled_from_funnel_commit")

    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {SUMMARY_JSON.relative_to(ROOT)}")

    report = render_report_md(summary, gold.get("sampled_from_funnel_commit"))
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text(report, encoding="utf-8")
    print(f"wrote {REPORT_MD.relative_to(ROOT)}")

    print("\n=== summary ===")
    print(f"  decided: {summary['n_decided']}/{summary['n_labels']}")
    if summary["overall_precision"] is not None:
        print(f"  overall precision: {summary['overall_precision']:.0%}")
    if summary["failure_modes"]:
        print(f"  failure modes: {summary['failure_modes']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
