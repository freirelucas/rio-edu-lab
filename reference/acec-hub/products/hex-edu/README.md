# HEX-EDU — Mapa H3 de Inequidade Educacional Carioca

> Decomposição multi-escala da desigualdade educacional intra-Rio aplicando o framework de Theil (1967) sobre células H3, replicando metodologia de acessibilidade urbana de Pereira et al. (2019).

**Status:** 🟡 Em desenvolvimento (MVP-1 do ACEC-Hub).

## Pergunta de pesquisa

Em que escala espacial a desigualdade educacional carioca atinge seu máximo? A literatura clássica sobre o Modifiable Areal Unit Problem (MAUP) sugere que escolhas administrativas de fronteira (bairro, RA, CRE) podem mascarar ou amplificar padrões de inequidade. Aplicando indexação H3 multi-resolução (5 a 10) sobre os indicadores educacionais do data.rio, queremos identificar a escala "ótima" para políticas focalizadas — e quantificar o quanto a inequidade observada é artefato de escolha de unidade.

## Paper-base

- **Theil, H. (1967).** *Economics and Information Theory.* Amsterdam: North-Holland. — decomposição clássica de desigualdade entre/dentro de grupos.
- **Pereira, R. H. M., et al. (2019).** "Tudo nos Conformes? Análise de equidade no acesso a oportunidades em São Paulo via H3." IPEA. — uso de H3 em dados urbanos brasileiros.
- **Brewer, C. A., & Pickle, L. (1999).** "Comparing Ratio Maps for the United States." *Annals of the Association of American Geographers* — sensibilidade a MAUP.

## Dados utilizados

Subset do Grupo Educação do data.rio:

| Item | ID | Tipo | Uso |
|------|-----|------|-----|
| IDEB por bairro 2007–2023 | (a confirmar) | Excel | Variável de qualidade educacional |
| Taxa de alfabetização 1991/2000/2010/2022 | (a confirmar) | Excel/CSV | Variável temporal |
| Pontos de Escolas Municipais | `0a220ea7972449e39a28210dd317f636` | Feature Service | Geocodificação base |
| Polígonos das CREs | `fbfcbfae92654e248bdf1452cf260626` | Feature Service | Validação cruzada |
| Limites de bairros | (do GeoRio) | Externo | Conversão para H3 |

## Método

1. **Ingestão**: download via `acec.ingest.arcgis` dos itens listados.
2. **Geocodificação**: cada escola → célula H3 res 9; agregar para res 5–10.
3. **Construção do indicador**: composto IDEB + alfabetização normalizado.
4. **Decomposição Theil**: `T = T_between + T_within` em cada par (resolução, ano).
5. **Análise MAUP**: comparar T para H3 res 5–10 vs unidades administrativas (RA, CRE, bairro).
6. **Visualização**: app Streamlit com seletor de resolução + decomposição interativa.

## Estrutura

```
hex-edu/
├── notebooks/
│   ├── 01_explore.ipynb        # Exploração inicial dos itens
│   ├── 02_theil.ipynb          # Decomposição em unidades administrativas
│   └── 03_h3_multiscale.ipynb  # Análise H3 multi-resolução
├── app/
│   └── streamlit_app.py        # Visualização interativa
├── paper/
│   ├── manuscript.qmd          # Quarto manuscript
│   └── refs.bib                # Bibliografia
└── tests/
    └── test_theil.py           # Testes da decomposição
```

## Roadmap

- [ ] Download e exploração dos itens-base
- [ ] Implementação da decomposição Theil em `acec.transform.inequality`
- [ ] Pipeline de geocodificação H3 em `acec.geo.h3_aggregation`
- [ ] Notebooks 01–03
- [ ] App Streamlit
- [ ] Manuscript Quarto
- [ ] Submissão (target: *Computers, Environment and Urban Systems*)

## Caveats metodológicos

- **MAUP é o objeto de análise** — não um problema a esconder; o paper deve reportar sensibilidade a escolhas de resolução.
- **Comparabilidade temporal** dos censos 1991→2022 requer harmonização (ver Nota Técnica 44 do IPP sobre adaptação metodológica do IDS).
- **IDEB mudou metodologia** em 2007 e há revisão em 2024–2025 (GT Novo IDEB do INEP); usar apenas séries comparáveis.
- **Cobertura H3 vs administrativa**: bairros cariocas têm tamanhos muito heterogêneos; H3 res 8 (~0,7 km²) é provavelmente a granularidade adequada para bairros médios.
- **Imputação**: bairros sem escolas suficientes terão erro padrão alto; reportar sample size.

## Como rodar

```bash
# Da raiz do repo
uv pip install -e ".[viz,notebooks]"

# Atualizar manifest e baixar dados
acec manifest refresh
acec ingest download --type "Microsoft Excel"
acec ingest download --type "Feature Service"  # quando suportado

# Rodar notebooks
jupyter lab products/hex-edu/notebooks/

# App
streamlit run products/hex-edu/app/streamlit_app.py
```
