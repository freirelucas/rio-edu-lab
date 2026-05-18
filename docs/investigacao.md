---
title: Investigação técnica — rio-edu-lab
description: Lista cronológica de relatórios. Para quem busca um relatório específico, ou quer seguir o fio metodológico do começo.
---

# Investigação técnica

Os relatórios são publicados em ordem cronológica de execução. Cada um introduz uma decisão metodológica ou expõe um achado intermediário. Para a narrativa principal e os produtos finais, vá para [Tour](tour.md) ou [Produtos](produtos/index.md). Esta página é a sala de máquinas — útil para auditar, replicar ou citar relatórios específicos.

## Inventário do acervo (01–05)

Mapeamento empírico do Grupo Educação do data.rio: 186 itens, 127 Excels, 35 PDFs. Onde estão, o que tem dentro, o que presta para análise.

| # | Relatório | Em uma frase |
|---|---|---|
| 01 | [EDA do manifest](reports/01_manifest_eda.md) | 186 itens, 127 Excels, distribuição por tipo / ano / tag. |
| 02 | [Probe da API](reports/02_ingestion_probe.md) | 5 endpoints testados; 170 itens "sem URL" no manifest **não** estão quebrados. |
| 03 | [Catálogo dos Excels](reports/03_excel_catalog.md) | 12.3 MiB total, 126/127 são `.xls` legacy (não xlsx); 1991–2024. |
| 04 | [Auditoria do shortlist](reports/04_shortlist_audit.md) | 8 candidatos USE / 3 NEEDS_CLEANING / 1 SKIP. |
| 05 | [Corpus dos PDFs](reports/05_pdf_corpus.md) | 35 publicações IPP; 25 com texto extraível, 10 escaneadas. |

## HEX-EDU profundo (06–10)

Theil base, robustez, mapa estático, mapa interativo, replicação metodológica.

| # | Relatório | Em uma frase |
|---|---|---|
| 06 | [Theil sobre IDEB por bairro](reports/06_theil_ideb.md) | 60–70% within-RA em todos os 9 anos; achado-base do HEX-EDU. |
| 06b | [Theil ponderado por matrícula](reports/06b_theil_weighted.md) | Robustez: ponderação reduz T_total ~44%, share_within continua &gt; 50%. |
| 07 | [HEX-EDU estático](reports/07_hex_edu_static.md) | Painel 4 anos × 2 colunas (RA vs H3); argumento visual. |
| 08 | [HEX-EDU interativo](reports/08_hex_edu_interactive.md) | Mapa Folium com seletor de ano. Versão pública: [Mapa](mapa.md). |
| 09 | [IDEB séries finais (9º)](reports/09_anos_finais.md) | Mesma metodologia em ANOS_FINAIS — within-share 70%. |
| 10 | [Replicação metodológica](reports/10_method_replication.md) | Theil sobre Aprovação, SAEB, IDEB separadamente — 64–70% within. |

## Outros produtos do MVP-1 (11–13)

| # | Relatório | Em uma frase |
|---|---|---|
| 11 | [THESHA-Rio (3-level)](reports/11_thesha_rio.md) | Decomposição AP / RA-em-AP / bairro-em-RA = 8% / 26% / 67%. |
| 12 | [FUN-Rio (pseudocoortes)](reports/12_fun_rio.md) | 768 transições 5º→9º; 87% pioram, slope −0.53 vs IDEB inicial. |
| 13 | [PM-12 (lei de escala)](reports/13_pm_12.md) | β = 0.77 sublinear (R² 0.80); SAMI mapeia déficit infra-estrutural. |

## HEX-EDU v0.6 acessibilidade (14)

| # | Relatório | Em uma frase |
|---|---|---|
| 14 | [Acessibilidade Pereira-style](reports/14_acessibilidade.md) | Acesso ponderado por IDEB sobre H3 res 8; AP 3 lidera (113), AP 4 último (29). |

## VULN-EDU (15)

| # | Relatório | Em uma frase |
|---|---|---|
| 15 | [IDS × IDEB por bairro](reports/15_vuln_edu.md) | Reardon (2011) intra-Rio; gradiente +0.40, R²=0.16; 39% dos bairros em quadrantes não-concordantes. |

## Recursos auxiliares

- [API do data.rio](data-rio-api.md) — endpoints validados pelo probe.
- [Glossário](glossario.md) — IDEB, Theil, AP, RA, bairro, H3, SAMI, etc.
- [Reproduzir](reproduzir.md) — quickstart técnico.

## Ler na ordem cronológica

Se quiser seguir como o lab foi se construindo: 01 → 02 → 03 → 04 → 05 → 06 → 06b → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15. Cada relatório foi mergeado em PR separado, então o histórico de commits também conta a história.
