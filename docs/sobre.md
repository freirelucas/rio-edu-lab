---
title: Sobre o rio-edu-lab
description: O que o lab é, como citá-lo, glossário dos termos técnicos e padrões do deposit Zenodo.
---

# Sobre

O **rio-edu-lab** é um pipeline aberto de replicação de papers acadêmicos sobre educação contra os 9.855 dados públicos do Rio de Janeiro. **4 estágios:** descoberta via snowball bibliométrico, filtro temático contra a [taxonomia de 10 categorias](dados.md), checagem de cobertura no data.rio, curadoria e replicação. Pipeline reproduzível ponta-a-ponta, 28 testes invariantes verdes em CI, DOI Zenodo. Sem claim de causalidade — só replicação literal de método publicado contra dado público.

**Páginas relacionadas:**

- [Histórico técnico](investigacao.md) — os 15 relatórios cronológicos de como o lab foi se construindo desde o inventário do data.rio.
- [API técnica do data.rio](data-rio-api.md) — endpoints validados pra quem quer baixar dado direto do portal.
- [Reproduzir em 4 minutos](reproduzir.md) — clone limpo → charts da landing.

## Citar

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620) — concept DOI (sempre aponta pra última versão). Ver [`CITATION.cff`](https://github.com/freirelucas/rio-edu-lab/blob/main/CITATION.cff).

```bibtex
@misc{freire2026rioedulab,
  author       = {Freire, Lucas},
  title        = {{rio-edu-lab} --- laborat\'orio de replica\c{c}\~ao de papers em educa\c{c}\~ao aplicados ao Rio},
  year         = {2026},
  version      = {v0.9.0},
  doi          = {10.5281/zenodo.20060620},
  url          = {https://doi.org/10.5281/zenodo.20060620},
}
```

## Glossário

Termos técnicos em ordem alfabética. Cardinalidades pro município do Rio.

**AP — Área de Planejamento.** Maior unidade administrativa do município. 5 APs (Centro, Zona Sul, Zona Norte, Jacarepaguá/Barra, Zona Oeste).

**Aprovação (%).** Percentual de alunos aprovados ao final do ano letivo. Componente de fluxo do IDEB.

**ANOS_INICIAIS / ANOS_FINAIS.** No IDEB, "anos iniciais" cobre o 1º ao 5º ano do fundamental (avaliação no 5º). "Anos finais" cobre 6º ao 9º (avaliação no 9º).

**Bairro.** Menor unidade espacial pública do Rio. 163 bairros oficiais segundo o IPP. Granularidade-alvo do HEX-EDU.

**β (beta) — expoente da lei de escala.** No PM-12: `escolas = A · matrículas^β`. β = 1 = linear; β < 1 = sublinear (bairros maiores sub-servidos); β > 1 = superlinear.

**CRE — Coordenadoria Regional de Educação.** Subdivisão administrativa da Secretaria Municipal de Educação. 11 CREs.

**H3.** Sistema de discretização espacial hexagonal da Uber. Resolução 8 (~0,7 km², ~1593 hexes para o Rio) é a usada no HEX-EDU.

**IDEB.** Índice de Desenvolvimento da Educação Básica, calculado pelo INEP. Produto de Aprovação (fluxo) × Média SAEB normalizada (desempenho). Escala 0–10.

**INEP.** Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira. Calcula e publica o IDEB.

**IPP.** Instituto Pereira Passos. Órgão da Prefeitura do Rio responsável por estatísticas urbanas e pelo portal data.rio.

**MAUP — Modifiable Areal Unit Problem.** Tendência de resultados estatísticos espaciais mudarem com a definição das unidades de área.

**Pseudocoorte.** Aproximação de coorte real quando microdados individuais não estão disponíveis. Confound: alunos transferidos/evadidos entre os pontos.

**RA — Região Administrativa.** 33 RAs subdividem as 5 APs. Granularidade típica de painéis municipais. HEX-EDU mostra que essa granularidade esconde 67% da variância do IDEB.

**RP — Região de Planejamento.** Subdivisão intermediária. ~16 RPs. Pouco usada na prática.

**SAEB.** Sistema de Avaliação da Educação Básica. Prova nacional aplicada bienalmente. Componente de desempenho do IDEB.

**SAMI — Scaling Adjusted Metropolitan Indicator.** Resíduo de uma regressão log-log de leis de escala. SAMI = log(observado) − log(previsto pela lei de escala). Permite comparar bairros depois de controlar pelo tamanho.

**Theil-T (entropia de Theil).** Índice de desigualdade da família GE(α=1):

$$T = \\frac{1}{N} \\sum_i \\frac{y_i}{\\bar y} \\ln\\!\\frac{y_i}{\\bar y}$$

Aceita decomposição aditiva exata em parcelas **between-grupo** + **within-grupo**. Método-base do HEX-EDU e do THESHA-Rio.

**Theil 3-níveis.** Decomposição Theil aplicada a uma hierarquia aninhada (AP → RA-em-AP → bairro-em-RA). Resultado: 8% / 26% / 67%. Ver [Relatório 11](reports/11_thesha_rio.md).

## Padrões do deposit Zenodo

Esta seção documenta os padrões de edição manual do deposit (requer login do autor). Webhook GitHub→Zenodo já está ativo; futuros releases mintam DOI automaticamente.

**Título canônico** (substitui o auto-gerado pelo GitHub):

```
rio-edu-lab — laboratório de replicação de papers em educação aplicados ao Rio version 0.X.0
```

**Description em duas partes.** Parte 1 — resumo funcional estável (não muda entre versões):

> rio-edu-lab is a paper-driven replication laboratory on the Education group of data.rio (the open-data portal of the City of Rio de Janeiro, maintained by Instituto Pereira Passos). The lab maintains an open catalog of education papers — each entry cross-referenced with data.rio coverage, replication status, and (when replicated) a policy insight for municipal managers. Pipeline ingests, catalogs, and analyzes the 9.855 items of data.rio, producing reproducible artifacts (Theil-T decomposition of IDEB by bairro, H3 spatial substrate with Pereira-style accessibility, IDS×IDEB gradient decomposition). Companion Python package `acec` provides canonical statistics with formal additive-decomposition invariants tested in CI.

Parte 2 — changelog da versão específica (varia).

**Keywords** (substituem os 3-4 genéricos auto-gerados):

```
educational inequality · spatial inequality · Theil index · GE(1) entropy
H3 hexagonal grid · choropleth bias · modifiable areal unit problem · IDEB
data.rio · Brazilian municipal education · Instituto Pereira Passos
educational policy · urban scaling laws · SAMI · hierarchical decomposition
educational cohorts · pseudo-cohort analysis
```

**Related identifiers** a adicionar:

| Relação | Identifier |
|---|---|
| `IsSupplementTo` | `https://github.com/freirelucas/rio-edu-lab` |
| `IsDerivedFrom` | `https://www.data.rio/search?orgid=OlP4dGNtIcnD3RYf` |
| `IsBasedOn` | `https://hdl.handle.net/10419/240730` (Pereira et al. 2019) |
| `References` | `https://h3geo.org/` (Uber H3) |
| `References` | `https://www.gov.br/inep/` (INEP/IDEB) |

**Licenças** (Zenodo permite múltiplas): MIT (código) + CC BY 4.0 (dados derivados).

**Padrão de referência:** community [Generic Mapping Tools](https://zenodo.org/communities/generic-mapping-tools/records?q=&l=list&p=1&s=10&sort=newest) — título humano + version, description funcional estável (não changelog), authors com afiliação + ORCID, keywords de domínio.

## Licença

Código MIT · dados derivados CC BY 4.0 · dados brutos seguem licença original do data.rio / IPP.
