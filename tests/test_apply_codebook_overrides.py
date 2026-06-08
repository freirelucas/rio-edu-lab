"""Tests pro `analysis/49b_apply_codebook_overrides.py`.

Cobre load_overrides (validação schema) + apply_overrides (idempotência,
strict mode, replace-not-merge). Não toca disco real — usa tmp_path.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_49b():
    spec = importlib.util.spec_from_file_location(
        "apply_codebook", str(ANALYSIS / "49b_apply_codebook_overrides.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── load_overrides ───────────────────────────────────────────────────────


def test_load_overrides_happy_path(tmp_path):
    mod = _import_49b()
    p = tmp_path / "ov.yml"
    p.write_text(yaml.safe_dump({
        "version": 1,
        "overrides": {"item_a": {"domain": "educacao-basica", "confidence": 0.9}},
    }), encoding="utf-8")
    got = mod.load_overrides(p)
    assert got == {"item_a": {"domain": "educacao-basica", "confidence": 0.9}}


def test_load_overrides_missing_file_raises(tmp_path):
    mod = _import_49b()
    try:
        mod.load_overrides(tmp_path / "nope.yml")
        raise AssertionError("should have raised")
    except FileNotFoundError:
        pass


def test_load_overrides_wrong_version_raises(tmp_path):
    mod = _import_49b()
    p = tmp_path / "ov.yml"
    p.write_text(yaml.safe_dump({"version": 99, "overrides": {}}), encoding="utf-8")
    try:
        mod.load_overrides(p)
        raise AssertionError("should have raised")
    except ValueError as e:
        assert "version" in str(e)


def test_load_overrides_overrides_not_dict_raises(tmp_path):
    mod = _import_49b()
    p = tmp_path / "ov.yml"
    p.write_text(yaml.safe_dump({"version": 1, "overrides": ["a", "b"]}), encoding="utf-8")
    try:
        mod.load_overrides(p)
        raise AssertionError("should have raised")
    except ValueError as e:
        assert "overrides" in str(e)


def test_load_overrides_handles_missing_overrides_key(tmp_path):
    """version OK + no overrides → empty dict (não levanta)."""
    mod = _import_49b()
    p = tmp_path / "ov.yml"
    p.write_text(yaml.safe_dump({"version": 1}), encoding="utf-8")
    assert mod.load_overrides(p) == {}


def test_load_overrides_root_not_dict_raises(tmp_path):
    mod = _import_49b()
    p = tmp_path / "ov.yml"
    p.write_text(yaml.safe_dump(["just a list"]), encoding="utf-8")
    try:
        mod.load_overrides(p)
        raise AssertionError("should have raised")
    except ValueError as e:
        assert "root" in str(e).lower()


# ─── apply_overrides ──────────────────────────────────────────────────────


def _make_manifest(items: list[dict]) -> dict:
    return {"items": items}


def test_apply_overrides_writes_codebook():
    mod = _import_49b()
    manifest = _make_manifest([{"id": "x", "title": "X"}])
    overrides = {"x": {"domain": "educacao-basica", "confidence": 0.8}}
    n_applied, n_unchanged, missing = mod.apply_overrides(manifest, overrides)
    assert n_applied == 1
    assert n_unchanged == 0
    assert missing == []
    assert manifest["items"][0]["code_book"] == {"domain": "educacao-basica", "confidence": 0.8}


def test_apply_overrides_replaces_existing_codebook_not_merge():
    """Re-apply substitui completamente — não merge parcial."""
    mod = _import_49b()
    manifest = _make_manifest([{
        "id": "x",
        "code_book": {
            "domain": "saude",                       # vai sumir
            "key_variables": ["old"],                # vai sumir
            "temporal_coverage": "1990 (legacy)",    # vai sumir
        },
    }])
    overrides = {"x": {"domain": "educacao-basica", "confidence": 0.8}}
    n_applied, _, _ = mod.apply_overrides(manifest, overrides)
    assert n_applied == 1
    # Substituído inteiro: apenas chaves do override.
    cb = manifest["items"][0]["code_book"]
    assert cb == {"domain": "educacao-basica", "confidence": 0.8}
    assert "key_variables" not in cb
    assert "temporal_coverage" not in cb


def test_apply_overrides_idempotent_second_call_noop():
    mod = _import_49b()
    manifest = _make_manifest([{"id": "x"}])
    overrides = {"x": {"domain": "educacao-basica", "confidence": 0.8}}
    mod.apply_overrides(manifest, overrides)
    # Re-apply: já igual → unchanged.
    n_applied, n_unchanged, missing = mod.apply_overrides(manifest, overrides)
    assert n_applied == 0
    assert n_unchanged == 1
    assert missing == []


def test_apply_overrides_missing_item_id_collected_not_raised_by_default():
    mod = _import_49b()
    manifest = _make_manifest([{"id": "x"}])
    overrides = {"y": {"domain": "x"}, "z": {"domain": "y"}}
    n_applied, _, missing = mod.apply_overrides(manifest, overrides)
    assert n_applied == 0
    assert set(missing) == {"y", "z"}


def test_apply_overrides_strict_raises_on_missing_item():
    mod = _import_49b()
    manifest = _make_manifest([{"id": "x"}])
    overrides = {"missing_id": {"domain": "x"}}
    try:
        mod.apply_overrides(manifest, overrides, strict=True)
        raise AssertionError("should have raised")
    except KeyError as e:
        assert "missing_id" in str(e)


def test_apply_overrides_partial_mixed_hit_and_miss():
    mod = _import_49b()
    manifest = _make_manifest([
        {"id": "a"},
        {"id": "b", "code_book": {"domain": "saude"}},
    ])
    overrides = {
        "a": {"domain": "educacao-basica"},  # applied (no cb)
        "b": {"domain": "saude"},             # unchanged (cb equal)
        "c": {"domain": "x"},                  # missing
    }
    n_applied, n_unchanged, missing = mod.apply_overrides(manifest, overrides)
    assert n_applied == 1
    assert n_unchanged == 1
    assert missing == ["c"]


def test_apply_overrides_empty_overrides_is_noop():
    mod = _import_49b()
    manifest = _make_manifest([{"id": "x"}])
    n_applied, n_unchanged, missing = mod.apply_overrides(manifest, {})
    assert n_applied == 0
    assert n_unchanged == 0
    assert missing == []


# ─── integration sanity ───────────────────────────────────────────────────


def test_committed_overrides_yaml_loads_and_targets_real_items():
    """Sanity: o overrides YAML committed bate em items reais do manifest."""
    mod = _import_49b()
    ov_path = ROOT / "data" / "codebook_overrides.yml"
    mf_path = ROOT / "data" / "manifest.json"
    if not ov_path.exists() or not mf_path.exists():
        return  # CI sem os fixtures — skip
    overrides = mod.load_overrides(ov_path)
    manifest = json.loads(mf_path.read_text(encoding="utf-8"))
    item_ids = {it["id"] for it in manifest["items"]}
    bad = [oid for oid in overrides if oid not in item_ids]
    assert bad == [], f"overrides apontam pra item ids inexistentes: {bad[:5]}"
    # Schema básico: cada override tem domain, api_capability, confidence
    for oid, cb in overrides.items():
        assert "api_capability" in cb, f"{oid}: missing api_capability"
        assert "confidence" in cb, f"{oid}: missing confidence"
        assert "_source" in cb, f"{oid}: missing _source provenance"
