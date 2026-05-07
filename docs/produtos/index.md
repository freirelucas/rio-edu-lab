---
title: Produtos do rio-edu-lab
description: O lab opera como pipeline paper-driven sobre o Grupo Educação do data.rio. Catálogo honesto de produtos, em ordem de maturidade.
---

# Produtos

O lab opera como pipeline **paper-driven**: cada produto operacionaliza um paper específico, com dados disponíveis no data.rio (ou complementares públicos), gerando uma ferramenta replicável e citável.

## Status do MVP — honesto

| Produto | Paper-base | Maturidade | Achado / objetivo |
|---|---|---|---|
| **HEX-EDU** | Theil (1967), com extensão Pereira et al. (2019) IPEA em curso | v0.5 (Theil) → v0.6 (acessibilidade) | Decomposição da inequidade do IDEB municipal por bairro; **66% within-RA**. Próxima iteração inclui análise de acessibilidade educacional via H3 + OSM |
| **VULN-EDU** | a definir (Reardon 2011 / Filmer & Pritchett 1999 candidatos) | em planejamento | Cruzar IPS/IDS por bairro com IDEB para mapear gradientes socioeconômicos da educação |

## O que NÃO é mais MVP

A v0.5 publicou 4 produtos. A revisão honesta encolheu para 1 ativo + 2 em planejamento. Os 3 cortados continuam como **análises de robustez** acessíveis via [Investigação técnica](../investigacao.md), porque os dados e código são reais e o pipeline é reproduzível — só não merecem o status de produtos paper-driven distintos.

| Antiga vitrine | Status atual |
|---|---|
| ~~THESHA-Rio (Bourguignon, Ferreira & Menéndez 2007)~~ | **Subseção do HEX-EDU**: decomposição Theil em 3 níveis aninhados (AP / RA / bairro). Ver [Relatório 11](../reports/11_thesha_rio.md). |
| ~~FUN-Rio (Mare 1980 + Reardon & Owens 2014)~~ | **Análise descritiva**: pseudocoorte 5º→9º ano, simples diferença de IDEB. Não replica o método dos papers citados; serve como sanity-check temporal. Ver [Relatório 12](../reports/12_fun_rio.md). |
| ~~PM-12 (Bettencourt 2010 inter-capitais)~~ | **Análise auxiliar intra-Rio**: a implementação que entregamos é intra-cidade (não é Bettencourt clássico). Útil como diagnóstico SAMI de bairros sub-servidos. Ver [Relatório 13](../reports/13_pm_12.md). |

## Por que dois produtos novos em vez de "apenas continuar"

A premissa do lab é "operacionalização de papers" — não "análises ad hoc do data.rio com referências bibliográficas". A revisão deixou claro que:

- HEX-EDU como **só decomposição Theil** sub-utiliza a metodologia Pereira et al. (2019) IPEA, que combina H3 com **acessibilidade** (distância × qualidade) e **decomposição por equidade** (renda, raça). Temos dados que habilitam essa replicação e o paper cobre Rio especificamente.
- O dado do data.rio inclui **IPS, IDS, dados PNAD/Censo** — nada disso entrou nos produtos atuais. Um produto que cruze vulnerabilidade socioeconômica com performance educacional faz sentido aqui e tem fundamentação acadêmica disponível.

## Continue

<div class="grid cards" markdown>

-   [:material-rocket-launch-outline: Tour 5 min](../tour.md)
-   [:material-map: Mapa interativo](../mapa.md)
-   [:material-format-list-bulleted: Bairros prioritários](../bairros-prioritarios.md)
-   [:material-book-open-variant: Investigação técnica](../investigacao.md)

</div>
