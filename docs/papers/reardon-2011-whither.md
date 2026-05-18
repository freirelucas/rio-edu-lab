---
title: "Reardon (2011) — The widening academic-achievement gap between the rich and the poor: New evidenc"
description: "Documenta que o gap de desempenho entre o quintil mais rico e o mais pobre nos EUA cresceu ~40% desde os anos 1970 e excede o gap racial branco-negro. Método: o"
---

# Reardon (2011)

**The widening academic-achievement gap between the rich and the poor: New evidence and possible explanations**

_Whither Opportunity? (Duncan & Murnane eds.), Russell Sage Foundation, ch. 5_

<a href="https://cepa.stanford.edu/sites/default/files/reardon%20whither%20opportunity%20-%20chapter%205.pdf" target="_blank">https://cepa.stanford.edu/sites/default/files/reardon%20whither%20opportunity%20-%20chapter%205.pdf</a>

<div class="status-hero status-partial" aria-label="Status no lab: Replicação parcial">
  <span class="icon" aria-hidden="true">◐</span>
  <div class="text">
    <span class="label">Replicação parcial</span>
    <span class="headline">Operacionalizado no produto <a href="../../produtos/vuln_edu/">VULN-EDU</a>. Ver <a href="../../reports/15_vuln_edu/">relatório 15</a>.</span>
  </div>
</div>

**Citações (OpenAlex, 2026-05-18):** 1.146

## Resumo

Documenta que o gap de desempenho entre o quintil mais rico e o mais pobre nos EUA cresceu ~40% desde os anos 1970 e excede o gap racial branco-negro. Método: ordenar por SES, ordenar por desempenho, decompor o gap por percentil.

## Categorias

- **Área:** desigualdade, SES e desempenho, tendências longitudinais
- **Método:** gap por percentil, decomposição de variância
- **Brasil-específico:** não

## Requisitos de dados × cobertura no data.rio

| Requisito | Status | Item data.rio |
|---|---|---|
| indicador socioeconômico granular | ✅ disponível no data.rio | `ids-rm-2010` |
| indicador de desempenho educacional | ✅ disponível no data.rio | `ideb-municipal-bairros` |

## Replicação no lab

- **Produto associado:** VULN-EDU
- **Relatórios:** [15](../reports/15_vuln_edu.md)
- **Scripts:** `analysis/28_*.py`, `analysis/29_*.py`, `analysis/30_*.py`

<div class="policy-callout">
  <header>
    <span class="icon" aria-hidden="true">🔬</span>
    <h3>Insight da replicação aplicado ao Rio</h3>
  </header>
  <div class="body">
    <div class="cell"><strong>Achado replicado</strong>: Gradiente SES × IDEB no Rio existe mas é modesto (R²=0.16); 39% dos bairros estão em quadrantes não-concordantes (resilientes ou sub-performance) — desfaz a leitura "Zona Sul = privilégio uniforme".</div>
  </div>
  <footer><a href="../../reports/15_vuln_edu/">Como auditar: relatório 15 →</a></footer>
</div>


## Referência completa

Reardon (2011). _The widening academic-achievement gap between the rich and the poor: New evidence and possible explanations_. Whither Opportunity? (Duncan & Murnane eds.), Russell Sage Foundation, ch. 5.

[← Voltar ao catálogo](index.md)
