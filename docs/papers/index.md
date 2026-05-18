---
title: "Catálogo de papers — rio-edu-lab"
description: "Papers em educação aplicados ao Rio: status de replicação + cobertura no data.rio."
---

# 📚 Catálogo de papers

O laboratório opera um catálogo aberto de **papers em educação aplicados ao Rio**, cruzados com os dados do data.rio. Cada entrada indica o status de replicação no lab e a cobertura dos requisitos de dados.

**Estado atual:** 12 papers catalogados — 1 totalmente replicados, 2 em replicação parcial, 6 catalogados pendentes, 3 indisponíveis por dados.

> **Roadmap pós-v0.7:** ampliar para os 100 papers mais influentes. A v0.7 entrega o framework + 12 papers seed (3 já replicados + 5 alvo de novas replicações + 4 metodológicos).

## Replicados (operacionalizados em produtos do lab)

| Paper | Ano | Área | Brasil? | Citações | Cobertura data.rio |
|---|---|---|---|---|---|
| [Theil (1967)](theil-1967-economics.md) | 1967 | desigualdade |  | 7.659 | 2/2 |
| [Reardon (2011)](reardon-2011-whither.md) | 2011 | desigualdade |  | 1.146 | 2/2 |
| [Pereira et al. (2019)](pereira-2019-ipea.md) | 2019 | acessibilidade | 🇧🇷 | 79 | 3/4 |

## Catalogados — replicação leve planejada

| Paper | Ano | Área | Brasil? | Citações | Cobertura data.rio |
|---|---|---|---|---|---|
| [Coleman et al. (1966)](coleman-1966-eeo.md) | 1966 | sociologia educacional |  | 2.776 | 2/2 |
| [Hanushek (1986)](hanushek-1986-jel.md) | 1986 | economia da educação |  | 2.715 | 2/2 |
| [Hoxby (2000)](hoxby-2000-aer.md) | 2000 | economia da educação |  | 1.105 | 2/2 |
| [Soares & Andrade (2006)](soares-andrade-2006.md) | 2006 | sociologia educacional | 🇧🇷 | 3 | 2/3 |
| [Alves & Soares (2013)](alves-soares-2013.md) | 2013 | política educacional | 🇧🇷 | 101 | 1/2 |
| [Reardon & Owens (2014)](reardon-owens-2014.md) | 2014 | segregação escolar |  | 503 | 2/2 |

## Catalogados — dados não disponíveis no data.rio

| Paper | Ano | Área | Brasil? | Citações | Cobertura data.rio |
|---|---|---|---|---|---|
| [Becker (1964)](becker-1964-human-capital.md) | 1964 | economia da educação |  | 5.240 | 0/2 |
| [Card & Krueger (1992)](card-krueger-1992-jpe.md) | 1992 | economia da educação |  | 1.183 | 0/2 |
| [Cunha & Heckman (2007)](cunha-heckman-2007.md) | 2007 | economia da educação |  | 3.001 | 0/2 |

## Sobre a curadoria

- **Critério de inclusão:** papers seminais em educação (top-citados em economia, sociologia, política educacional) + papers brasileiros relevantes + metodológicos canônicos.
- **Fonte de citações:** [OpenAlex](https://openalex.org), snapshot na curadoria. Atualizado periodicamente por `analysis/34_fetch_openalex.py`.
- **Catálogo versionado:** edits ao YAML são auditáveis via git diff.
- **Não é ranking objetivo:** é lista justificada por curadoria.

## Reproduzir

```bash
pip install -r requirements.txt
python3 analysis/34_fetch_openalex.py     # opcional: refresh de citações
python3 analysis/31_build_paper_catalog.py
python3 analysis/32_render_papers_pages.py
```
