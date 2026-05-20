---
title: HEX-EDU — detalhe técnico (Theil + Pereira aplicados ao Rio)
description: Decomposição Theil-T do IDEB por bairro + acessibilidade Pereira-style. Substrato H3 res 8 (1.593 hexes). Achados, viz e código.
---

# HEX-EDU — detalhe técnico

> **Saída do funil. Dois papers cruzados num substrato comum (H3 res 8 + bairros IPP).**
> Theil (1967) responde "onde está a desigualdade do IDEB"; Pereira et al. (2019) responde "qual zona tem mais acesso a boas escolas".

[← Voltar pra Achados](../achados.md){ .md-button }

## Desigualdade do IDEB — 66% within-RA { #desigualdade }

**Achado:** **66% da variância do IDEB municipal carioca está dentro das Regiões Administrativas, não entre.** Robusto em 6 séries × 9 anos: a parcela within-RA fica entre 59% e 73%. Nenhuma série cruza paridade 50%.

**Paper:** Theil, H. (1967). *Economics and Information Theory*. North-Holland. [Mini-page →](../papers/theil-1967-economics.md)

**Método aplicado.** Decomposição Theil-T (índice GE(α=1)) do IDEB por bairro, particionado por RA:

$$T_{total} = T_{between} + T_{within}$$

onde `T_within / T_total` mede a fração da desigualdade que vive dentro das RAs (não entre).

### Robustez (6 séries × 9 anos)

<div data-chart="../_assets/charts/tour_slide_3.json"></div>

A parcela within-RA fica entre 59% e 73% em todos os 9 anos, em todas as 6 séries (5º, 9º, ponderado por matrícula, Aprovação/SAEB/IDEB).

### Visualização espacial (RA vs H3)

![HEX-EDU 2023](../reports/_assets/07_hex_edu_2023.png)

Esquerda: por RA (33 unidades). Direita: por hex H3 (1.593, resolução 8). Mesma escala de cor, mesmo dado. Bolsões vermelhos visíveis na direita estão dentro de RAs cuja média é "ok".

[:material-map: Versão interativa em /mapa/](../mapa.md){ .md-button }

### Como auditar

- [Relatório 06 — Decomposição Theil do IDEB por bairro](../reports/06_theil_ideb.md)
- [Relatório 11 — Theil 3-níveis (AP/RA/bairro)](../reports/11_thesha_rio.md): 8% / 26% / 67%
- Código: `analysis/10_theil_ideb.py`, `analysis/16_theil_weighted.py`, `analysis/18_thesha_rio.py`

```python
from acec.stats import theil_decompose
import pandas as pd
df = pd.read_csv("data/processed/ideb_bairros.csv")
df = df[df["year"] == 2023].dropna()
t, tb, tw = theil_decompose(df["ideb"], df["ra"])
print(f"share_within = {tw/t:.0%}")  # 68%
```

---

## Acessibilidade — AP 3 lidera, não Zona Sul { #acessibilidade }

**Achado:** **AP 3 (Zona Norte) lidera o acesso ponderado por IDEB com média 113.** Centro (AP 1) fica em 96, Zona Sul (AP 2) em 59, AP 4 (Barra/Jacarepaguá) em 29. **Densidade vence qualidade isolada.**

**Paper:** Pereira, R. H. M., Braga, C. K. V., Serra, B., & Nadalin, V. G. (2019). *Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras — 2019*. IPEA Texto para Discussão 2535. [Mini-page →](../papers/pereira-2019-ipea.md)

**Método aplicado (parcial).** Para cada hex H3 (1.593 unidades, res 8) computamos:

```
acesso_quality(i) = Σ_j IDEB(j) · exp(-d(i,j)/d0)
```

onde *j* são as escolas elegíveis (Municipal + CIEP + Especial = 1.022) em raio de 5 km, *d* é a distância haversine, e `d0 = 1.5 km` é o parâmetro de impedância.

### Limites da replicação atual

- Pereira et al. usam isócronas reais via OpenTripPlanner (rede viária + GTFS). Aqui usamos haversine como proxy — versão futura precisa adicionar OSM + GTFS RioCard (categoria `travel-network` no funil, hoje **external**).
- Decomposição por **renda** e **raça** do paper original não está replicada — fica pra próximo bump quando microdado SES per-hex estiver disponível.

### Como auditar

- [Relatório 14 — Acessibilidade Pereira-style](../reports/14_acessibilidade.md)
- Código: `analysis/13_hex_edu_static.py`, `analysis/14_hex_edu_folium.py`

---

## Caveats compartilhados

- **MAUP** (Modifiable Areal Unit Problem, Brewer & Pickle 1999): sensibilidade à definição de unidade de área. Documentado.
- **Apenas rede municipal.** Bairros com escola privada/estadual dominante saem do dataset municipal de IDEB.
- **Peso igual por bairro** na versão base; ponderação por matrícula reduz T_total ~44% mas preserva achado within > between ([Relatório 06b](../reports/06b_theil_weighted.md)).

## Substrato espacial (compartilhado pelas duas análises)

Ambas usam o mesmo grid:

- **H3 hexagonal grid**, resolução 8 (~0,7 km² por hex)
- **1.593 hexes** cobrindo o município
- **163 bairros oficiais** (IPP) como partição administrativa
- Geometry: data.rio item `dc94b29fc3594a5bb4d297bee0c9a3f2`

A v0.6 mede "quanta opção tenho perto"; a v0.5 mede "quanta variância existe entre opções, agregada por escala administrativa". Mesmo substrato, perguntas diferentes — duas saídas do funil sobre o mesmo dado.

## Reproduzir

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

## Continue

<div class="grid cards" markdown>

-   [:material-map: Mapa interativo](../mapa.md)
-   [:material-library-shelves: Papers](../papers/index.md)
-   [:material-format-list-bulleted: Bairros prioritários](../bairros-prioritarios.md)
-   [:material-magnify: Outros achados](../achados.md)

</div>
