"""Smoke tests para rioedu: catálogo, template, geração de notebook, provenance."""
from __future__ import annotations

from pathlib import Path

import nbformat


def _repo_root() -> Path:
    """Walk up from this test file até achar papers_catalog.yml (raiz do lab)."""
    for d in Path(__file__).resolve().parents:
        if (d / "data" / "papers_catalog.yml").exists():
            return d
    raise RuntimeError("não estou dentro do rio-edu-lab — papers_catalog.yml não achado")


def test_catalog_loads_and_finds_theil():
    from rioedu import render

    root = _repo_root()
    catalog = render.load_catalog(root / "data" / "papers_catalog.yml")
    assert len(catalog) >= 1, "catálogo vazio"
    paper = render.load_paper_meta(root / "data" / "papers_catalog.yml", "theil-1967-economics")
    assert paper is not None, "theil-1967-economics ausente do catálogo"
    assert "title" in paper


def test_theil_template_exists_other_doesnt():
    from rioedu import render

    assert render.has_template("theil-1967-economics") is True
    assert render.has_template("paper-que-nao-existe-xyz") is False


def test_generate_theil_produces_valid_notebook():
    from rioedu import provenance, render

    root = _repo_root()
    paper = render.load_paper_meta(root / "data" / "papers_catalog.yml", "theil-1967-economics")
    prov = provenance.compute(root)
    nb = render.render_notebook(paper, prov)
    nbformat.validate(nb)
    assert len(nb["cells"]) >= 8, "notebook curto demais — template provavelmente quebrou"
    assert nb.metadata.get("rioedu_paper_id") == "theil-1967-economics"
    assert "repo_commit" in nb.metadata.get("rioedu_provenance", {})
    # Selo de proveniência também aparece na última célula (visível no Colab).
    last = nb["cells"][-1].source
    if isinstance(last, list):
        last = "".join(last)
    assert prov["repo_commit"] in last
    assert prov["manifest_hash"] in last


def test_paper_id_kebab_to_module_underscore():
    from rioedu.render import _paper_to_module

    assert _paper_to_module("theil-1967-economics") == "theil_1967_economics"
    assert _paper_to_module("pereira-2019-ipea") == "pereira_2019_ipea"
