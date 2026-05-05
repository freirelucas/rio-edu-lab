"""CLI principal do ACEC-Hub.

Uso:
    acec manifest refresh           # Atualiza manifest.json
    acec manifest stats             # Estatísticas do manifest atual
    acec ingest download --type "Microsoft Excel"
    acec ingest download --all
"""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from acec.ingest import ArcGISHubClient, GROUP_ID

app = typer.Typer(
    help="ACEC-Hub — pipeline de dados do data.rio Educação.",
    no_args_is_help=True,
)
manifest_app = typer.Typer(help="Operações sobre o manifest dos 186 itens.")
ingest_app = typer.Typer(help="Download de dados brutos do data.rio.")
app.add_typer(manifest_app, name="manifest")
app.add_typer(ingest_app, name="ingest")

console = Console()

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "manifest.json"
DATA_RAW = REPO_ROOT / "data" / "raw"


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


@manifest_app.command("refresh")
def manifest_refresh(
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Re-busca os 186 itens do data.rio e regrava manifest.json."""
    _setup_logging(verbose)
    with ArcGISHubClient() as client:
        items = client.list_group_items()
        client.write_manifest(items, MANIFEST_PATH)
    console.print(f"[green]✓[/green] Manifest atualizado: {len(items)} itens.")


@manifest_app.command("stats")
def manifest_stats() -> None:
    """Mostra distribuição por tipo dos itens do manifest."""
    if not MANIFEST_PATH.exists():
        console.print(f"[red]✗[/red] Manifest não encontrado em {MANIFEST_PATH}")
        console.print("Rode: [cyan]acec manifest refresh[/cyan]")
        raise typer.Exit(code=1)

    meta, items = ArcGISHubClient.load_manifest(MANIFEST_PATH)
    counts = Counter(it.type for it in items)

    table = Table(title=f"Manifest — {meta.get('total_items')} itens (fetched {meta.get('fetched_at')})")
    table.add_column("Tipo", style="cyan")
    table.add_column("Quantidade", justify="right", style="magenta")
    for t, n in counts.most_common():
        table.add_row(t, str(n))
    console.print(table)


@ingest_app.command("download")
def ingest_download(
    type_filter: str = typer.Option(None, "--type", help='Tipo a baixar (ex: "Microsoft Excel")'),
    all_types: bool = typer.Option(False, "--all", help="Baixar todos os tipos baixáveis"),
    overwrite: bool = typer.Option(False, "--overwrite"),
    verbose: bool = typer.Option(False, "-v", "--verbose"),
) -> None:
    """Baixa itens baixáveis para data/raw/{tipo}/{id}.{ext}."""
    _setup_logging(verbose)

    if not all_types and not type_filter:
        console.print("[red]✗[/red] Forneça --type ou --all")
        raise typer.Exit(code=1)

    if not MANIFEST_PATH.exists():
        console.print("[yellow]Manifest ausente, regenerando...[/yellow]")
        manifest_refresh(verbose=verbose)

    _, items = ArcGISHubClient.load_manifest(MANIFEST_PATH)
    if type_filter:
        items = [it for it in items if it.type == type_filter]

    items_dl = [it for it in items if it.is_downloadable]
    console.print(f"Baixando {len(items_dl)} itens (de {len(items)} no filtro)...")

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    with ArcGISHubClient() as client:
        for it in items_dl:
            res = client.download_item(it, DATA_RAW, overwrite=overwrite)
            if res:
                ok += 1
            else:
                fail += 1

    console.print(f"[green]✓[/green] {ok} baixados, [yellow]{fail}[/yellow] falhas.")


if __name__ == "__main__":
    app()
