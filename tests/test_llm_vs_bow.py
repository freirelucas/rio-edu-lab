"""Tests pro `analysis/56_llm_vs_bow_compare.py`.

Cobre: helpers de top-1 / set extraction, Jaccard, compute_comparison
sobre fixtures conhecidas, compute_gold_set_eval, render_report_md (smoke).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ANALYSIS = Path(__file__).resolve().parent.parent / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_56():
    """Importa o 56 (nome começa com dígito → importlib)."""
    spec = importlib.util.spec_from_file_location(
        "llm_vs_bow", str(ANALYSIS / "56_llm_vs_bow_compare.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── helpers (top1 / sets / jaccard) ──────────────────────────────────────

def test_bow_top1_picks_highest_score():
    cmp = _import_56()
    c = {
        "suggested_requirements": [
            {"category_id": "A", "score": 5.0},
            {"category_id": "B", "score": 10.0},
            {"category_id": "C", "score": 3.0},
        ]
    }
    assert cmp._bow_top1(c) == "B"


def test_bow_top1_returns_none_when_empty():
    cmp = _import_56()
    assert cmp._bow_top1({}) is None
    assert cmp._bow_top1({"suggested_requirements": []}) is None


def test_llm_top1_picks_highest_confidence():
    cmp = _import_56()
    c = {
        "llm_suggested_requirements": [
            {"category_id": "X", "confidence": 0.5},
            {"category_id": "Y", "confidence": 0.9},
        ]
    }
    assert cmp._llm_top1(c) == "Y"


def test_bow_set_extracts_all_cats():
    cmp = _import_56()
    c = {
        "suggested_requirements": [
            {"category_id": "A"}, {"category_id": "B"}, {"category_id": "A"},
        ]
    }
    assert cmp._bow_set(c) == {"A", "B"}


def test_jaccard_identical():
    cmp = _import_56()
    assert cmp._jaccard({"A", "B"}, {"A", "B"}) == 1.0


def test_jaccard_disjoint():
    cmp = _import_56()
    assert cmp._jaccard({"A"}, {"B"}) == 0.0


def test_jaccard_partial():
    cmp = _import_56()
    # |{"A","B"} ∩ {"B","C"}| / |{"A","B","C"}| = 1/3
    assert abs(cmp._jaccard({"A", "B"}, {"B", "C"}) - 1 / 3) < 1e-9


def test_jaccard_empty_both():
    cmp = _import_56()
    assert cmp._jaccard(set(), set()) == 1.0


def test_jaccard_one_empty():
    cmp = _import_56()
    assert cmp._jaccard({"A"}, set()) == 0.0


# ─── compute_comparison ───────────────────────────────────────────────────

def _candidate(oid: str, citations: int = 100, bow=None, llm=None, gap=False, gap_desc=None):
    return {
        "openalex_id": f"https://openalex.org/{oid}",
        "title": f"Paper {oid}",
        "citations": citations,
        "abstract": f"Abstract for {oid}",
        "suggested_requirements": bow or [],
        "llm_suggested_requirements": llm or [],
        "llm_taxonomy_gap": gap,
        "llm_gap_description": gap_desc,
    }


def test_compute_comparison_empty_both():
    cmp = _import_56()
    # Sem candidates com ambos signals — agreement rate é None, sem crash.
    result = cmp.compute_comparison([_candidate("W1")])
    assert result["n_with_both"] == 0
    assert result["top1_agreement"]["rate"] is None


def test_compute_comparison_perfect_agreement():
    """Bow e LLM concordam em top-1 e set total → agreement=100%, jaccard=1."""
    cmp = _import_56()
    candidates = [
        _candidate(
            "W1",
            bow=[{"category_id": "performance-aggregated", "score": 10}],
            llm=[{"category_id": "performance-aggregated", "confidence": 0.9}],
        ),
        _candidate(
            "W2",
            bow=[{"category_id": "geometry-schools", "score": 8}],
            llm=[{"category_id": "geometry-schools", "confidence": 0.85}],
        ),
    ]
    r = cmp.compute_comparison(candidates)
    assert r["n_with_both"] == 2
    assert r["top1_agreement"]["n_agree"] == 2
    assert r["top1_agreement"]["rate"] == 1.0
    assert r["jaccard"]["mean"] == 1.0


def test_compute_comparison_full_disagreement():
    cmp = _import_56()
    candidates = [
        _candidate(
            "W1",
            bow=[{"category_id": "performance-aggregated", "score": 10}],
            llm=[{"category_id": "ses-aggregated", "confidence": 0.9}],
        ),
    ]
    r = cmp.compute_comparison(candidates)
    assert r["top1_agreement"]["rate"] == 0.0
    assert r["jaccard"]["mean"] == 0.0
    assert len(r["disagreement_examples"]) == 1
    ex = r["disagreement_examples"][0]
    assert ex["bow_top1"] == "performance-aggregated"
    assert ex["llm_top1"] == "ses-aggregated"


def test_compute_comparison_taxonomy_gap_aggregated():
    cmp = _import_56()
    candidates = [
        _candidate("W1",
                   bow=[{"category_id": "performance-aggregated", "score": 8}],
                   llm=[{"category_id": "performance-aggregated", "confidence": 0.9}],
                   gap=True, gap_desc="needs healthcare access data"),
        _candidate("W2",
                   bow=[{"category_id": "ses-aggregated", "score": 7}],
                   llm=[{"category_id": "ses-aggregated", "confidence": 0.8}],
                   gap=False),
    ]
    r = cmp.compute_comparison(candidates)
    assert r["taxonomy_gap"]["n_flagged"] == 1
    assert r["taxonomy_gap"]["rate"] == 0.5
    assert len(r["taxonomy_gap"]["examples"]) == 1
    assert r["taxonomy_gap"]["examples"][0]["gap_description"] == "needs healthcare access data"


def test_compute_comparison_confusion_matrix():
    """Confusion matrix conta corretamente bow_top1 × llm_top1."""
    cmp = _import_56()
    candidates = [
        _candidate("W1",
                   bow=[{"category_id": "performance-aggregated", "score": 8}],
                   llm=[{"category_id": "ses-aggregated", "confidence": 0.9}]),
        _candidate("W2",
                   bow=[{"category_id": "performance-aggregated", "score": 7}],
                   llm=[{"category_id": "ses-aggregated", "confidence": 0.85}]),
        _candidate("W3",
                   bow=[{"category_id": "performance-aggregated", "score": 9}],
                   llm=[{"category_id": "performance-aggregated", "confidence": 0.9}]),
    ]
    r = cmp.compute_comparison(candidates)
    cm = r["confusion_matrix"]
    assert cm["performance-aggregated"]["ses-aggregated"] == 2
    assert cm["performance-aggregated"]["performance-aggregated"] == 1


def test_compute_comparison_disagreement_sorted_by_citations():
    cmp = _import_56()
    candidates = [
        _candidate("W1", citations=50,
                   bow=[{"category_id": "A", "score": 8}],
                   llm=[{"category_id": "B", "confidence": 0.9}]),
        _candidate("W2", citations=500,
                   bow=[{"category_id": "C", "score": 8}],
                   llm=[{"category_id": "D", "confidence": 0.9}]),
        _candidate("W3", citations=100,
                   bow=[{"category_id": "E", "score": 8}],
                   llm=[{"category_id": "F", "confidence": 0.9}]),
    ]
    r = cmp.compute_comparison(candidates)
    da = r["disagreement_examples"]
    assert len(da) == 3
    # Order: W2 (500), W3 (100), W1 (50)
    assert da[0]["citations"] == 500
    assert da[1]["citations"] == 100
    assert da[2]["citations"] == 50


# ─── compute_gold_set_eval ────────────────────────────────────────────────

def test_gold_eval_returns_none_when_no_decided_labels():
    cmp = _import_56()
    labels = [
        {"openalex_id": "W1", "is_correct": None},
        {"openalex_id": "W2", "is_correct": "unsure"},
    ]
    assert cmp.compute_gold_set_eval([], labels) is None


def test_gold_eval_returns_none_when_no_overlap_with_llm():
    """Gold tem labels mas candidates dele não foram processados pelo LLM."""
    cmp = _import_56()
    labels = [
        {"openalex_id": "https://openalex.org/W1",
         "predicted_category": "A", "is_correct": True},
    ]
    candidates = [_candidate("W1")]  # sem llm_suggested_requirements
    assert cmp.compute_gold_set_eval(candidates, labels) is None


def test_gold_eval_computes_precision_per_method():
    cmp = _import_56()
    # 2 labels decided: 1 true, 1 false (com true_category)
    labels = [
        {"openalex_id": "https://openalex.org/W1",
         "predicted_category": "performance-aggregated",
         "true_category": None,
         "is_correct": True},
        {"openalex_id": "https://openalex.org/W2",
         "predicted_category": "performance-aggregated",
         "true_category": "ses-aggregated",
         "is_correct": False},
    ]
    candidates = [
        _candidate("W1",
                   bow=[{"category_id": "performance-aggregated", "score": 8}],
                   llm=[{"category_id": "performance-aggregated", "confidence": 0.9}]),
        _candidate("W2",
                   bow=[{"category_id": "performance-aggregated", "score": 6}],
                   llm=[{"category_id": "ses-aggregated", "confidence": 0.85}]),
    ]
    result = cmp.compute_gold_set_eval(candidates, labels)
    assert result is not None
    assert result["n_gold_decided"] == 2
    assert result["n_overlap_with_llm"] == 2
    # Bow: 1 TP (W1) + 1 FP (W2) → 50%
    assert result["bow_tp"] == 1
    assert result["bow_fp"] == 1
    assert result["bow_precision"] == 0.5
    # LLM: W1 (no true_category, is_correct=True, llm=performance-agg=predicted_bow) → TP
    #      W2 (true=ses, llm=ses) → TP
    assert result["llm_tp"] == 2
    assert result["llm_fp"] == 0
    assert result["llm_precision"] == 1.0


# ─── render_report_md (smoke) ─────────────────────────────────────────────

def test_render_report_handles_empty_both():
    """Sem candidates com ambos → admonition pedindo pra rodar 55."""
    cmp = _import_56()
    summary = cmp.compute_comparison([])
    summary["funnel_size"] = 0
    report = cmp.render_report_md(summary, gold_eval=None)
    assert "Nenhum candidate tem ambos signals" in report


def test_render_report_includes_agreement_when_data_present():
    cmp = _import_56()
    candidates = [
        _candidate("W1",
                   bow=[{"category_id": "A", "score": 8}],
                   llm=[{"category_id": "A", "confidence": 0.9}]),
    ]
    summary = cmp.compute_comparison(candidates)
    summary["funnel_size"] = 1
    report = cmp.render_report_md(summary, gold_eval=None)
    assert "Top-1 agreement" in report
    assert "Confusion matrix" in report


def test_render_report_gold_eval_section():
    """Gold-set eval renderiza tabela P bow vs llm."""
    cmp = _import_56()
    summary = cmp.compute_comparison([
        _candidate("W1",
                   bow=[{"category_id": "A", "score": 8}],
                   llm=[{"category_id": "A", "confidence": 0.9}])
    ])
    summary["funnel_size"] = 1
    gold_eval = {
        "n_gold_decided": 10,
        "n_overlap_with_llm": 5,
        "bow_tp": 2, "bow_fp": 3, "bow_precision": 0.4,
        "llm_tp": 4, "llm_fp": 1, "llm_precision": 0.8,
    }
    report = cmp.render_report_md(summary, gold_eval)
    assert "Precision contra gold-set" in report
    assert "bow" in report
    assert "llm" in report
    # Diff > 5pp triggers tip about trocando inferência principal
    assert "trocar inferência principal" in report
