# 07 — HEX-EDU estático: o que o coroplético por RA esconde

Primeiro entregável visual do produto **HEX-EDU**. Apresenta lado-a-lado o mesmo dado de IDEB séries iniciais em duas resoluções espaciais: agregado por **Região Administrativa** (33 unidades, padrão IPP) e por **hex H3 res 8** (1593 unidades, herdando o IDEB do bairro do centroide).

Justificativa metodológica direta no [Relatório 06](06_theil_ideb.md): 60–70% da desigualdade do IDEB municipal está dentro das RAs em todos os 9 anos disponíveis. O mapa da esquerda mascara essa variação. O da direita a preserva.
## Mapa principal — 2023

![HEX-EDU 2023](_assets/07_hex_edu_2023.png)

_1593 hexes H3 ao todo; 1524 carregam IDEB de 2023 do bairro do seu centroide. Hexes em cinza: bairro sem IDEB municipal naquele ano (rede privada/estadual dominante, escolas suprimidas por baixa amostra, ou bairros sem escolas básicas reportadas)._

## Painel temporal — 4 snapshots de 2007 a 2023

![HEX-EDU painel](_assets/07_hex_edu_panel.png)

## Cobertura por ano

| Ano | Hexes com IDEB | % cobertura |
| ---: | ---: | ---: |
| 2007 | 1528 | 96% |
| 2013 | 1527 | 96% |
| 2019 | 1517 | 95% |
| 2023 | 1524 | 96% |

## Como ler

- **Paleta divergente** ancorada em IDEB = 6.0 (≈ média municipal). Vermelho = abaixo da média, azul = acima.
- **Range fixado** em [4.5, 7.5] para que diferentes anos sejam comparáveis lado-a-lado. IDEB municipal raramente sai desse intervalo na prática.
- **Linhas pretas finas** no mapa H3 são os limites de bairro do IPP — ajudam a identificar regiões.
- **Cinza claro**: sem dado naquele ano. Comum em 2007 (ano inicial do IDEB) e em bairros pequenos sem escolas municipais.

## Caveats herdados

Tudo do Relatório 06 continua válido — peso igual por bairro, IDEB ≠ qualidade total, rede municipal apenas, MAUP. Aqui, dois novos:
- **7 bairros não têm hex centroide em res 8** (Abolição, Argentino, Bancários, Cocotá, Jabour, Lapa, Saúde — todos pequenos). Aparecem em branco mesmo quando têm IDEB. Subir para res 9 (~12k hexes) cobriria todos, ao custo de mais ruído visual.
- **O hex herda o IDEB do bairro inteiro**: dentro de bairros grandes (Santa Cruz, Campo Grande, Jacarepaguá), todos os hexes são uniformes. A real variância intra-bairro só apareceria com dado por escola, que o data.rio não publica.

## Reprodutibilidade

```bash
pip install -r requirements.txt
python3 analysis/11_fetch_bairros.py    # se ainda não fez
python3 analysis/12_h3_grid.py
python3 analysis/13_hex_edu_static.py
```
Saídas: `data/processed/hex_ideb_panel.csv`, e os PNGs em `docs/reports/_assets/`.

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [08 — Mapa interativo (técnico)](08_hex_edu_interactive.md)
    - [Mapa interativo (página pública)](../mapa.md)
    - [HEX-EDU (página de produto)](../produtos/hex_edu.md)
