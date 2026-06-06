# rioedu

Wizard CLI + notebook generator pro `rio-edu-lab`. **Template curado por paper**: nada de LLM no caminho crítico de notebook — reprodutibilidade total, output determinístico.

## Instalação (dev)

```bash
pip install -e rioedu/
```

## Uso

```bash
rioedu list-papers                                        # ver papers do catálogo + quais têm template
rioedu generate --paper theil-1967-economics \
                --output theil.ipynb                       # gera notebook executável
```

## Estrutura

- `src/rioedu/cli.py` — Typer app (`list-papers`, `generate`)
- `src/rioedu/render.py` — dispatch paper-id → módulo-template
- `src/rioedu/provenance.py` — selo de proveniência (commit + manifest hash + timestamp)
- `src/rioedu/templates/<paper_id>.py` — um por paper; exporta `build(paper, prov, **kw) -> NotebookNode`

Adicionar template = novo arquivo em `templates/` que exporta `build()`. Sem reconfiguração.
