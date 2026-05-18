---
title: Tour de 5 minutos — como ler o rio-edu-lab
description: Em 5 painéis, como o lab opera, o achado-base que sustenta tudo, e como contribuir.
hide:
  - toc
---

# Tour de 5 minutos

Cinco painéis, cada um com um chart interativo. Tempo total de leitura: ~5 min. Ao final, links para o catálogo de papers, os produtos e o repo. Este tour **não recapitula achados** — é uma orientação sobre **como ler o lab**.

<section class="tour-slide" markdown>

## <span class="tour-slide-num">1</span> O que este lab é

**rio-edu-lab** é um **laboratório de replicação de papers em educação aplicados ao Rio**. O produto primário é um **catálogo aberto de papers** ([12 seed, alvo 100](papers/index.md)) cruzado com o data.rio — cada paper indica requisitos de dados, cobertura no portal e status de replicação.

A premissa é que **a infra de dados aberta do Rio (IPP + data.rio) é rica o suficiente para operacionalizar achados clássicos da literatura de educação** — bastava cruzar. O lab é o pipeline + catálogo + DOI Zenodo que materializa essa premissa.

<div data-chart="../_assets/charts/tour_slide_1.json"></div>

[Próximo →](#2-como-nos-lemos-um-paper){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">2</span> Como nós lemos um paper

Cada entrada do catálogo segue o mesmo template — visível em qualquer [mini-page de paper](papers/pereira-2019-ipea.md):

1. **Bibliografia + DOI** + snapshot de citações OpenAlex (versionado em CI).
2. **Resumo** em pt-BR, 1-3 frases.
3. **Categorias** (área, método, Brasil-específico).
4. **Requisitos de dados × cobertura no data.rio** — tabela paper-driven, não data-driven. O paper diz o que precisa; o lab declara o que está disponível no portal (✅ disponível, ◐ parcial, ⚠️ externo, ✗ ausente).
5. **Status de replicação** (replicado, parcial, catalogado, sem cobertura).
6. **Para gestores públicos** (quando o paper é replicado): achado + implicação + ações — sempre com link "Como auditar" para o relatório técnico.

O catálogo é **versionado em YAML** ([`data/papers_catalog.yml`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/papers_catalog.yml)) — `git diff` audita curadoria.

[Próximo →](#3-o-achado-empirico-que-sustenta-tudo){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">3</span> O achado-empírico que sustenta tudo

O lab gira em torno de **um achado empírico anchor**: aplicando a decomposição **Theil-T** (Theil 1967) sobre o IDEB municipal por bairro, **66% da desigualdade está dentro das Regiões Administrativas**, não entre.

<div data-chart="../_assets/charts/tour_slide_3.json"></div>

A parcela within-RA fica entre 59% e 73% em **9 anos × 6 séries** (5º, 9º, ponderado por matrícula, Aprovação, SAEB, IDEB). Nenhuma série cruza a paridade 50%. O achado **justifica a granularidade de bairro** como escala de intervenção — e é a razão de HEX-EDU operar sobre H3 (1593 hexes) em vez de RA (33 unidades).

[Próximo →](#4-como-voce-navega-o-catalogo){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">4</span> Como você navega o catálogo

O [catálogo de papers](papers/index.md) está organizado em **três faixas** acessíveis por tabs:

- **Replicados (3)** — papers já operacionalizados em produtos do lab (Theil 1967, Reardon 2011, Pereira et al. 2019).
- **Catalogados (6)** — próxima leitura: dados básicos cobertos no data.rio, replicação leve planejada (Coleman, Hanushek, Hoxby, Soares & Andrade, Alves & Soares, Reardon & Owens).
- **Sem cobertura (3)** — papers seminais que pedem dados externos (Becker, Card & Krueger, Cunha & Heckman). Ficam aqui para referência teórica.

Cada faixa é navegável por cards Pudding-style — clique no card para a mini-page do paper, ou use a busca nativa do site para nomes de autores e áreas.

[Próximo →](#5-como-contribuir){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">5</span> Como contribuir

O catálogo é **público e aberto a contribuição**. Roteiro:

1. **Sugerir um paper**: PR para [`data/papers_catalog.yml`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/papers_catalog.yml) seguindo o schema (autor, ano, DOI, abstract, requisitos de dados). CI valida + gera mini-page automaticamente via [`32_render_papers_pages.py`](https://github.com/freirelucas/rio-edu-lab/blob/main/analysis/32_render_papers_pages.py).
2. **Replicação leve**: pegar um paper em `pending`, escrever um relatório `analysis/NN_*.py` + `docs/reports/NN_*.md`, mover status para `partial` ou `full`.
3. **Erratas / críticas**: abrir [issue no repo](https://github.com/freirelucas/rio-edu-lab/issues) — replicações são auditáveis via `acec` package (28 testes invariantes em CI).

O lab tem **DOI Zenodo** ([10.5281/zenodo.20060620](https://doi.org/10.5281/zenodo.20060620)) — pode citar em paper, relatório técnico, post de blog. Contribuições viram co-autoria via [`CITATION.cff`](https://github.com/freirelucas/rio-edu-lab/blob/main/CITATION.cff).

## Continue

<div class="grid cards" markdown>

-   [:material-library-shelves: Catálogo de papers](papers/index.md)
-   [:material-package-variant: Produtos detalhados](produtos/index.md)
-   [:material-account-tie: Para gestores](gestores.md)
-   [:material-source-branch: Repo no GitHub](https://github.com/freirelucas/rio-edu-lab)

</div>

</section>
