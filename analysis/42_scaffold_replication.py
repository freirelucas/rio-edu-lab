"""Scaffold: gera arquivos placeholder para replicar um paper `pending`.

Reduz fricção da próxima replicação leve. Dado um paper-id no catálogo
(estado `pending`), cria:

  1. `analysis/<NN>_<slug>.py` — template Python com docstring + imports
     padrão do lab + skeleton de `main()`.
  2. `docs/reports/<NN>_<slug>.md` — template Markdown com YAML frontmatter
     + seções padrão (Contexto / Paper-base / Método / Dados / Resultados /
     Caveats / Reproduzir).

Não modifica `data/papers_catalog.yml` — o curador faz a edição final
(adiciona `report_ids`, `scripts`, muda `replication_status`, escreve
`policy_insight`) depois de implementar a replicação.

`<NN>` é detectado automaticamente: próximo inteiro disponível em
`analysis/` (script) e `docs/reports/` (relatório), respectivamente
— não precisam coincidir.

Uso:
  python3 analysis/42_scaffold_replication.py coleman-1966-eeo
  python3 analysis/42_scaffold_replication.py soares-andrade-2006 \\
      --report-id 16 --script-id 35
  python3 analysis/42_scaffold_replication.py hoxby-2000-aer --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
ANALYSIS_DIR = ROOT / "analysis"
REPORTS_DIR = ROOT / "docs" / "reports"

NN_RE = re.compile(r"^(\d+)([a-z]?)_")


def next_id(directory: Path) -> int:
    """Highest existing NN prefix + 1; ignores letter suffixes (06b)."""
    max_n = 0
    for p in directory.glob("*"):
        m = NN_RE.match(p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def load_paper(paper_id: str) -> dict | None:
    if not CATALOG_YML.exists():
        return None
    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8")) or {}
    for p in catalog.get("papers") or []:
        if p.get("id") == paper_id:
            return p
    return None


def fmt_authors(authors: list[str]) -> str:
    if not authors:
        return "?"
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} & {authors[1]}"
    return f"{authors[0]} et al."


def script_template(p: dict, paper_id: str) -> str:
    title = p["title"].strip()
    venue = p.get("venue", "?")
    doi = p.get("doi_or_url", "")
    authors = fmt_authors(p.get("authors", []))
    year = p["year"]
    reqs = p.get("data_requirements", []) or []
    req_bullets = "\n".join(f"#   - {r}" for r in reqs) or "#   (preencher)"
    return f'''"""Replicação leve de {authors} ({year}).

Paper:
  {title}
  _{venue}_
  {doi}

Operacionaliza o método sobre os dados do data.rio quando possível.
Esta replicação é **leve** — adapta o núcleo do método ao escopo do
Rio (granularidade, período disponível) sem reproduzir o paper completo.

Requisitos de dados (do catálogo):
{req_bullets}

Para servir a replicação no site:
  1. Implementar o método aqui (este arquivo).
  2. Escrever interpretação literal dos achados em
     `docs/reports/<NN>_{paper_id}.md` (já scaffoldado).
  3. Editar `data/papers_catalog.yml` no paper `{paper_id}`:
       replication_status: partial      # ou full
       report_ids: [<N>]                # do .md gerado
       scripts:   [<N>]                 # deste arquivo
       product:   <opcional>            # se cria/atualiza produto
       policy_insight: |                # 1-3 frases descritivas
         <achado replicado aplicado ao Rio>
  4. Rodar: python3 analysis/31_build_paper_catalog.py
            python3 analysis/32_render_papers_pages.py
            python3 analysis/41_match_requirements.py

Stance: replicação **fria, exata e replicável**. Sem advocacy.
Achado literal aplicado ao Rio + caveats do paper. Stop.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "processed"


def main() -> int:
    # TODO: implementar replicação
    #   1. Carregar dados do data.rio (data/raw/ ou cache)
    #   2. Aplicar método do paper-base
    #   3. Escrever CSV/JSON em OUT_DIR
    #   4. Imprimir métricas-chave para o relatório consumir
    print("scaffold {paper_id} — implementar replicação leve aqui")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def report_template(p: dict, paper_id: str, nn: int, script_nn: int) -> str:
    title = p["title"].strip()
    venue = p.get("venue", "?")
    doi = p.get("doi_or_url", "")
    authors = fmt_authors(p.get("authors", []))
    authors_full = ", ".join(p.get("authors") or [])
    year = p["year"]
    return f'''---
title: "{nn:02d} — Replicação leve: {authors} ({year})"
description: "Replicação leve do método de {authors} ({year}) aplicada aos dados do data.rio. Achado descritivo, sem extrapolação."
---

# Relatório {nn:02d} — Replicação leve: {authors} ({year})

## Paper-base

**{authors_full} ({year}).** *{title}*. {venue}.
<{doi}>

Ver mini-page no catálogo: [`{paper_id}`](../papers/{paper_id}.md).

## Por que esta replicação

(_preencher: pergunta original do paper, e o que dela faz sentido replicar com dados do data.rio. Stance: descritivo, sem advocacy._)

## Dados utilizados

(_preencher: itens do data.rio efetivamente usados. Cite item_id + tabela do manifest. Para itens externos, declare a fonte e a janela temporal._)

## Método

(_preencher: equação/algoritmo principal do paper, exatamente como aparece no paper. Documente diferenças vs. o paper original (granularidade, período, ponderação) como caveat — não como contribuição._)

```python
# Trecho ilustrativo do método (não cópia integral do script)
# Script completo em analysis/{script_nn:02d}_{paper_id}.py
```

## Resultados

(_preencher: tabela / chart / número-chave. Achado descritivo, sem claim de causalidade._)

## Caveats do paper aplicados ao Rio

(_preencher: o que o paper assume que NÃO foi possível replicar; o que vai precisar de v+1; janelas temporais; granularidade. Replication-focused, não advocacy._)

## Reproduzir

```bash
python3 analysis/{script_nn:02d}_{paper_id}.py
```

Saída em `data/processed/`. Achados deste relatório derivados de CSV listados ali.

## Como este relatório aparece no catálogo

Atualizar `data/papers_catalog.yml` para o paper `{paper_id}`:

```yaml
replication_status: partial   # ou full quando aplicável
report_ids: [{nn}]
scripts: [{script_nn}]
policy_insight: |
  (achado literal aplicado ao Rio — 1-3 frases descritivas)
```

Depois rodar:

```bash
python3 analysis/31_build_paper_catalog.py
python3 analysis/32_render_papers_pages.py
python3 analysis/41_match_requirements.py
```

A mini-page do paper passará a exibir status `partial`/`full` e o callout
"Insight da replicação aplicado ao Rio".
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paper_id", help="ID do paper no catálogo (ex: coleman-1966-eeo)")
    ap.add_argument("--script-id", type=int, help="NN do script (default: auto)")
    ap.add_argument("--report-id", type=int, help="NN do relatório (default: auto)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Não escreve arquivos; imprime nomes que seriam criados")
    ap.add_argument("--force", action="store_true",
                    help="Sobrescreve arquivos existentes")
    args = ap.parse_args()

    p = load_paper(args.paper_id)
    if p is None:
        print(f"error: paper '{args.paper_id}' not found in catalog", file=sys.stderr)
        return 1

    status = p.get("replication_status")
    if status not in ("pending", "unfeasible"):
        print(
            f"warning: paper '{args.paper_id}' has status '{status}', "
            f"not pending. Scaffold continues but make sure that's intentional.",
            file=sys.stderr,
        )

    script_nn = args.script_id or next_id(ANALYSIS_DIR)
    report_nn = args.report_id or next_id(REPORTS_DIR)

    slug = args.paper_id
    script_path = ANALYSIS_DIR / f"{script_nn:02d}_{slug}.py"
    report_path = REPORTS_DIR / f"{report_nn:02d}_{slug}.md"

    for path in (script_path, report_path):
        if path.exists() and not args.force:
            print(f"error: {path.relative_to(ROOT)} exists (use --force to overwrite)",
                  file=sys.stderr)
            return 2

    script_body = script_template(p, slug)
    report_body = report_template(p, slug, report_nn, script_nn)

    if args.dry_run:
        print("[dry-run] would create:")
        print(f"  {script_path.relative_to(ROOT)} ({len(script_body)} chars)")
        print(f"  {report_path.relative_to(ROOT)} ({len(report_body)} chars)")
        return 0

    script_path.write_text(script_body, encoding="utf-8")
    report_path.write_text(report_body, encoding="utf-8")
    print(f"wrote {script_path.relative_to(ROOT)}")
    print(f"wrote {report_path.relative_to(ROOT)}")
    print("\nnext steps:")
    print(f"  1. implementar replicação em {script_path.relative_to(ROOT)}")
    print(f"  2. preencher achados em {report_path.relative_to(ROOT)}")
    print(f"  3. editar data/papers_catalog.yml no paper '{slug}':")
    print(f"       report_ids: [{report_nn}]")
    print(f"       scripts: [{script_nn}]")
    print(f"       replication_status: partial  # quando estiver pronto")
    print(f"  4. python3 analysis/31_build_paper_catalog.py")
    print(f"     python3 analysis/32_render_papers_pages.py")
    print(f"     python3 analysis/41_match_requirements.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
