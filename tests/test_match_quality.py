"""Tests pra `analysis/51_match_quality_report.py:compute_summary`.

Fixtures simulam o gold-set; valida P/R, confusion matrix, score bands, failure modes,
e graceful degradation quando ninguém preencheu labels.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ANALYSIS = Path(__file__).resolve().parent.parent / "analysis"


def _import_51():
    """Importa o módulo 51 (nome começa com dígito → import normal não funciona)."""
    path = ANALYSIS / "51_match_quality_report.py"
    spec = importlib.util.spec_from_file_location("match_quality_report", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_metric_basic():
    mq = _import_51()
    p, r = mq.metric(tp=3, fp=1, fn=2)
    assert abs(p - 0.75) < 1e-9
    assert abs(r - 0.6) < 1e-9


def test_metric_zero_denom_returns_none():
    mq = _import_51()
    p, r = mq.metric(tp=0, fp=0, fn=0)
    assert p is None and r is None


def test_compute_summary_per_category_precision_recall():
    """Fixture com 2 cats (A, B); cada uma tem TP e FP conhecidos."""
    mq = _import_51()
    labels = [
        # 3 corretos pra A
        {"predicted_category": "A", "true_category": None, "is_correct": True, "score": 12.0},
        {"predicted_category": "A", "true_category": None, "is_correct": True, "score": 10.0},
        {"predicted_category": "A", "true_category": None, "is_correct": True, "score": 8.0},
        # 1 errado pra A (true era B)
        {"predicted_category": "A", "true_category": "B", "is_correct": False, "score": 6.0},
        # 1 correto pra B
        {"predicted_category": "B", "true_category": None, "is_correct": True, "score": 11.0},
        # 1 errado pra B (true era A)
        {"predicted_category": "B", "true_category": "A", "is_correct": False, "score": 5.5},
        # 1 unsure (não conta)
        {"predicted_category": "A", "true_category": None, "is_correct": "unsure", "score": 9.0},
    ]
    s = mq.compute_summary(labels)

    assert s["n_labels"] == 7
    assert s["n_correct"] == 4
    assert s["n_wrong"] == 2
    assert s["n_unsure"] == 1
    assert s["n_unlabeled"] == 0
    assert s["n_decided"] == 6

    # Per-category
    a = s["per_category"]["A"]
    assert a["tp"] == 3 and a["fp"] == 1 and a["fn"] == 1
    assert abs(a["precision"] - 0.75) < 1e-9    # 3/(3+1)
    assert abs(a["recall"] - 0.75) < 1e-9       # 3/(3+1)

    b = s["per_category"]["B"]
    assert b["tp"] == 1 and b["fp"] == 1 and b["fn"] == 1
    assert abs(b["precision"] - 0.5) < 1e-9
    assert abs(b["recall"] - 0.5) < 1e-9


def test_compute_summary_all_unsure_graceful():
    """Edge case: todos unsure → P/R None, sem crash."""
    mq = _import_51()
    labels = [
        {"predicted_category": "A", "is_correct": "unsure", "score": 10.0},
        {"predicted_category": "B", "is_correct": "unsure", "score": 8.0},
    ]
    s = mq.compute_summary(labels)
    assert s["n_decided"] == 0
    assert s["overall_precision"] is None
    # Per-cat existe mas P/R None
    for cat_metrics in s["per_category"].values():
        assert cat_metrics["precision"] is None
        assert cat_metrics["recall"] is None


def test_compute_summary_unlabeled_skipped():
    """Labels com is_correct=null não contam em decided."""
    mq = _import_51()
    labels = [
        {"predicted_category": "A", "is_correct": None, "score": 10.0},
        {"predicted_category": "A", "is_correct": True, "score": 12.0},
    ]
    s = mq.compute_summary(labels)
    assert s["n_unlabeled"] == 1
    assert s["n_correct"] == 1
    assert s["n_decided"] == 1


def test_score_bands_split_correctly():
    mq = _import_51()
    labels = [
        # banda 5-7
        {"predicted_category": "A", "is_correct": True, "score": 5.5},
        {"predicted_category": "A", "is_correct": False, "true_category": "B", "score": 6.5},
        # banda 10-15
        {"predicted_category": "A", "is_correct": True, "score": 12.0},
    ]
    s = mq.compute_summary(labels)
    bands = {b["band"]: b for b in s["score_bands"]}
    assert bands["5-7"]["n_labeled"] == 2
    assert bands["5-7"]["n_correct"] == 1
    assert bands["5-7"]["n_wrong"] == 1
    assert bands["5-7"]["precision"] == 0.5
    assert bands["10-15"]["n_labeled"] == 1
    assert bands["10-15"]["n_correct"] == 1


def test_failure_mode_taxonomy_gap():
    """FP com true_category=null → tag = taxonomy-gap."""
    mq = _import_51()
    labels = [
        {"predicted_category": "performance-aggregated", "true_category": None,
         "is_correct": False, "score": 6.0},
    ]
    s = mq.compute_summary(labels)
    assert s["failure_modes"] == {"taxonomy-gap": 1}


def test_failure_mode_cross_domain_leak():
    """Predito edu, true é external → tag = cross-domain-leak."""
    mq = _import_51()
    labels = [
        {"predicted_category": "performance-aggregated", "true_category": "microdata-student",
         "is_correct": False, "score": 7.0},
    ]
    s = mq.compute_summary(labels)
    assert s["failure_modes"] == {"cross-domain-leak": 1}
