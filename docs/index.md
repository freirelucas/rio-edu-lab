# rio-edu-lab

> Laboratório exploratório sobre o Grupo Educação do data.rio.

Sandbox de pesquisa que precede e alimenta o produto **ACEC-Hub** — Atlas Cibernético da Educação Carioca. Aqui ficam as análises do inventário, probes de ingestão e relatórios reprodutíveis. A arquitetura-alvo do produto está versionada em [`reference/acec-hub/`](https://github.com/freirelucas/rio-edu-lab/tree/main/reference/acec-hub).

## Em uma linha

O Grupo Educação do data.rio publica **186 itens** (1991–2024) — séries históricas, mapas, painéis. Este lab destrincha esse acervo, valida o caminho de ingestão e produz inputs para os produtos do ACEC-Hub.

## Onde começar

| Quero… | Vá para |
|---|---|
| Entender o acervo | [Relatório 01 — EDA do manifest](reports/01_manifest_eda.md) |
| Entender como acessar os dados | [API do data.rio](data-rio-api.md) |
| Ver se o pipeline de ingestão funciona | [Relatório 02 — Probe de ingestão](reports/02_ingestion_probe.md) |
| Ver o que tem dentro dos 127 Excels | [Relatório 03 — Catálogo empírico dos Excels](reports/03_excel_catalog.md) |
| Saber quais Excels prestam para HEX-EDU | [Relatório 04 — Auditoria do shortlist](reports/04_shortlist_audit.md) |
| Ver os 35 PDFs catalogados | [Relatório 05 — Corpus dos PDFs](reports/05_pdf_corpus.md) |
| Ver Theil sobre IDEB do Rio | [Relatório 06 — Theil sobre IDEB por bairro](reports/06_theil_ideb.md) |
| Ler o produto-alvo | [README do ACEC-Hub](https://github.com/freirelucas/rio-edu-lab/blob/main/reference/README-acec-hub.md) |

## Achados-chave (medidos, não estimados)

- **186 itens** no manifest, dominados por séries históricas em Excel (127, 68%).
- **89% das visualizações** se concentram em 5 itens interativos — confirma o gap que o ACEC-Hub propõe ocupar.
- **127/127 Excels acessíveis** via API: 92 s, 12.3 MiB total. A estimativa anterior de 100 MiB (extrapolada de 1 amostra) estava ~8× errada.
- **126 dos 127 Excels são `.xls` legacy**, não `.xlsx`, apesar do `Content-Type` da API afirmar o contrário. Implicação: precisa `xlrd>=2.0`, não só `openpyxl`.
- **Janela temporal real do conteúdo**: 1991–2024. 30 arquivos com span ≥ 21 anos.
- **Granularidade dominante**: ~52% dos Excels têm 13–30 valores únicos na coluna 0 (compatível com RP / parcial RA); apenas 13 chegam à granularidade de bairro e 3 a escola.
- **35/35 PDFs baixados**, 71% com camada de texto extraível (10 são imagens escaneadas). Quatro coleções editoriais do IPP cobrem 32 deles.
- **66% da desigualdade do IDEB municipal está DENTRO das RAs** (média 2007–2023), não entre elas — política em granularidade de RA mascara a maior parte da variação relevante. Justificativa direta para HEX-EDU.

## Reproduzir

```bash
git clone https://github.com/freirelucas/rio-edu-lab.git
cd rio-edu-lab

# Análises 01 e 02 usam só a stdlib do Python 3.10+
python3 analysis/01_manifest_eda.py    # gera CSV enriquecido + relatório 01
python3 analysis/02_ingestion_probe.py # probe da API + relatório 02

# Análise 03 lê conteúdo real dos arquivos
pip install -r requirements.txt
python3 analysis/03_download_excels.py     # ~92 s, 12.3 MiB
python3 analysis/04_excel_catalog.py       # <1 s
python3 analysis/05_report_excel_catalog.py
```

Para rodar o site localmente:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

## Licença

Código MIT. Dados derivados CC BY 4.0. Dados brutos seguem licença original do data.rio / IPP.
