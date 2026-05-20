---
title: Mapa HEX-EDU interativo — IDEB por bairro do Rio
description: 1593 hexágonos H3 com IDEB de cada ano (2007-2023). Hover por bairro, seletor de ano.
---

# Mapa interativo HEX-EDU

Cada hexágono H3 (resolução 8, ≈ 0.7 km²) herda o IDEB do bairro do seu centroide. **Hover** mostra bairro, ano e valor. Use o painel direito para alternar entre os 9 anos disponíveis (2007–2023, IDEB séries iniciais da rede municipal).

!!! info "Como ler"
    - **Vermelho** = IDEB abaixo da média municipal de 6.0.
    - **Azul** = acima.
    - **Cinza** = bairro sem IDEB municipal naquele ano (rede privada/estadual dominante, ou supressão por baixa amostra).
    - 7 bairros muito pequenos (Lapa, Saúde, Bancários, Cocotá, Abolição, Argentino, Jabour) não têm hex centroide nesta resolução; aparecem em branco mesmo com dado.

<div class="lazy-iframe-wrap">
<iframe src="../reports/_assets/08_hex_edu_interactive.html"
        loading="lazy"
        title="Mapa HEX-EDU interativo"></iframe>
</div>

## Onde isto vem de

- **Fonte do IDEB**: data.rio item `9fd1a8cc207a48c5bda7131e4e74b1ca`, sheet `ANOS_INICIAIS`.
- **Fonte da geometria**: data.rio item `dc94b29fc3594a5bb4d297bee0c9a3f2` ("Limite de Bairros", IPP).
- **Pipeline**: 17 scripts em `analysis/`. O grid H3 é gerado por `analysis/12_h3_grid.py`; o mapa interativo por `analysis/14_hex_edu_folium.py`.

## Continue

<div class="grid cards" markdown>

-   [:material-map-outline: Versão estática (4 anos × RA vs H3)](reports/07_hex_edu_static.md)
-   [:material-library-shelves: Papers](papers/index.md)
-   [:material-format-list-bulleted: Bairros prioritários](bairros-prioritarios.md)
-   [:material-text-box-outline: Análise técnica do HEX-EDU](produtos/hex_edu.md)

</div>
