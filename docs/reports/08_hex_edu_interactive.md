# 08 — HEX-EDU interativo

Mesmo conteúdo do [Relatório 07](07_hex_edu_static.md), mas em formato interativo: panning, zoom, tooltip por hex, e seletor de ano (toggle entre os 9 IDEBs disponíveis, 2007–2023).

<iframe src="_assets/08_hex_edu_interactive.html" width="100%" height="640" style="border:1px solid #ddd; border-radius:4px;"></iframe>

## Como usar

- **Painel direito**: alterne entre os anos disponíveis. Camada `Bordas de bairros` é always-on.
- **Hover sobre um hex**: mostra bairro, IDEB do ano selecionado, RP e AP.
- **Zoom**: scroll do mouse. Clique-arraste para mover.
- **Hexes cinza**: bairro sem IDEB municipal naquele ano.

## Limites técnicos

- HTML standalone com 9 camadas pré-renderizadas (~1593 features cada). Tamanho: ~1–2 MiB. Carrega de uma vez; não há lazy-loading.
- Não funciona offline (depende dos tiles `cartodbpositron`).
- Versão hospedada Streamlit (com slider contínuo, filtros por faixa de IDEB, pesos por matrícula) fica no roadmap pós-v0.1.

## Reprodutibilidade

```bash
pip install -r requirements.txt   # inclui folium e branca
python3 analysis/14_hex_edu_folium.py
```
