---
title: HEX-EDU — Theil aplicado ao IDEB do Rio
description: Replicação do índice de Theil (1967) sobre o IDEB municipal carioca em granularidade de bairro.
---

# 📐 HEX-EDU

> Mapa H3 do IDEB por bairro municipal do Rio. **66% da desigualdade educacional está dentro das RAs**, não entre.

[![paper](https://img.shields.io/badge/paper--base-Theil_1967-008572)](https://en.wikipedia.org/wiki/Theil_index)
[![relatórios](https://img.shields.io/badge/leitura_t%C3%A9cnica-relat%C3%B3rios_06%2C_07%2C_08-grey)](../reports/06_theil_ideb.md)
[![mapa](https://img.shields.io/badge/mapa_interativo-%E2%86%92-2166ac)](../mapa.md)

<div class="compare-grid" markdown>

<div class="compare-paper" markdown>
### Theil (1967) — paper-base

**O que é**: o livro *Economics and Information Theory* introduz a métrica $T = (1/N) \sum_i (y_i/\bar y) \ln(y_i/\bar y)$, derivada da entropia de Shannon, como medida de desigualdade. Vantagem matemática: **decomposição aditiva exata** em parcela between-grupo + within-grupo.

**Domínio original**: distribuição de **renda** entre países, populações, classes sociais.

**Achado canônico**: a maior parte da desigualdade global de renda é entre países (between), não dentro de cada país (within). Conclusão geopolítica: políticas de transferência internacional movem mais a agulha que redistribuição doméstica.
</div>

<div class="compare-rio" markdown>
### O que achamos no Rio

**O que é**: aplicamos exatamente a mesma fórmula ao **IDEB séries iniciais por bairro** (163 bairros, 9 anos, 2007–2023, fonte data.rio item `9fd1a8cc...`).

**Decomposição**: agrupamos por Região Administrativa (33 RAs).

**Achado**: em todos os 9 anos, **T_within > T_between**. Média da parcela within = **66%**. O **inverso** do achado canônico de Theil sobre renda inter-países.

A decomposição $T_b + T_w \to T$ holds dentro de 1e-6 em todos os anos — virou um teste hard-fail no nosso CI.
</div>

</div>

## Comparação

A inversão do padrão "between domina" de Theil para "within domina" no nosso caso tem 2 leituras possíveis:

1. **A unidade administrativa é grossa demais**. RA é um agregado político-burocrático cuja fronteira nem sempre coincide com fronteira sócio-econômica. Bairro está mais perto da escala em que processos educacionais acontecem.
2. **O fenômeno educacional municipal é fundamentalmente intra-vizinhança**. Diferenças entre escolas dentro de um mesmo bairro/RA explicam mais do que diferenças entre RAs ou APs. Compatível com a literatura de stratificação educacional intra-cidade.

A diferença substantiva: o paper original sugere agir entre países; nossa replicação sugere agir intra-cidade na granularidade fina.

## Mapa do achado (2023)

![HEX-EDU 2023](../reports/_assets/07_hex_edu_2023.png)

Esquerda: por RA (33 unidades). Direita: por bairro (1593 hex H3 res 8). Mesma escala de cor, mesmo dado. Bolsões vermelhos visíveis na direita estão dentro de RAs cuja média é "ok".

[:material-map: Versão interativa em /mapa/](../mapa.md){ .md-button }

## Robustez (linha do tempo)

A parcela within-RA não é peculiar a 2023. Em todos os 9 anos, fica entre 59% e 73%:

<div data-chart="../../_assets/charts/tour_slide_3.json"></div>

Confirmado também sob 2 alternativas (relatórios 06b e 10):
- **Ponderação por matrícula** (2 anos): share_within continua > 50%.
- **Componentes separados**: Aprovação 70%, SAEB 64%, IDEB 66%. Robusto à escolha de indicador.

## Caveats

- **Peso igual por bairro** na versão base (cada bairro = 1 unidade). Ponderação por matrícula reduz T_total ~44% e share_within ~10pp, mas preserva o sinal (relatório 06b).
- **Apenas rede municipal**. Bairros com escola privada/estadual dominante saem do dataset.
- **MAUP**: fronteiras de bairro mudam ao longo dos anos.
- **IDEB combina fluxo (Aprovação) com desempenho (SAEB)**. Análises por componente em [Relatório 10](../reports/10_method_replication.md).

## Reproduzir

```bash
pip install -r requirements.txt
pip install -e reference/acec-hub  # pacote acec com Theil canônico

python3 analysis/03_download_excels.py     # baixa o IDEB Excel
python3 analysis/10_theil_ideb.py          # decomposição base
python3 analysis/13_hex_edu_static.py      # mapas estáticos
python3 analysis/14_hex_edu_folium.py      # mapa interativo
```

Sanity check do achado:

```python
from acec.stats import theil_decompose
import pandas as pd
df = pd.read_csv("data/processed/ideb_bairros.csv")
df = df[df["year"] == 2023].dropna()
t, tb, tw = theil_decompose(df["ideb"], df["ra"])
print(f"share_within = {tw/t:.0%}")  # 68%
```

## Referências

- Theil, H. (1967). *Economics and Information Theory*. North-Holland.
- Pereira et al. (2019) — citado no README do ACEC-Hub como paper-base; título exato e DOI não localizados nos artefatos do lab. Replicação numérica direta: backlog.

## Continue

<div class="grid cards" markdown>

-   [:material-map: Mapa interativo](../mapa.md)
-   [:material-rocket-launch-outline: Tour 5 min](../tour.md)
-   [:material-format-list-bulleted: Bairros prioritários](../bairros-prioritarios.md)
-   [:material-flask-outline: Paper draft](../paper/hex_edu_manuscript.md)

</div>
