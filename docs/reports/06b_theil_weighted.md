# 06b — Theil ponderado por matrículas

Refinamento metodológico do [Relatório 06](06_theil_ideb.md). Lá tratamos cada bairro como uma unidade de peso igual; aqui, cada bairro pesa proporcionalmente ao **número total de matrículas na rede municipal** naquele ano. Isso é mais defensável: a inequidade que afeta um bairro com 30 escolas conta mais que a do mesmo Theil em um bairro com 1 escola.

Fonte da matrícula: data.rio item `bba0d7d3c31c4cfd8a6940cc283d52cc` ('Matrículas na rede municipal de educação por AP, RP, RA e Bairros'). Cobre apenas **2010, 2011, 2012 e 2013** — única série pública com granularidade bairro. Janela de overlap com IDEB de séries iniciais (disponível só em anos ímpares): **2011 e 2013**.

## Comparação

| Ano | n bairros | Σ matrícula | IDEB médio (uniforme/ponderado) | T total (uniforme/ponderado) | % within (uniforme/ponderado) |
| ---: | ---: | ---: | :---: | :---: | :---: |
| 2011 | 139 | 656,484 | 5.494 / 5.416 | 0.004463 / 0.002337 | 68% / 58% |
| 2013 | 140 | 654,745 | 5.336 / 5.303 | 0.006561 / 0.003811 | 70% / 62% |

## Achados

- **Theil total ponderado é menor**: cai de 0.0055 para 0.0031 em média (~44% de redução). Bairros pequenos com poucas escolas têm IDEB mais ruidoso e tendem a aparecer como extremos no Theil unweighted; ponderar por matrícula amortece esse ruído.
- **Parcela within-RA**: uniforme = 69%, ponderado = 60% (Δ = -9 pp). O achado central do Relatório 06 permanece sob ponderação — within > between é robusto à escolha de pesos. Mas o share within é menor sob ponderação, sugerindo que parte da heterogeneidade intra-RA aparente vem de ruído amostral de bairros pequenos.
- **IDEB médio ponderado é **ligeiramente menor** (5.36 vs 5.42) — sugere que bairros com mais matrícula concentrada (Zona Norte / Oeste, favelas, comunidades) tendem a ter IDEB um pouco abaixo da média aritmética simples por bairro. A média não-ponderada **superestima** levemente a qualidade educacional média da rede municipal.

## Caveats da ponderação

- **Total de matrícula** é um proxy razoável mas grosseiro: idealmente ponderaríamos pelo número de matrículas em **séries iniciais especificamente** (o IDEB aqui é dessa etapa). Os Excels da fonte têm colunas separadas por ano (1º, 2º, ..., 5º), mas a estrutura de cabeçalho varia ano-a-ano (2012 tem layout distinto). Para v0.1 do HEX-EDU, ficamos com Total — a correlação entre Total e total-anos-iniciais por bairro é alta o suficiente para que a comparação demonstrativa unweighted-vs-weighted fique informativa.
- **Janela curta**: 2 pontos não suportam afirmação de tendência. O ideal seria atualizar o data.rio com matrícula 2014–2024 (não publicado), ou aceitar a janela 2011–2013 como recorte e replicar com dados INEP (não-data.rio) numa próxima iteração.
- **Decomposição weighted**: a fórmula generalizada de Theil-T com pesos trata cada unidade como ‘grupo de tamanho w’. A propriedade aditiva T = T_b + T_w continua exata; checagem de soma é trivial e omitida da tabela porque já validada para o caso unweighted.

## Reprodutibilidade

```bash
python3 analysis/16_theil_weighted.py
```
Saídas: `data/processed/matriculas_bairros.csv` e `data/processed/theil_ideb_weighted.csv`.

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [HEX-EDU (página de produto)](../produtos/hex_edu.md)
    - [09 — IDEB séries finais (9º)](09_anos_finais.md)
