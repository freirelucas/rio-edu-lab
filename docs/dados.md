---
title: Dados — rio-edu-lab
description: 9.855 itens públicos no data.rio. 4 ativados pelo catálogo. 9.851 inexplorados — território vasto pra papers futuros.
---

# Dados

**9.855 itens públicos no data.rio. 4 ativados pelo catálogo. 9.851 inexplorados.** Cada paper do funil é matchado contra esse substrato — quando bate, vira candidato a replicação; quando não, vira sinal do que falta no portal.

<div class="chart-duo" markdown>

<div class="chart-card" markdown>
#### :material-chart-donut: Cobertura atual

<div data-chart="../_assets/charts/data_rio_coverage.json"></div>

Cobertura é baixa **por construção**: o catálogo curado tem só 12 papers, e cada um cita 1-4 itens. O resto do portal é território pra próximos sprints.
</div>

<div class="chart-card" markdown>
#### :material-chart-bar: Temas no funil

<div data-chart="../_assets/charts/themes.json"></div>

253 candidatos do snowball, distribuídos por categoria de dado que precisariam pra replicar. **Performance agregada** lidera (estilo IDEB); **microdado de aluno** aparece forte, mas é majoritariamente *external* no Rio (INEP não publica nominal). Os números por categoria saem do funil — leia direto no gráfico.
</div>

</div>

## 10 categorias canônicas

A taxonomia em [`data/requirements_taxonomy.yml`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/requirements_taxonomy.yml) define **10 categorias** de dado que papers de educação tipicamente requerem. Cada categoria mapeia pra itens do data.rio via aliases EN+PT.

| Categoria | Nível | Cobertura típica no data.rio |
|---|---|---|
| `geometry-schools` | agregado | Feature Service IPP — disponível |
| `geometry-neighborhoods` | agregado | Limite de Bairros IPP — disponível |
| `performance-aggregated` | agregado | IDEB por escola/bairro — disponível |
| `ses-aggregated` | agregado | IDS Censo, IPS — disponível |
| `spatial-partition` | meta | RA/AP/RP — disponível |
| `enrollment-counts` | agregado | Matrículas anuais — parcial |
| `travel-network` | meta | OSM + GTFS — **externo** |
| `microdata-student` | individual | INEP nominal — **externo** |
| `microdata-household` | individual | PNAD/Censo individual — **externo** |
| `longitudinal-cohort` | individual | RAIS/INEP coorte — **externo** |

7 categorias têm cobertura no data.rio; 3 são intrinsecamente externas (microdado individual nominal não é publicado pela LGPD / convenção INEP).

## 4 itens hoje ativos

Os 4 itens do data.rio cobertos pelo catálogo curado, ordenados por número de papers que os usam:

| Item data.rio | Papers que usam | Categoria |
|---|---|---|
| `ideb-municipal-bairros` | 9 papers (Theil, Reardon, Pereira, Coleman, Hanushek...) | `performance-aggregated` |
| `0a220ea7972d4adf85b3e63d23a4b9b1` (Escolas Municipais) | 3 (Pereira, Hoxby, Coleman) | `geometry-schools` |
| `bairros-ipp` (Limite de Bairros IPP) | 3 (Theil, Reardon, Pereira) | `geometry-neighborhoods` |
| `ids-rm-2010` (IDS Censo 2010 RM) | 3 (Reardon, Soares & Andrade, Alves & Soares) | `ses-aggregated` |

Reverse-browse: pra cada item do data.rio referenciado pelo catálogo, [Papers por item do data.rio](papers-by-data-rio.md) lista quais papers o utilizam e que requisito ele atende. Gerado por `analysis/41_match_requirements.py`.

## Distribuição por tipo (top-10)

O portal `data.rio` é uma instância do ArcGIS Hub. Snapshot 2026-05-18:

| Tipo | Quantidade |
|---|---|
| PDF | 4.073 |
| Image | 1.115 |
| Microsoft Excel | 987 |
| Feature Service | 876 |
| Web Map | 506 |
| Hub Page | 391 |
| Scene Service | 331 |
| Dashboard | 294 |
| Web Mapping Application | 269 |
| Form | 197 |

PDFs dominam (estudos cariocas, notas técnicas). Excels e Feature Services são o grosso do dado tabular/geoespacial replicável.

## Como achar dado pra um paper novo

O pipeline de matching segue 3 passos:

1. **Extrair requisitos do paper.** O script `46_extract_requirements.py` tokeniza título + abstract do candidato e classifica em uma das 10 categorias da taxonomia (top-3 sugestões por candidato, com score).
2. **Matchar contra manifest data.rio.** O script `47_check_coverage.py` toma cada categoria sugerida e busca best-match no manifest (9.855 itens) por scoring **IDF-weighted** (unigrams + bigrams). Score ≥5,0 = `available`; ≥2,0 = `partial`; categoria sem cobertura no portal = `external`; abaixo disso = `missing`.
3. **Promover ao catálogo (curador).** Quando há cobertura e o paper é relevante, o curador marca `accept` em `papers_funnel.yml` e roda `48_promote_funnel.py` pra gerar entrada em `papers_catalog.yml`.

Calibração atual: o best-match quase sempre acha algo no portal; a pergunta é se o score IDF passa o corte de `available` (≥5,0) ou cai pra `partial`/`missing`. Os 3 papers `unfeasible` do catálogo têm categorias intrinsecamente externas (microdado), não score baixo.

## Inexplorado — 9.851 itens órfãos

A grande maioria do portal não foi citada por nenhum paper do catálogo. Isso é **oportunidade**, não problema: novos seeds bibliométricos (outras subáreas de educação, ou subáreas adjacentes como saúde escolar, transporte, urbanismo educacional) puxam papers que poderiam usar:

- 4.073 PDFs com estudos cariocas (Estudos Cariocas, Notas Técnicas IPP)
- 1.115 Images (mapas históricos, infográficos)
- 987 Excels não auditados (planilhas de matrícula, infraestrutura, IDS por unidade)
- 876 Feature Services geoespaciais

Modo reverso ("item → papers candidatos") não existe ainda — seria feedback loop valioso pra calibrar Stage 2.

## API técnica do data.rio

Quem precisa baixar dado direto: o portal é ArcGIS Hub padrão, sem documentação oficial do IPP. Os endpoints úteis estão validados em [API do data.rio (referência técnica)](data-rio-api.md).

[API técnica →](data-rio-api.md){ .md-button } [Papers por item →](papers-by-data-rio.md){ .md-button } [Reproduzir pipeline →](reproduzir.md){ .md-button }
