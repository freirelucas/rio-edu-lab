"""Notebook rendering: dispatch paper-id → per-paper template module → nbformat."""
from __future__ import annotations

import importlib
from pathlib import Path

import nbformat
import yaml


def load_catalog(catalog_path: Path) -> list[dict]:
    """Load `papers` list from papers_catalog.yml ([] if missing)."""
    if not catalog_path.exists():
        return []
    data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    return data.get("papers") or []


def load_paper_meta(catalog_path: Path, paper_id: str) -> dict | None:
    for p in load_catalog(catalog_path):
        if p.get("id") == paper_id:
            return p
    return None


def _paper_to_module(paper_id: str) -> str:
    """Kebab-case paper id → snake_case module name."""
    return paper_id.replace("-", "_")


def has_template(paper_id: str) -> bool:
    """True if a `rioedu.templates.<paper_module>` exists and exports `build`."""
    mod_name = f"rioedu.templates.{_paper_to_module(paper_id)}"
    try:
        module = importlib.import_module(mod_name)
    except ImportError:
        return False
    return callable(getattr(module, "build", None))


def render_notebook(paper: dict, prov: dict, **extra) -> nbformat.NotebookNode:
    """Dispatch to the per-paper template module and validate the output."""
    paper_id = paper["id"]
    mod_name = f"rioedu.templates.{_paper_to_module(paper_id)}"
    module = importlib.import_module(mod_name)
    nb = module.build(paper, prov, **extra)
    nbformat.validate(nb)
    return nb


def write_notebook(nb: nbformat.NotebookNode, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        nbformat.write(nb, f)
