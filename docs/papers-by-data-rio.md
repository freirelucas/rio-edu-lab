---
title: Papers por item do data.rio
description: Link reverso auto-gerado — para cada item do manifest data.rio referenciado pelo catálogo de papers, quais papers o utilizam e que requisito atende.
---

# Papers por item do data.rio

Auto-gerado por `analysis/41_match_requirements.py` a partir de `data/papers_catalog.yml` + `data/manifest.json`. Para cada item do data.rio referenciado por algum paper do catálogo, lista quais papers o utilizam e que requisito ele atende.

**Estado atual:** 7 itens do data.rio referenciados por 15 papers no catálogo.

| Item ID | Título | Tipo | # papers | Papers (requisito atendido) |
|---|---|---|---:|---|
| `ideb-municipal-bairros` | (unknown — not in manifest) |  | 9 | Pereira et al. (2019) — _indicador de qualidade educacional_<br>Reardon (2011) — _indicador de desempenho educacional_<br>Theil (1967) — _valores positivos por unidade_<br>Soares & Andrade (2006) — _desempenho por escola_<br>Alves & Soares (2013) — _IDEB por bairro_<br>Coleman et al. (1966) — _desempenho por unidade_<br>Hanushek (1986) — _indicador de output_<br>Reardon & Owens (2014) — _indicador de matrícula_<br>Hoxby (2000) — _indicador de desempenho_ |
| `0a220ea7972d4adf85b3e63d23a4b9b1` | (unknown — not in manifest) |  | 3 | Pereira et al. (2019) — _geometria de escolas_<br>Hanushek (1986) — _indicador de input_<br>Hoxby (2000) — _indicador de oferta de escolas_ |
| `bairros-ipp` | (unknown — not in manifest) |  | 3 | Pereira et al. (2019) — _geometria de bairros_<br>Theil (1967) — _agrupamento hierárquico_<br>Coleman et al. (1966) — _agrupamento espacial_ |
| `ids-rm-2010` | (unknown — not in manifest) |  | 3 | Reardon (2011) — _indicador socioeconômico granular_<br>Soares & Andrade (2006) — _NSE por escola ou bairro_<br>Reardon & Owens (2014) — _composição SES por bairro_ |
| `498e637753bd4e0da76e90103dd21eb7` | Mapa Digital do Rio de Janeiro - Escolas Municipais e Estratégia da Saúde | Web Map | 3 | Coleman et al. (1982) — _geometria de escolas_<br>Dupriez & Dumay (2006) — _geometria de escolas_<br>Schwartz (2011) — _geometria de escolas_ |
| `fa85ddc76a524380ad7fc60e3006ee97` | Índice de Desenvolvimento Social (IDS) por Áreas de Planejamento (AP), Regiões de Planejamento (RP), Regiões Administrativas (RA), Bairros e Favelas do Município do Rio de Janeiro - 2010 | Microsoft Excel | 3 | Coleman et al. (1982) — _INSE por escola_<br>Dupriez & Dumay (2006) — _INSE por escola_<br>Schwartz (2011) — _INSE por escola_ |
| `6b375a1fcab642779398aa12108c906f` | Índice de Qualidade do Emprego Municipal  (Março/2026) | PDF | 3 | Coleman et al. (1982) — _IDEB por bairro_<br>Dupriez & Dumay (2006) — _IDEB por bairro_<br>Schwartz (2011) — _IDEB por bairro_ |

## Como reproduzir

```bash
python3 analysis/41_match_requirements.py
```
