# 11 — THESHA-Rio: decomposição Theil em 3 níveis

Segundo produto do MVP-1 do ACEC-Hub. Onde o HEX-EDU (Relatório 06) mediu desigualdade educacional carioca em 2 níveis (RAs vs bairros), o THESHA-Rio decompõe em 3 níveis aninhados, inspirado em Bourguignon, Ferreira & Menéndez (2007) sobre decomposição de desigualdade por características hierárquicas.

Identidade aditiva (testada em `reference/acec-hub/tests/test_acec_stats.py`):

```
T_total = T_between_AP + T_between_RA_within_AP + T_within_RA
```

## Mapa principal

![THESHA-Rio panel](_assets/11_thesha_rio_panel.png)

## Decomposição por ano

| Ano | T total | entre APs | entre RAs (em AP) | entre bairros (em RA) | residual |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2007 | 0.004763 | 0.000376 (8%) | 0.001562 (33%) | 0.002825 (59%) | -0.00e+00 |
| 2009 | 0.005226 | 0.000642 (12%) | 0.001023 (20%) | 0.003561 (68%) | 0.00e+00 |
| 2011 | 0.004362 | 0.000322 (7%) | 0.00104 (24%) | 0.003 (69%) | -0.00e+00 |
| 2013 | 0.006587 | 0.000188 (3%) | 0.001579 (24%) | 0.004821 (73%) | -0.00e+00 |
| 2015 | 0.00397 | 0.000145 (4%) | 0.001178 (30%) | 0.002646 (67%) | -0.00e+00 |
| 2017 | 0.003494 | 0.000307 (9%) | 0.001003 (29%) | 0.002183 (62%) | -0.00e+00 |
| 2019 | 0.002639 | 0.000107 (4%) | 0.000747 (28%) | 0.001785 (68%) | -0.00e+00 |
| 2021 | 0.004523 | 0.00067 (15%) | 0.001074 (24%) | 0.00278 (61%) | -0.00e+00 |
| 2023 | 0.003508 | 0.000326 (9%) | 0.000795 (23%) | 0.002387 (68%) | -0.00e+00 |

## Achado principal

Médias entre 9 anos:

- Entre APs (5 zonas): **8%**
- Entre RAs dentro da AP (33 unidades): **26%**
- Entre bairros dentro da RA (163 unidades): **66%**

O componente **bairro-within-RA** domina (66%). A diferença entre 'eu moro em uma RA azul ou vermelha' (intermediário) é ~3× **menor** que a diferença entre 'eu moro em qual bairro dessa RA' (o que efetivamente determina o IDEB da escola que meu filho frequenta). A diferença entre APs (zonas amplas: Centro, Norte, Sul, Oeste) é a menor parcela (8%) — agregar ainda mais grosseiro do que RA esconderia praticamente toda a variância.

## Implicação para política

Programa que aloque recursos por AP (típico de planejamento estratégico macro) erra a parcela majoritária. Programa que aloque por RA (típico do IPP) também erra. **A escala correta de intervenção é o bairro** — exatamente o que o HEX-EDU torna visível (Relatório 07).

## Caveats

- **Mesma fonte do HEX-EDU**: IDEB séries iniciais por bairro (data.rio item `9fd1a8cc...`). Não é dado independente.
- **Bairros agregados de fato heterogêneos**: dentro de Campo Grande (bairro 5º maior do Rio em pop.) há sub-zonas que não aparecem aqui. Granularidade infra-bairro só com dado por escola.
- **5 APs apenas**: T_between_AP tem só 5 graus de liberdade — qualquer outlier puxa a parcela. RA-level é mais robusto estatisticamente.
- **Sanity numérica**: cada linha da tabela inclui `check_residual`. Valores absolutos < 1e-6 confirmam que a decomposição aditiva está correta dentro de precisão de ponto flutuante.

## Reprodutibilidade

```bash
pip install -e reference/acec-hub  # se ainda não
pip install -r requirements.txt
python3 analysis/18_thesha_rio.py
```
Saídas: `data/processed/thesha_rio.csv` e os PNGs em `docs/reports/_assets/`.

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [THESHA-Rio (página de produto)](../produtos/thesha_rio.md)
    - [HEX-EDU (2-níveis)](../produtos/hex_edu.md)
    - [Bairros prioritários](../bairros-prioritarios.md)
