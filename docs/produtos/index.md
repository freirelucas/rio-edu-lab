---
title: Produtos do rio-edu-lab
description: O lab opera como pipeline paper-driven sobre o Grupo Educação do data.rio. Catálogo honesto de produtos, em ordem de maturidade.
---

# Produtos

O lab opera como pipeline **paper-driven**: cada produto operacionaliza um paper específico, com dados disponíveis no data.rio (ou complementares públicos), gerando uma ferramenta replicável e citável.

## Status do MVP — honesto

| Produto | Paper-base | Maturidade | Achado / objetivo |
|---|---|---|---|
| **[HEX-EDU](hex_edu.md)** | Theil (1967) + Pereira et al. (2019) IPEA | v0.5 (Theil) + v0.6.1 (acessibilidade haversine) | Inequidade do IDEB municipal por bairro (**66% within-RA**) + acesso Pereira-style ponderado por IDEB. Próxima iteração: isócronas OSM reais |
| **[VULN-EDU](vuln_edu.md)** | Reardon (2011) | **v0.1 entregue** | IDS Censo 2010 × IDEB 2023 por bairro. Correlação modesta (+0.40), R²=0.16 — **39% dos bairros estão em quadrantes não-concordantes** (resilientes + sub-performance) |

## O que NÃO é mais MVP

A v0.5 publicou 4 produtos. A revisão honesta consolidou em **2 ativos** (HEX-EDU + VULN-EDU). Os 3 cortados continuam como **análises de robustez** acessíveis via [Investigação técnica](../investigacao.md), porque os dados e código são reais e o pipeline é reproduzível — só não merecem o status de produtos paper-driven distintos.

| Antiga vitrine | Status atual |
|---|---|
| ~~THESHA-Rio (Bourguignon, Ferreira & Menéndez 2007)~~ | **Subseção do HEX-EDU**: decomposição Theil em 3 níveis aninhados (AP / RA / bairro). Ver [Relatório 11](../reports/11_thesha_rio.md). |
| ~~FUN-Rio (Mare 1980 + Reardon & Owens 2014)~~ | **Análise descritiva**: pseudocoorte 5º→9º ano, simples diferença de IDEB. Não replica o método dos papers citados; serve como sanity-check temporal. Ver [Relatório 12](../reports/12_fun_rio.md). |
| ~~PM-12 (Bettencourt 2010 inter-capitais)~~ | **Análise auxiliar intra-Rio**: a implementação que entregamos é intra-cidade (não é Bettencourt clássico). Útil como diagnóstico SAMI de bairros sub-servidos. Ver [Relatório 13](../reports/13_pm_12.md). |

## Por que dois produtos em vez de "apenas continuar"

A premissa do lab é "operacionalização de papers" — não "análises ad hoc do data.rio com referências bibliográficas". A revisão deixou claro que:

- HEX-EDU como **só decomposição Theil** sub-utilizava Pereira et al. (2019) IPEA, que combina H3 com **acessibilidade** (distância × qualidade) e **decomposição por equidade**. A v0.6.1 entrega a métrica de acesso ponderada por IDEB; v0.7 traz isócronas reais.
- O dado do data.rio inclui **IPS, IDS, dados PNAD/Censo** — nada disso entrava nos produtos da v0.5. **VULN-EDU v0.1** cruza IDS por bairro (Censo 2010) com IDEB para testar empiricamente o pressuposto do gradiente SES → desempenho. Achado: gradiente real mas modesto.

## Continue

<div class="grid cards" markdown>

-   [:material-library-shelves: Papers](../papers/index.md)
-   [:material-map: Mapa interativo](../mapa.md)
-   [:material-format-list-bulleted: Bairros prioritários](../bairros-prioritarios.md)
-   [:material-book-open-variant: Investigação técnica](../investigacao.md)

</div>
