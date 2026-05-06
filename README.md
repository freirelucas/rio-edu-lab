# rio-edu-lab

[![pages](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml)
[![ci](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
<!-- DOI badge será inserido após ativação do webhook Zenodo (instruções em CHANGELOG.md) -->

Laboratório exploratório sobre o Grupo Educação do [data.rio](https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310). Sandbox que precede e alimenta o produto **ACEC-Hub** (cuja estrutura-alvo está versionada em `reference/`).

**Achado-headline**: 66% da desigualdade do IDEB municipal carioca está dentro das Regiões Administrativas, não entre elas (média 2007–2023). Justificativa quantitativa direta para granularidade de bairro nos painéis de educação.

Site publicado: <https://freirelucas.github.io/rio-edu-lab/>.
Versão atual: **v0.1.0** (ver [`CHANGELOG.md`](./CHANGELOG.md)).

## Estrutura

```
rio-edu-lab/
├── data/
│   ├── manifest.json              # snapshot canônico dos 186 itens
│   ├── manifest_enriched.csv      # derivado: granularidade + temas heurísticos
│   └── raw/probe/                 # respostas brutas do probe da API
├── analysis/
│   ├── 01_manifest_eda.py         # gera CSV enriquecido + relatório 01
│   └── 02_ingestion_probe.py      # probe da API + relatório 02
├── docs/                          # fonte do site (MkDocs Material)
│   ├── index.md
│   ├── data-rio-api.md            # documentação dos endpoints validados
│   └── reports/                   # gerados pelos scripts em analysis/
├── reference/
│   ├── README-acec-hub.md         # descrição do produto-alvo
│   └── acec-hub/                  # esqueleto Python do ACEC-Hub
├── mkdocs.yml
└── .github/workflows/pages.yml    # deploy automático em pushes para main
```

## Reproduzir as análises

```bash
python3 analysis/01_manifest_eda.py
python3 analysis/02_ingestion_probe.py
```

Sem dependências externas; só stdlib do Python 3.10+.

## Site local

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

## Citar

Ver [`CITATION.cff`](./CITATION.cff). Após ativação do webhook Zenodo (instruções em `CHANGELOG.md`), citações também via DOI.

## Histórico

Ver [`CHANGELOG.md`](./CHANGELOG.md) para o que entrou em cada release.
