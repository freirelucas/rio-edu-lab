---
title: HEX-EDU — H3 hexagonal grid aplicado ao IDEB do Rio
description: Operacionalização da metodologia Pereira et al. (2019) IPEA para acessibilidade educacional no Rio Municipal.
---

# 📐 HEX-EDU

> Aplicação do **H3 hexagonal grid** ao IDEB municipal carioca por bairro. Versão atual entrega decomposição Theil-T da inequidade educacional. Próxima iteração estende para **análise de acessibilidade** seguindo Pereira et al. (2019) IPEA.

[![paper](https://img.shields.io/badge/paper--base-Pereira_et_al._2019_IPEA-008572)](https://hdl.handle.net/10419/240730)
[![paper](https://img.shields.io/badge/m%C3%A9todo--base-Theil_1967-008572)](https://en.wikipedia.org/wiki/Theil_index)
[![relatórios](https://img.shields.io/badge/leitura_t%C3%A9cnica-relat%C3%B3rios_06%2C_07%2C_08-grey)](../reports/06_theil_ideb.md)
[![mapa](https://img.shields.io/badge/mapa_interativo-%E2%86%92-2166ac)](../mapa.md)

## Paper-base

**Pereira, R. H. M.; Braga, C. K. V.; Serra, B.; Nadalin, V. G. (2019).** *Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019.* IPEA Texto para Discussão. <https://hdl.handle.net/10419/240730>

**Método dos autores**: discretização do território urbano em hexágonos H3 (resolução variável conforme densidade), cálculo de **acessibilidade a oportunidades** (educação, saúde, emprego, lazer) ponderada pela **proximidade temporal** (isócronas via OSM) e pela **qualidade/quantidade** da oportunidade. Decomposição da acessibilidade por **renda** e **raça** revela inequidades sistemáticas: pessoas brancas e de alta renda têm maior acessibilidade.

**Cidades cobertas no paper**: São Paulo, Rio de Janeiro, Belo Horizonte, Recife, Fortaleza, Porto Alegre, Curitiba (transporte público) + 20 cidades para transporte ativo.

## O que entregamos hoje (v0.5)

**Subseção do método Pereira aplicada ao Rio**: usamos H3 resolução 8 (≈ 0.7 km², ≈ 1593 hexes para o município) sobre o IDEB municipal por bairro. Cada hexágono herda o IDEB do bairro do seu centroide. Em vez da métrica de acessibilidade do paper original, **aplicamos decomposição Theil-T** do IDEB para mensurar a heterogeneidade espacial.

**Achado**: 66% da desigualdade do IDEB municipal carioca está **dentro das RAs**, não entre. Coropléticos por RA mascaram a maior parte da variância relevante. ([Relatório 06](../reports/06_theil_ideb.md))

## O que falta para a replicação completa (v0.6)

A versão atual **não entrega** a métrica de acessibilidade per se. Falta:

1. **Pontos das escolas municipais geocoded** — disponível como Feature Service no data.rio (item `0a220ea7972449e39a28210dd317f636`).
2. **Rede viária** — extração via OSMnx ou OSM Planet.
3. **Isócronas** — tempos de viagem por hex até as N escolas mais próximas (a pé e/ou ônibus).
4. **Ponderação por qualidade** — multiplicar acessibilidade por IDEB da escola atingida.
5. **Decomposição por SES** — usar IPS/IDS por bairro (ambos disponíveis no data.rio) como variável de equidade.

Esse é o roadmap explicito do **PR-E** subsequente. Até lá, a página comunica honestamente: HEX-EDU v0.5 = Theil + H3 grid pronto; acessibilidade Pereira-style em construção.

## Visualizações disponíveis hoje

### Mapa estático: RA vs H3 (2023)

![HEX-EDU 2023](../reports/_assets/07_hex_edu_2023.png)

Esquerda: por RA (33). Direita: por hex H3 (1593). Mesma escala de cor, mesmo dado. Bolsões vermelhos visíveis na direita estão dentro de RAs cuja média é "ok".

[:material-map: Versão interativa em /mapa/](../mapa.md){ .md-button }

### Robustez do achado Theil (linha do tempo, 6 séries)

<div data-chart="../../_assets/charts/tour_slide_3.json"></div>

A parcela within-RA fica entre 59% e 73% em todos os 9 anos, em todas as 6 séries (5º, 9º, ponderado, Aprovação, SAEB, IDEB).

## Caveats

- **A v0.5 não é Pereira et al. 2019 ainda**. É uma sub-análise (Theil sobre H3 grid) que reusa o substrato espacial. A replicação completa fica para v0.6 — declarado explicitamente.
- **Apenas rede municipal**. Bairros com escola privada/estadual dominante saem do dataset municipal de IDEB.
- **MAUP** (Brewer & Pickle 1999): sensibilidade à definição de unidade de área. Documentado.
- **Peso igual por bairro** na versão base. Ponderação por matrícula reduz T_total ~44% mas preserva o achado within > between (Relatório 06b).

## Reproduzir (v0.5)

```bash
pip install -r requirements.txt
pip install -e reference/acec-hub

python3 analysis/03_download_excels.py     # IDEB Excel
python3 analysis/10_theil_ideb.py          # decomposição base
python3 analysis/11_fetch_bairros.py       # geometry IPP
python3 analysis/12_h3_grid.py             # H3 res 8
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

- **Pereira, R. H. M.; Braga, C. K. V.; Serra, B.; Nadalin, V. G. (2019).** *Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019.* IPEA. <https://hdl.handle.net/10419/240730>. **Paper-base canônico do HEX-EDU**.
- **Theil, H. (1967).** *Economics and Information Theory*. North-Holland. **Método estatístico-base da decomposição Theil-T usada na sub-análise atual.**
- Brewer, C. A.; Pickle, L. (1999) — método do MAUP, citado nos caveats.

## Continue

<div class="grid cards" markdown>

-   [:material-map: Mapa interativo](../mapa.md)
-   [:material-rocket-launch-outline: Tour 5 min](../tour.md)
-   [:material-format-list-bulleted: Bairros prioritários](../bairros-prioritarios.md)
-   [:material-book-open-variant: Investigação técnica](../investigacao.md)

</div>
