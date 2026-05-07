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

## 4 papers, 4 produtos, 1 conclusão

Operacionalizamos métodos publicados sobre o acervo educacional do data.rio. Cada produto compara o que o paper original descobriu com o que encontramos aplicando ao Rio.

<div class="papers-strip" markdown>

<a class="paper-badge" href="produtos/hex_edu/">
<span class="paper-icon">📐</span>
<span class="paper-title">HEX-EDU</span>
<span class="paper-cite">Theil (1967) — entropia</span>
</a>

<a class="paper-badge" href="produtos/thesha_rio/">
<span class="paper-icon">🪜</span>
<span class="paper-title">THESHA-Rio</span>
<span class="paper-cite">Bourguignon, Ferreira & Menéndez (2007) — decomposição hierárquica</span>
</a>

<a class="paper-badge" href="produtos/fun_rio/">
<span class="paper-icon">⏳</span>
<span class="paper-title">FUN-Rio</span>
<span class="paper-cite">Mare (1980) + Reardon & Owens (2014) — transições escolares</span>
</a>

<a class="paper-badge" href="produtos/pm_12/">
<span class="paper-icon">📈</span>
<span class="paper-title">PM-12</span>
<span class="paper-cite">Bettencourt (2010) + Heinrich Mora (2023) — leis de escala</span>
</a>

</div>

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

    4 produtos paper-driven, código reproduzível, DOI Zenodo, 28 testes verdes.

    [:octicons-arrow-right-24: Produtos](produtos/index.md)

-   :material-code-tags:{ .lg } **Desenvolvedor**

    ---

    Pipeline reproduzível ponta-a-ponta, pacote `acec` instalável.

    [:octicons-arrow-right-24: Reproduzir](reproduzir.md)

</div>

## O que cada produto descobriu

| Produto | Em uma frase |
|---|---|
| **HEX-EDU** | Mapa H3 do IDEB por bairro — **66% da desigualdade está dentro das RAs**, não entre. |
| **THESHA-Rio** | Decomposição em 3 níveis: bairro = **67%**, RA-em-AP = 26%, AP = 8%. Política em escala ampla esconde quase tudo. |
| **FUN-Rio** | **87%** das pseudocoortes 5º→9º pioram. Slope −0.53 vs IDEB inicial — bairros de IDEB mais alto caem mais. |
| **PM-12** | β = **0.77** (sublinear). Bairros maiores em matrícula têm desproporcionalmente menos escolas. |

Os 4 padrões apontam para a mesma direção de política: **a granularidade de bairro é a escala correta**.

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
