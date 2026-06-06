---
title: "Pereira et al. (2019) — Qual zona do Rio tem mais acesso a boas escolas?"
description: "Acesso ponderado por IDEB: AP 3 com 113, AP 4 (Jacarepaguá/Barra) com 29. A Zona Sul tem escolas excelentes, mas espalhadas e poucas — por isso o acesso ponderado fica abaixo."
---

# Qual zona do Rio tem mais acesso a boas escolas?

**AP 3 (Zona Norte) lidera — não a Zona Sul.**

Acesso ponderado por IDEB: AP 3 com 113, AP 4 (Jacarepaguá/Barra) com 29. A Zona Sul tem escolas excelentes, mas espalhadas e poucas — por isso o acesso ponderado fica abaixo.

<div class="status-hero status-partial" aria-label="Status no lab: Replicação parcial">
  <span class="icon" aria-hidden="true">◐</span>
  <div class="text">
    <span class="label">Replicação parcial</span>
    <span class="headline">Operacionalizado no produto <a href="../../produtos/hex_edu/">HEX-EDU</a>. Ver <a href="../../reports/14_acessibilidade/">relatório 14</a>.</span>
  </div>
</div>


## O que esse paper diz

Discretiza o território urbano em hexágonos H3 e calcula acessibilidade a oportunidades (educação, saúde, emprego) ponderada por proximidade temporal via isócronas OSM e pela qualidade da oportunidade. Decompõe por renda e raça em 7 capitais brasileiras.

## Aplicado ao Rio

AP 3 (Zona Norte) lidera acesso ponderado por IDEB; Zona Sul tem IDEB médio mais alto mas baixa densidade. Coropléticos por AP escondem variância intra-AP. Operacionalizado no produto **HEX-EDU** ([detalhe técnico](../produtos/hex_edu.md)).

**Como auditar:**

- [Relatório 14](../reports/14_acessibilidade.md)

## Provenance

**Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019**

_Pereira, Braga, Serra, Nadalin (2019). IPEA Texto para Discussão 2535._

<a href="https://hdl.handle.net/10419/240730" target="_blank">https://hdl.handle.net/10419/240730</a>

**Citações (OpenAlex, 2026-06-06):** 79

**Área:** acessibilidade, equidade espacial, geografia urbana

**Método:** H3 grid, acessibilidade ponderada, decomposição por SES

**🇧🇷 Brasil-específico.**

### Requisitos de dados × cobertura no data.rio

| Requisito | Status | Item data.rio |
|---|---|---|
| geometria de escolas | ✅ disponível no data.rio | `0a220ea7972d4adf85b3e63d23a4b9b1` |
| indicador de qualidade educacional | ✅ disponível no data.rio | `ideb-municipal-bairros` |
| rede viária / tempos de viagem | ⚠️ dado externo necessário | `—` |
| geometria de bairros | ✅ disponível no data.rio | `bairros-ipp` |

**Código:** `analysis/25_*.py`, `analysis/26_*.py`, `analysis/27_*.py`

[← Voltar aos papers](index.md)
