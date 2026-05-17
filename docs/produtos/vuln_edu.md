---
title: VULN-EDU — gradiente socioeconômico × educacional por bairro
description: Cruzamento IDS (Censo 2010) × IDEB 2023 por bairro do Rio. Achado v0.1 — 40% de correlação, mas só 16% de R²; metade dos bairros está em quadrantes não-concordantes.
---

# 🧭 VULN-EDU

> **Vulnerabilidade socioeconômica prediz desempenho educacional no Rio?** Parcialmente. A correlação IDS × IDEB existe (Pearson +0.40), mas o IDS explica só **16%** da variância do IDEB municipal. **Quase metade dos bairros desafia o gradiente esperado** — 22% são resilientes (baixo SES, bom IDEB), 17% sub-performam (bom SES, baixo IDEB).

[![paper](https://img.shields.io/badge/paper--base-Reardon_2011-008572)](https://cepa.stanford.edu/sites/default/files/reardon%20whither%20opportunity%20-%20chapter%205.pdf)
[![v0.1](https://img.shields.io/badge/v0.1-IDS_%C3%97_IDEB_bairros-2166ac)](../reports/15_vuln_edu.md)
[![mapa](https://img.shields.io/badge/mapa_de_quadrantes-%E2%86%92-2166ac)](../reports/15_vuln_edu.md)

## Paper-base

**Reardon, S. F. (2011).** *The widening academic-achievement gap between the rich and the poor: New evidence and possible explanations.* In Duncan & Murnane (Eds.), *Whither Opportunity?*, Russell Sage Foundation.

O paper documenta que o gap de desempenho entre o quintil mais rico e o mais pobre nos EUA **cresceu ~40% desde os anos 1970** e **excede o gap racial branco-negro**. A operacionalização é direta: ordenar por SES, ordenar por desempenho, decompor o gap. Aqui, fazemos o análogo intra-Rio usando IDS (proxy SES composto) e IDEB séries iniciais.

## O que entrega

**Mapa cruzado** dos 144 bairros municipais (98% do IDEB) classificados em 4 quadrantes pela mediana de IDS e IDEB:

- **Q1 privilegiado** — alto IDS + alto IDEB (n=47, 33%). Concentrado em AP 2 (Zona Sul).
- **Q2 resiliente** — baixo IDS + alto IDEB (n=32, 22%). Onde a rede municipal entrega apesar do contexto.
- **Q3 sub-performance** — alto IDS + baixo IDEB (n=25, 17%). Possível efeito de migração para rede privada.
- **Q4 vulnerável** — baixo IDS + baixo IDEB (n=40, 28%). Prioridade política natural.

**VULN_score** padronizado: ranqueia bairros pela soma de desvios negativos em IDS e IDEB. Top-5 mais vulneráveis em 2023: **Santo Cristo, Sampaio, Gardênia Azul, Parque Columbia, Acari**.

## Visualizações

### Gradiente IDS × IDEB por bairro

<div data-chart="../_assets/charts/vuln_edu_scatter.json"></div>

OLS modesta: `IDEB = 4.29 + 2.87·IDS`. Reta com R² = 0.16 — o IDS prevê o IDEB em direção certa mas com **muita variância residual**.

### Mapa de quadrantes

<div data-chart="../_assets/charts/vuln_edu_map.json"></div>

Q4 (vermelho) aparece em todas as APs, inclusive AP 2 — desfaz a leitura "Zona Sul = privilégio uniforme".

### Top 15

<div data-chart="../_assets/charts/vuln_edu_top.json"></div>

## Por que isto importa

Política pública municipal frequentemente assume que **investir onde o SES é baixo basta para subir o IDEB** (Q4 → Q1) ou que **bairros de baixo IDS já têm IDEB baixo** (mapa coroplético implícito). Os dados refutam ambas:

1. **30% de concordância nos quintis 5×5**: ordenação por SES e ordenação por IDEB são bem diferentes.
2. **Q2 resiliente (22%)** sugere que existem **bairros onde a escola municipal compensa** — vale aprender o que esses casos fazem diferente. Candidatos: Vargem Grande, bairros periféricos de Jacarepaguá com IDEB > 6 apesar de IDS < 0.55.
3. **Q3 sub-performance (17%)** alerta para um padrão oculto: bairros com SES alto onde **o IDEB municipal é baixo** — provável efeito de migração da elite local para a rede privada, deixando a municipal sub-utilizada e sub-investida. Casos: Maria da Graça, partes da Tijuca.

## Caveats

- **IDS é de 2010, IDEB de 2023**. Censo 2022 ainda não fechou IDS completo — NT-44 do IPP documenta a transição. v0.2 reroda quando IDS 2022 sair.
- **Agregação setor → bairro via mediana** suaviza heterogeneidade interna (favela + asfalto no mesmo bairro). CSV inclui IQR para auditoria.
- **IDEB por bairro ≠ IDEB por escola**. Migração para rede privada/estadual em bairros de IDS alto distorce a leitura de Q3.
- **Correlação ≠ causalidade**. Reta OLS descreve associação, não efeito de tratamento.
- **3 bairros não casados** (renomeações pós-2010): cobertura efetiva = 144/147.

## v0.2 — o que melhora

- OLS multivariado para isolar **qual sub-indicador do IDS** mais discrimina (renda? analfabetismo? saneamento?).
- Cruzar com **IPS por RA (2016–2024)** — painel temporal.
- IDEB **por escola** via microdado INEP (fora do data.rio mas público).
- Moran's I para autocorrelação espacial dos resíduos.

## Reproduzir

```bash
pip install -r requirements.txt

python3 analysis/11_fetch_bairros.py
python3 analysis/28_fetch_ids.py
python3 analysis/29_vuln_edu.py
python3 analysis/30_vuln_edu_charts.py
```

## Referências

- **Reardon, S. F. (2011).** *The widening academic-achievement gap between the rich and the poor.* In Duncan & Murnane (Eds.), *Whither Opportunity?*, Russell Sage Foundation. **Paper-base canônico do VULN-EDU.**
- **IPP / PCRJ (2010, 2024).** *Índice de Desenvolvimento Social — Município do Rio de Janeiro.* Nota Técnica 44 (Dez/2024). data.rio item `0afd8c12...`.
- **Theil, H. (1967).** Conceito-base da decomposição de desigualdade, usado em HEX-EDU (Relatório 06).

## Continue

<div class="grid cards" markdown>

-   [:material-rocket-launch-outline: Tour 5 min](../tour.md)
-   [:material-map: Mapa interativo](../mapa.md)
-   [:material-format-list-bulleted: Bairros prioritários](../bairros-prioritarios.md)
-   [:material-book-open-variant: Investigação técnica](../investigacao.md)

</div>
