# 10 — Replicação metodológica em sub-componentes do IDEB

Cross-validação interna do método do Relatório 06. O IDEB de cada bairro é, por construção, **o produto** de dois indicadores publicados na mesma fonte:

- **Aprovação** (% de alunos aprovados, fluxo)
- **Média SAEB** (escore Prova Brasil, desempenho)

Aqui rodamos a mesma decomposição Theil-T do Relatório 06 sobre cada componente isoladamente, para os 9 anos disponíveis, e perguntamos: **o achado within > between é robusto a essa escolha de medida?**

## Sobre a referência a Pereira et al. (2019)

O README do ACEC-Hub cita 'Pereira et al. (2019) + Theil (1967)' como paper-base do HEX-EDU, sem título exato nem DOI. O paper não foi localizado nos artefatos do lab. **A replicação aqui é metodológica** (mesmo algoritmo aplicado a dados diferentes), **não bibliográfica**. Replicação numérica direta do paper Pereira et al. fica como backlog quando a referência for confirmada.

## Hipóteses pré-registradas

Antes de olhar os números, registrei o que esperava ver:

1. **Aprovação tem teto natural** (raramente acima de 100%, raramente abaixo de 70% em rede municipal). Variância comprimida → Theil baixo.
2. **SAEB é contínuo, sem teto efetivo** → Theil maior que Aprovação.
3. **IDEB**, por ser produto, fica entre os dois.
4. **share_within deve ser similar (~60-70%) nos três** se o método for invariante.

## Médias entre 9 anos

| Componente | Mean | T total médio | share_within médio |
| :--- | ---: | ---: | ---: |
| **aprovacao** | 95.038 | 0.000798 | 70% |
| **saeb** | 5.869 | 0.002943 | 64% |
| **ideb** | 5.468 | 0.004341 | 66% |

## Detalhe por ano

| Ano | T (apro) | T (saeb) | T (ideb) | within (apro/saeb/ideb) |
| ---: | ---: | ---: | ---: | :---: |
| 2007 | 0.000336 | 0.003501 | 0.004763 | 66% / 60% / 59% |
| 2009 | 0.001856 | 0.002669 | 0.005226 | 73% / 64% / 68% |
| 2011 | 0.001131 | 0.002608 | 0.004362 | 70% / 65% / 69% |
| 2013 | 0.001035 | 0.003232 | 0.006587 | 67% / 72% / 73% |
| 2015 | 0.001323 | 0.002166 | 0.003970 | 67% / 61% / 67% |
| 2017 | 0.000718 | 0.002454 | 0.003494 | 72% / 64% / 62% |
| 2019 | 0.000532 | 0.002121 | 0.002639 | 69% / 62% / 68% |
| 2021 | 0.000094 | 0.004386 | 0.004523 | 77% / 60% / 61% |
| 2023 | 0.000159 | 0.003353 | 0.003508 | 68% / 66% / 68% |

## Resultados vs hipóteses

1. **Aprovação Theil < SAEB Theil**: ✅ (0.000798 vs 0.002943). Confirma a hipótese de teto natural na Aprovação.
2. **IDEB entre os dois**: ⚠️ (0.004341). IDEB **não** está entre os dois extremos — efeito não-linear da multiplicação.
3. **share_within similar entre os 3**: apro=70%, saeb=64%, ideb=66%. Δ_max = 6 pp. ✅ **Within > between é robusto à medida**: o achado central do Relatório 06 não é artefato do IDEB combinado, vale para Aprovação e SAEB separadamente.

## Conclusão metodológica

Esta replicação interna **fortalece o argumento do Relatório 06**: a desigualdade educacional intra-RA do Rio Municipal não é peculiaridade do indicador IDEB. Ela aparece tanto no fluxo (Aprovação) quanto no desempenho (SAEB), com mesma direção (within > between) e magnitudes similares. O HEX-EDU é, portanto, **invariante à escolha do indicador educacional** dentro deste corpus.

## Caveats

- **Mesma fonte para todos**: Aprovação, SAEB e IDEB vêm da mesma planilha. Fontes independentes não foram cruzadas. Isso é cross-validação, não validação externa.
- **Aprovação como % é unbounded acima por ano-rep**: alguns valores >100% aparecem no dataset por motivos de matrícula re-classificada — descartados pelo filtro `v > 0` mas não pelo limite superior. Vale auditar valores extremos antes de citar em paper.
- **SAEB normalizado é diferente entre 5º e 9º ano**: aqui só rodamos 5º (ANOS_INICIAIS).

## Reprodutibilidade

```bash
python3 analysis/17_theil_components.py
```
Saídas: `data/processed/ideb_components_long.csv` e `data/processed/theil_components.csv`. Decomposição aditiva validada via `check_sum ≈ 0` em todos os 27 component-year rows.

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [HEX-EDU (página de produto)](../produtos/hex_edu.md)
    - [Glossário](../glossario.md)
