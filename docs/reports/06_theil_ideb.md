# 06 — Decomposição Theil do IDEB por bairro

Primeira aplicação metodológica do lab: medir desigualdade educacional na rede municipal de ensino do Rio usando o **índice de Theil-T**, decomposto em parcela **entre-RAs** e **dentro-de-RA**, sobre dados reais de IDEB séries iniciais (2007–2023).

Fonte: data.rio item `9fd1a8cc207a48c5bda7131e4e74b1ca` ('IDEB das séries iniciais e finais segundo as Áreas de Planejamento, Regiões de Planejamento, Regiões Administrativas e Bairros'). Sheet `ANOS_INICIAIS`. Hierarquia AP → RP → RA → bairro reconstruída do conteúdo de uma única coluna.

## Método

Theil-T com peso igual por unidade (cada bairro conta 1):

```
T = (1/N) * Σ_i (y_i / ȳ) * ln(y_i / ȳ)
```

Decomposição aditiva por grupos g (RAs):

```
T_between = Σ_g (n_g/N) * (ȳ_g/ȳ) * ln(ȳ_g/ȳ)
T_within  = Σ_g (n_g/N) * (ȳ_g/ȳ) * T_g
T         = T_between + T_within
```

Theil aceita ratio scale com positividade. IDEB ∈ [0, 10] e na prática carioca fica entre ~4.5 e ~7.5 — bem dentro do range válido.

Bairros com IDEB faltante (`...` no Excel) são descartados naquele ano. RAs com 0–1 bairros válidos contribuem 0 ao within (esperado: variância dentro de unidade singular é nula).

## Achado principal

Em todos os 9 anos com dados (2007–2023), **66% da desigualdade do IDEB municipal está dentro das RAs, não entre elas** (média anual; entre-RA fica em 34%). Em outras palavras: políticas públicas educacionais que tratam a RA como unidade homogênea (que é a granularidade típica do IPP, do IPS e da maioria dos painéis municipais) estão errando o foco — a maior parte da variância está em escala mais fina, **bairro a bairro**.

Esse achado é justamente o tipo de evidência que o produto HEX-EDU pretende tornar visível: um mapa H3 do Rio em que cada hexágono carrega o IDEB interpolado pelo bairro de origem, em lugar do agregado por RA que mascara a variação relevante.

## Decomposição por ano

| Ano | n bairros | n RAs | IDEB médio | T total | T entre-RA | T dentro-RA | % entre | % dentro |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2007 | 150 | 33 | 4.59 | 0.0048 | 0.0019 | 0.0028 | 41% | 59% |
| 2009 | 149 | 32 | 5.10 | 0.0052 | 0.0017 | 0.0036 | 32% | 68% |
| 2011 | 148 | 32 | 5.48 | 0.0044 | 0.0014 | 0.0030 | 31% | 69% |
| 2013 | 148 | 32 | 5.33 | 0.0066 | 0.0018 | 0.0048 | 27% | 73% |
| 2015 | 147 | 33 | 5.63 | 0.0040 | 0.0013 | 0.0026 | 33% | 67% |
| 2017 | 145 | 33 | 5.80 | 0.0035 | 0.0013 | 0.0022 | 38% | 62% |
| 2019 | 145 | 33 | 5.81 | 0.0026 | 0.0009 | 0.0018 | 32% | 68% |
| 2021 | 129 | 30 | 5.47 | 0.0045 | 0.0017 | 0.0028 | 39% | 61% |
| 2023 | 147 | 33 | 6.00 | 0.0035 | 0.0011 | 0.0024 | 32% | 68% |

## Variação 2007 → 2023

- IDEB médio: 4.59 → 6.00 (Δ +1.41)
- T total: 0.0048 → 0.0035 (Δ -0.0013)
- T entre-RA: 0.0019 → 0.0011 (Δ -0.0008)
- T dentro-RA: 0.0028 → 0.0024
- Parcela entre-RA: 41% → 32%

## Ranking de RAs por IDEB médio em 2023

| # | RA | IDEB médio | n bairros válidos |
| ---: | :--- | ---: | ---: |
| 1 | XXVIII Jacarezinho | 5.20 | 1 |
| 2 | XXI  Paquetá | 5.20 | 1 |
| 3 | XXV Pavuna | 5.30 | 6 |
| 4 | XXIX Complexo do Alemão | 5.40 | 1 |
| 5 | I Portuária | 5.47 | 3 |
| 6 | XXX Maré | 5.60 | 1 |
| 7 | XVII Bangu | 5.68 | 5 |
| 8 | XXXI Vigário Geral | 5.73 | 4 |
| 9 | XXXIII Cidade de Deus | 5.80 | 1 |
| 10 | XII Inhaúma | 5.82 | 6 |
| 11 | XIII Méier | 5.84 | 12 |
| 12 | XXIII Santa Teresa | 5.90 | 1 |
| 13 | XXVII Rocinha | 5.90 | 1 |
| 14 | XV Madureira | 5.92 | 13 |
| 15 | XXII Anchieta | 5.93 | 4 |
| 16 | III Rio Comprido | 6.00 | 3 |
| 17 | VIII Tijuca | 6.00 | 3 |
| 18 | XIV Irajá | 6.02 | 5 |
| 19 | XIX Santa Cruz | 6.03 | 3 |
| 20 | XX Ilha do Governador | 6.09 | 13 |
| 21 | VII São Cristóvão | 6.10 | 3 |
| 22 | IX Vila Isabel | 6.12 | 4 |
| 23 | XXIV Barra da Tijuca | 6.14 | 5 |
| 24 | XVI Jacarepaguá | 6.14 | 10 |
| 25 | XVIII Campo Grande | 6.22 | 5 |
| 26 | X Ramos | 6.22 | 4 |
| 27 | VI Lagoa | 6.23 | 7 |
| 28 | XI Penha | 6.23 | 3 |
| 29 | II Centro | 6.30 | 1 |
| 30 | XXVI Guaratiba | 6.33 | 3 |
| 31 | V Copacabana | 6.35 | 2 |
| 32 | XXXII Realengo | 6.35 | 6 |
| 33 | IV Botafogo | 6.50 | 7 |

## Caveats

- **Peso igual por bairro**: tratamos cada bairro como uma unidade. Em rigor, o IDEB de um bairro com 30 escolas e o de um com 1 escola contam igual no T. Ponderação por nº de matrículas seria mais defensável; o data.rio tem dados de matrícula em outros itens — implementar na próxima iteração.
- **IDEB ≠ qualidade educacional total**: é uma combinação de fluxo (aprovação) e desempenho (SAEB). Análises mais ricas decompõem cada componente separado, como faz Pereira et al. (2019).
- **Rede municipal apenas**: IDEB reportado aqui cobre a rede pública municipal. Bairros sem escolas municipais (ou com IDEB suprimido por baixa amostra) ficam fora — viés sistemático contra zonas com forte presença privada/estadual.
- **MAUP**: a definição de bairro segue o IPP. Mudanças de fronteira ao longo dos anos podem inflar/deflar `T_within`. Não corrigido aqui.
- **Sanity check**: a coluna `check_sum` em `theil_ideb_anos_iniciais.csv` é `T_b + T_w - T` e deve ser ≈ 0 (precisão de ponto flutuante). Cheque antes de citar números.

## Reprodutibilidade

```bash
pip install xlrd>=2.0
python3 analysis/03_download_excels.py    # se ainda não baixou
python3 analysis/10_theil_ideb.py
```
Saídas: `data/processed/ideb_bairros.csv` (long format) e `data/processed/theil_ideb_anos_iniciais.csv`.
