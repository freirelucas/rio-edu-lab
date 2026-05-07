# rio-edu-lab

[![pages](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml)
[![ci](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
Laboratório exploratório sobre o Grupo Educação do [data.rio](https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310). Sandbox que precede e alimenta o produto **ACEC-Hub** (cuja estrutura-alvo está versionada em `reference/`).

**Achado-headline (v0.5.0)**: três padrões convergentes mostram que a granularidade de bairro é a escala correta de intervenção em educação no Rio Municipal.

1. **Decomposição espacial Theil em 3 níveis** (THESHA-Rio): 67% da desigualdade do IDEB está entre bairros dentro da mesma RA; só 8% entre Áreas de Planejamento.
2. **Trajetórias 5º→9º ano** (FUN-Rio): 87% das pseudocoortes pioram; bairros que começam mais altos caem mais (slope −0.53), refutando o efeito Mateus.
3. **Lei de escala** (PM-12): alocação de escolas é sublinear (β = 0.77) — bairros maiores em matrícula têm desproporcionalmente menos escolas.

Site publicado: <https://freirelucas.github.io/rio-edu-lab/>.
Versão atual: **v0.5.0** (ver [`CHANGELOG.md`](./CHANGELOG.md)).

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
