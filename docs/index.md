---
title: rio-edu-lab — laboratório de replicação de papers em educação aplicados ao Rio
description: Catálogo aberto de papers em educação cruzados com o data.rio. Replicação fria, exata e replicável; insight literal aplicado ao Rio sem extrapolação. Mapa H3 + decomposição Theil + DOI Zenodo.
hide:
  - toc
---

<div class="hero" markdown>

<div class="hero-text" markdown>
# Replicação **fria, exata e replicável** de papers em educação aplicados ao Rio.

> Catálogo aberto de papers seminais. Cada entrada cruza **método publicado** × **dados abertos do data.rio**. Replicação exata quando os dados permitem; insight literal aplicado ao Rio, sem extrapolação.

[:material-library-shelves: Ver o catálogo](papers/index.md){ .md-button .md-button--primary }
[:material-map: Mapa interativo](mapa.md){ .md-button }
[:material-rocket-launch-outline: Tour de 5 minutos](tour.md){ .md-button }

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20060620.svg)](https://doi.org/10.5281/zenodo.20060620)
</div>

<div class="hero-viz" markdown>
<div id="hero-toggle-map" data-chart="_assets/charts/hero_toggle.json"></div>
</div>

</div>

<div class="how-to-read" markdown>
### Como ler este site

O produto primário é o **[catálogo de papers](papers/index.md)** — cada entrada cruza um paper de educação com a cobertura no data.rio + status de replicação + achado literal aplicado ao Rio. Para a leitura curta, use o **[Tour 5 min](tour.md)**. Para a sala de máquinas (15 relatórios técnicos), **[Investigação](investigacao.md)**.
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

-   :material-flask-outline:{ .lg } **Replicador / pesquisador**

    ---

    Catálogo paper × dado, status de replicação, DOI Zenodo, pipeline reprodutível, 39 testes verdes em CI. Schema YAML auditável via git diff.

    [:octicons-arrow-right-24: Catálogo de papers](papers/index.md)

-   :material-newspaper-variant-multiple-outline:{ .lg } **Jornalista / cidadão**

    ---

    Achados replicados em linguagem direta. 5 painéis curtos mostram o que sai de cada replicação aplicada ao Rio.

    [:octicons-arrow-right-24: Tour 5 min](tour.md)

-   :material-code-tags:{ .lg } **Desenvolvedor**

    ---

    Pipeline reproduzível ponta-a-ponta, pacote `acec` instalável, CSVs em `data/processed/`.

    [:octicons-arrow-right-24: Reproduzir](reproduzir.md)

</div>

## O que o lab replicou (estado atual)

Cada item é um método publicado aplicado literalmente aos dados do data.rio. Achados são descritivos — nenhum carrega claim de causalidade ou recomendação de política. O leitor decide o que fazer com eles.

- **Theil (1967) — decomposição Theil-T aplicada ao IDEB municipal por bairro**: a parcela within-RA fica em **66%**. Robusto em 6 séries (anos iniciais/finais × ponderação × Aprovação/SAEB/IDEB). ([Relatório 06](reports/06_theil_ideb.md))
- **Theil hierárquico aplicado em 3 níveis** (AP / RA-em-AP / bairro-em-RA): 8% / 26% / 67%. ([Relatório 11](reports/11_thesha_rio.md))
- **Pseudocoortes 5º→9º (descritivo, não Mare 1980 fully)**: em 768 transições, 87% pioram. Confound provável: migração à rede privada no 6º ano. ([Relatório 12](reports/12_fun_rio.md))
- **Lei de escala intra-Rio (escolas × matrícula)**: β = 0,77 (sublinear, R² 0,80). ([Relatório 13](reports/13_pm_12.md))
- **Pereira et al. (2019) IPEA — acessibilidade Pereira-style (parcial, haversine + IDEB)**: AP 3 lidera (113), AP 4 último (29). ([Relatório 14](reports/14_acessibilidade.md))
- **Reardon (2011) intra-Rio — gradiente IDS Censo 2010 × IDEB 2023**: Pearson +0,40, R² 0,16, 39% dos bairros em quadrantes não-concordantes. ([Relatório 15](reports/15_vuln_edu.md))

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
