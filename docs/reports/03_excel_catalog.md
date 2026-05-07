# 03 — Catálogo empírico dos Excels

Gerado a partir dos 127 arquivos do tipo `Microsoft Excel` baixados em `data/raw/excel/`. Diferente dos relatórios anteriores (que se apoiam em metadados do manifest e regex sobre títulos), este relatório lê o conteúdo real de cada arquivo via `xlrd`/`openpyxl`. Onde houver discrepância com as heurísticas anteriores, ela é apontada explicitamente.

## Visão geral

| Métrica | Valor |
| :--- | :--- |
| Arquivos | 127 |
| Sheets totais | 630 |
| Tamanho total em disco | 12.3 MiB (12,858,912 B) |
| Tamanho p50 / p90 / p99 | 46 KiB / 268 KiB / 829 KiB |
| Janela temporal global | 1991–2024 |

## Achado #1 — quase tudo é `.xls` legacy, não `.xlsx`

Apesar do `type: Microsoft Excel` no manifest e do `Content-Type` `...spreadsheetml.sheet` reportado pela API (que sugere XLSX), o conteúdo real é majoritariamente o **formato binário pré-2007** (Composite Document, magic bytes `D0 CF 11 E0`):

| Formato real (magic bytes) | Arquivos | % |
| :--- | ---: | ---: |
| xls | 126 | 99.2% |
| xlsx | 1 | 0.8% |

Implicação prática: `pandas.read_excel(..., engine='openpyxl')` falha em 126 dos 127 arquivos. É preciso usar `xlrd>=2.0` (que lê `.xls`) ou converter previamente. O probe da API (Relatório 02) reporta MIME XLSX porque o portal anota o type genericamente, sem sniffing real.

## Achado #2 — sizes empíricos: 12.3 MiB total, não ~100 MiB

O total real é **12.3 MiB** (média ~99 KiB/arquivo). A estimativa anterior neste lab (Relatório 02) era ~100 MiB, baseada em **uma única amostra** (o IPS, que é justamente o maior arquivo do corpus). É um caso clássico de extrapolar de outlier — sirva de aviso.


Distribuição de tamanho (bytes): mediana **47,104**, p90 **274,944**, p99 **848,416**, máximo **1,772,032**.

## Estrutura: sheets por arquivo

| Sheets/arquivo | Arquivos |
| ---: | ---: |
| 1 | 44 |
| 2 | 19 |
| 3 | 15 |
| 4 | 7 |
| 5 | 13 |
| 6 | 5 |
| 7 | 4 |
| 8 | 4 |
| 13 | 1 |
| 14 | 1 |
| 15 | 4 |
| 17 | 1 |
| 24 | 9 |

44 arquivos (35%) têm sheet única; outros 9 têm 24 sheets cada — padrão de 'um sheet por ano' (provavelmente IDS / IPS por ano).

## Cobertura temporal (lida do conteúdo)

A detecção considera anos 4-dígitos em strings ou em células numéricas **dentro das primeiras 4 linhas** de cada sheet (cabeçalhos). Valores numéricos no corpo da tabela em range 1990–2030 são ignorados, porque há contagens (ex.: número de professores) que cairiam no range — corrigido após detectar células com `2070`, `2038` em meio a dados.

| Span | Arquivos |
| :--- | ---: |
| 0 anos (snapshot único) | 10 |
| 1–5 anos | 17 |
| 6–10 anos | 37 |
| 11–20 anos | 33 |
| 21+ anos | 30 |

## Granularidade espacial (heurística por unicos da 1ª coluna)

O número de valores únicos na primeira coluna (descontadas as 3 primeiras linhas presumidas como cabeçalho) é cruzado com as quantidades conhecidas de unidades administrativas do Rio: **5 APs**, **11 CREs**, **33 RAs**, ~**163 bairros**, milhares de escolas. É heurístico — pode haver sheet com múltiplas escalas misturadas — mas é a primeira aproximação empírica.

| Bucket | Arquivos |
| :--- | ---: |
| 13–30 (compatível com RP / parcial RA) | 66 |
| 7–12 (compatível com 11 CREs) | 26 |
| 31–50 (compatível com 33 RAs) | 16 |
| 51–200 (compatível com ~163 bairros) | 13 |
| 200+ (escola ou linha-por-observação) | 3 |
| 4–6 (compatível com 5 APs) | 2 |
| 1–3 (totais agregados) | 1 |

## Top 10 por visualizações (cruzando com dados empíricos)

| Views | Format | Sheets | Linhas | Anos | Unq col 0 | Título |
| ---: | :--- | ---: | ---: | :--- | ---: | :--- |
| 1,403 | xlsx | 13 | 1495 | 2010–2024 | 35 | Base de dados do Índice de Progresso Social - IPS por Regiõe |
| 635 | xls | 6 | 532 | 1991–2010 | 131 | Taxa de analfabetos por faixas etárias, por Bairros ou grupo |
| 601 | xls | 6 | 1282 | 2005–2021 | 112 | IDEB das séries iniciais e finais segundo as Áreas de Planej |
| 551 | xls | 3 | 156 | 2007–2022 | 24 | Ensino Fundamental e Ensino Médio - Número médio de alunos p |
| 503 | xls | 4 | 1030 | 2010–2013 | 218 | Unidades escolares da rede municipal de educação, por tipo,  |
| 435 | xls | 4 | 1029 | 2010–2013 | 184 | Matrículas na rede municipal de educação, por níveis de ensi |
| 422 | xls | 5 | 129 | 2000–2022 | 12 | Ensino Médio - Número de escolas e dependências físicas exis |
| 387 | xls | 1 | 262 | 2010–2010 | 218 | Pessoas analfabetas por grupos de idade, segundo as Áreas de |
| 385 | xls | 5 | 154 | 2000–2022 | 15 | Ensino Fundamental - Número de escolas e dependências física |
| 372 | xls | 8 | 252 | 2000–2022 | 14 | Número de professores em exercício, por organização acadêmic |

## Shortlist preliminar para HEX-EDU

Critério: span ≥ 5 anos **e** unicos da coluna 0 ≥ 30 (proxy para granularidade RA-ou-mais-fina). Ordenado por span (decrescente), depois views. Esta é a porta de entrada da próxima fase, **não** uma escolha metodológica — toda candidata aqui ainda precisa de auditoria manual de cabeçalhos antes de virar input para Theil.

| Anos | Unq col 0 | Sheets | Views | Título | ID |
| :--- | ---: | ---: | ---: | :--- | :--- |
| 2000–2024 | 50 | 24 | 110 | Ensino de pós-graduação: número de programas de pós-graduaçã | `1f908c6de87f42e7b4ae513788e0ccce` |
| 1991–2010 | 131 | 6 | 635 | Taxa de analfabetos por faixas etárias, por Bairros ou grupo | `fb6ece5b0fc14c18839e9f510fcae09b` |
| 1991–2010 | 131 | 7 | 189 | Percentagem de crianças por faixa etária: matriculados em cr | `b7b66567492942adb5b49085a93cffb8` |
| 2005–2021 | 112 | 6 | 601 | IDEB das séries iniciais e finais segundo as Áreas de Planej | `9fd1a8cc207a48c5bda7131e4e74b1ca` |
| 2001–2017 | 49 | 6 | 69 | Número e valor do Investimentos realizados pelo CNPQ em bols | `6bba93cdd9014dac9cdc7c36d226cf15` |
| 1992–2007 | 40 | 2 | 139 | Educação Infantil e Ensino Fundamental: matrículas inicial e | `6574a63ac2ce4fb39ba528a8c4bdec15` |
| 2010–2024 | 35 | 13 | 1,403 | Base de dados do Índice de Progresso Social - IPS por Regiõe | `918dd39478594792a9cfa7080b84c0b5` |
| 2001–2015 | 102 | 1 | 90 | Ensino de pós-graduação: investimentos realizados pelo CNPQ  | `169c46ae23b04dc8ad494e4fe6c04eb5` |
| 2001–2015 | 335 | 3 | 62 | Investimentos realizados pelo CNPQ em bolsas e no fomento à  | `4f7b7e9578e14e5c8d865c4e5c2074ba` |
| 1991–2003 | 129 | 5 | 354 | Indicadores de Educação: atendimento educacional ao adulto,  | `c9e9bae1f47c46a8a0e17e56e774bede` |
| 1991–2003 | 129 | 5 | 188 | Indicadores de Educação: atendimento educacional ao adolesce | `1e5dbe226f594be292bf490ead9d2666` |
| 1991–2003 | 129 | 5 | 102 | Indicadores de Educação: analfabetismo funcional, percentual | `dbed8b55cf28474296457ab9989f91c5` |
| 2000–2010 | 36 | 2 | 196 | Número de estudantes da rede pública por nível de ensino, se | `6b99c568d38646bb97dcf2751c501e7f` |
| 2000–2010 | 37 | 2 | 120 | Número e proporção das pessoas de 0 a 4 anos que frequentam  | `0a5a97fed2e540fd8320c05e70867491` |
| 2000–2010 | 36 | 2 | 116 | Número e proporção de estudantes de 7 a 14 anos, da rede púb | `d155c513f84944a8b3bf5df867719faf` |
| 2000–2010 | 36 | 2 | 104 | Número de estudante por nível de ensino, segundo as Regiões  | `8e720d57e9544794ba66aba6afac5980` |
| 2000–2010 | 36 | 2 | 101 | Número e proporção de não estudantes entre 7 e 14 anos por i | `c5f0cf8ed56c447fa58af9265833e25a` |
| 2000–2010 | 36 | 2 | 69 | Número e proporção das pessoas de 5 anos ou mais de idade qu | `5e7a88898605441a8f7818602e02ecc7` |
| 2002–2009 | 32 | 8 | 74 | Educação Infantil e Ensino Fundamental: unidades escolares d | `1dc77ea3ee9b4df1abe19c3a8dcbb1fd` |

## Discrepâncias com heurísticas anteriores

- **Tamanho total**: heurística (Relatório 02) projetava ~100 MiB; real = **12.3 MiB**. Erro de ~8×, causado por extrapolação a partir de um outlier.
- **Formato**: `Content-Type` HTTP afirma XLSX; conteúdo real é **126 XLS legacy + 1 XLSX**. O portal não faz sniffing.
- **Anos detectados**: 127/127 têm cobertura temporal extraível do conteúdo. Antes da correção, 5 arquivos apareciam com `years_max=2030` porque células numéricas como `2030`, `2038`, `2070` (contagens de professores/alunos) eram interpretadas como anos. Detecção numérica restrita a cabeçalhos resolveu.
- **Heurística temática (Relatório 01)**: ainda é regex sobre `title` + `snippet`. Vale auditar contra os cabeçalhos reais agora disponíveis em `data/processed/excel_sheets.csv`.

## Reprodutibilidade

```bash
pip install openpyxl xlrd>=2.0
python3 analysis/03_download_excels.py    # ~92 s, 12.3 MiB
python3 analysis/04_excel_catalog.py      # <1 s
python3 analysis/05_report_excel_catalog.py
```

Os binários em `data/raw/excel/` ficam gitignored (12.3 MiB cabe no repo tranquilamente, mas seria poluição — o catálogo derivado em `data/processed/` já condensa o que importa, com 2 CSVs leves).

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [04 — Auditoria do shortlist](04_shortlist_audit.md)
    - [Glossário](../glossario.md)
