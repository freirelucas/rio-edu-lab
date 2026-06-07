---
title: rio-edu-lab — pipeline aberto de replicação de papers de educação contra os dados públicos do Rio
description: Um sistema que processa papers acadêmicos sobre educação contra os 9.855 itens do data.rio. Do snowball bibliométrico ao catálogo curado e aos achados replicados — aberto em todos os passos.
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

<div class="hero-text" markdown>
# Da academia até o achado, com paper e código.

> Um pipeline aberto que processa papers acadêmicos sobre educação contra os **9.855 itens públicos do data.rio**. Aberto em todos os passos: você vê o que entrou no funil, o que sobreviveu, e o que virou achado.

[:material-magnify: Achados](achados.md){ .md-button .md-button--primary }
[:material-library-shelves: Papers](papers/index.md){ .md-button }
[:material-database-search: Dados](dados.md){ .md-button }

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
</div>

<div class="hero-viz" markdown>
<div data-chart="_assets/charts/funnel.json"></div>
</div>

</div>

## O que descobrimos até agora

Três achados sobre educação no Rio. Cada um é a replicação literal de um paper acadêmico publicado, aplicado aos dados públicos do município. Sem opinião, sem extrapolação — só método aberto contra dado aberto.

<div class="paper-grid">

<a class="paper-card status-full" href="achados/#desigualdade">
  <span class="drop-cap" aria-hidden="true">1</span>
  <h4>Onde está a desigualdade educacional?</h4>
  <p class="meta">Theil (1967) · IDEB por bairro</p>
  <p class="insight"><strong>Dentro dos bairros, não entre regiões.</strong> 66% da variância do IDEB municipal carioca está dentro das Regiões Administrativas. Coropléticos por RA escondem a maior parte do problema.</p>
  <span class="cta">Ver achado →</span>
</a>

<a class="paper-card status-partial" href="achados/#acessibilidade">
  <span class="drop-cap" aria-hidden="true">2</span>
  <h4>Qual zona tem mais acesso a boas escolas?</h4>
  <p class="meta">Pereira et al. (2019) · acessibilidade ponderada</p>
  <p class="insight"><strong>AP 3 (Zona Norte) lidera — não a Zona Sul.</strong> Acesso ponderado por IDEB: AP 3 com 113, AP 4 com 29. A Zona Sul tem IDEB médio mais alto mas baixa densidade de escolas boas.</p>
  <span class="cta">Ver achado →</span>
</a>

<a class="paper-card status-partial" href="achados/#vulnerabilidade">
  <span class="drop-cap" aria-hidden="true">3</span>
  <h4>Riqueza prediz boa escola no Rio?</h4>
  <p class="meta">Reardon (2011) · IDS Censo × IDEB</p>
  <p class="insight"><strong>Parcialmente.</strong> Gradiente SES → IDEB é real (Pearson +0,40) mas modesto (R²=0,16). <strong>39% dos bairros</strong> desafiam o gradiente esperado — resilientes ou sub-performando.</p>
  <span class="cta">Ver achado →</span>
</a>

</div>

[Ver todos os achados em detalhe →](achados.md){ .md-button }

## O sistema em estado

O pipeline tem 4 estágios, todos auditáveis. Hoje:

<!-- funnel:bignums:start (gerado por analysis/25_funnel_state.py) -->
<div class="big-num-grid">
  <div class="big-num"><span class="num">2080</span><span class="label">candidatos no funil (snowball bibliométrico)</span></div>
  <div class="big-num"><span class="num">394</span><span class="label">com tema educacional relevante</span></div>
  <div class="big-num"><span class="num">15</span><span class="label">papers no catálogo curado</span></div>
  <div class="big-num"><span class="num">3</span><span class="label">replicados publicados</span></div>
</div>
<!-- funnel:bignums:end -->

## Como o funil funciona

<div class="grid cards" markdown>

-   :material-magnify-scan:{ .lg } **Stage 1 — Descoberta**

    ---

    Snowball bibliométrico sobre os seeds canônicos da literatura de educação (incluindo acesso/transporte escolar), expansão backward + forward via OpenAlex. Produz a leva bruta de candidatos.

    `analysis/45_bulk_discover.py`

-   :material-filter-variant:{ .lg } **Stage 2 — Filtro temático**

    ---

    Edu-filter por keywords (≥2 termos educacionais EN/PT) + scoring IDF-weighted contra 10 categorias da taxonomia, afunilando os candidatos brutos aos de tema educacional relevante.

    `analysis/46_extract_requirements.py`

-   :material-database-check:{ .lg } **Stage 3 — Cobertura no data.rio**

    ---

    Cada requisito é matchado contra os 9.855 itens do data.rio. Marca status: disponível, parcial, externo (microdado INEP/PNAD), missing. 4 itens ativados hoje, **9.851 inexplorados**.

    `analysis/47_check_coverage.py`

-   :material-check-decagram:{ .lg } **Stage 4 — Promoção ao catálogo**

    ---

    Curadoria humana revisa candidatos e promove ao catálogo. Cada paper aceito ganha mini-page com cruzamento de dados + status de replicação.

    `analysis/48_promote_funnel.py`

</div>

<div class="chart-duo" markdown>

<div class="chart-card" markdown>
#### :material-chart-donut: Cobertura do data.rio

<div data-chart="_assets/charts/data_rio_coverage.json"></div>

4 itens cobertos pelo catálogo. 9.851 inexplorados. [Browse →](dados.md)
</div>

<div class="chart-card" markdown>
#### :material-chart-bar: Temas no funil

<div data-chart="_assets/charts/themes.json"></div>

Distribuição dos candidatos do funil por categoria de dado requerida. [Detalhe →](dados.md)
</div>

</div>

## Princípios

- **Replicação literal.** O método do paper é aplicado exatamente como publicado. Sem extrapolação, sem opinião — só o que sai dos números.
- **Aberto em todos os passos.** YAML versionado por git, scripts numerados, CSVs derivados commitados. Cada decisão é auditável.
- **Cobertura honesta.** Quando o data.rio não tem o dado, dizemos. Os 3 papers `unfeasible` ficam no catálogo como referência, com o que falta documentado.
- **Sem produto, sem cliente.** O lab é um pipeline de descoberta científica. HEX-EDU e VULN-EDU são saídas de exemplo, não produtos finais.

## Citar e contribuir

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620) · Código MIT · dados derivados CC BY 4.0 · dados brutos seguem licença original do [data.rio](https://www.data.rio) / IPP.

[Reproduzir em 4 minutos](reproduzir.md){ .md-button } [Sobre o lab](sobre.md){ .md-button } [Repo no GitHub](https://github.com/freirelucas/rio-edu-lab){ .md-button }
