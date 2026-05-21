---
title: Bairros que sofrem dois sinais ao mesmo tempo — rio-edu-lab
description: Bairros com déficit de escolas E queda de IDEB ao longo do fundamental. Lista descritiva, sem prescrição.
---

# Bairros que sofrem dois sinais ao mesmo tempo

**Alguns bairros do Rio têm dois problemas simultâneos: menos escolas do que a matrícula sugere E alunos que pioram entre 5º e 9º ano.** Esta página lista quem cruza os dois sinais. A lista é descritiva — o lab mostra a coincidência, não prescreve ação.

Os dois sinais vêm de análises de robustez:

- **SAMI** ([Relatório 13](reports/13_pm_12.md)) mede infraestrutura: SAMI < 0 = bairro tem **menos escolas** que o esperado pelo volume de matrícula.
- **Δ médio** ([Relatório 12](reports/12_fun_rio.md)) mede trajetória: Δ < 0 = a turma piora ao longo do fundamental (queda de IDEB do 5º pro 9º ano em pseudocoortes).

Bairros com **SAMI negativo E Δ negativo** estão nos dois sinais. O score combinado é a soma dos z-scores das duas métricas.

## Top 20

<div data-chart="../_assets/charts/tour_slide_5.json"></div>

A lista completa de 115 bairros está em [`data/processed/bairros_prioritarios.csv`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/processed/bairros_prioritarios.csv).

## Cuidado importante: confound de migração privada

Alguns bairros no topo (Humaitá, Leblon, Jardim Botânico) provavelmente refletem **migração pra escola privada** entre 5º e 9º ano: alunos com mais recursos saem da rede municipal no 6º ano, e o cohorte municipal do 9º fica enviesado pra baixo. Esse é um problema **real** mas de natureza diferente do subinvestimento estrutural (Pavuna, Pilares, Curicica). Sem microdado por escola e cobertura privada, não dá pra separar mecanicamente. A coluna "AP" é heurística:

- **AP 2** (Zona Sul) → mais provável confound de privatização.
- **AP 3 e 5** (Zona Norte / Oeste) → mais provável subinvestimento estrutural.

## Reproduzir

```bash
python3 analysis/16_theil_weighted.py     # gera matriculas_bairros.csv
python3 analysis/19_fun_rio.py            # gera fun_rio_transitions.csv
python3 analysis/20_pm_12.py              # gera pm12_scaling.csv
python3 analysis/23_build_priority_list.py
```

Saídas: `data/processed/bairros_prioritarios.csv` (115 bairros) e `bairros_prioritarios_top20.csv`.

## Caveats

- **Janela temporal mista**: SAMI é de 2011 (único ano com matrícula + IDEB), Δ FUN-Rio é média de 2007–2023. Comparamos "estoque infra" com "trajetória temporal". Um bairro pode ter melhorado em infra após 2011 sem aparecer aqui.
- **Pseudocoorte ≠ coorte real**: o 5º ano de 2007 não é o mesmo grupo do 9º de 2011. Sem microdado por escola não dá pra segui-los individualmente.
- **Fora da rede municipal**: bairros com escola dominantemente privada/estadual (parte da Zona Sul, Barra) saem do dataset porque o IDEB municipal é suprimido. Aparecem como "sem dado".
- **Score combinado é heurística simples** (soma de z-scores). Outras combinações são possíveis e podem reordenar a lista. O CSV traz os componentes separados.

## Continue

<div class="grid cards" markdown>

-   [:material-magnify: Outros achados](achados.md)
-   [:material-library-shelves: Papers](papers/index.md)
-   [:material-text-box-outline: Lei de escala (Relatório 13)](reports/13_pm_12.md)
-   [:material-clock-time-eight-outline: Trajetórias 5º→9º (Relatório 12)](reports/12_fun_rio.md)

</div>
