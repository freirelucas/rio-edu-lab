---
title: Reproduzir em 4 minutos — rio-edu-lab
description: Clone limpo do repo até charts da landing. 96s de download + ~3 min de processing.
---

# Reproduzir em 4 minutos

Clone limpo do repo → charts da landing. **96 s de download + ~3 min de processing**.

## Setup

```bash
git clone https://github.com/freirelucas/rio-edu-lab.git
cd rio-edu-lab

# Python ≥ 3.10
pip install -r requirements.txt           # core: pandas, geopandas, h3, plotly, openpyxl, xlrd, pypdf
pip install -r requirements-docs.txt      # mkdocs-material para o site
pip install -r requirements-dev.txt       # pytest + ruff (opcional)
pip install -e reference/acec-hub         # pacote `acec` (Theil + parsers + H3)
```

## Pipeline analítico (em ordem)

```bash
# Inventário do data.rio (rápido, stdlib only)
python3 analysis/01_manifest_eda.py
python3 analysis/02_ingestion_probe.py

# Ingestão (~96 s para Excels + 35 PDFs)
python3 analysis/03_download_excels.py    # 127 arquivos, 12.3 MiB
python3 analysis/04_excel_catalog.py
python3 analysis/05_report_excel_catalog.py
python3 analysis/06_shortlist_audit.py
python3 analysis/07_download_pdfs.py      # 35 arquivos, 63 MiB
python3 analysis/08_pdf_corpus.py
python3 analysis/09_report_pdf_corpus.py

# Theil base (HEX-EDU)
python3 analysis/10_theil_ideb.py
python3 analysis/11_fetch_bairros.py      # geometry IPP
python3 analysis/12_h3_grid.py            # ~1593 hex
python3 analysis/13_hex_edu_static.py
python3 analysis/14_hex_edu_folium.py     # 5.8 MiB HTML

# Robustez + outros produtos MVP-1
python3 analysis/15_anos_finais.py        # IDEB 9º ano
python3 analysis/16_theil_weighted.py     # Theil ponderado por matrícula
python3 analysis/17_theil_components.py   # Aprovação / SAEB / IDEB separadamente
python3 analysis/18_thesha_rio.py         # 3-level Theil
python3 analysis/19_fun_rio.py            # pseudocoortes 5º→9º
python3 analysis/20_pm_12.py              # lei de escala

# UX charts (PR-A)
python3 analysis/21_build_tour_charts.py  # 6 Plotly JSONs
python3 analysis/23_build_priority_list.py
```

## Testes

```bash
pytest tests/                                                      # 31 lab tests
pytest reference/acec-hub/tests/test_acec_stats.py                 # 20 acec tests
```

Total: **51 testes verdes** (incluindo invariantes Theil 2-níveis e 3-níveis, primitivas do matching IDF/code-book, e o achado central `share_within ∈ [55%, 75%]` — bound bilateral — como teste hard-fail).

## Site

```bash
mkdocs serve                              # http://127.0.0.1:8000
mkdocs build --strict                     # produz site/ — usado pelo workflow Pages
```

## Sanity check final

```bash
python3 -c "
import csv
rows = list(csv.DictReader(open('data/processed/theil_ideb_anos_iniciais.csv')))
shares = [float(r['share_within']) for r in rows]
print(f'share_within: min={min(shares):.0%}, max={max(shares):.0%}, mean={sum(shares)/len(shares):.0%}')
# Esperado: min=59%, max=73%, mean=66% — o achado-headline do projeto.
"
```

## Estrutura

```
rio-edu-lab/
├── analysis/                    # 23 scripts numerados
├── reference/acec-hub/          # pacote `acec` instalável
│   ├── src/acec/{stats,transform,geo,ingest}/
│   └── tests/
├── data/
│   ├── manifest.json            # snapshot canônico do data.rio (186 itens)
│   ├── raw/{excel,pdf,geo}/     # downloads (gitignored exceto _index.json)
│   └── processed/               # 19 CSVs derivados, todos commitados
├── docs/                        # site MkDocs Material
│   ├── _assets/{logo.svg, charts/*.json}
│   ├── stylesheets/extra.css
│   ├── javascripts/charts.js
│   ├── reports/                 # relatórios técnicos 01–13
│   ├── produtos/                # páginas-produto (Fio B comparativo)
│   └── paper/                   # manuscrito
├── tests/                       # pytest do lab
└── .github/workflows/{ci,pages}.yml
```

## Continue

<div class="grid cards" markdown>

-   [:material-source-branch: Repo no GitHub](https://github.com/freirelucas/rio-edu-lab)
-   [:material-library-shelves: Papers](papers/index.md)
-   [:material-information-outline: Sobre o lab](sobre.md)

</div>
