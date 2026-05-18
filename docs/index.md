---
title: rio-edu-lab — laboratório de replicação de papers em educação aplicados ao Rio
description: Catálogo aberto de papers em educação cruzados com o data.rio. 67% da desigualdade do IDEB municipal está dentro das RAs, não entre. Mapa H3 + decomposição Theil + DOI Zenodo.
hide:
  - toc
---

<div class="hero" markdown>

<div class="hero-text" markdown>
# **2 em cada 3** das diferenças no IDEB do Rio são **dentro** da mesma RA — não entre.

> **rio-edu-lab** — laboratório de replicação de papers em educação aplicados ao Rio. **100 papers, 1 base de dados**.

[:material-library-shelves: Ver o catálogo](papers/index.md){ .md-button .md-button--primary }
[:material-map: Mapa interativo](mapa.md){ .md-button }
[:material-rocket-launch-outline: Tour de 5 minutos](tour.md){ .md-button }

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
</div>

<div class="hero-viz" markdown>
<div id="hero-toggle-map" data-chart="_assets/charts/hero_toggle.json"></div>
</div>

</div>

## O que o lab faz

Catálogo aberto de **papers em educação aplicados ao Rio**: cada entrada cruza requisitos de dados do paper com itens disponíveis no [data.rio](https://www.data.rio), indica o status de replicação no lab e (quando replicado) traz um insight para gestores públicos. O catálogo é versionado, auditável via git e enriquecido com citações OpenAlex.

**Estado atual (v0.7):** 12 papers seed catalogados — 3 já operacionalizados em produtos (Pereira 2019, Reardon 2011, Theil 1967), 5 alvo de replicação leve na próxima release (Soares & Andrade, Alves & Soares, Coleman, Hanushek, Reardon & Owens), 4 metodológicos canônicos (Becker, Cunha & Heckman, Hoxby, Card & Krueger). **Roadmap:** expandir para 100 papers em sprints temáticos.

[Ver o catálogo completo →](papers/index.md){ .md-button }

<div class="papers-strip" markdown>

<a class="paper-badge" href="produtos/hex_edu/">
<span class="paper-icon">📐</span>
<span class="paper-title">HEX-EDU v0.6.1</span>
<span class="paper-cite">Pereira et al. (2019) IPEA — acessibilidade via H3 · 1022 escolas, 1593 hexes</span>
</a>

<a class="paper-badge" href="produtos/vuln_edu/">
<span class="paper-icon">🧭</span>
<span class="paper-title">VULN-EDU v0.1</span>
<span class="paper-cite">Reardon (2011) — IDS Censo 2010 × IDEB 2023 · 144 bairros, gradiente modesto (R²=0.16)</span>
</a>

</div>

> **VULN-EDU v0.1 entregue**: cruzamento IDS Censo 2010 × IDEB 2023 por bairro (144 bairros, 98% do município). Achado: gradiente socioeconômico-educacional real mas modesto (Pearson +0.40, R²=0.16) — **39% dos bairros estão em quadrantes não-concordantes**. Ver [Relatório 15](reports/15_vuln_edu.md).

> **Nota de transparência:** a v0.5 publicou 4 produtos. A revisão v0.6 consolidou em **2 produtos ativos** (HEX-EDU + VULN-EDU). Os 3 cortados (THESHA-Rio, FUN-Rio, PM-12) viraram análises de robustez — o código continua reproduzível, mas a fundamentação acadêmica deles era frágil. Detalhe em [Produtos](produtos/index.md).

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

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620) — release atual em preparação **v0.7.0**, ver [`CITATION.cff`](https://github.com/freirelucas/rio-edu-lab/blob/main/CITATION.cff).

```bibtex
@misc{freire2026rioedulab,
  author       = {Freire, Lucas},
  title        = {{rio-edu-lab} --- laborat\'orio de replica\c{c}\~ao de papers em educa\c{c}\~ao aplicados ao Rio},
  year         = {2026},
  version      = {v0.7.0},
  doi          = {10.5281/zenodo.20060620},
  url          = {https://doi.org/10.5281/zenodo.20060620},
}
```

> **Renomeação na v0.7.** Até a v0.6.2 o lab era apresentado como "Atlas Cibernético da Educação Carioca". A v0.7 reposiciona o trabalho como **laboratório de replicação de papers**, com o catálogo público como produto primário. O DOI Zenodo é preservado (concept DOI). Detalhe no [CHANGELOG](https://github.com/freirelucas/rio-edu-lab/blob/main/CHANGELOG.md).

## Licença

Código MIT · dados derivados CC BY 4.0 · dados brutos seguem licença original do data.rio / IPP.
