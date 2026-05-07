# 04 — Auditoria do shortlist preliminar

Auditoria manual via inspeção dos primeiros 12 × 8 cells de cada sheet primária. Critério para o shortlist: span ≥ 5 anos e ≥ 30 valores únicos na coluna 0 (Relatório 03). Aqui faço o passo seguinte: olhar o conteúdo em si para emitir um veredito conservador (`USE` / `NEEDS_CLEANING` / `SKIP`) sobre se vale levar adiante para o produto HEX-EDU.

## Resumo

Ordenado pela ordem auditada (span desc, views desc).

| Veredito | Anos | Unq col 0 | Views | Título | ID |
| --- | --- | --- | --- | --- | --- |
| USE | 2000–2024 | 50 | 110 | Ensino de pós-graduação: número de programas de pós-gra | `1f908c6d…` |
| USE | 1991–2010 | 131 | 635 | Taxa de analfabetos por faixas etárias, por Bairros ou  | `fb6ece5b…` |
| USE | 1991–2010 | 131 | 189 | Percentagem de crianças por faixa etária: matriculados  | `b7b66567…` |
| USE | 2005–2021 | 112 | 601 | IDEB das séries iniciais e finais segundo as Áreas de P | `9fd1a8cc…` |
| SKIP | 2001–2017 | 49 | 69 | Número e valor do Investimentos realizados pelo CNPQ em | `6bba93cd…` |
| NEEDS_CLEANING | 1992–2007 | 40 | 139 | Educação Infantil e Ensino Fundamental: matrículas inic | `6574a63a…` |
| USE | 2010–2024 | 35 | 1403 | Base de dados do Índice de Progresso Social - IPS por R | `918dd394…` |
| NEEDS_CLEANING | 2001–2015 | 102 | 90 | Ensino de pós-graduação: investimentos realizados pelo  | `169c46ae…` |
| NEEDS_CLEANING | 2001–2015 | 335 | 62 | Investimentos realizados pelo CNPQ em bolsas e no fomen | `4f7b7e95…` |
| USE | 1991–2003 | 129 | 354 | Indicadores de Educação: atendimento educacional ao adu | `c9e9bae1…` |
| USE | 1991–2003 | 129 | 188 | Indicadores de Educação: atendimento educacional ao ado | `1e5dbe22…` |
| USE | 1991–2003 | 129 | 102 | Indicadores de Educação: analfabetismo funcional, perce | `dbed8b55…` |

Tudo que estiver marcado `NEEDS_CLEANING` precisa de investigação manual antes de virar input para Theil. `USE` significa que estrutura mínima existe — não que os dados estejam validados.

## USE — Ensino de pós-graduação: número de programas de pós-graduação, por nível, agrupados por Instituição no Município do Rio de Janeiro entre 2000-2022

- ID: `1f908c6de87f42e7b4ae513788e0ccce` · format: `xls` · sheets: 24 · anos: 2000–2024 · views: 110

- Veredito: **USE** — sheet '2000' header @ linha 5; granularidade: RA / bairro (nomes geográficos do Rio); 8 colunas no header
- Granularidade real (col 0 abaixo do header): RA / bairro (nomes geográficos do Rio)

### Sheet de dados — `2000` (34 × 8, header em linha 5)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA RIO | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 1726 - Ensino de… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Instituição | Total | Mestrado | Doutorado | Mestrado/ Doutorado | Mestrado Profissional | Mestrado/ Doutorado/ M.… | Mestrado/ Mestrado Prof… |
| · | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Total | 167 | 54 | 1 | 108 | 1 | 2 | 1 |
| Centro Brasileiro de Pe… | 1 | - | - | - | - | 1 | - |
| Centro Federal de Educa… | 1 | 1 | - | - | - | - | - |

_Outras sheets: `2001`, `2002`, `2003`, `2004`, `2005`, `2006`…_

## USE — Taxa de analfabetos por faixas etárias, por Bairros ou grupos de Bairros no Município do Rio de Janeiro em 1991/2000/2010

- ID: `fb6ece5b0fc14c18839e9f510fcae09b` · format: `xls` · sheets: 6 · anos: 1991–2010 · views: 635

- Veredito: **USE** — sheet 'RA_1991' header @ linha 5; granularidade: RA / bairro (nomes geográficos do Rio); 7 colunas no header
- Granularidade real (col 0 abaixo do header): RA / bairro (nomes geográficos do Rio)

### Sheet de dados — `RA_1991` (46 × 8, header em linha 5)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 535 - Indicadore… | · | · | · | · | · | · | · |
| Regiões Administrativas… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Regiões Administrativas | · | Percentual de crianças … | Percentual de crianças … | Percentual de adolescen… | Percentual de jovens de… | Percentual de pessoas d… | Percentual de pessoas d… |
| · | · | · | · | · | · | · | · |
| · | Rio de Janeiro | 8.272665944610797 | 3.3176111807839055 | 2.5059518986154328 | 3.0795960542508816 | 6.099643296141806 | 6.573638081891472 |
| 1 | Portuária | 14.654414190930293 | 5.86345728097576 | 5.264685220856724 | 5.544865100403462 | 10.77373996019354 | 12.433770345576903 |
| 2 | Centro | 5.680379916250626 | 3.1032469094109225 | 3.425893995321426 | 1.813617924201672 | 3.0732354355307265 | 3.2612393029876516 |
| 3 | Rio Comprido | 8.089992376857275 | 3.598548046370584 | 2.179198649478131 | 3.298313626597403 | 6.191360827517959 | 7.0556431723421795 |
| 4 | Botafogo | 3.216316763061608 | 1.5237298875802274 | 1.275437815210751 | 3.0416443886119535 | 2.5291678794060024 | 2.5203712587161107 |

_Outras sheets: `RA_2000`, `RA_2010`, `Bairros_1991`, `Bairros_2000`, `Bairros_2010`_

## USE — Percentagem de crianças por faixa etária: matriculados em creches/escolas; com mais de um ano de atraso escolar; matriculados com acesso ao ensino fundamental e frequência escolar no Município do Rio de Janeiro em 1991/2000/2010

- ID: `b7b66567492942adb5b49085a93cffb8` · format: `xls` · sheets: 7 · anos: 1991–2010 · views: 189

- Veredito: **USE** — sheet 'RA_1991' header @ linha 7; granularidade: RA / bairro (nomes geográficos do Rio); 7 colunas no header
- Granularidade real (col 0 abaixo do header): RA / bairro (nomes geográficos do Rio)

### Sheet de dados — `RA_1991` (48 × 11, header em linha 7)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela - 537 - Educação… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Regiões Administrativas | · | Percentual de crianças … | · | · | · | Percentual de crianças … | · |
| · | · | de 4 e 5 anos* | de 5 a 6 anos | de 7 a 14 anos | de 10 a 14 anos | de 7 a 14 anos | de 10 a 14 anos |
| · | · | · | · | · | · | · | · |
| · | Riode Janeiro | - | 59.45884043275821 | 91.94108994841326 | 92.6698043761078 | 28.895039345945438 | 41.60249337346198 |
| 1 | Portuária | - | 54.780904951018236 | 91.74793453751954 | 91.82578865526905 | 35.27750484879644 | 49.25751519972834 |
| 2 | Centro | - | 68.65117831060476 | 94.25765591449286 | 93.38417252247372 | 25.06503026988318 | 38.45797499927162 |
| 3 | Rio Comprido | - | 56.63951111542039 | 89.68032922560147 | 90.8748042201551 | 30.293356364285344 | 43.04076130507447 |
| 4 | Botafogo | - | 73.29766859971033 | 92.686008192367 | 92.8318446300906 | 15.81231724622589 | 22.197824128933675 |

_Outras sheets: `Definições`, `RA_2000`, `RA_2010 `, `Bairros_1991`, `Bairros_2000`, `Bairros_2010`_

## USE — IDEB das séries iniciais e finais segundo as Áreas de Planejamento (AP), Regiões de Planejamento (RP), Regiões Administrativas (RA) e Bairros do Município do Rio de Janeiro em 2007/2009/2011/2013/2015/2017/2019/2021/2023

- ID: `9fd1a8cc207a48c5bda7131e4e74b1ca` · format: `xls` · sheets: 6 · anos: 2005–2021 · views: 601

- Veredito: **USE** — sheet 'ANOS_INICIAIS' header @ linha 6; granularidade: RA / bairro (nomes geográficos do Rio); 7 colunas no header
- Granularidade real (col 0 abaixo do header): RA / bairro (nomes geográficos do Rio)

### Sheet de dados — `ANOS_INICIAIS` (269 × 37, header em linha 6)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA.RIO | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 2640 - Índice de… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Áreas de Planejamento, … | Escolas Participantes | · | · | · | · | · | · |
| · | 2007 | 2009 | 2011 | 2013 | 2015 | 2017 | 2019 |
| · | · | · | · | · | · | · | · |
| Total | 802 | 789 | 832 | 738 | 695 | 673 | 665 |
| Área de Planejamento 1 | 38 | 37 | 39 | 33 | 29 | 30 | 29 |
| · | · | · | · | · | · | · | · |
| Região de Planejamento … | 38 | 37 | 39 | 33 | 29 | 30 | 29 |

_Outras sheets: `definições`, `ANOS_FINAIS`, `metas IDEB`, `SAEB e Prova Brasil questões`, `ESRI_MAPINFO_SHEET`_

## SKIP — Número e valor do Investimentos realizados pelo CNPQ em bolsas e no fomento à pesquisa segundo a modalidade no Estado do Rio de Janeiro entre 2001-2015

- ID: `6bba93cdd9014dac9cdc7c36d226cf15` · format: `xls` · sheets: 6 · anos: 2001–2017 · views: 69

- Veredito: **SKIP** — granularidade: (totais / agregado)
- Granularidade real (col 0 abaixo do header): (totais / agregado)

### Sheet de dados — `País_1` (58 × 13, header em linha 6)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 2048 - Ensino de… | · | · | · | · | · | · | · |
| por modalidade - Estado… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Modalidade | 2001 - Bolsa-ano (1) | · | 2002 - Bolsa-ano (1) | · | 2003 - Bolsa-ano (1) | · | 2004 - Bolsa-ano (1) |
| · | Qtd | R$ mil | Qtd | R$ mil | Qtd | R$ mil | Qtd |
| · | · | · | · | · | · | · | · |
| Total | 7967 | 65028 | 8067 | 66152 | 7908 | 75728 | 8383 |
| Apoio à Difusão do Conh… | - | - | - | - | - | - | - |
| Apoio Técnico à Pesquisa | 405 | 1919 | 427 | 2007 | 415 | 1974 | 434 |
| Apoio Técnico em Extens… | - | - | - | - | - | - | - |

_Outras sheets: `pais_2`, `Exterior_1`, `Exterior_2`, `Fomento_1`, `Fomento_2`_

## NEEDS_CLEANING — Educação Infantil e Ensino Fundamental: matrículas inicial e final, por ano, segundo a correspondência entre séries e segmentos na rede pública municipal do Rio de Janeiro, entre 1992-2007

- ID: `6574a63ac2ce4fb39ba528a8c4bdec15` · format: `xls` · sheets: 2 · anos: 1992–2007 · views: 139

- Veredito: **NEEDS_CLEANING** — sheet '1992-2004' header @ linha 7; granularidade não reconhecida ((rótulos heterogêneos — auditar manualmente))
- Granularidade real (col 0 abaixo do header): (rótulos heterogêneos — auditar manualmente)

### Sheet de dados — `1992-2004` (102 × 13, header em linha 7)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 978 | Educação infantil/ensin… | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Séries / Ciclo | 1992 | · | 1993 | · | 1994 | · | 1995 |
| · | inicial | final | inicial | final | inicial | final | inicial |
| · | · | · | · | · | · | · | · |
| Total | 648853 | 603808 | 673590 | 625265 | 689179 | 629477 | 685093 |
| · | · | · | · | · | · | · | · |
| Educação infantil (crec… | - | - | - | - | - | - | - |
| Educação infantil (4 e … | 20068 | 19153 | 21311 | 21468 | 23575 | 24239 | 29392 |
| Classe de alfabetização… | 54832 | 52102 | 54263 | 52065 | 56898 | 53774 | 57437 |

_Outras sheets: `2005-2007`_

## USE — Base de dados do Índice de Progresso Social - IPS por Regiões Administrativas (RA) - Município do Rio de Janeiro - 2016/2018/2020/2022/2024

- ID: `918dd39478594792a9cfa7080b84c0b5` · format: `xlsx` · sheets: 13 · anos: 2010–2024 · views: 1403

- Veredito: **USE** — sheet 'Dimensões e Componentes 2016' header @ linha 6; granularidade: RA (numeração romana — XX RAs do Rio); 6 colunas no header
- Granularidade real (col 0 abaixo do header): RA (numeração romana — XX RAs do Rio)

### Sheet de dados — `Dimensões e Componentes 2016` (45 × 18, header em linha 6)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA.RIO | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela - Índices das di… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Regiões Administrativas | Índice de Progresso Soc… | Necessidades Humanas Bá… | · | · | · | · | Fundamentos do Bem-Estar |
| · | · | · | · | · | · | · | · |
| · | · | Nota da dimensão | Nutrição e cuidados méd… | Água e saneamento | Moradia | Segurança pessoal | Nota da dimensão |
| · | · | · | · | · | · | · | · |
| RIO DE JANEIRO | 60.77 | 75.84 | 70.19 | 83.68 | 78.16 | 71.34 | 53.28 |
| I PORTUARIA | 45.33 | 59.1 | 87.63 | 80.8 | 67.97 | 0 | 41.67 |
| II CENTRO | 57.75 | 62.43 | 59.38 | 74.18 | 91.85 | 24.31 | 52.41 |
| III RIO COMPRIDO | 52.43 | 58.97 | 61.22 | 84.36 | 64.78 | 25.52 | 47.19 |

_Outras sheets: `Metodologia`, `Indicadores - 2016`, `Dimensões e Componentes 2018`, `Indicadores - 2018`, `Dimensões e Componentes 2020`, `Indicadores - 2020`…_

## NEEDS_CLEANING — Ensino de pós-graduação: investimentos realizados pelo CNPQ em bolsas e no fomento à pesquisa, segundo a área de conhecimento, no Estado do Rio de Janeiro entre 2001-2015

- ID: `169c46ae23b04dc8ad494e4fe6c04eb5` · format: `xls` · sheets: 1 · anos: 2001–2015 · views: 90

- Veredito: **NEEDS_CLEANING** — sheet 'T 1688' header @ linha 7; granularidade não reconhecida ((rótulos heterogêneos — auditar manualmente))
- Granularidade real (col 0 abaixo do header): (rótulos heterogêneos — auditar manualmente)

### Sheet de dados — `T 1688` (135 × 46, header em linha 7)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 1688 - Ensino de… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Área do conhecimento | Bolsa no País (1) | · | · | · | · | · | · |
| · | 2001 | 2002 | 2003 | 2004 | 2005 | 2006 | 2007 |
| · | · | · | · | · | · | · | · |
| Total | 65026.8 | 66152.32 | 75727.77 | 95145.43 | 100941.18 | 110430.95999999998 | 117447.74837000004 |
| Administração | 1156.66 | 1122.69 | 772.49 | 720.36 | 873.41 | 933.72 | 977.09531 |
| Administração Hospitalar | - | - | - | - | - | - | - |
| Agronomia | 1607.98 | 1030.27 | 1022.29 | 1175.91 | 1301.86 | 1334.86 | 1583.63143 |
| Antropologia | 1075.19 | 1195.33 | 1460.82 | 1757.96 | 1837.08 | 2008.61 | 2188.36249 |

## NEEDS_CLEANING — Investimentos realizados pelo CNPQ em bolsas e no fomento à pesquisa, segundo a Instituição no Estado do Rio de Janeiro, entre 2001-2015

- ID: `4f7b7e9578e14e5c8d865c4e5c2074ba` · format: `xls` · sheets: 3 · anos: 2001–2015 · views: 62

- Veredito: **NEEDS_CLEANING** — sheet '2001-2005' header @ linha 7; granularidade não reconhecida ((rótulos heterogêneos — auditar manualmente))
- Granularidade real (col 0 abaixo do header): (rótulos heterogêneos — auditar manualmente)

### Sheet de dados — `2001-2005` (374 × 16, header em linha 7)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 2049 - Ensino de… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Instituição | Bolsa no País | · | · | · | · | Bolsa no Exterior | · |
| · | 2001 | 2002 | 2003 | 2004 | 2005 | 2001 | 2002 |
| · | · | · | · | · | · | · | · |
| Total | 65026.8 | 66152.34 | 75708.72 | 95104.4 | 100940.79 | 7629.719999999999 | 8161.62 |
| Academia Brasileira de … | - | - | - | - | - | - | - |
| Acquanature Alimentos | - | - | - | - | - | - | - |
| Ambidados Consultoria e… | - | - | - | - | - | - | - |
| Ambio Participações | - | - | - | - | - | - | - |

_Outras sheets: `2006-2012`, `2013 -2015`_

## USE — Indicadores de Educação: atendimento educacional ao adulto, nível de escolaridade de pessoas de 25 anos e mais, por Bairros ou Grupos de Bairros, em 1991/2000

- ID: `c9e9bae1f47c46a8a0e17e56e774bede` · format: `xls` · sheets: 5 · anos: 1991–2003 · views: 354

- Veredito: **USE** — sheet 'RA_1991' header @ linha 7; granularidade: RA / bairro (nomes geográficos do Rio); 7 colunas no header
- Granularidade real (col 0 abaixo do header): RA / bairro (nomes geográficos do Rio)

### Sheet de dados — `RA_1991` (44 × 7, header em linha 7)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 |
| --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados       … | · | · | · | · | · | · |
| Tabela 534 - Indicadore… | · | · | · | · | · | · |
| · | · | · | · | · | · | · |
| · | · | · | · | · | · | · |
| Regiões Administrativas | · | Média de anos de estudo… | Percentual de pessoas d… | Percentual de pessoas d… | Percentual de pessoas d… | Percentual de pessoas d… |
| · | · | · | · | · | · | · |
| · | Rio de Janeiro | 7.726470326012904 | 45.963696990256594 | 18.349576020712217 | 1.6969897451243376 | 7.0305351340691 |
| 1 | Portuária | 5.639090224134121 | 64.32172619322772 | 5.699788864223083 | 0.5541252410141606 | 1.3233925719763955 |
| 2 | Centro | 8.25401607966733 | 38.781645364434766 | 18.014140130370414 | 2.106784204733563 | 7.077484794325699 |
| 3 | Rio Comprido | 7.438166191089193 | 48.72168152707509 | 16.638482509580033 | 1.8123280500814767 | 5.359276588295958 |
| 4 | Botafogo | 10.751515127264064 | 22.915947071443952 | 43.61344805925607 | 3.3474458299553103 | 21.43528074531208 |
| 5 | Copacabana | 10.745648750744003 | 21.23847155645958 | 41.58647966991039 | 2.584781533151538 | 19.608082582953777 |

_Outras sheets: `Definições`, `RA_2000`, `Bairros_1991`, `Bairros_2000`_

## USE — Indicadores de Educação: atendimento educacional ao adolescente e jovem, percentagem de adolescentes e jovens por nível educacional e frequência escolar, por Bairros ou grupos de Bairros, incluindo definições, em 1991/2000

- ID: `1e5dbe226f594be292bf490ead9d2666` · format: `xls` · sheets: 5 · anos: 1991–2003 · views: 188

- Veredito: **USE** — sheet 'RA_1991' header @ linha 7; granularidade: RA / bairro (nomes geográficos do Rio); 8 colunas no header
- Granularidade real (col 0 abaixo do header): RA / bairro (nomes geográficos do Rio)

### Sheet de dados — `RA_1991` (44 × 14, header em linha 7)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 | c7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Tabela 533 - Indicadore… | · | · | · | · | · | · | · |
| · | · | · | · | · | · | · | · |
| Regiões Administrativas | · | Percentual de adolescen… | Percentual de adolescen… | Percentual de adolescen… | Percentual de adolescen… | Percentual de pessoas n… | Percentual de jovens de… |
| · | · | · | · | · | · | · | · |
| · | Rio de Janeiro | 73.14198254265023 | 61.65802585462147 | 31.014993171557535 | 34.11837685190336 | 65.89268128473115 | 35.92254290011096 |
| 1 | Portuária | 63.78157717644438 | 73.10963799706215 | 20.27107360923158 | 21.098228599497492 | 52.086935058945805 | 45.25693145193811 |
| 2 | Centro | 65.3041980165365 | 58.320363903046015 | 28.600323372181645 | 31.877023754512756 | 105.35837442876317 | 29.72041333087993 |
| 3 | Rio Comprido | 74.74381541755054 | 63.19819139431067 | 29.63608618291616 | 31.60649202201542 | 71.6991766968996 | 42.00941720203083 |
| 4 | Botafogo | 82.30942803016423 | 37.98263928330737 | 54.06259711032927 | 55.54300103395137 | 95.5775203390085 | 21.558400429559335 |
| 5 | Copacabana | 77.9020432650698 | 40.080495408831666 | 48.21112634711994 | 51.26626240073929 | 88.80302509121863 | 21.75201322997287 |

_Outras sheets: `Definições`, `RA_2000`, `Bairros_1991`, `Bairros_2000`_

## USE — Indicadores de Educação: analfabetismo funcional, percentual de analfabetos funcionais por faixas etárias, segundo as regiões administrativas em 1991/2000

- ID: `dbed8b55cf28474296457ab9989f91c5` · format: `xls` · sheets: 5 · anos: 1991–2003 · views: 102

- Veredito: **USE** — sheet 'RA_1991' header @ linha 7; granularidade: RA / bairro (nomes geográficos do Rio); 7 colunas no header
- Granularidade real (col 0 abaixo do header): RA / bairro (nomes geográficos do Rio)

### Sheet de dados — `RA_1991` (44 × 7, header em linha 7)

| c0 | c1 | c2 | c3 | c4 | c5 | c6 |
| --- | --- | --- | --- | --- | --- | --- |
| Armazém de Dados | · | · | · | · | · | · |
| · | · | · | · | · | · | · |
| Tabela 536 - Indicadore… | · | · | · | · | · | · |
| · | · | · | · | · | · | · |
| Regiões Administrativas | · | Percentual de crianças … | Percentual de adolescen… | Percentual de jovens de… | Percentual de pessoas d… | Percentual de pessoas d… |
| · | · | · | · | · | · | · |
| · | Rio de Janeiro | 50.40365428523519 | 13.142887614660314 | 10.93853669617789 | 16.33907787849128 | 17.71767175194201 |
| 1 | Portuária | 53.86396333790163 | 14.888055376140061 | 14.799036078602281 | 24.858303811055496 | 27.99550599244552 |
| 2 | Centro | 46.52589473169454 | 12.35231400774371 | 10.505185171574896 | 13.253993408832473 | 13.736224292073974 |
| 3 | Rio Comprido | 51.06117702738809 | 18.246211105146116 | 12.603770841972176 | 17.77038107910172 | 18.769190831796003 |
| 4 | Botafogo | 37.60525870632308 | 10.740870448680749 | 11.691538842186375 | 9.363903867594706 | 8.943485532456155 |
| 5 | Copacabana | 43.92247680266795 | 11.991321503776547 | 11.93190846485184 | 8.639214051796355 | 8.02132546216663 |

_Outras sheets: `Definições`, `RA_2000`, `Bairros_1991`, `Bairros_2000`_

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [06 — Theil base](06_theil_ideb.md)
    - [HEX-EDU (página de produto)](../produtos/hex_edu.md)
