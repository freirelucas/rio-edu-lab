---
title: Como editar o deposit Zenodo do rio-edu-lab
description: Passo-a-passo para refinar o deposit v0.7 (10.5281/zenodo.20060620) seguindo padrões de comunidades como Generic Mapping Tools.
---

# Editar o deposit Zenodo

> Este guia documenta o **passo manual** que requer login do autor no Zenodo. O webhook GitHub→Zenodo já está ativo; futuros releases mintam DOI automaticamente. Esta página existe para padronizar o que editar a cada bump major (v0.7 e seguintes).

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

## Edição recomendada (para o v0.7)

### 1. Título (substitui o auto-gerado pelo GitHub)

```
rio-edu-lab — laboratório de replicação de papers em educação aplicados ao Rio version 0.7.0
```

(Em vez do `freirelucas/rio-edu-lab: v0.7.0` que o GitHub auto-gera.)

### 2. Description em duas partes

**Parte 1 — Resumo funcional estável** (não muda entre versões; descreve o lab):

> rio-edu-lab is a paper-driven replication laboratory on the Education group of data.rio (the open-data portal of the City of Rio de Janeiro, maintained by Instituto Pereira Passos). The lab maintains an open catalog of education papers — each entry cross-referenced with data.rio coverage, replication status, and (when replicated) a policy insight for municipal managers. Pipeline ingests, catalogs, and analyzes the 186 items of data.rio's Education group, producing reproducible artifacts (Theil-T decomposition of IDEB by bairro, H3 spatial substrate with Pereira-style accessibility, IDS×IDEB gradient decomposition). Companion Python package `acec` provides canonical statistics with formal additive-decomposition invariants tested in CI.

**Parte 2 — Changelog desta versão**:

> v0.7.0 introduces the paper catalog as primary product: 12 seed papers (3 fully/partially replicated + 5 catalogued for upcoming replications + 4 methodological reference). Each catalog entry crosses paper data requirements with data.rio item coverage. Conceptual rebrand from "Atlas Cibernético da Educação Carioca" (v0.5–v0.6.2) to "laboratório de replicação de papers em educação aplicados ao Rio". Concept DOI preserved. Two active products: HEX-EDU (Pereira 2019 IPEA — H3 accessibility, v0.6.1) and VULN-EDU (Reardon 2011 — IDS×IDEB gradient, v0.1). See CHANGELOG.md for full version history.

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
