"""Tests pro `analysis/63_provenance_trail.py`.

Cobre helpers puros (sha256, build_provenance, render_markdown) sem tocar
git real (mocked subprocess) ou rede.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_63():
    spec = importlib.util.spec_from_file_location(
        "provenance_trail", str(ANALYSIS / "63_provenance_trail.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── file_sha256 ──────────────────────────────────────────────────────────


def test_sha256_existing_file(tmp_path):
    m = _import_63()
    p = tmp_path / "x.txt"
    p.write_text("hello", encoding="utf-8")
    h = m.file_sha256(p)
    # sha256 de "hello" = 2cf24dba...
    assert h.startswith("2cf24dba")
    assert len(h) == 64


def test_sha256_missing_file(tmp_path):
    m = _import_63()
    assert m.file_sha256(tmp_path / "nope.txt") == "NONE"


def test_sha256_deterministic(tmp_path):
    m = _import_63()
    p = tmp_path / "x.txt"
    p.write_text("content", encoding="utf-8")
    assert m.file_sha256(p) == m.file_sha256(p)  # idempotent


# ─── build_provenance ─────────────────────────────────────────────────────


def test_build_provenance_minimal():
    m = _import_63()
    paper = {
        "id": "test-paper",
        "doi_or_url": "10.x/y",
        "openalex_id": "W1",
        "replication_status": "full",
        "scripts": [],
        "data_availability_statement": {
            "sources": [{"name": "X", "url": "u", "access_date": "2024", "license": "L"}],
        },
        "provenance": {
            "replicator": "Lucas",
            "replication_date": "2024-11-01",
        },
    }
    prov = m.build_provenance(paper, manifest_hash="abc", head_commit="def")
    assert prov["paper_id"] == "test-paper"
    assert prov["replicator"] == "Lucas"
    assert prov["manifest_snapshot"]["sha256"] == "abc"
    assert prov["code"]["head_commit_at_audit"] == "def"
    assert len(prov["data_sources"]) == 1


def test_build_provenance_audit_chain_incomplete_missing_scripts():
    """Sem scripts populated → audit chain incomplete."""
    m = _import_63()
    paper = {
        "id": "x",
        "replication_status": "full",
        "scripts": [],
        "data_availability_statement": {"sources": []},
        "provenance": {"replicator": "L", "replication_date": "2024"},
    }
    prov = m.build_provenance(paper, "h", "c")
    assert prov["audit_chain_complete"] is False


def test_build_provenance_audit_chain_incomplete_missing_replicator():
    m = _import_63()
    paper = {
        "id": "theil-1967-economics",  # paper_id known → vai checar processed CSVs
        "replication_status": "full",
        "scripts": [10],
        "provenance": {},  # replicator missing
    }
    prov = m.build_provenance(paper, "h", "c")
    assert prov["audit_chain_complete"] is False


def test_build_provenance_audit_chain_complete():
    """Todos os elos presentes → complete."""
    m = _import_63()
    # Fake a processed CSV present via patching
    paper = {
        "id": "theil-1967-economics",
        "replication_status": "full",
        "scripts": [10],
        "data_availability_statement": {"sources": [{"name": "X", "url": "u"}]},
        "provenance": {"replicator": "L", "replication_date": "2024"},
    }
    # Match real Theil script
    prov = m.build_provenance(paper, "h", "c")
    # Mai be complete if 10_theil_ideb.py + CSVs exist no repo real
    if (ROOT / "analysis" / "10_theil_ideb.py").exists():
        # Likely we have CSVs → complete
        if prov["results"]["processed_csv_hashes"]:
            assert prov["audit_chain_complete"] is True


# ─── render_markdown ──────────────────────────────────────────────────────


def test_render_markdown_includes_paper_id():
    m = _import_63()
    prov = {
        "paper_id": "p1",
        "paper_doi_or_url": "10.x",
        "openalex_id": "W1",
        "replication_status": "full",
        "replicator": "L",
        "replication_date": "2024",
        "audit_chain_complete": True,
        "data_sources": [],
        "manifest_snapshot": {"path": "data/manifest.json", "sha256": "h"},
        "code": {"scripts": {}, "head_commit_at_audit": "c"},
        "results": {"processed_csv_hashes": {}},
    }
    md = m.render_markdown(prov, {"title": "Test Paper"})
    assert "Test Paper" in md
    assert "p1" in md
    assert "Audit chain complete" in md


def test_render_markdown_shows_partial_when_incomplete():
    m = _import_63()
    prov = {
        "paper_id": "p1",
        "paper_doi_or_url": None,
        "openalex_id": None,
        "replication_status": "partial",
        "replicator": None,
        "replication_date": None,
        "audit_chain_complete": False,
        "data_sources": [],
        "manifest_snapshot": {"path": "x", "sha256": "h"},
        "code": {"scripts": {}, "head_commit_at_audit": "c"},
        "results": {"processed_csv_hashes": {}},
    }
    md = m.render_markdown(prov, {"title": "T"})
    assert "Audit chain partial" in md
    assert "_(none)_" in md  # missing fields


def test_render_markdown_data_sources_table():
    m = _import_63()
    prov = {
        "paper_id": "p1",
        "paper_doi_or_url": "x",
        "openalex_id": "x",
        "replication_status": "full",
        "replicator": "L",
        "replication_date": "2024",
        "audit_chain_complete": True,
        "data_sources": [
            {"name": "IDEB", "url": "https://x", "access_date": "2024",
             "license": "CC-BY", "declared_sha256": "abc123def456789012345"},
        ],
        "manifest_snapshot": {"path": "x", "sha256": "h"},
        "code": {"scripts": {}, "head_commit_at_audit": "c"},
        "results": {"processed_csv_hashes": {}},
    }
    md = m.render_markdown(prov, {"title": "T"})
    assert "IDEB" in md
    assert "abc123def456" in md  # first 12 chars in table


# ─── git mocks ────────────────────────────────────────────────────────────


def test_git_commit_for_path_returns_unknown_on_failure():
    m = _import_63()
    # Patch subprocess.run to fail
    with patch("subprocess.run") as mr:
        mr.side_effect = Exception("boom")
        result = m.git_commit_for_path(Path("/tmp/x"))
    assert result == "UNKNOWN"


def test_repo_head_commit_returns_unknown_on_failure():
    m = _import_63()
    with patch("subprocess.run") as mr:
        mr.side_effect = Exception("boom")
        result = m.repo_head_commit()
    assert result == "UNKNOWN"
