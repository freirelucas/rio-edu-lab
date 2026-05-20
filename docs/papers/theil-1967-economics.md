---
title: "Theil (1967) — Onde está a desigualdade educacional no Rio?"
description: "66% da variância do IDEB municipal carioca está dentro das Regiões Administrativas, não entre. Robusto em 6 séries × 9 anos (5º/9º ano, ponderado por matrícula, Aprovação/SAEB/IDEB). Nenhuma série cru"
---

# Onde está a desigualdade educacional no Rio?

**Dentro dos bairros — não entre regiões.**

66% da variância do IDEB municipal carioca está dentro das Regiões Administrativas, não entre. Robusto em 6 séries × 9 anos (5º/9º ano, ponderado por matrícula, Aprovação/SAEB/IDEB). Nenhuma série cruza a paridade 50%.

<div class="status-hero status-full" aria-label="Status no lab: Replicado">
  <span class="icon" aria-hidden="true">✓</span>
  <div class="text">
    <span class="label">Replicado</span>
    <span class="headline">Operacionalizado no produto <a href="../../produtos/hex_edu/">HEX-EDU</a>. Ver <a href="../../reports/06_theil_ideb/">relatório 06</a>.</span>
  </div>
</div>


## O que esse paper diz

Introduz o índice T da entropia (GE(1)) e a decomposição aditiva between/within. Base metodológica para todas as análises de desigualdade decomponível do lab.

## Aplicado ao Rio

Decomposição Theil revela que 66% da desigualdade do IDEB municipal carioca está dentro das RAs, não entre — coropléticos por RA escondem a maior parte do sinal. Operacionalizado no produto **HEX-EDU** ([detalhe técnico](../produtos/hex_edu.md)).

**Como auditar:**

- [Relatório 06](../reports/06_theil_ideb.md)
- [Relatório 07](../reports/07_hex_edu_static.md)
- [Relatório 09](../reports/09_anos_finais.md)
- [Relatório 11](../reports/11_thesha_rio.md)

## Provenance

**Economics and Information Theory**

_Theil (1967). North-Holland Publishing._

<a href="https://www.worldcat.org/title/economics-and-information-theory/oclc/489908" target="_blank">https://www.worldcat.org/title/economics-and-information-theory/oclc/489908</a>

**Citações (OpenAlex, 2026-05-18):** 7.659

**Área:** desigualdade, teoria da informação

**Método:** entropia generalizada, decomposição aditiva

### Requisitos de dados × cobertura no data.rio

| Requisito | Status | Item data.rio |
|---|---|---|
| valores positivos por unidade | ✅ disponível no data.rio | `ideb-municipal-bairros` |
| agrupamento hierárquico | ✅ disponível no data.rio | `bairros-ipp` |

**Código:** `analysis/10_*.py`, `analysis/16_*.py`, `analysis/17_*.py`, `analysis/18_*.py`

[← Voltar aos papers](index.md)
