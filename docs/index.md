---
title: rio-edu-lab — desigualdade educacional do Rio em granularidade que importa
description: 67% da desigualdade do IDEB municipal carioca está dentro das RAs, não entre. Mapa H3 + decomposição Theil + DOI Zenodo.
hide:
  - toc
---

<div class="hero" markdown>

<div class="hero-text" markdown>
# **2 em cada 3** das diferenças no IDEB do Rio são **dentro** da mesma RA — não entre.

> Atlas Cibernético da Educação Carioca — desigualdade educacional do Rio em granularidade que importa.

[:material-map: Ver o mapa interativo](mapa.md){ .md-button .md-button--primary }
[:material-rocket-launch-outline: Tour de 5 minutos](tour.md){ .md-button }

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
</div>

<div class="hero-viz" markdown>
<div id="hero-toggle-map" data-chart="_assets/charts/hero_toggle.json"></div>
</div>

</div>

## Pipeline paper-driven

Lab que opera papers em produtos. Cada produto **operacionaliza um paper específico** com dados disponíveis no data.rio (ou complementares públicos). O catálogo é honesto sobre maturidade.

<div class="papers-strip" markdown>

<a class="paper-badge" href="produtos/hex_edu/">
<span class="paper-icon">📐</span>
<span class="paper-title">HEX-EDU</span>
<span class="paper-cite">Pereira et al. (2019) IPEA — acessibilidade via H3 · v0.5 (Theil) → v0.6 (acessibilidade)</span>
</a>

<a class="paper-badge" href="produtos/index/">
<span class="paper-icon">🧭</span>
<span class="paper-title">VULN-EDU</span>
<span class="paper-cite">Paper-base a definir (Reardon 2011 candidato) · em planejamento</span>
</a>

</div>

> **Nota de transparência:** a v0.5 publicou 4 produtos. A revisão v0.6 (em curso) consolida em **1 produto ativo + 1 em planejamento**. Os 3 cortados (THESHA-Rio, FUN-Rio, PM-12) viraram análises de robustez — o código continua reproduzível, mas a fundamentação acadêmica deles era frágil. Detalhe em [Produtos](produtos/index.md).

## Para quem é isto

<div class="grid cards" markdown>

-   :material-newspaper-variant-multiple-outline:{ .lg } **Jornalista / cidadão**

    ---

    Mostra como a granularidade administrativa esconde a desigualdade real.

    [:octicons-arrow-right-24: Tour 5 min](tour.md)

-   :material-city-variant-outline:{ .lg } **Gestor público / IPP**

    ---

    Lista de bairros prioritários cruzando déficit de escolas e queda de IDEB.

    [:octicons-arrow-right-24: Bairros prioritários](bairros-prioritarios.md)

-   :material-flask-outline:{ .lg } **Pesquisador**

    ---

    1 produto ativo + 1 em planejamento, paper-base canônico (Pereira IPEA 2019), pipeline reprodutível, DOI Zenodo, 28 testes verdes.

    [:octicons-arrow-right-24: Produtos](produtos/index.md)

-   :material-code-tags:{ .lg } **Desenvolvedor**

    ---

    Pipeline reproduzível ponta-a-ponta, pacote `acec` instalável.

    [:octicons-arrow-right-24: Reproduzir](reproduzir.md)

</div>

## O que o lab descobriu (até v0.5)

A análise central — **decomposição Theil-T do IDEB municipal por bairro** — é robusta em 6 séries (anos iniciais/finais, ponderação por matrícula, Aprovação/SAEB/IDEB):

- **66% da desigualdade do IDEB municipal está dentro das RAs**, não entre. Coropléticos por RA mascaram a maior parte da variância. ([Relatório 06](reports/06_theil_ideb.md))
- **3-níveis aninhados**: bairro = 67%, RA-em-AP = 26%, AP = 8%. ([Relatório 11](reports/11_thesha_rio.md))
- Pseudocoortes 5º→9º pioram em **87%** dos casos; bairros que começam com IDEB alto caem mais. Confound provável: migração para escola privada no 6º ano. ([Relatório 12](reports/12_fun_rio.md))
- Lei de escala intra-Rio entre escolas e matrícula: β = 0.77 (sublinear) — bairros maiores em matrícula têm desproporcionalmente menos escolas. ([Relatório 13](reports/13_pm_12.md))

Os 4 padrões apontam para **granularidade de bairro como escala correta** de intervenção.

## Citar

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620) — versão atual **v0.5.0**, ver [`CITATION.cff`](https://github.com/freirelucas/rio-edu-lab/blob/main/CITATION.cff).

```bibtex
@misc{freire2026rioedulab,
  author       = {Freire, Lucas},
  title        = {{rio-edu-lab} — Atlas Cibern\'etico da Educa\c{c}\~ao Carioca},
  year         = {2026},
  version      = {v0.5.0},
  doi          = {10.5281/zenodo.20060620},
  url          = {https://doi.org/10.5281/zenodo.20060620},
}
```

## Licença

Código MIT · dados derivados CC BY 4.0 · dados brutos seguem licença original do data.rio / IPP.
