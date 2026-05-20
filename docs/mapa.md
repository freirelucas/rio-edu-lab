---
title: Onde a educação no Rio é mais desigual (por bairro) — rio-edu-lab
description: 1.593 hexágonos H3 com IDEB de cada ano (2007-2023). Bolsões de baixo desempenho dentro de regiões médias. Hover por bairro, seletor de ano.
---

# Onde a educação no Rio é mais desigual (por bairro)

Coropléticos do IDEB por Região Administrativa fazem o Rio parecer monolítico — Zona Sul "ok", Zona Norte "média". O mapa abaixo mostra a verdade em granularidade fina: **bolsões de baixo desempenho convivem com bairros médios dentro da mesma região**. É o achado Theil (66% within-RA) tornado visual.

!!! info "Como ler"
    - **Vermelho** = IDEB abaixo da média municipal de 6.0.
    - **Azul** = acima.
    - **Cinza** = bairro sem IDEB municipal naquele ano (rede privada/estadual dominante, ou supressão por baixa amostra).
    - Use o painel direito pra alternar entre os 9 anos disponíveis (2007–2023, IDEB séries iniciais da rede municipal).

<div class="lazy-iframe-wrap">
<iframe src="../reports/_assets/08_hex_edu_interactive.html"
        loading="lazy"
        title="Mapa HEX-EDU interativo"></iframe>
</div>

## Por dentro da viz

Cada hexágono H3 (resolução 8, ≈ 0,7 km²) herda o IDEB do bairro do seu centroide. 1.593 hexes cobrem o município. 7 bairros muito pequenos (Lapa, Saúde, Bancários, Cocotá, Abolição, Argentino, Jabour) não têm hex centroide nesta resolução e aparecem em branco mesmo com dado.

### Fontes

- **IDEB**: data.rio item `9fd1a8cc207a48c5bda7131e4e74b1ca`, sheet `ANOS_INICIAIS`.
- **Geometria de bairros**: data.rio item `dc94b29fc3594a5bb4d297bee0c9a3f2` ("Limite de Bairros", IPP).
- **Pipeline**: scripts `12_h3_grid.py` (grid), `13_hex_edu_static.py` (versão estática), `14_hex_edu_folium.py` (mapa interativo).

## Continue

<div class="grid cards" markdown>

-   [:material-magnify: Outros achados](achados.md)
-   [:material-map-outline: Versão estática (RA vs H3)](reports/07_hex_edu_static.md)
-   [:material-library-shelves: Papers](papers/index.md)
-   [:material-format-list-bulleted: Bairros prioritários](bairros-prioritarios.md)

</div>
