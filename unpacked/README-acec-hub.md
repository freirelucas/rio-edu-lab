# ACEC-Hub — Atlas Cibernético da Educação Carioca

> Operacionalização de papers acadêmicos sobre os 186 itens do Grupo Educação do [data.rio](https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310), na forma de análises reproduzíveis e visualizações interativas.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data License: CC BY 4.0](https://img.shields.io/badge/Data-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Status: WIP](https://img.shields.io/badge/status-work%20in%20progress-orange.svg)]()

## Missão

O ACEC-Hub aplica métodos quantitativos de papers seminais ao acervo educacional aberto da Cidade do Rio de Janeiro — produzido pelo Instituto Pereira Passos (IPP) e disponibilizado via portal data.rio. Cada produto tem três componentes acoplados: **paper-base** (referência metodológica) + **dados do data.rio** + **visualização interativa**.

A premissa é simples: existe método publicado, existem dados disponíveis, falta a aplicação operacional ao Rio com visualização que sirva tanto a pesquisadores quanto a gestores.

## Acervo de referência

O Grupo Educação do data.rio contém **186 itens** (atualizado em `manifest.json`):

| Tipo | Quantidade |
|------|-----------:|
| Microsoft Excel (séries históricas) | 127 |
| PDF (Coleção Estudos Cariocas, Rio Estudos, Notas Técnicas IPP, Cadernos do Rio) | 35 |
| Image (mapas temáticos) | 6 |
| Document Link | 6 |
| Feature Service (camadas SIG) | 4 |
| Web Mapping Application | 4 |
| CSV Collection | 2 |
| Code Attachment | 1 |
| Hub Site Application | 1 |

Cobertura temporal: 1991–2024. Granularidades: município, AP, RP, RA, CRE, bairro, escola.

## Produtos

A roadmap completa contempla 15 produtos, organizados em quatro eixos. O foco atual é o eixo de **operacionalização de papers** (sem science of science nesta fase).

### Em desenvolvimento (MVP-1)

| Produto | Paper-base | Status |
|---------|-----------|:------:|
| **HEX-EDU** — Mapa H3 de inequidade educacional | Pereira et al. (2019) + Theil (1967) | 🟡 WIP |

### Próximos (priorizados)

| Produto | Paper-base | Status |
|---------|-----------|:------:|
| **THESHA-Rio** — Decompositor de desigualdade educacional | Bourguignon, Ferreira & Menéndez (2007) | ⚪ Planejado |
| **PM-12** — Comparador inter-capitais com SAMI | Bettencourt et al. (2010) + Heinrich Mora et al. (2023) | ⚪ Planejado |
| **FUN-Rio** — Trajetórias de coortes educacionais | Mare (1980) + Reardon & Owens (2014) | ⚪ Planejado |

### Backlog (avaliação futura)

PSA-Rio (índice composto de stress), PósPAN-Rio (recuperação pós-pandemia), Cronotopia (quebras estruturais), demais produtos do roadmap original.

## Estrutura do repositório

```
acec-hub/
├── manifest.json           # Inventário canônico dos 186 itens do data.rio
├── src/acec/               # Pacote Python compartilhado entre produtos
│   ├── ingest/             # Cliente ArcGIS Hub API
│   ├── transform/          # Normalização de séries
│   ├── geo/                # H3, projeções, joins espaciais
│   └── viz/                # Helpers de visualização
├── products/               # Um diretório por produto
│   └── hex-edu/            # MVP-1
│       ├── notebooks/
│       ├── app/            # Streamlit
│       ├── paper/          # Quarto manuscript
│       └── tests/
├── data/
│   ├── raw/                # Download bruto (gitignored)
│   ├── interim/            # Limpeza (gitignored)
│   └── processed/          # Parquet final (commitado quando leve)
├── docs/                   # Quarto Website do ACEC-Hub
└── .github/workflows/      # CI + atualização periódica do manifest
```

## Quickstart

```bash
git clone https://github.com/freirelucas/acec-hub.git
cd acec-hub

# Ambiente Python (uv recomendado, mas pip funciona)
uv venv && source .venv/bin/activate
uv pip install -e .

# Atualizar manifest e baixar dados brutos
python -m acec.ingest.arcgis --refresh-manifest
python -m acec.ingest.arcgis --download-type "Microsoft Excel"

# Rodar o produto HEX-EDU
streamlit run products/hex-edu/app/streamlit_app.py
```

## Princípios

- **Paper-driven**: todo produto cita o paper-base no README e replica seu método antes de estender.
- **Reprodutibilidade**: notebooks executáveis ponta-a-ponta, dados versionados via DVC quando necessário, CI testando ingestão.
- **Atribuição**: data.rio e IPP creditados em toda visualização; `CITATION.cff` mantido atualizado.
- **Honestidade metodológica**: caveats explicitados no README de cada produto (MAUP, comparabilidade, mudanças metodológicas do INEP/IBGE).

## Como citar

Ver [`CITATION.cff`](./CITATION.cff). Releases recebem DOI via Zenodo.

## Reconhecimentos

- **Instituto Pereira Passos (IPP)** — produção e disponibilização dos dados via data.rio.
- **Prefeitura da Cidade do Rio de Janeiro** — política de dados abertos.
- Comunidade open source: ArcGIS Hub, Uber H3, Streamlit, Quarto, DuckDB.

## Licença

- **Código**: [MIT](./LICENSE)
- **Dados derivados e visualizações**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Dados brutos**: licença original do data.rio / IPP.

## Status

Pesquisa pessoal, em desenvolvimento ativo. Issues e contribuições bem-vindas.
