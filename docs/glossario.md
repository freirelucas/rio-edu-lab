---
title: Glossário — rio-edu-lab
description: Definições rápidas dos termos técnicos usados no lab.
---

# Glossário

Termos técnicos em ordem alfabética. Cardinalidades reportadas para o município do Rio de Janeiro.

## A

**AP — Área de Planejamento**
:   Maior unidade administrativa do município. **5 APs** dividem o Rio em zonas amplas (Centro, Zona Sul, Zona Norte, Jacarepaguá/Barra, Zona Oeste).

**Aprovação (%)**
:   Percentual de alunos aprovados ao final do ano letivo. Componente de "fluxo" do IDEB. Tem teto natural (raramente acima de 100%, raramente abaixo de 70% na rede municipal).

**ANOS_INICIAIS / ANOS_FINAIS**
:   No IDEB, "anos iniciais" cobre o 1º ao 5º ano do fundamental (avaliação é no 5º). "Anos finais" cobre 6º ao 9º (avaliação no 9º).

## B

**Bairro**
:   Menor unidade espacial pública do Rio. **163 bairros oficiais** segundo o IPP. Granularidade-alvo do HEX-EDU.

**β (beta) — expoente da lei de escala**
:   No PM-12: `escolas = A · matrículas^β`. β = 1 = linear (alocação proporcional); β &lt; 1 = sublinear (bairros maiores sub-servidos); β &gt; 1 = superlinear (concentração).

## C

**CRE — Coordenadoria Regional de Educação**
:   Subdivisão administrativa da Secretaria Municipal de Educação. **11 CREs**.

## H

**H3**
:   Sistema de discretização espacial hexagonal da Uber. Hexágonos cobrem qualquer região com poucas distorções. Resolução 8 (~0.7 km², ~1593 hexes para Rio) é a usada no HEX-EDU.

## I

**IDEB**
:   Índice de Desenvolvimento da Educação Básica, calculado pelo INEP. É o **produto** de Aprovação (fluxo) com Média SAEB normalizada (desempenho). Escala 0–10.

**INEP**
:   Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira. Calcula e publica o IDEB.

**IPP**
:   Instituto Pereira Passos. Órgão da Prefeitura do Rio responsável por estatísticas urbanas e pelo portal data.rio.

## M

**MAUP — Modifiable Areal Unit Problem**
:   Tendência de resultados estatísticos espaciais mudarem com a definição das unidades de área. Discutido nos caveats de cada produto: fronteiras de bairro mudam ao longo dos anos.

## P

**Pseudocoorte**
:   Aproximação de coorte real quando microdados individuais não estão disponíveis. No FUN-Rio, o IDEB 5º ano de 2007 é tratado como o "mesmo grupo" do IDEB 9º ano de 2011. Confound: alunos transferidos / evadidos entre os dois pontos enviesam a comparação.

## R

**RA — Região Administrativa**
:   **33 RAs** subdividem as 5 APs. Granularidade típica de painéis municipais (incluindo IPP). HEX-EDU mostra que essa granularidade esconde 67% da variância do IDEB.

**RP — Região de Planejamento**
:   Subdivisão intermediária. ~16 RPs. Pouco usada na prática; aparece como hierarquia residual nos Excels do data.rio.

## S

**SAEB**
:   Sistema de Avaliação da Educação Básica. Prova nacional aplicada bienalmente. Componente de "desempenho" do IDEB, sem teto efetivo (escala contínua).

**SAMI — Scaling Adjusted Metropolitan Indicator**
:   Resíduo de uma regressão log-log de leis de escala. No PM-12: SAMI = log(escolas observadas) − log(escolas previstas pela lei de escala). Permite comparar bairros depois de "controlar" pelo seu tamanho. Heinrich Mora et al. (2023) introduziram o termo na literatura cross-cidades.

## T

**Theil-T (entropia de Theil)**
:   Índice de desigualdade da família GE(α=1). Definição:
    
    $$T = \\frac{1}{N} \\sum_i \\frac{y_i}{\\bar y} \\ln\\!\\frac{y_i}{\\bar y}$$
    
    Aceita decomposição aditiva exata em parcelas **between-grupo** + **within-grupo**. É o método-base do HEX-EDU e do THESHA-Rio.

**THESHA-Rio**
:   Decomposição Theil em 3 níveis aninhados (AP → RA-em-AP → bairro-em-RA). Adapta Bourguignon, Ferreira & Menéndez (2007) para a hierarquia administrativa do Rio.

## Continue

<div class="grid cards" markdown>

-   [:material-rocket-launch-outline: Tour 5 min](tour.md)
-   [:material-package-variant: Produtos](produtos/index.md)
-   [:material-map: Mapa interativo](mapa.md)

</div>
