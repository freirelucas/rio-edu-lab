"""Tests pro `analysis/45c_apply_code_signals.py`.

Mocks YAML loading + funnel mutation. Não toca disco real.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_45c():
    spec = importlib.util.spec_from_file_location(
        "apply_code_signals", str(ANALYSIS / "45c_apply_code_signals.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── load_signals ─────────────────────────────────────────────────────────


def test_load_signals_happy_path(tmp_path):
    mod = _import_45c()
    p = tmp_path / "s.yml"
    p.write_text(yaml.safe_dump({
        "version": 1,
        "signals": {"W1": {"doi": "10.x/y", "n_code_hits": 0}},
    }), encoding="utf-8")
    got = mod.load_signals(p)
    assert got == {"W1": {"doi": "10.x/y", "n_code_hits": 0}}


def test_load_signals_missing_file_raises(tmp_path):
    mod = _import_45c()
    try:
        mod.load_signals(tmp_path / "nope.yml")
        raise AssertionError("should have raised")
    except FileNotFoundError:
        pass


def test_load_signals_wrong_version_raises(tmp_path):
    mod = _import_45c()
    p = tmp_path / "s.yml"
    p.write_text(yaml.safe_dump({"version": 99, "signals": {}}), encoding="utf-8")
    try:
        mod.load_signals(p)
        raise AssertionError("should have raised")
    except ValueError as e:
        assert "version" in str(e)


def test_load_signals_handles_missing_signals_key(tmp_path):
    """version OK + no signals → empty dict."""
    mod = _import_45c()
    p = tmp_path / "s.yml"
    p.write_text(yaml.safe_dump({"version": 1}), encoding="utf-8")
    assert mod.load_signals(p) == {}


def test_load_signals_signals_not_dict_raises(tmp_path):
    mod = _import_45c()
    p = tmp_path / "s.yml"
    p.write_text(yaml.safe_dump({"version": 1, "signals": ["a"]}), encoding="utf-8")
    try:
        mod.load_signals(p)
        raise AssertionError("should have raised")
    except ValueError as e:
        assert "signals" in str(e)


# ─── apply_signals ────────────────────────────────────────────────────────


def test_apply_signals_writes_code_signal():
    mod = _import_45c()
    cands = [{"openalex_id": "W1", "title": "X"}]
    signals = {"W1": {"n_code_hits": 3, "top_repos": ["a/b"]}}
    n_applied, n_unchanged, missing = mod.apply_signals(cands, signals)
    assert n_applied == 1
    assert n_unchanged == 0
    assert missing == []
    assert cands[0]["code_signal"] == {"n_code_hits": 3, "top_repos": ["a/b"]}


def test_apply_signals_idempotent():
    mod = _import_45c()
    cands = [{"openalex_id": "W1"}]
    sig = {"W1": {"n_code_hits": 0}}
    mod.apply_signals(cands, sig)
    n_applied, n_unchanged, missing = mod.apply_signals(cands, sig)
    assert n_applied == 0
    assert n_unchanged == 1
    assert missing == []


def test_apply_signals_replaces_not_merge():
    """Re-apply substitui inteiro — não merge parcial."""
    mod = _import_45c()
    cands = [{
        "openalex_id": "W1",
        "code_signal": {"old_field": "x", "n_code_hits": 5},
    }]
    signals = {"W1": {"n_code_hits": 0}}  # sem old_field
    n_applied, _, _ = mod.apply_signals(cands, signals)
    assert n_applied == 1
    assert cands[0]["code_signal"] == {"n_code_hits": 0}
    assert "old_field" not in cands[0]["code_signal"]


def test_apply_signals_missing_collected_not_raised_by_default():
    mod = _import_45c()
    cands = [{"openalex_id": "W1"}]
    signals = {"W2": {"n_code_hits": 0}, "W3": {"n_code_hits": 1}}
    n_applied, _, missing = mod.apply_signals(cands, signals)
    assert n_applied == 0
    assert set(missing) == {"W2", "W3"}


def test_apply_signals_strict_raises_on_missing():
    mod = _import_45c()
    cands = [{"openalex_id": "W1"}]
    try:
        mod.apply_signals(cands, {"missing": {"n_code_hits": 0}}, strict=True)
        raise AssertionError("should have raised")
    except KeyError as e:
        assert "missing" in str(e)


def test_apply_signals_ignores_candidates_without_openalex_id():
    """Candidates sem openalex_id key (corner case) não devem virar key None."""
    mod = _import_45c()
    cands = [
        {"openalex_id": "W1"},
        {"title": "no id"},  # no openalex_id at all
        {"openalex_id": None, "title": "explicit None"},
    ]
    signals = {"W1": {"n_code_hits": 0}}
    n_applied, _, missing = mod.apply_signals(cands, signals)
    assert n_applied == 1
    assert missing == []
    # The other two candidates não receberam code_signal
    assert "code_signal" not in cands[1]
    assert "code_signal" not in cands[2]


def test_apply_signals_empty_signals_is_noop():
    mod = _import_45c()
    cands = [{"openalex_id": "W1"}]
    n_applied, n_unchanged, missing = mod.apply_signals(cands, {})
    assert (n_applied, n_unchanged, missing) == (0, 0, [])


def test_apply_signals_normalizes_url_vs_bare_id():
    """Funnel armazena 'https://openalex.org/W1'; YAML pode usar 'W1'. Match."""
    mod = _import_45c()
    cands = [{"openalex_id": "https://openalex.org/W1"}]
    signals = {"W1": {"n_code_hits": 0}}
    n_applied, _, missing = mod.apply_signals(cands, signals)
    assert n_applied == 1
    assert missing == []
    assert cands[0]["code_signal"] == {"n_code_hits": 0}


def test_apply_signals_normalizes_both_with_urls():
    """YAML também pode usar URL completa; match continua."""
    mod = _import_45c()
    cands = [{"openalex_id": "https://openalex.org/W2"}]
    signals = {"https://openalex.org/W2": {"n_code_hits": 5}}
    n_applied, _, _ = mod.apply_signals(cands, signals)
    assert n_applied == 1
