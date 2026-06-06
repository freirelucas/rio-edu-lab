---
title: "Reardon (2011) — Riqueza prediz boa escola no Rio?"
description: "O gradiente SES → IDEB existe (Pearson +0,40) mas é modesto. 22% dos bairros são resilientes (baixo SES, bom IDEB) e 17% sub-performam (bom SES, baixo IDEB) — quase metade desafia a leitura "Zona Sul"
---

# Riqueza prediz boa escola no Rio?

**Parcialmente. R²=0,16; 39% dos bairros desafiam o gradiente.**

O gradiente SES → IDEB existe (Pearson +0,40) mas é modesto. 22% dos bairros são resilientes (baixo SES, bom IDEB) e 17% sub-performam (bom SES, baixo IDEB) — quase metade desafia a leitura "Zona Sul = privilégio uniforme".

<div class="status-hero status-partial" aria-label="Status no lab: Replicação parcial">
  <span class="icon" aria-hidden="true">◐</span>
  <div class="text">
    <span class="label">Replicação parcial</span>
    <span class="headline">Operacionalizado no produto <a href="../../produtos/vuln_edu/">VULN-EDU</a>. Ver <a href="../../reports/15_vuln_edu/">relatório 15</a>.</span>
  </div>
</div>


## O que esse paper diz

Documenta que o gap de desempenho entre o quintil mais rico e o mais pobre nos EUA cresceu ~40% desde os anos 1970 e excede o gap racial branco-negro. Método: ordenar por SES, ordenar por desempenho, decompor o gap por percentil.

## Aplicado ao Rio

Gradiente SES × IDEB no Rio existe mas é modesto (R²=0.16); 39% dos bairros estão em quadrantes não-concordantes (resilientes ou sub-performance) — desfaz a leitura "Zona Sul = privilégio uniforme". Operacionalizado no produto **VULN-EDU** ([detalhe técnico](../produtos/vuln_edu.md)).

**Como auditar:**

- [Relatório 15](../reports/15_vuln_edu.md)

## Provenance

**The widening academic-achievement gap between the rich and the poor: New evidence and possible explanations**

_Reardon (2011). Whither Opportunity? (Duncan & Murnane eds.), Russell Sage Foundation, ch. 5._

<a href="https://cepa.stanford.edu/sites/default/files/reardon%20whither%20opportunity%20-%20chapter%205.pdf" target="_blank">https://cepa.stanford.edu/sites/default/files/reardon%20whither%20opportunity%20-%20chapter%205.pdf</a>

**Citações (OpenAlex, 2026-06-06):** 1.146

**Área:** desigualdade, SES e desempenho, tendências longitudinais

**Método:** gap por percentil, decomposição de variância

### Requisitos de dados × cobertura no data.rio

| Requisito | Status | Item data.rio |
|---|---|---|
| indicador socioeconômico granular | ✅ disponível no data.rio | `ids-rm-2010` |
| indicador de desempenho educacional | ✅ disponível no data.rio | `ideb-municipal-bairros` |

**Código:** `analysis/28_*.py`, `analysis/29_*.py`, `analysis/30_*.py`

[← Voltar aos papers](index.md)
