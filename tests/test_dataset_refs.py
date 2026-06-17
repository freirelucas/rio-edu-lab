"""Tests pro `analysis/45d_dataset_refs.py`.

Cobre priority_pool ordering, DATASET_TYPES constant, write_funnel
roundtrip. Não chama OpenAlex real (mocked fetch).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_45d():
    spec = importlib.util.spec_from_file_location(
        "dataset_refs", str(ANALYSIS / "45d_dataset_refs.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── DATASET_TYPES constant ───────────────────────────────────────────────


def test_dataset_types_includes_canonical():
    m = _import_45d()
    assert "dataset" in m.DATASET_TYPES
    assert "software-source-code" in m.DATASET_TYPES
    # Forward-compat — software type não nativo no OpenAlex hoje
    assert "software" in m.DATASET_TYPES


def test_dataset_types_excludes_articles():
    m = _import_45d()
    assert "article" not in m.DATASET_TYPES
    assert "book-chapter" not in m.DATASET_TYPES
    assert "dissertation" not in m.DATASET_TYPES


# ─── priority_pool ────────────────────────────────────────────────────────


def test_priority_pool_skips_no_refs():
    m = _import_45d()
    cands = [
        {"referenced_works": [], "citations": 1000},                # sem refs → skip
        {"referenced_works": ["W1"], "citations": 100,
         "coverage": [{"status": "available"}]},                     # tier 1
        {"referenced_works": ["W2"], "citations": 50,
         "is_brazilian": True},                                       # tier 2
        {"referenced_works": ["W3"], "citations": 200},              # tier 3
    ]
    pool = m.priority_pool(cands)
    assert 0 not in pool  # sem refs
    assert pool == [1, 2, 3]  # tier 1 → 2 → 3


def test_priority_pool_orders_by_citation_within_tier():
    m = _import_45d()
    cands = [
        {"referenced_works": ["W1"], "citations": 500,
         "coverage": [{"status": "available"}]},  # tier 1 high
        {"referenced_works": ["W2"], "citations": 5000,
         "coverage": [{"status": "available"}]},  # tier 1 highest
        {"referenced_works": ["W3"], "citations": 100,
         "coverage": [{"status": "available"}]},  # tier 1 low
    ]
    pool = m.priority_pool(cands)
    # Ordenado por cit desc: 5000, 500, 100 → idx 1, 0, 2
    assert pool == [1, 0, 2]


def test_priority_pool_caps_tier3_at_200():
    """Tier 3 (rest) tem cap 200 pra não explodir budget OpenAlex."""
    m = _import_45d()
    cands = []
    for i in range(300):
        cands.append({"referenced_works": ["W"], "citations": i})
    pool = m.priority_pool(cands)
    # Sem tier1 nem tier2; tier3 caps em 200
    assert len(pool) == 200


def test_priority_pool_handles_partial_coverage():
    """Partial coverage NÃO é fully → tier 2 ou 3, não 1."""
    m = _import_45d()
    cands = [
        {"referenced_works": ["W1"], "citations": 1000,
         "coverage": [{"status": "available"}, {"status": "external"}]},  # partial
        {"referenced_works": ["W2"], "citations": 100,
         "coverage": [{"status": "available"}, {"status": "available"}]},  # full → tier 1
    ]
    pool = m.priority_pool(cands)
    # Tier1 first (idx 1), then tier3 (idx 0)
    assert pool[0] == 1


# ─── write_funnel roundtrip ───────────────────────────────────────────────


def test_write_funnel_preserves_header(tmp_path):
    m = _import_45d()
    funnel = tmp_path / "funnel.yml"
    funnel.write_text(
        "# header comment\n# more comments\nversion: 1\n\ncandidates:\n  - id: x\n",
        encoding="utf-8",
    )
    m.write_funnel(funnel, [{"id": "y", "dataset_refs": []}])
    out = funnel.read_text(encoding="utf-8")
    assert "# header comment" in out
    assert "version: 1" in out
    assert "id: y" in out


# ─── full smoke test (mocked OpenAlex) ────────────────────────────────────


def test_main_dry_run_no_network(tmp_path, monkeypatch, capsys):
    """--dry-run não chama OpenAlex; só lista plan."""
    m = _import_45d()
    funnel = tmp_path / "funnel.yml"
    funnel.write_text(
        "version: 1\n\ncandidates:\n"
        "  - id: x\n"
        "    title: Test paper\n"
        "    citations: 100\n"
        "    referenced_works: ['W1', 'W2']\n"
        "    coverage:\n"
        "      - status: available\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv",
                        ["45d", "--dry-run", "--funnel", str(funnel)])
    # Sem patch em fetch_works_batch — dry-run skip
    rc = m.main()
    assert rc == 0


def test_main_persists_dataset_refs_on_match(tmp_path, monkeypatch):
    """Quando OpenAlex retorna ref tipo dataset, salva no candidate."""
    m = _import_45d()
    funnel = tmp_path / "funnel.yml"
    funnel.write_text(
        "version: 1\n\ncandidates:\n"
        "  - id: x\n"
        "    title: Test\n"
        "    citations: 100\n"
        "    referenced_works: ['W1', 'W2']\n"
        "    coverage:\n"
        "      - status: available\n",
        encoding="utf-8",
    )

    def fake_fetch(ids, verbose=False):
        return [
            {"openalex_id": "W1", "doi": "10.x/1", "title": "Dataset paper", "type": "dataset"},
            {"openalex_id": "W2", "doi": "10.x/2", "title": "Article", "type": "article"},
        ]

    monkeypatch.setattr(m, "fetch_works_batch", fake_fetch)
    monkeypatch.setattr(sys, "argv",
                        ["45d", "--funnel", str(funnel)])
    rc = m.main()
    assert rc == 0

    # Verify YAML persisted
    import yaml as y
    out = y.safe_load(funnel.read_text(encoding="utf-8"))
    candidate = out["candidates"][0]
    assert "dataset_refs" in candidate
    assert len(candidate["dataset_refs"]) == 1
    assert candidate["dataset_refs"][0]["type"] == "dataset"
    assert candidate["dataset_refs"][0]["doi"] == "10.x/1"


def test_main_skips_when_already_populated(tmp_path, monkeypatch):
    """--refresh=False (default) pula candidates com dataset_refs já presente."""
    m = _import_45d()
    funnel = tmp_path / "funnel.yml"
    funnel.write_text(
        "version: 1\n\ncandidates:\n"
        "  - id: x\n"
        "    title: T\n"
        "    citations: 100\n"
        "    referenced_works: ['W1']\n"
        "    coverage:\n"
        "      - status: available\n"
        "    dataset_refs:\n"
        "      - openalex_id: W1\n"
        "        type: dataset\n",
        encoding="utf-8",
    )

    fetch_called = []
    def fake_fetch(ids, verbose=False):
        fetch_called.append(ids)
        return []

    monkeypatch.setattr(m, "fetch_works_batch", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["45d", "--funnel", str(funnel)])
    m.main()
    assert fetch_called == []  # skipped, no fetch call


def test_main_with_refresh_re_queries(tmp_path, monkeypatch):
    """--refresh força re-query mesmo se dataset_refs presente."""
    m = _import_45d()
    funnel = tmp_path / "funnel.yml"
    funnel.write_text(
        "version: 1\n\ncandidates:\n"
        "  - id: x\n"
        "    title: T\n"
        "    citations: 100\n"
        "    referenced_works: ['W1']\n"
        "    coverage:\n"
        "      - status: available\n"
        "    dataset_refs: []\n",
        encoding="utf-8",
    )

    fetch_called = []
    def fake_fetch(ids, verbose=False):
        fetch_called.append(ids)
        return [{"openalex_id": "W1", "doi": "10.x/y", "title": "New", "type": "dataset"}]

    monkeypatch.setattr(m, "fetch_works_batch", fake_fetch)
    monkeypatch.setattr(sys, "argv", ["45d", "--funnel", str(funnel), "--refresh"])
    m.main()
    assert len(fetch_called) == 1
