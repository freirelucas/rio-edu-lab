# rio-edu-lab

[![pages](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml)
[![ci](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
**Laboratório de replicação de papers em educação aplicados ao Rio.** Catálogo aberto de papers seminais (foco em educação) cruzado com o [Grupo Educação do data.rio](https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310). Cada entrada do catálogo mapeia requisitos de dados → itens disponíveis → status de replicação no lab + insight para gestores quando replicado.

**Achado-central que originou o lab**: na decomposição Theil-T do IDEB por bairro, **66% da desigualdade está dentro das RAs** (não entre). Coropléticos por RA mascaram a maior parte da variância. Robusto em 6 séries (anos iniciais/finais, ponderação por matrícula, Aprovação/SAEB/IDEB).

**Estado atual (v0.7)**: 12 papers seed catalogados (3 já replicados, 5 alvo de replicação leve, 4 metodológicos); roadmap = expandir para 100 papers. 2 produtos ativos:

- **HEX-EDU**: v0.5 (Theil sobre H3 grid, **66% within-RA**) + v0.6.1 (acessibilidade Pereira-style com distância haversine, 1022 escolas elegíveis). Operacionaliza Pereira et al. 2019.
- **VULN-EDU v0.1**: cruzamento IDS Censo 2010 × IDEB 2023 por bairro. Achado — gradiente SES-educacional real mas modesto (Pearson +0.40, R²=0.16); **39% dos bairros estão em quadrantes não-concordantes** (resilientes + sub-performance). Operacionaliza Reardon 2011.

**Renomeação na v0.7.** Até a v0.6.2 o lab foi apresentado como "Atlas Cibernético da Educação Carioca". A v0.7 reposiciona o trabalho como laboratório de replicação de papers; o catálogo público (`docs/papers/`) é o produto primário. DOI Zenodo preservado.

Site publicado: <https://freirelucas.github.io/rio-edu-lab/>.

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

Ver [`CITATION.cff`](./CITATION.cff). DOI Zenodo: <https://doi.org/10.5281/zenodo.20060620>.

## Histórico

Ver [`CHANGELOG.md`](./CHANGELOG.md) para o que entrou em cada release.
