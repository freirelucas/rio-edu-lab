---
title: 14 — Acessibilidade educacional H3 (HEX-EDU v0.6, Pereira-style)
description: Replicação metodológica da Pereira et al. (2019) IPEA aplicada ao Rio Municipal — acessibilidade ponderada por IDEB.
---

# 14 — Acessibilidade educacional H3 (HEX-EDU v0.6)

> Operacionalização parcial de Pereira, Braga, Serra & Nadalin (2019) para o Rio Municipal: para cada célula H3 do município, computamos uma métrica de **acesso a equipamentos educacionais ponderada pela qualidade** (IDEB do bairro da escola) e penalizada pela distância. Esta v0.6.1 usa **distância haversine** entre centroide do hex e ponto da escola; v0.7 substituirá por isócronas via OSM road network.

## Paper-base

**Pereira, R. H. M.; Braga, C. K. V.; Serra, B.; Nadalin, V. G. (2019).** *Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019.* IPEA TD. <https://hdl.handle.net/10419/240730>

O paper computa acessibilidade a oportunidades (educação, saúde, emprego, lazer) em 7 capitais brasileiras (Rio incluso) usando isócronas H3 sobre redes de transporte público + ativo. Decompõe por raça e renda. Achado canônico: pessoas brancas e de alta renda têm maior acessibilidade.

## Insumos

| Dado | Fonte | Quantidade |
|---|---|---:|
| Equipamentos educacionais (pontos geo) | data.rio Feature Service `0a220ea7972449e39a28210dd317f636` | 1590 totais |
| Filtro: equipamentos elegíveis ao IDEB séries iniciais | Escola Municipal + CIEP + Escola Especial Municipal | 1022 |
| Grid espacial | H3 res 8 (Sessão 12) | 1593 hexes |
| Qualidade da escola | IDEB do bairro do equipamento (Relatório 06), ano 2023 | 993/1022 com IDEB |
| Geometria de bairros | data.rio item `dc94b29f...` (IPP) | 166 bairros |

29 escolas (3%) ficam em bairros sem IDEB municipal — preenchidas com a mediana 6.0.

## Métricas computadas

Para cada hex i:

```
n_2km(i)            = # equipamentos eleg. em raio de 2 km
n_5km(i)            = # equipamentos eleg. em raio de 5 km
dist_min_km(i)      = distância haversine ao equipamento eleg. mais próximo
acesso_qty(i)       = Σ_j exp(-d(i,j)/d0)              (j em raio de 5 km)
acesso_quality(i)   = Σ_j IDEB(j) · exp(-d(i,j)/d0)    (j em raio de 5 km)
```

com `d0 = 1.5 km` (parâmetro de impedância — distância caminhável típica de ~18 min). `acesso_quality` é a métrica Pereira-style: oportunidade educacional ponderada por qualidade da opção, com penalização exponencial pela distância.

## Resultado

### Mapa

<div data-chart="../_assets/charts/acessibilidade_map.json"></div>

### Distribuição por AP

<div data-chart="../_assets/charts/acessibilidade_dist.json"></div>

## Achado-headline

| AP | n hexes | acesso_quality médio | acesso_quality mediano |
|---:|---:|---:|---:|
| AP 3 (Zona Norte) | 270 | **113** | 126 |
| AP 1 (Centro) | 44 | 96 | 99 |
| AP 2 (Zona Sul) | 134 | 59 | 54 |
| AP 5 (Zona Oeste) | 757 | 45 | 33 |
| AP 4 (Barra/Jacarepaguá) | 388 | 29 | 18 |

**A Zona Norte (AP 3) lidera o acesso ponderado** — não a Zona Sul. Esse é um achado contra-intuitivo se a expectativa é "melhor IDEB médio = melhor acesso". A explicação: AP 3 combina **alta densidade urbana** (muitas escolas próximas) com IDEB municipal mediano. AP 2 (Zona Sul) tem IDEB médio mais alto mas densidade muito menor — e os melhores alunos provavelmente estão na rede privada, fora do nosso recorte. AP 4 (Barra/Jacarepaguá) sofre **dispersão** e dependência de transporte.

Em política pública: granularidade administrativa **AP** continua escondendo variância — o achado within-RA do Relatório 06 se repete aqui em forma diferente (entre APs há variação relevante; mas a média por AP esconde a variação intra-AP, que continua dominante).

## Caveats

- **Distância haversine ≠ tempo de viagem real**. Caminho até a escola passa por ruas, morros, pontes, transporte público. Esta v0.6.1 usa "linha reta" como aproximação — útil como ordenação, mas não como métrica absoluta. v0.7 substitui por isócronas OSM (osmnx + grafos rodoviários).
- **Qualidade = IDEB do bairro** não é IDEB da escola. Conflate múltiplas escolas dentro de um bairro num único valor. Pereira et al. usavam métricas próprias por equipamento; nós usamos o melhor proxy disponível no data.rio.
- **Apenas rede municipal**. Migração para escola privada (que confunde o FUN-Rio) também distorce este produto: equipamentos privados/estaduais não aparecem.
- **Filtro 5 km**: hexes em zonas peri-urbanas (Guaratiba, Vargem) têm poucas ou zero opções no raio. 18 hexes têm n_5km = 0.
- **d0 = 1.5 km arbitrário**: parâmetro de impedância calibrado para "distância caminhável típica". Pereira et al. usam tempos de viagem (tipicamente 30 ou 60 min). v0.7 calibra contra dados reais.

## v0.7 — o que falta para a replicação completa

1. **OSM road network** via `osmnx.graph_from_place("Rio de Janeiro, Brazil", network_type="walk")`.
2. **Isócronas**: para cada hex centroide, computar shortest-path real até cada escola.
3. **Decomposição por SES**: cruzar com IPS/IDS por bairro para reproduzir a "decomposição por renda" de Pereira. Esta v0.6 só decompõe por AP (geografia), não por SES.
4. **Múltiplas resoluções**: Pereira usa H3 res 9 (~12k hexes) para áreas densas. v0.7 pode ter resolução variável por densidade urbana.

## Reproduzir

```bash
pip install -r requirements.txt   # inclui scipy

python3 analysis/11_fetch_bairros.py            # se ainda não fez
python3 analysis/12_h3_grid.py                  # se ainda não fez
python3 analysis/25_fetch_escolas_municipais.py # 1590 features, ~500 KiB
python3 analysis/26_hex_accessibility.py        # ~5 s
python3 analysis/27_accessibility_charts.py     # Plotly JSONs
```

Saídas: `data/processed/hex_accessibility.csv` (1593 hexes × 9 colunas) + 2 figuras Plotly.

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [HEX-EDU (produto canônico)](../produtos/hex_edu.md)
    - [Bairros prioritários (cruzamento com FUN+PM12)](../bairros-prioritarios.md)
    - [Mapa interativo](../mapa.md)
