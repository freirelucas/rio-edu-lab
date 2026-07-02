"""Tests pro `analysis/67_render_sala.py` (Sala de Operação pública)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_67():
    spec = importlib.util.spec_from_file_location("render_sala", str(ANALYSIS / "67_render_sala.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seed_processed(tmp_path):
    """Cria JSONs mínimos pra render não depender do repo real."""
    p = tmp_path / "data" / "processed"
    p.mkdir(parents=True)
    (p / "funnel_state.json").write_text(json.dumps({
        "stage1_candidates": 2266, "stage2_with_requirements": 482,
        "data_rio_total": 9855, "data_rio_active": 4, "data_rio_orphan": 9851,
    }), encoding="utf-8")
    (p / "papers_catalog_summary.json").write_text(json.dumps({
        "n_papers": 18, "by_replication_status": {"full": 1, "partial": 2, "pending": 12},
    }), encoding="utf-8")
    (p / "curatorial_inbox.json").write_text(json.dumps([
        {"title": "BR paper", "is_brazilian": True, "citations": 200, "priority_score": 22.8},
        {"title": "US paper", "is_brazilian": False, "citations": 5000, "priority_score": 30.0},
    ]), encoding="utf-8")
    (p / "top_summary.json").write_text(json.dumps({
        "n_papers": 18, "mean_total_score": 4.5, "max_possible": 16,
    }), encoding="utf-8")
    (p / "provenance_summary.json").write_text(json.dumps([
        {"paper_id": "theil-1967-economics", "audit_chain_complete": True,
         "n_data_sources": 2, "n_scripts": 4, "n_processed_outputs": 3},
        {"paper_id": "pereira-2019-ipea", "audit_chain_complete": False,
         "n_data_sources": 3, "n_scripts": 3, "n_processed_outputs": 0},
    ]), encoding="utf-8")
    (p / "paper_dataset_links.json").write_text(json.dumps([
        {"title": "Ingersoll", "n_dataset_refs": 2},
    ]), encoding="utf-8")
    return p


def test_render_includes_kpis(tmp_path, monkeypatch):
    m = _import_67()
    _seed_processed(tmp_path)
    monkeypatch.setattr(m, "PROCESSED", tmp_path / "data" / "processed")
    md = m.render()
    assert "2266" in md          # candidates
    assert "18" in md            # catálogo (from catalog summary, fresher)
    assert "1 full" in md        # replication status honest
    assert "2 partial" in md


def test_render_has_live_badges(tmp_path, monkeypatch):
    m = _import_67()
    _seed_processed(tmp_path)
    monkeypatch.setattr(m, "PROCESSED", tmp_path / "data" / "processed")
    md = m.render()
    # Live GitHub Actions status badges (imagens, sempre atuais)
    assert "badge.svg" in md
    assert "s3star-audit.yml" in md
    assert "s4-scout.yml" in md
    assert "snowball.yml" in md  # dormente mas listado


def test_render_observar_vs_agir(tmp_path, monkeypatch):
    """A distinção central: pública pra observar, GitHub autentica pra agir."""
    m = _import_67()
    _seed_processed(tmp_path)
    monkeypatch.setattr(m, "PROCESSED", tmp_path / "data" / "processed")
    md = m.render()
    assert "Observar" in md
    assert "Agir" in md
    assert "control room" in md.lower() or "sala de controle" in md.lower()


def test_render_inbox_and_provenance(tmp_path, monkeypatch):
    m = _import_67()
    _seed_processed(tmp_path)
    monkeypatch.setattr(m, "PROCESSED", tmp_path / "data" / "processed")
    md = m.render()
    assert "BR paper" in md or "US paper" in md
    assert "🇧🇷" in md
    # provenance chain status
    assert "✅" in md  # theil complete
    assert "theil-1967-economics" in md


def test_render_handles_missing_jsons(tmp_path, monkeypatch):
    """Sem JSONs → não crasha, usa fallbacks."""
    m = _import_67()
    empty = tmp_path / "data" / "processed"
    empty.mkdir(parents=True)
    monkeypatch.setattr(m, "PROCESSED", empty)
    md = m.render()
    assert "Sala de Operação" in md  # renderiza mesmo vazio
    assert "—" in md  # fallback markers


def test_render_deterministic(tmp_path, monkeypatch):
    """Mesmos JSONs → mesmo output (drift-check safe)."""
    m = _import_67()
    _seed_processed(tmp_path)
    monkeypatch.setattr(m, "PROCESSED", tmp_path / "data" / "processed")
    assert m.render() == m.render()
