---
title: 15 — VULN-EDU v0.1 (IDS × IDEB por bairro)
description: Operacionalização do gradiente socioeconômico-educacional de Reardon (2011) sobre dados cariocas. Achado contra-intuitivo: IDS explica apenas 16% da variância do IDEB; metade dos bairros está em quadrantes não-concordantes.
---

# 15 — VULN-EDU v0.1 (IDS × IDEB por bairro)

> Cruzamento entre o **Índice de Desenvolvimento Social (IDS)** do IPP (Censo 2010) e o **IDEB séries iniciais 2023** por bairro do Município do Rio. Testamos empiricamente o pressuposto de que vulnerabilidade socioeconômica prediz desempenho educacional. Acha-se um gradiente real mas modesto — e identifica-se a maior assimetria do mapa: bairros **resilientes** (baixa SES + alto IDEB) e **sub-performance** (alta SES + baixo IDEB).

## Paper-base

**Reardon, S. F. (2011).** *The widening academic-achievement gap between the rich and the poor: New evidence and possible explanations.* In G. J. Duncan & R. J. Murnane (Eds.), *Whither Opportunity? Rising Inequality, Schools, and Children's Life Chances*. Russell Sage Foundation, pp. 91–116.

O paper documenta que, nos EUA, o gap de desempenho entre o quintil mais rico e o mais pobre cresceu ~40% desde os anos 1970 e excede o gap racial branco-negro. A operacionalização é simples: ordene escolas/regiões por SES, ordene por desempenho, meça a correlação e a estrutura do gap. Aqui, fazemos o análogo intra-Rio.

## Insumos

| Dado | Fonte | Quantidade |
|---|---|---:|
| IDS por setor censitário | data.rio item `0afd8c12...` (IPP, baseado em Censo 2010) | **10.504 setores** no município |
| Sub-indicadores IDS | água, esgoto, lixo, banheiros/pessoa, analfabetismo 10-14, renda do responsável (3 faixas) | 8 |
| IDEB séries iniciais 2023 por bairro | Relatório 06 (Excel IDEB hierarquizado) | 147 bairros |
| Geometria de bairros | data.rio item `dc94b29f...` (IPP) | 166 bairros |

**Matching**: 144/147 bairros do IDEB têm IDS após inner-join por nome. Os 3 sem casamento (`Imperial de São Cristóvão`, `Jabour`, `Vila Kennedy`) refletem renomeações posteriores ao Censo 2010 — abordagem é documentar, não imputar.

## Método

### Agregação por bairro

O IDS é publicado por **setor censitário** (média de ~70 setores/bairro). Agregamos para bairro via **mediana**, escolhida sobre a média por ser robusta à heterogeneidade interna (especialmente em bairros que misturam favelas com áreas formais — ex.: Vidigal, Complexo do Alemão).

### Cruzamento

```
correlação Pearson(IDS, IDEB)
correlação Spearman (rank-based, robusta a não-linearidades)
OLS:  IDEB = α + β·IDS + ε
quintis cruzados (5×5)
quadrantes (4 zonas pela mediana de cada variável)
VULN_score = ( -z(IDS) + -z(IDEB) ) / 2
```

`VULN_score` é uma média padronizada: positiva quando o bairro está abaixo da média em **ambos** os eixos (vulnerável + baixo desempenho). Bairros excelentes em ambos saem com score negativo.

## Resultado

### Scatter por AP + reta OLS

<div data-chart="../_assets/charts/vuln_edu_scatter.json"></div>

### Mapa de quadrantes

<div data-chart="../_assets/charts/vuln_edu_map.json"></div>

### Top 15 mais e menos vulneráveis

<div data-chart="../_assets/charts/vuln_edu_top.json"></div>

## Achado-headline

**A correlação IDS × IDEB existe mas é modesta**: Pearson +0.40 (Spearman +0.39). OLS produz `IDEB = 4.29 + 2.87·IDS` com R² = 0.16 — isto é, **o IDS explica só 16% da variância do IDEB municipal por bairro**.

Em escala interpretável: **+0.1 ponto de IDS corresponde a +0.29 ponto de IDEB**. Tomando dois bairros nos extremos (IDS ~0.45 vs ~0.85), a expectativa OLS difere em ~1.15 pontos de IDEB — relevante mas longe de determinístico.

### Quadrantes (medianas: IDS = 0.58, IDEB = 6.0)

| Quadrante | n | % | Interpretação |
|---|---:|---:|---|
| **Q1** — alto IDS + alto IDEB | 47 | 33% | Bairros privilegiados onde tudo funciona. Concentrados em AP 2 (Zona Sul). |
| **Q2** — baixo IDS + alto IDEB | 32 | 22% | **Bairros resilientes**: escola municipal entrega bom IDEB mesmo em contexto SES adverso. |
| **Q3** — alto IDS + baixo IDEB | 25 | 17% | **Sub-performance**: SES bom não traduzido em desempenho da rede municipal. Possível efeito de migração para rede privada/estadual. |
| **Q4** — baixo IDS + baixo IDEB | 40 | 28% | **Vulnerável**: o cenário esperado de cumulatividade — prioridade política natural. |

**Quase metade (39%) dos bairros está nos quadrantes contra-intuitivos** (Q2 + Q3). Concordância em quintis (5×5): apenas **43/144 (30%)** caem na diagonal. Política pública que assume IDEB → IDS (ou vice-versa) erra mais que acerta.

### Por Área de Planejamento

| AP | n | IDS mediano | IDEB mediano | VULN mediano |
|---|---:|---:|---:|---:|
| AP 2 (Zona Sul) | 24 | **0.72** | 6.25 | **−1.14** |
| AP 4 (Barra/Jaca) | 16 | 0.59 | 6.15 | +0.05 |
| AP 5 (Zona Oeste) | 20 | 0.56 | 6.15 | +0.16 |
| AP 3 (Zona Norte) | 73 | 0.58 | 5.90 | +0.23 |
| AP 1 (Centro) | 11 | 0.55 | 5.80 | +0.48 |

A escala administrativa AP **subestima a heterogeneidade real** — exatamente o achado consistente com o Relatório 06 (Theil). Bairros vulneráveis aparecem em todas as APs, inclusive AP 2 (Vidigal entra no top-15 por VULN_score).

### Top-5 mais vulneráveis (Q4)

| Bairro | RA | AP | IDS | IDEB | VULN |
|---|---|---|---:|---:|---:|
| Santo Cristo | I Portuária | AP 1 | 0.55 | 4.90 | +1.45 |
| Sampaio | XIII Méier | AP 3 | 0.56 | 4.80 | +1.44 |
| Gardênia Azul | XVI Jacarepaguá | AP 4 | 0.54 | 5.00 | +1.38 |
| Parque Columbia | XXV Pavuna | AP 3 | 0.53 | 5.10 | +1.38 |
| Acari | XXV Pavuna | AP 3 | 0.53 | 5.20 | +1.32 |

CSV completo: [`data/processed/vuln_edu_bairros.csv`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/processed/vuln_edu_bairros.csv).

## Caveats

- **IDS é de 2010, IDEB é de 2023**. Diferença temporal de 13 anos — gentrificação, mudanças demográficas e novas favelas pós-Censo 2010 ficam fora. O IDS 2022 (Censo 2022) ainda não está disponível para todos os setores; quando sair, refaremos. NT-44 do IPP documenta a adaptação metodológica em curso.
- **Agregação setor → bairro via mediana** descarta variância interna. Para bairros muito heterogêneos (Vidigal mistura favela do morro com vista pra praia), a mediana pode subestimar a polarização. CSV inclui `ids_iqr` para auditoria.
- **Imputação por bairro do IDEB** continua sendo o gargalo: o IDEB é da rede municipal naquele bairro, não da escola individual. Migração para rede privada/estadual em bairros AP 2/4 confunde a leitura de Q3 (sub-performance).
- **Correlação ≠ causalidade**. A reta OLS é descritiva. O slope (+2.87) entra em escala de IDEB/IDS, sem ajuste por variáveis omitidas (matrícula, infraestrutura escolar, tamanho de turma).
- **3 bairros não casados** (Imperial de São Cristóvão, Jabour, Vila Kennedy): renomeações pós-Censo 2010. Cobertura efetiva = 144/147 = 98% do IDEB municipal por bairro.

## v0.2 — o que melhora a próxima iteração

1. **Decomposição por sub-indicador**: rodar OLS multivariado `IDEB ~ I_RENDA + I_ANALFAB + I_ESGOTO + …` para isolar qual dimensão do IDS mais discrimina. Esperamos `I_RENDARESP_POS_SM` dominar.
2. **Cruzar com IPS por RA (2016–2024)**: IPS é publicado anualmente, IDS é decenal. Painel temporal IPS × IDEB testa estabilidade do achado modesto-correlação.
3. **Substituir IDEB-bairro por agregação ponderada de IDEB-escola**: depende de microdado INEP por escola, que não está no data.rio mas é público no INEP. Resolve o gargalo Q3.
4. **Análise espacial**: Moran's I do resíduo OLS para checar autocorrelação geográfica (bairros próximos partilham resíduos similares?).

## Reproduzir

```bash
pip install -r requirements.txt

python3 analysis/11_fetch_bairros.py    # se ainda não fez
python3 analysis/28_fetch_ids.py        # 10.504 setores → CSV slim ~2 MiB
python3 analysis/29_vuln_edu.py         # cruza com IDEB 2023
python3 analysis/30_vuln_edu_charts.py  # Plotly JSONs
```

`28_fetch_ids.py --with-geometry` salva também o GeoJSON completo (~27 MiB, gitignored) para quem quiser fazer coroplético por setor.

Outputs: `data/processed/vuln_edu_bairros.csv` (144 × 20), `data/processed/vuln_edu_summary.json`, três figuras Plotly em `docs/_assets/charts/vuln_edu_*.json`.

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [VULN-EDU (produto canônico)](../produtos/vuln_edu.md)
    - [HEX-EDU (produto irmão — acessibilidade)](../produtos/hex_edu.md)
    - [Bairros prioritários (cruzamento com outros sinais)](../bairros-prioritarios.md)
    - [Mapa interativo](../mapa.md)
