# rio-edu-lab

[![pages](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml)
[![ci](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
Laboratório **paper-driven** sobre o Grupo Educação do [data.rio](https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310). Operacionaliza o método **Pereira, Braga, Serra & Nadalin (2019)** [IPEA — Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras](https://hdl.handle.net/10419/240730) sobre o IDEB municipal carioca.

**Achado central da v0.5**: na decomposição Theil-T do IDEB por bairro, **66% da desigualdade está dentro das RAs** (não entre). Coropléticos por RA mascaram a maior parte da variância. Robusto em 6 séries (anos iniciais/finais, ponderação por matrícula, Aprovação/SAEB/IDEB).

**Status do MVP**: 2 produtos ativos.

- **HEX-EDU**: v0.5 (Theil sobre H3 grid, **66% within-RA**) + v0.6.1 (acessibilidade Pereira-style com distância haversine, 1022 escolas elegíveis). v0.7 planejado para isócronas OSM reais.
- **VULN-EDU v0.1**: cruzamento IDS Censo 2010 × IDEB 2023 por bairro. Achado — gradiente socioeconômico-educacional real mas modesto (Pearson +0.40, R²=0.16); **39% dos bairros estão em quadrantes não-concordantes** (resilientes + sub-performance).

A v0.6 consolidou o catálogo da v0.5 que tinha 4 produtos com fundamentação acadêmica heterogênea — detalhes no [CHANGELOG](./CHANGELOG.md).

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
