"""Typer CLI: `rioedu list-papers`, `rioedu generate`."""
from __future__ import annotations

from pathlib import Path

import typer

from . import render, provenance

app = typer.Typer(no_args_is_help=True, add_completion=False, help=__doc__)


def _repo_root() -> Path:
    """Walk up from cwd until we find papers_catalog.yml (the lab marker)."""
    cur = Path.cwd().resolve()
    for d in [cur, *cur.parents]:
        if (d / "data" / "papers_catalog.yml").exists():
            return d
    raise typer.BadParameter(
        f"rioedu must run from inside the rio-edu-lab repo (no papers_catalog.yml above {cur})"
    )


@app.command(name="list-papers")
def list_papers() -> None:
    """List papers in the catalog and whether a notebook template exists."""
    root = _repo_root()
    catalog = render.load_catalog(root / "data" / "papers_catalog.yml")
    typer.echo(f"{len(catalog)} papers in catalog:")
    for p in catalog:
        pid = p.get("id", "?")
        marker = "✓ template" if render.has_template(pid) else "  (no template)"
        typer.echo(f"  {pid:35s} {marker}")


@app.command()
def generate(
    paper: str = typer.Option(..., "--paper", "-p", help="Catalog paper id (kebab-case)"),
    output: Path = typer.Option(..., "--output", "-o", help="Output .ipynb path"),
) -> None:
    """Render a catalog paper's template into an executable .ipynb."""
    root = _repo_root()
    meta = render.load_paper_meta(root / "data" / "papers_catalog.yml", paper)
    if meta is None:
        typer.echo(f"error: paper '{paper}' not in catalog", err=True)
        raise typer.Exit(1)
    if not render.has_template(paper):
        typer.echo(f"error: no template module for '{paper}' (looked for rioedu.templates.{paper.replace('-', '_')})", err=True)
        raise typer.Exit(2)
    prov = provenance.compute(root)
    nb = render.render_notebook(meta, prov)
    render.write_notebook(nb, output)
    typer.echo(f"wrote {output} ({len(nb['cells'])} cells, commit={prov['repo_commit']})")


if __name__ == "__main__":
    app()
