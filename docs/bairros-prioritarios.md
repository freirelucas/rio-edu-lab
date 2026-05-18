---
title: Bairros prioritários — cruzamento SAMI × Δ FUN-Rio
description: Lista descritiva dos bairros que cruzam déficit de escolas (SAMI < 0) e queda de IDEB 5º→9º (Δ FUN-Rio < 0). Interpretação política fica com o leitor.
---

# Bairros prioritários — cruzamento SAMI × Δ FUN-Rio

Lista descritiva dos bairros que cruzam dois sinais ortogonais do MVP-1. **Interpretação política fica com o leitor** — o lab entrega o cruzamento, não a recomendação.

- **SAMI** ([Relatório 13](reports/13_pm_12.md)): desvio da lei de escala. SAMI &lt; 0 = bairro tem **menos escolas** que o esperado pelo seu volume de matrícula (sub-servido em infraestrutura).
- **Δ médio** ([Relatório 12](reports/12_fun_rio.md)): média da queda de IDEB do 5º para o 9º ano em pseudocoortes. Δ &lt; 0 = a turma piora ao longo do fundamental.

Bairros com **SAMI negativo E Δ negativo** cruzam os dois sinais negativos. O score combinado é a soma negativa dos z-scores das duas métricas — descreve quem está nos dois sinais ao mesmo tempo, sem prescrever ação.

!!! warning "Distinção importante (confound de migração privada)"
    Alguns bairros que aparecem no topo (Humaitá, Leblon, Jardim Botânico) provavelmente refletem **migração para escola privada** entre 5º e 9º ano: alunos com mais recursos saem da rede municipal no 6º ano, e o cohorte municipal do 9º fica enviesado para baixo. Esse é um problema **real** mas de natureza diferente do subinvestimento estrutural (Pavuna, Pilares, Curicica). Sem microdado por escola e cobertura privada, não conseguimos separar mecanicamente. Use a coluna "AP" como heurística:
    
    - **AP 2** (Zona Sul) → mais provável confound de privatização.
    - **AP 3 e 5** (Zona Norte / Oeste) → mais provável subinvestimento estrutural.

## Top 20

<div data-chart="../_assets/charts/tour_slide_5.json"></div>

A lista completa de 115 bairros está em [`data/processed/bairros_prioritarios.csv`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/processed/bairros_prioritarios.csv).

## Como reproduzir

```bash
# Pré-requisitos: matrículas, FUN-Rio, PM-12 já gerados.
python3 analysis/16_theil_weighted.py     # gera matriculas_bairros.csv
python3 analysis/19_fun_rio.py            # gera fun_rio_transitions.csv
python3 analysis/20_pm_12.py              # gera pm12_scaling.csv
python3 analysis/23_build_priority_list.py
```

Saídas: `data/processed/bairros_prioritarios.csv` (115 bairros) e `bairros_prioritarios_top20.csv`.

## Caveats

- **Janela temporal mista**: SAMI é de 2011 (único ano com matrícula + IDEB), Δ FUN-Rio é média de 2007–2023. Estamos comparando "estoque infra-estrutural" com "trajetória temporal". Um bairro pode ter melhorado em infra após 2011 sem aparecer aqui.
- **Pseudocoorte ≠ coorte real**: o 5º ano de 2007 não é o mesmo grupo do 9º de 2011. Sem microdado por escola não dá pra segui-los individualmente.
- **Fora da rede municipal**: bairros com escola dominantemente privada/estadual (parte da Zona Sul, Barra) saem do dataset porque o IDEB municipal é suprimido. Aparecem como "sem dado" — não foram analisados.
- **Score combinado é heurística** simples (soma de z-scores). Outras combinações possíveis (média ponderada por matrícula, máximo dos dois, etc.) podem reordenar a lista. O CSV traz os componentes separados para você combinar como preferir.

## Continue

<div class="grid cards" markdown>

-   [:material-map: Ver no mapa interativo](mapa.md)
-   [:material-rocket-launch-outline: Tour 5 min](tour.md)
-   [:material-text-box-outline: Lei de escala (Relatório 13)](reports/13_pm_12.md)
-   [:material-clock-time-eight-outline: Trajetórias 5º→9º (Relatório 12)](reports/12_fun_rio.md)

</div>
