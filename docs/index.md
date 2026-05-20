---
title: rio-edu-lab — papers de educação testados contra os dados públicos do Rio
description: Catálogo de papers de educação cruzados com os 9.855 datasets públicos do data.rio. Status de replicação, código aberto, DOI Zenodo. Reproduzível em 4 minutos.
hide:
  - toc
---

<div class="hero" markdown>

<div class="hero-text" markdown>
# Selecione um paper. Cheque se replica no Rio. Reproduza em 4 minutos.

> Cada paper de educação aqui é cruzado com os 9.855 datasets públicos do Rio.
> Se os dados existem, replicamos. O código é seu.

[:material-library-shelves: Explorar papers](papers/index.md){ .md-button .md-button--primary }
[:material-filter-check-outline: O que dá pra replicar](papers/index.md#replicados-3){ .md-button }
[:material-rocket-launch-outline: Rodar você mesmo](reproduzir.md){ .md-button }

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
</div>

<div class="hero-viz" markdown>
<div id="hero-toggle-map" data-chart="_assets/charts/hero_toggle.json"></div>
</div>

</div>

## Como funciona

Pegamos 12 papers de educação relevantes pro Rio. Pra cada um, listamos os dados que ele precisa, batemos contra o [data.rio](data-rio-api.md) e marcamos: **✅ replicado** · **⚠ parcial** · **⛔ falta dado**. Quando replicamos, publicamos o achado e o código. Quando não dá, dizemos o que tá faltando. Tudo aberto, tudo versionado, [reprodutível em 4 minutos](reproduzir.md).

<div class="big-num-grid">
  <div class="big-num"><span class="num">12</span><span class="label">papers no catálogo</span></div>
  <div class="big-num"><span class="num">3</span><span class="label">replicados</span></div>
  <div class="big-num"><span class="num">6</span><span class="label">prontos pra replicar</span></div>
  <div class="big-num"><span class="num">9.855</span><span class="label">datasets do data.rio cobertos</span></div>
</div>

## O que já foi replicado

Cada item é um método publicado aplicado literalmente aos dados do data.rio. Achados descritivos — sem claim de causalidade, sem recomendação de política. O leitor decide o que fazer com eles.

- **[Theil (1967)](papers/theil-1967-economics.md) — desigualdade do IDEB por bairro.** Decomposição Theil-T mostra **66% da variância dentro das RAs**, não entre. Robusto em 6 séries × 9 anos. [Relatório 06](reports/06_theil_ideb.md).
- **[Pereira et al. (2019) IPEA](papers/pereira-2019-ipea.md) — acessibilidade escolar.** Replicação parcial (haversine + IDEB): AP 3 lidera (113), AP 4 último (29). [Relatório 14](reports/14_acessibilidade.md).
- **[Reardon (2011)](papers/reardon-2011-whither.md) — gradiente SES × educação.** IDS Censo 2010 × IDEB 2023 por bairro: Pearson +0,40, R²=0,16, **39% dos bairros em quadrantes não-concordantes**. [Relatório 15](reports/15_vuln_edu.md).

[Ver todos os papers →](papers/index.md){ .md-button }

## Quem usa isto

<div class="grid cards" markdown>

-   :material-newspaper-variant-multiple-outline:{ .lg } **Jornalista ou cidadão**

    ---

    Achados em linguagem direta. Cada paper diz o que foi descoberto e o que falta pra checar no Rio.

    [:octicons-arrow-right-24: Explorar papers](papers/index.md)

-   :material-flask-outline:{ .lg } **Replicador ou pesquisador**

    ---

    Catálogo paper × dado em YAML auditável. DOI Zenodo, pipeline reprodutível, 28 testes em CI.

    [:octicons-arrow-right-24: Sobre o método](sobre.md)

-   :material-code-tags:{ .lg } **Desenvolvedor**

    ---

    Pipeline ponta-a-ponta. Pacote `acec` instalável. CSVs derivados em `data/processed/`.

    [:octicons-arrow-right-24: Reproduzir](reproduzir.md)

</div>

## Licença

Código MIT · dados derivados CC BY 4.0 · dados brutos seguem licença original do [data.rio](https://www.data.rio) / IPP.
