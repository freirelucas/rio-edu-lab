"""Template: Theil (1967) — decomposição da variância do IDEB Rio.

Reproduz o achado central do lab (66% da variância está within-RA) lendo o CSV
canônico `theil_ideb_anos_iniciais.csv` já computado por `analysis/10_theil_ideb.py`
no commit do repo. Notebook é self-contained pra rodar em Colab sem clonar o lab.
"""
from __future__ import annotations

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

# CSV canônico hospedado no GitHub (raw); muda o commit no provenance footer.
DATA_URL = (
    "https://raw.githubusercontent.com/freirelucas/rio-edu-lab/main/"
    "data/processed/theil_ideb_anos_iniciais.csv"
)


def build(paper: dict, prov: dict, **kwargs) -> nbf.NotebookNode:
    title = paper.get("title", "")
    doi = paper.get("doi_or_url") or ""
    authors = paper.get("authors") or []
    year = paper.get("year", "?")
    citation = f"{', '.join(authors)} ({year}). *{title}*."

    colab_badge = (
        "[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
        "(https://colab.research.google.com/github/freirelucas/rio-edu-lab/blob/"
        "notebooks/theil_1967_economics.ipynb)"
    )

    cells = [
        new_markdown_cell(
            f"# Decomposição Theil do IDEB Rio — replicação\n"
            f"### Achado central: **66% da variância está *dentro* das Regiões Administrativas**\n\n"
            f"**Paper-base:** {citation}  \n"
            f"**DOI / link:** [{doi}]({doi})  \n\n"
            f"{colab_badge}\n\n"
            f"Decomposição Theil-T mostra que a maior parte da desigualdade do IDEB municipal "
            f"carioca está **dentro** das RAs, não entre — coropléticos por RA escondem o sinal. "
            f"Este notebook lê o CSV canônico já computado pelo lab e reproduz a visualização "
            f"que sustenta o achado."
        ),
        new_markdown_cell("## Setup"),
        new_code_cell(
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt"
        ),
        new_markdown_cell(
            "## Dados — `theil_ideb_anos_iniciais.csv`\n\n"
            "CSV produzido por `analysis/10_theil_ideb.py` no commit "
            f"`{prov['repo_commit']}` do repo. Colunas: `year`, `T_total`, `T_between`, "
            "`T_within`, `share_within`, `check_sum` (este último valida a identidade Theil "
            "T = T_b + T_w em até 1e-6)."
        ),
        new_code_cell(
            f'df = pd.read_csv("{DATA_URL}")\n'
            "df"
        ),
        new_markdown_cell(
            "## Sanity check — identidade do Theil\n\n"
            "Hard-fail no lab (`tests/test_theil.py`): cada linha do CSV deve ter "
            "`|check_sum| < 1e-6`. Reverificamos aqui."
        ),
        new_code_cell(
            "mx = df['check_sum'].abs().max()\n"
            "assert mx < 1e-6, 'identidade Theil quebrada'\n"
            "print(f'check_sum max: {mx:.2e} ✓')"
        ),
        new_markdown_cell(
            "## Visualização — share_within por ano\n\n"
            "A linha de referência em 50% é a **paridade** (within = between). Nenhum "
            "ano da série cruza."
        ),
        new_code_cell(
            "fig, ax = plt.subplots(figsize=(10, 5))\n"
            "ax.bar(df['year'].astype(str), df['share_within'] * 100, color='#1f77b4', alpha=0.85)\n"
            "ax.axhline(50, color='gray', linestyle='--', linewidth=1, label='Paridade 50%')\n"
            "ax.set_ylabel('share within-RA (%)')\n"
            "ax.set_xlabel('Ano')\n"
            "ax.set_title('IDEB anos iniciais (5º ano) — % da desigualdade que está DENTRO das RAs')\n"
            "ax.set_ylim(0, 100)\n"
            "ax.legend(loc='lower right')\n"
            "for i, v in enumerate(df['share_within'] * 100):\n"
            "    ax.text(i, v + 1, f'{v:.0f}%', ha='center', fontsize=9)\n"
            "plt.tight_layout()\n"
            "plt.show()"
        ),
        new_markdown_cell(
            "## Interpretação\n\n"
            "O `share_within` fica entre **59% e 73%** ao longo de 2007–2023, nunca cruzando a "
            "paridade de 50%. Implicação direta de política: focar em equalizar IDEB **entre** "
            "RAs deixa de fora a maior parte da desigualdade, que vive **dentro** das próprias "
            "RAs, entre bairros vizinhos.\n\n"
            "Próximos passos: ver `analysis/18_thesha_rio.py` pra decomposição em 3 níveis "
            "(AP / RA / within-RA) e `docs/produtos/hex_edu.md` pra a visualização em H3."
        ),
        new_markdown_cell(
            "---\n\n"
            "## Selo de proveniência\n\n"
            f"| Campo | Valor |\n"
            f"|---|---|\n"
            f"| **Paper-base DOI** | `{doi}` |\n"
            f"| **Repo commit** | `{prov['repo_commit']}` |\n"
            f"| **Manifest data.rio hash** | `{prov['manifest_hash']}` |\n"
            f"| **Gerado em (UTC)** | `{prov['generated_at']}` |\n"
            f"| **CSV-fonte** | [`theil_ideb_anos_iniciais.csv`]({DATA_URL}) |\n\n"
            f"_Reprodução total:_ rodar `rioedu generate --paper theil-1967-economics --output theil.ipynb` "
            f"no commit `{prov['repo_commit']}` reproduz este notebook byte-a-byte (exceto o campo "
            f"`generated_at`)."
        ),
    ]
    nb = new_notebook(cells=cells)
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nb.metadata["language_info"] = {"name": "python"}
    nb.metadata["rioedu_provenance"] = prov
    nb.metadata["rioedu_paper_id"] = paper.get("id")
    return nb
