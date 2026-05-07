---
title: Como editar o deposit Zenodo do rio-edu-lab
description: Passo-a-passo para refinar o deposit v0.5.0 (10.5281/zenodo.20060620) seguindo padrões de comunidades como Generic Mapping Tools.
---

# Editar o deposit Zenodo

> Este guia documenta o **passo manual** que requer login do autor no Zenodo. O webhook GitHub→Zenodo já está ativo; futuros releases mintam DOI automaticamente. Esta página existe para padronizar o que editar **uma vez** no v0.5.0 (e em cada bump major futuro).

## DOI atual

Concept DOI (sempre aponta para a última versão):

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)

## Como inspirar-se nas comunidades de software de pesquisa

A community **Generic Mapping Tools** ([zenodo.org/communities/generic-mapping-tools](https://zenodo.org/communities/generic-mapping-tools/records?q=&l=list&p=1&s=10&sort=newest)) serve de modelo. Padrões observados:

- Título inclui nome humano + "version" + semver: `"The Generic Mapping Tools version 6.6.0"`.
- Description é **resumo funcional estável** (o que o software faz; capacidades), não um changelog.
- Authors com afiliação institucional explícita.
- Keywords de domínio (cartografia, geofísica), não genéricas.
- License destacada (BSD 3-Clause). License múltipla quando aplicável.
- Stats de view/download visíveis por padrão.

## Edição recomendada (para o v0.5.0)

### 1. Título (substitui o auto-gerado pelo GitHub)

```
rio-edu-lab — Atlas Cibernético da Educação Carioca (lab MVP-1) version 0.5.0
```

(Em vez do `freirelucas/rio-edu-lab: v0.5.0` que o GitHub auto-gera.)

### 2. Description em duas partes

**Parte 1 — Resumo funcional estável** (não muda entre versões; descreve o lab):

> rio-edu-lab is a paper-driven research lab on the Education group of data.rio (the open-data portal of the City of Rio de Janeiro, maintained by Instituto Pereira Passos). The lab operationalizes the methodology of Pereira, Braga, Serra & Nadalin (2019) — *Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras*, IPEA — on Rio's municipal IDEB data, using H3 hexagonal grids and equity decomposition. Pipeline ingests, catalogs, and analyzes the 186 items of data.rio's Education group, producing reproducible artifacts (Theil-T decomposition of IDEB by bairro, H3 spatial substrate, accessibility-aware extension in development). Companion Python package `acec` provides canonical statistics with formal additive-decomposition invariants tested in CI.

**Parte 2 — Changelog desta versão**:

> v0.5.0 delivers the Theil-T pipeline foundation: IDEB decomposition by 163 bairros across 33 RAs and 5 APs, robust across 6 series (years × Aprovação/SAEB/IDEB × weighting). Central finding: 66% of IDEB inequality is within-RA, not between. Three companion robustness analyses are included as technical reports (THESHA-Rio 3-level decomposition, FUN-Rio pseudo-cohort transitions, PM-12 intra-city scaling). The full Pereira-style accessibility analysis (isochrones via OSM + decomposition by SES) ships in v0.6. See CHANGELOG.md for full version history.

### 3. Authors com afiliação + ORCID

Quando você tiver ORCID:

- Acessar deposit no Zenodo → Edit
- Em Authors, adicionar o ID ORCID e a afiliação atual (universidade, IPP, ou "Independent researcher")
- Salvar

Atualizar também `CITATION.cff`:

```yaml
authors:
  - family-names: "Freire"
    given-names: "Lucas"
    orcid: "https://orcid.org/0000-XXXX-XXXX-XXXX"
    affiliation: "..."
```

Mints futuros (v0.6+) vão importar automaticamente do `CITATION.cff` editado.

### 4. Keywords ricas (substituir os 3-4 genéricos atuais)

```
educational inequality
spatial inequality
Theil index
GE(1) entropy
H3 hexagonal grid
choropleth bias
modifiable areal unit problem
IDEB
data.rio
Brazilian municipal education
Instituto Pereira Passos
educational policy
urban scaling laws
SAMI
hierarchical decomposition
educational cohorts
pseudo-cohort analysis
```

### 5. Communities (submeter para indexação)

Cada community Zenodo tem um owner que aprova. Considerar pedir entrada em:

- **Open Education** (se existir)
- **Brazilian research output** ou similar
- **Urban analytics** ou **Geospatial open data**

Mesmo que algumas rejeitem, a presença na queue é evidência de outreach.

### 6. Related identifiers

Adicionar:

| Relação | Identifier |
|---|---|
| `IsSupplementTo` | `https://github.com/freirelucas/rio-edu-lab` |
| `IsDerivedFrom` | `https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310` |
| `IsBasedOn` | `https://hdl.handle.net/10419/240730` (Pereira et al. 2019, paper-base) |
| `References` | `https://h3geo.org/` (Uber H3) |
| `References` | `https://www.gov.br/inep/` (INEP/IDEB) |

### 7. License

Confirmar:

- **MIT** (código)
- **CC BY 4.0** (dados derivados — CSVs em `data/processed/`, PNGs em `docs/_assets/`)

Zenodo permite múltiplas licenças. Selecionar ambas no formulário.

## Resultado esperado

O deposit do Zenodo passa a ser:

- Indexável por keywords científicos (vs genéricos hoje).
- Visualmente comparável a comunidades estabelecidas como GMT.
- Discoverable via ORCID quando você tiver.
- Linkado a fontes de dados originais (data.rio) e ferramentas relacionadas (H3, INEP).

Quem cita o lab encontra contexto rico, não apenas o tarball do release.
