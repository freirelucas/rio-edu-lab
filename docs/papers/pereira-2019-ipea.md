---
title: "Pereira et al. (2019) — Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras —"
description: "Discretiza o território urbano em hexágonos H3 e calcula acessibilidade a oportunidades (educação, saúde, emprego) ponderada por proximidade temporal via isócro"
---

# Pereira et al. (2019)

**Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019**

_IPEA Texto para Discussão 2535_

<a href="https://hdl.handle.net/10419/240730" target="_blank">https://hdl.handle.net/10419/240730</a>

<div class="status-hero status-partial" aria-label="Status no lab: Replicação parcial">
  <span class="icon" aria-hidden="true">◐</span>
  <div class="text">
    <span class="label">Replicação parcial</span>
    <span class="headline">Operacionalizado no produto <a href="../../produtos/hex_edu/">HEX-EDU</a>. Ver <a href="../../reports/14_acessibilidade/">relatório 14</a>.</span>
  </div>
</div>

**Citações (OpenAlex, 2026-05-18):** 79

## Resumo

Discretiza o território urbano em hexágonos H3 e calcula acessibilidade a oportunidades (educação, saúde, emprego) ponderada por proximidade temporal via isócronas OSM e pela qualidade da oportunidade. Decompõe por renda e raça em 7 capitais brasileiras.

## Categorias

- **Área:** acessibilidade, equidade espacial, geografia urbana
- **Método:** H3 grid, acessibilidade ponderada, decomposição por SES
- **Brasil-específico:** sim

## Requisitos de dados × cobertura no data.rio

| Requisito | Status | Item data.rio |
|---|---|---|
| geometria de escolas | ✅ disponível no data.rio | `0a220ea7972d4adf85b3e63d23a4b9b1` |
| indicador de qualidade educacional | ✅ disponível no data.rio | `ideb-municipal-bairros` |
| rede viária / tempos de viagem | ⚠️ dado externo necessário | `—` |
| geometria de bairros | ✅ disponível no data.rio | `bairros-ipp` |

## Replicação no lab

- **Produto associado:** HEX-EDU
- **Relatórios:** [14](../reports/14_acessibilidade.md)
- **Scripts:** `analysis/25_*.py`, `analysis/26_*.py`, `analysis/27_*.py`

<div class="policy-callout">
  <header>
    <span class="icon" aria-hidden="true">🔬</span>
    <h3>Insight da replicação aplicado ao Rio</h3>
  </header>
  <div class="body">
    <div class="cell"><strong>Achado replicado</strong>: AP 3 (Zona Norte) lidera acesso ponderado por IDEB; Zona Sul tem IDEB médio mais alto mas baixa densidade. Coropléticos por AP escondem variância intra-AP.</div>
  </div>
  <footer><a href="../../reports/14_acessibilidade/">Como auditar: relatório 14 →</a></footer>
</div>


## Referência completa

Pereira, Braga, Serra, Nadalin (2019). _Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019_. IPEA Texto para Discussão 2535.

[← Voltar ao catálogo](index.md)
