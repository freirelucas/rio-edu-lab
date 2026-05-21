---
title: Como o lab descobriu isso (histórico técnico) — rio-edu-lab
description: Os 15 relatórios cronológicos que documentam como o lab evoluiu — do inventário inicial do data.rio aos achados de hoje. Para auditoria + leitura sequencial.
---

# Como o lab descobriu isso (histórico técnico)

Os 15 relatórios documentam, em ordem cronológica, como o lab evoluiu — do inventário inicial do data.rio até o catálogo + funil de papers atual. Esta página agrupa os relatórios em **cinco capítulos** com contexto narrativo. Para auditoria pé-a-pé, siga 01 → 15 dentro de cada capítulo.

Pra os achados em si (sem o passo-a-passo), vá pra [Achados](achados.md). Pra os papers organizados por tema, vá pra [Papers](papers/index.md). Esta página é a documentação cronológica.

<div class="chapter" data-num="I" markdown>

## Capítulo I — O que existe no data.rio (01–05)

O laboratório começou com uma pergunta básica: **o que está disponível no Grupo Educação do data.rio?** Sem mapeamento, qualquer análise vira teoria. Os 5 primeiros relatórios são o **inventário empírico**: 186 itens listados, 127 Excels catalogados, 35 PDFs corporados, shortlist de 12 candidatos auditados.

A surpresa central: **170 dos 186 itens "não têm URL no manifest"** mas estão acessíveis via 5 endpoints da API IPP — `data.rio` é mais rico do que o manifest sugere. O caminho de ingestão real difere do listado.

<div class="lede">Inventário empírico do Grupo Educação. 186 itens, 127 Excels, 35 PDFs — onde estão, o que tem dentro, o que presta para análise.</div>

<div class="reports">
<a class="report-link" href="../reports/01_manifest_eda/"><span class="rid">RELATÓRIO 01</span><span class="title">EDA do manifest — 186 itens por tipo / ano / tag</span></a>
<a class="report-link" href="../reports/02_ingestion_probe/"><span class="rid">RELATÓRIO 02</span><span class="title">Probe da API — 5 endpoints, 170 "sem URL" estão acessíveis</span></a>
<a class="report-link" href="../reports/03_excel_catalog/"><span class="rid">RELATÓRIO 03</span><span class="title">Catálogo dos Excels — 12.3 MiB, 126 .xls legacy, 1991–2024</span></a>
<a class="report-link" href="../reports/04_shortlist_audit/"><span class="rid">RELATÓRIO 04</span><span class="title">Shortlist auditado — 8 USE / 3 NEEDS_CLEANING / 1 SKIP</span></a>
<a class="report-link" href="../reports/05_pdf_corpus/"><span class="rid">RELATÓRIO 05</span><span class="title">Corpus dos PDFs — 25 com texto extraível, 10 escaneadas</span></a>
</div>

</div>

<div class="chapter" data-num="II" markdown>

## Capítulo II — O achado-base (06, 09, 10)

Com o inventário pronto, escolhemos uma pergunta concreta: **onde está a desigualdade do IDEB?** A intuição inicial era "Zona Sul × Zona Oeste". A decomposição Theil-T por bairro **refutou a intuição**: 66% da desigualdade está **dentro das RAs**, não entre. A escala administrativa atual mascara a maior parte do problema.

Os relatórios 09 e 10 confirmam que o achado é **robusto à escolha de indicador**: replica em ANOS_FINAIS (9º ano) com 70% within-share, e em decomposições separadas de Aprovação, SAEB e IDEB. A escolha do Theil-T não é arbitrária — é o índice canônico do Theil (1967), com a propriedade de decomposição aditiva.

<div class="lede">Decomposição Theil-T sobre IDEB por bairro: 66% within-RA em 9 anos × 3 séries × 2 ponderações. O achado-base que reorientou o lab para granularidade de bairro.</div>

<div class="reports">
<a class="report-link" href="../reports/06_theil_ideb/"><span class="rid">RELATÓRIO 06</span><span class="title">Theil sobre IDEB por bairro — 60–70% within-RA em 9 anos</span></a>
<a class="report-link" href="../reports/09_anos_finais/"><span class="rid">RELATÓRIO 09</span><span class="title">Replica em ANOS_FINAIS (9º) — within-share 70%</span></a>
<a class="report-link" href="../reports/10_method_replication/"><span class="rid">RELATÓRIO 10</span><span class="title">Theil separado por Aprovação / SAEB / IDEB — 64–70% within</span></a>
</div>

</div>

<div class="chapter" data-num="III" markdown>

## Capítulo III — HEX-EDU constrói-se (07, 08, 14)

O achado-base pediu uma **operacionalização visual**. Coropléticos por RA são o que a prefeitura já publica; o lab precisava de algo mais fino. O substrato H3 (Uber) discretiza o município em **1593 hexágonos res 8** — escala intermediária entre bairro e quarteirão.

O relatório 07 entrega o painel estático (RA vs H3, mesma escala de cor, mesmo dado — bolsões vermelhos visíveis na direita estão dentro de RAs cuja média é "ok"). O 08 traz a versão interativa via Folium. O 14 dá o salto conceitual: substitui "IDEB por hexágono" pela métrica **acesso ponderado** de Pereira et al. (2019) IPEA — distância × qualidade da escola.

<div class="lede">H3 hexagonal grid + Pereira-style accessibility. O HEX-EDU v0.6.1 entrega replicação parcial — núcleo do método com haversine; v0.7 traz isócronas OSM reais.</div>

<div class="reports">
<a class="report-link" href="../reports/07_hex_edu_static/"><span class="rid">RELATÓRIO 07</span><span class="title">HEX-EDU estático — painel 4 anos × 2 colunas (RA vs H3)</span></a>
<a class="report-link" href="../reports/08_hex_edu_interactive/"><span class="rid">RELATÓRIO 08</span><span class="title">HEX-EDU interativo — mapa Folium com seletor de ano</span></a>
<a class="report-link" href="../reports/14_acessibilidade/"><span class="rid">RELATÓRIO 14</span><span class="title">Acessibilidade Pereira-style — AP 3 lidera (113), AP 4 último (29)</span></a>
</div>

</div>

<div class="chapter" data-num="IV" markdown>

## Capítulo IV — Robustez (06b, 11, 12, 13)

Um achado isolado pode ser artefato. Os relatórios 06b, 11, 12 e 13 testam o achado-base em **quatro direções ortogonais**: ponderação por matrícula (06b), aninhamento 3-níveis (11), pseudocoortes temporais (12) e lei de escala intra-cidade (13). Em todas, o achado sobrevive.

Mais que confirmar, esses relatórios **descobrem** mecanismos: 87% das pseudocoortes 5º→9º pioram (provável migração à rede privada no 6º ano); a lei de escala é sublinear (β = 0,77) — bairros maiores em matrícula têm desproporcionalmente menos escolas. Ambos os sinais alimentam a lista de 15 bairros prioritários.

A revisão da v0.6 **rebaixou THESHA, FUN e PM-12 de "produtos" a "análises de robustez"** — a fundamentação acadêmica deles era frágil para o status original; o código continua reproduzível e os relatórios ficam aqui para auditoria.

<div class="lede">Robustez do achado-base em 4 dimensões: ponderação (06b), 3-níveis (11), pseudocoortes (12), lei de escala (13). Tudo sobreviveu — mas o status de "produto" não.</div>

<div class="reports">
<a class="report-link" href="../reports/06b_theil_weighted/"><span class="rid">RELATÓRIO 06b</span><span class="title">Theil ponderado por matrícula — T_total cai ~44%, share_within &gt; 50%</span></a>
<a class="report-link" href="../reports/11_thesha_rio/"><span class="rid">RELATÓRIO 11</span><span class="title">THESHA-Rio (3-level) — AP 8% / RA-em-AP 26% / bairro-em-RA 67%</span></a>
<a class="report-link" href="../reports/12_fun_rio/"><span class="rid">RELATÓRIO 12</span><span class="title">FUN-Rio (pseudocoortes) — 768 transições 5º→9º, 87% pioram</span></a>
<a class="report-link" href="../reports/13_pm_12/"><span class="rid">RELATÓRIO 13</span><span class="title">PM-12 (lei de escala) — β = 0.77 sublinear, R² 0.80</span></a>
</div>

</div>

<div class="chapter" data-num="V" markdown>

## Capítulo V — VULN-EDU (15)

Até aqui, o lab analisou **apenas IDEB**. A v0.7 introduz o IDS (Índice de Desenvolvimento Social, Censo 2010) por bairro como proxy SES e testa o gradiente Reardon (2011) intra-Rio: **SES alto prediz IDEB alto?**

A resposta empírica: parcialmente. Correlação +0.40, R² = 0.16. **39% dos bairros estão em quadrantes não-concordantes** — 22% são resilientes (baixo SES, bom IDEB), 17% sub-performam (bom SES, baixo IDEB). A operacionalização desafia o mapa-mental "investir onde o SES é baixo basta para subir o IDEB".

<div class="lede">Reardon (2011) intra-Rio: gradiente IDS × IDEB modesto (R²=0.16). Operacionaliza o segundo produto do lab (VULN-EDU v0.1).</div>

<div class="reports">
<a class="report-link" href="../reports/15_vuln_edu/"><span class="rid">RELATÓRIO 15</span><span class="title">IDS × IDEB por bairro — gradiente +0.40, R²=0.16, 39% não-concordantes</span></a>
</div>

</div>

## Recursos auxiliares

- [API do data.rio](data-rio-api.md) — endpoints validados pelo probe (relatório 02).
- [Sobre — glossário](sobre.md#glossario) — IDEB, Theil, AP, RA, bairro, H3, SAMI, IDS.
- [Reproduzir](reproduzir.md) — quickstart técnico ponta-a-ponta.

## Ler na ordem cronológica

Se quiser seguir como o lab foi se construindo: **01 → 02 → 03 → 04 → 05 → 06 → 06b → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15**. Cada relatório foi mergeado em PR separado, então o histórico de commits também conta a história.
