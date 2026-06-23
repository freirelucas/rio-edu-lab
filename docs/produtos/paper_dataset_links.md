---
title: Papers que citam datasets com DOI declarado
description: Sinal declarativo paper↔dataset via OpenAlex referenced_works filtered por type=dataset. Não inferência IDF — fato bibliográfico.
---

# Papers que citam datasets com DOI declarado

Resultado do `analysis/45d_dataset_refs.py` (v0.17.f). Pra cada candidate do funil, OpenAlex `referenced_works` foi filtrado por `type=dataset` — ou seja, papers que **declararam citar** um dataset com DOI canônico. Sinal de ~100% precisão (declaração do autor, não inferência semântica).

**Estado**: 2 papers com ≥1 dataset ref de 2266 candidates no funil.

## Top papers por sinal dataset

| BR? | n_refs | citações | Year | Paper | Dataset DOIs |
|---|---:|---:|---|---|---|
|   | 2 | 2933 | 2001 | Teacher Turnover and Teacher Shortages: An Organizational An | [Teacher Turnover, Teacher Shortages, and](https://doi.org/https://doi.org/10.1037/e384452004-001)<br>Projections of education statistics to 2 |
|   | 1 | 408 | 2001 | Teacher Turnover, Teacher Shortages, and the Organization of | Projections of education statistics to 2 |

## Como funciona

O OpenAlex captura o campo `referenced_works` de cada paper — IDs OpenAlex das obras CITADAS (não similaridade). Pra cada paper do priority pool (fully-covered + BR + top-cit), `analysis/45d_dataset_refs.py` faz batch-lookup dos refs e filtra `type ∈ {dataset, software-source-code, software, supplementary-materials}`.

Recomendação dos 5 agentes especialistas v0.16: este é o sinal **mais forte** pra paper↔dataset linkage (precisão ~100%) — autor declarou no manuscript que cita o dataset com DOI.