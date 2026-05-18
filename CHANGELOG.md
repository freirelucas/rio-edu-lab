# Changelog

Formato adaptado de [Keep a Changelog](https://keepachangelog.com/) e [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased — v0.7 in progress]

### v0.7.3 — funil de papers de impacto (descoberta → requisitos → coverage → promoção)

Infra para escalar o catálogo de 12 papers seed para muitos papers de impacto, cada um com `data_requirements` mapeados à taxonomia fechada. Os slices A+B+C (v0.7.x) entregaram peças isoladas — discovery OpenAlex, matching de requisitos vs data.rio, validator strict, scaffold de replicação. Faltava o **pipeline ponta-a-ponta** que liga essas peças num funil de 4 estágios.

Os 4 estágios:

1. **OpenAlex mapeia papers de impacto** — descoberta em lote sobre lista curada de themes (`data/openalex_concepts.yml`).
2. **Cada paper é investigado** — top-3 categorias da taxonomia sugeridas automaticamente a partir de título+abstract (reusa tokenizer do Slice B).
3. **Coverage check vs data.rio** — para cada requisito sugerido, top-1 item do manifest com status `available`/`partial`/`external`/`missing`.
4. **Promoção ao catálogo** — candidatos marcados `decision: accept` viram entradas válidas em `papers_catalog.yml` com `replication_status` auto-derivado e schema completo.

Adições (pipeline do funil):

- `analysis/_match.py` — primitivas extraídas de 41 (tokenize, score_item, category_keywords, load_taxonomy) + novo `score_against_categories` (text-side classifier). Reusado por 41, 46 e 47.
- `analysis/_openalex.py` — primitivas extraídas de 40 (fetch, build_query_url, parse_work) + novo `iterate_works` (paginação + throttle 1 req/s). Reusado por 40 e 45.
- `analysis/45_bulk_discover.py` — Stage 1: itera themes em `openalex_concepts.yml`, deduplica por `openalex_id`, faz **upsert** em `papers_funnel.yml` preservando decisões do curador. CLI: `--concepts`, `--top`, `--dry-run`.
- `analysis/46_extract_requirements.py` — Stage 2: para cada candidato sem sugestões, tokeniza title+abstract, pontua contra aliases das 10 categorias, escreve top-K (default 3). Idempotente; `--force` recomputa.
- `analysis/47_check_coverage.py` — Stage 3: para cada requisito sugerido, encontra top-1 item do manifest. Categorias `level=individual` ou notes "Não disponível no data.rio" são marcadas `external` direto (skip matching). Threshold default 5.0 para `available`.
- `analysis/48_promote_funnel.py` — Stage 4: filtra `decision: accept`, gera entrada YAML válida (schema do 31), anexa ao catalog com seção marker. `--dry-run` mostra antes de escrever. `replication_status` auto-derivado.
- `data/openalex_concepts.yml` — seed de 8 themes (educational inequality, school segregation, economics of education, school effects, early childhood, accessibility, education-Brazil, human capital).
- `data/papers_funnel.yml` — staging area, inicialmente vazio. Curador edita `decision` à mão antes de promover.

Edições:

- `analysis/40_openalex_discover.py` — agora importa de `_openalex`. Comportamento de saída idêntico.
- `analysis/41_match_requirements.py` — agora importa de `_match`. Comportamento de saída idêntico.
- `analysis/_openalex.py build_query_url` — fix de breaking change do OpenAlex: `from_publication_year` foi removido, agora é `publication_year:from-to` (range). 40 quebrava com HTTP 400 contra a API atual.
- `analysis/31_build_paper_catalog.py` — novo flag `--validate-funnel` valida schema de `papers_funnel.yml` (openalex_id único, decision em enum, category_ids na taxonomia, status em enum). Soft-fail se YAML ausente.
- `.github/workflows/ci.yml` — novo step `Validate paper funnel schema` (hard-fail se YAML corrompido).

Workflow do curador (end-to-end):

```bash
# uma vez: editar data/openalex_concepts.yml para calibrar themes
python3 analysis/45_bulk_discover.py                # Stage 1: ~30s/theme
python3 analysis/46_extract_requirements.py         # Stage 2: instantâneo
python3 analysis/47_check_coverage.py               # Stage 3: instantâneo
# editar data/papers_funnel.yml: decision: accept nos top-N escolhidos
python3 analysis/48_promote_funnel.py               # Stage 4: append ao catalog
python3 analysis/31_build_paper_catalog.py          # valida
python3 analysis/32_render_papers_pages.py          # gera mini-pages
python3 analysis/41_match_requirements.py           # link reverso
python3 analysis/34_fetch_openalex.py               # snapshot citations
# por paper que vire replicação:
python3 analysis/42_scaffold_replication.py <id>    # script + report stubs
```

Não muda (preservado):

- 12 papers seed do catálogo inalterados.
- Outputs de 31, 32, 34, 41 byte-idênticos ao estado anterior (refactor preserva comportamento — verificado via smoke test).
- Taxonomia fechada (10 categorias) inalterada — agora também enforçada para entradas auto-promovidas via `48_promote_funnel.py` (que usa `aliases[0]` como string canônica do requirement).

Próximas iterações (deferred):

- Curador roda 45 com os 8 themes seed → ~150 candidatos brutos esperados, ~30-50 com sugestões válidas após Stage 2 → primeira batch de promoção.
- Replicações leves dos papers promovidos viáveis (todos requisitos `available`/`partial`). Cada uma usa o scaffold de 42 → PR pequeno por paper.
- Fix dos 4 item_ids "(unknown — not in manifest)" no `papers-by-data-rio.md` — slugs (`ideb-municipal-bairros`, `bairros-ipp`, `ids-rm-2010`) que não existem no manifest; resolver via alias-table ou re-ingest do manifest.
- Calibração dos thresholds de 46 (`--min-score`) e 47 (`--threshold`) conforme primeiro batch de uso real.

### v0.7.0 — virada conceitual: catálogo de papers + rebrand do lab

Mudança estrutural: o lab deixa de se apresentar como "Atlas Cibernético da Educação Carioca com 2 produtos" e passa a se apresentar como **laboratório de replicação de papers em educação aplicados ao Rio**, com um catálogo público de papers como produto primário. Os 2 produtos ativos (HEX-EDU e VULN-EDU) permanecem inalterados — passam a ser as 2 entradas "replicadas" do catálogo.

Motivação:

- O padrão "1 paper = 1 produto = 1 PR" não escala. Para chegar nos 100 papers mais influentes da área, precisa de catálogo estruturado.
- Faltava cruzamento explícito **paper → requisitos de dados → item disponível no data.rio**. Cada análise descobria suas dependências ad-hoc.
- Relatórios técnicos são pouco acionáveis para gestores municipais. Agora cada produto inclui um bloco "Para gestores públicos" com achado, implicação e ações concretas.

Adições (infraestrutura do catálogo):

- `data/papers_catalog.yml` — fonte canônica do catálogo. 12 papers seed nesta v0.7: 3 já replicados (Pereira 2019, Reardon 2011, Theil 1967), 5 alvos de replicação leve em releases próximas (Soares & Andrade 2006, Alves & Soares 2013, Coleman et al. 1966, Hanushek 1986, Reardon & Owens 2014), 4 metodológicos canônicos (Becker 1964, Cunha & Heckman 2007, Hoxby 2000, Card & Krueger 1992).
- `analysis/31_build_paper_catalog.py` — valida YAML + gera mapping CSV + summary JSON.
- `analysis/32_render_papers_pages.py` — renderiza mini-pages por paper + index do catálogo.
- `analysis/34_fetch_openalex.py` — busca metadata e contagem de citações via OpenAlex API (12/12 papers matched no snapshot inicial; ranges de 3 a 7659 citações).
- `data/processed/paper_data_mapping.csv` — derivado, 27 linhas (paper × requisito × cobertura no data.rio).
- `data/processed/papers_catalog_summary.json` — agregados.
- `data/processed/openalex_citations.json` — snapshot OpenAlex de 2026-05-18.
- `docs/papers/index.md` — landing do catálogo com 3 tabelas (replicados / catalogados pendentes / dados indisponíveis).
- `docs/papers/*.md` (×12) — mini-pages por paper.

Adições (utilidades canônicas no pacote `acec`):

- `acec.stats.regression` com `pearson`, `spearman`, `ols_simple`, `quintile_grid` — promovidos do `analysis/29_vuln_edu.py`. Novos scripts de replicação importarão daqui.
- Testes em `reference/acec-hub/tests/test_acec_stats.py`: 11 novos casos → 20/20 verdes (era 9).

Modificações (rebrand):

- `docs/index.md` — hero reposicionado: título do site agora é "laboratório de replicação de papers em educação aplicados ao Rio". Botão "Catálogo" passa a ser CTA primário. BibTeX atualizado para v0.7. Nota de transparência sobre a renomeação.
- `mkdocs.yml` — `site_description` reescrito. Seção `Papers` adicionada ao nav com 13 entries (index + 12 papers).
- `README.md` — identidade + estado v0.7 + nota de renomeação.
- `docs/produtos/hex_edu.md` + `docs/produtos/vuln_edu.md` — bloco `!!! info "Para gestores públicos"` adicionado em cada produto. Achado em 1 frase, implicação para política, 3 ações concretas, como auditar.

Não muda (preservado):

- 2 produtos ativos (HEX-EDU + VULN-EDU) continuam reproduzíveis sem alteração de código analítico.
- 30 scripts em `analysis/` inalterados — só foram adicionados 31, 32, 34.
- DOI Zenodo `10.5281/zenodo.20060620` (concept) preservado — versionamento contínuo.
- `data/manifest.json` + insumos derivados intocados.
- Site ganhou seção `/papers/` mas o resto do nav permanece.

Próximas iterações (deferred):

- v0.7.x: replicações leves dos 5 papers-alvo (Soares & Andrade, Alves & Soares, Coleman, Hanushek, Reardon & Owens). Cada uma vira PR com 1 script + 1 relatório.
- Curadoria dos ~88 papers restantes para chegar nos 100. Batches temáticos (segregação, primeira infância, economia da educação, sociologia, política educacional, Brasil-específicos).
- `acec.viz.plotly_helpers` (palette + write_json) — refactor não-bloqueante.

## [Released]

### v0.6.2 — VULN-EDU v0.1 entregue (IDS × IDEB por bairro)

Segundo produto ativo do MVP-honesto. Operacionaliza Reardon (2011) "The widening academic-achievement gap between the rich and the poor" sobre dados cariocas: cruza IDS (Censo 2010, IPP) por bairro com IDEB séries iniciais 2023 para mensurar empiricamente o gradiente socioeconômico-educacional.

Achados:

- Pearson(IDS, IDEB) = +0.404 ; Spearman = +0.389. OLS `IDEB = 4.29 + 2.87·IDS` com **R² = 0.16** — IDS explica só 16% da variância do IDEB.
- 144/147 bairros casam (98% do município). 3 sem casamento por renomeação pós-Censo 2010.
- Quadrantes (pela mediana): Q1 privilegiado 47, Q2 resiliente 32, Q3 sub-performance 25, Q4 vulnerável 40 — **39% dos bairros caem nos quadrantes não-concordantes** (Q2+Q3).
- Concordância em quintis 5×5 = 30%. Política pública que assume IDS → IDEB erra mais que acerta.
- Top-5 vulneráveis (VULN_score composto): Santo Cristo, Sampaio, Gardênia Azul, Parque Columbia, Acari.

Adições:

- `analysis/28_fetch_ids.py` — IDS Feature Service (10.504 setores censitários).
- `analysis/29_vuln_edu.py` — agregação, correlação, OLS, quadrantes, VULN_score.
- `analysis/30_vuln_edu_charts.py` — 3 Plotly (scatter, mapa quadrantes, top-15).
- `data/raw/geo/ids_setores.csv` (~2 MiB slim — atributos por setor; geometria opt-in via `--with-geometry`).
- `data/processed/vuln_edu_bairros.csv` (144 × 20).
- `data/processed/vuln_edu_summary.json`.
- `docs/reports/15_vuln_edu.md`.
- `docs/produtos/vuln_edu.md` — VULN-EDU sai do "em planejamento" e vira segundo produto ativo.
- `docs/_assets/charts/vuln_edu_{scatter,map,top}.json`.

Não entrega ainda (v0.2):

- OLS multivariado por sub-indicador (renda/analfabetismo/saneamento isolados).
- Painel temporal IPS por RA (2016–2024) — IDS é decenal, IPS é anual.
- IDEB por escola via microdado INEP (resolve gargalo Q3 — sub-performance possivelmente por migração para rede privada).
- Moran's I dos resíduos OLS.

### v0.6.1 — HEX-EDU acessibilidade entregue (Pereira-style, haversine)

Operacionalização parcial de Pereira et al. (2019) IPEA: para cada hex H3 res 8 do município, computamos `acesso_quality(i) = Σ_j IDEB(j) · exp(-d(i,j)/d0)` sobre 1022 equipamentos elegíveis (Escola Municipal + CIEP + Especial). `d0 = 1.5 km`, distância haversine (linha reta).

Achados:

- AP 3 (Zona Norte) lidera (média 113), seguida do Centro (96).
- Zona Sul (AP 2) em 59 — IDEB médio mais alto não compensa baixa densidade.
- AP 4 (Barra/Jacarepaguá) em 29 — sprawl + dependência de transporte.
- 18 hexes têm zero escolas elegíveis em raio de 5 km.

Adições:

- `analysis/25_fetch_escolas_municipais.py` — Feature Service IPP (1590 features → 1022 elegíveis).
- `analysis/26_hex_accessibility.py` — métrica Pereira simplificada.
- `analysis/27_accessibility_charts.py` — Plotly figures.
- `data/raw/geo/escolas_municipais.geojson`
- `data/processed/hex_accessibility.csv`
- `docs/reports/14_acessibilidade.md`
- `docs/_assets/charts/acessibilidade_{map,dist}.json`

Não entrega ainda (v0.7):

- OSM road network + isócronas reais (substituem haversine).
- Decomposição por SES (IPS/IDS) em vez de só geográfica.
- IDEB por escola (microdado INEP, não em data.rio) — atualmente IDEB é por bairro.



### Honest re-framing of the MVP catalog

Revisão crítica do framing "4 produtos paper-driven" da v0.5 expôs que a fundamentação acadêmica de 3 dos 4 produtos era frouxa:

- **Pereira et al. (2019)** — paper-base canônico do HEX-EDU — finalmente localizado: <https://hdl.handle.net/10419/240730>. É sobre **acessibilidade espacial via H3 + decomposição por equidade**, cobrindo Rio entre 7 capitais. A v0.5 só entregou Theil sobre o H3 grid, **não a métrica de acessibilidade**. Replicação completa fica explícita como roadmap v0.6.
- **Bourguignon, Ferreira & Menéndez (2007)** (THESHA-Rio) — paper sobre desigualdade de **renda por características individuais**. A "decomposição em 3 níveis espaciais" que entregamos é extensão do Theil, não replicação do Bourguignon. Não é produto distinto.
- **Mare (1980) + Reardon & Owens (2014)** (FUN-Rio) — papers sobre **logit de transição** e **segregação racial/SES**. O que fizemos foi diferença bruta `IDEB_9º − IDEB_5º`. Distância metodológica grande. Não é produto paper-driven.
- **Bettencourt (2010) inter-capitais** (PM-12) — paper foi originalmente **comparador inter-capital**. Implementei intra-Rio. Diverge do plano original; mantemos como análise auxiliar mas não como replicação direta.

### Mudanças

- **Cortados como produtos**: THESHA-Rio, FUN-Rio, PM-12. Os relatórios técnicos (11, 12, 13) e código permanecem reproduzíveis e citáveis em `Investigação`. Apenas o status "produto paper-driven distinto" sai.
- **HEX-EDU re-fundamentado** em Pereira et al. (2019) IPEA. Página-produto reescrita explicitando: v0.5 = Theil sobre H3 grid; v0.6 = acessibilidade Pereira-style real (em construção, requer Escolas Municipais Feature Service + OSM road network + isócronas).
- **Novo produto em planejamento**: **VULN-EDU** — cruzamento IPS/IDS (vulnerabilidade socioeconômica) com IDEB. Paper-base a definir (Reardon 2011 candidato). Habilitado por dados que existem no data.rio mas não foram usados na v0.5.
- **Página `/paper/` deletada** (já merged no PR #27). A produção de "manuscrito" virou pose acadêmica que não fundamenta nada.
- **Catálogo público (`/produtos/`)** reduzido para 1 ativo + 1 em planejamento. Cards de THESHA/FUN/PM-12 substituídos por nota explicando a re-classificação.
- **CITATION.cff abstract** reescrito para refletir o framing honesto. **Pereira et al. (2019) IPEA adicionado como referência canônica**.

### Não muda

- Pipeline reproduzível, código, testes, dados derivados — todos preservados. Os 23 scripts em `analysis/` continuam rodando.
- DOI Zenodo `10.5281/zenodo.20060620` segue válido (concept DOI continua resolvendo para a última versão).
- 28 testes verdes mantidos.

## [v0.5.0] — 2026-05-06

MVP-1 do ACEC-Hub completo: os 4 produtos paper-driven entregues, mais bridge do lab para o pacote `acec`.

### Adicionado (produtos)

- **HEX-EDU** já entregue na v0.1.0 (mapa H3 do IDEB).
- **THESHA-Rio** (Relatório 11) — decomposição Theil em 3 níveis aninhados (AP → RA-em-AP → bairro-em-RA). Inspirado em Bourguignon, Ferreira & Menéndez (2007). Identidade aditiva exata em todos os 9 anos. Achado: bairro-within-RA = 67%, RA-within-AP = 26%, between-AP = 8%.
- **FUN-Rio** (Relatório 12) — trajetórias 5º → 9º ano por pseudocoorte. Mare (1980) + Reardon & Owens (2014) operacionalizados. 768 pseudocoortes em 124 bairros. Δ médio = −0.65 (87% pioram). Slope −0.53 vs IDEB-5 base — efeito Mateus refutado.
- **PM-12** (Relatório 13) — lei de escala intra-Rio. Bettencourt et al. (2010) + Heinrich Mora et al. (2023) adaptados. Fit `escolas = 0.008 · matrículas^0.77` (β sublinear, R² = 0.80). Hipótese de β=1 refutada. SAMI mapeia bairros over/under-served após controlar pelo tamanho.

### Adicionado (infraestrutura)

- **`acec` package** populado em `reference/acec-hub/src/acec/` (Sessão 11):
  - `acec.stats.theil_t`, `theil_decompose`, `theil_decompose_nested` (NOVO).
  - `acec.transform.ideb_parser.parse_hierarchical_sheet`.
  - `acec.geo.h3_grid.generate_grid`.
- CI ganha step separado para testar o pacote ACEC (`pip install -e reference/acec-hub`).
- 28 testes verdes (19 do lab + 9 do acec), incluindo identidade aditiva 3-níveis.

### Achado-headline da v0.5.0 (consolidando os 4 produtos)

A desigualdade educacional municipal carioca tem 3 padrões consistentes:

1. **Espacial fina**: 67% within-RA, 26% RA-em-AP, 8% between-AP (THESHA-Rio).
2. **Temporal**: 87% das pseudocoortes 5º→9º pioram, com slope −0.53 vs ponto-de-partida (FUN-Rio).
3. **De infraestrutura**: alocação sublinear (β=0.77) — bairros maiores estão sub-servidos no count de escolas (PM-12).

Os três padrões apontam para a **mesma direção de política**: granularidade de bairro é a escala correta de intervenção; AP/RA são agregações que escondem ou regridem ao centro.

### Limitações (mantidas para v0.6+)

- OCR dos 10 PDFs scanned do Relatório 05.
- Refatoração: pipeline em `analysis/*` ainda tem cópias locais das funções Theil; canônico já em `acec.stats`. Migração é trabalho de v0.6.
- PM-12 cross-cidades — versão atual é intra-Rio. Inter-capitais requer ingestão dos portais de outros municípios.
- FUN-Rio com microdado real — atual usa pseudocoorte; coorte real precisa de microdado INEP por escola.
- Streamlit hospedado para HEX-EDU — Folium estático suficiente para v1.

## [v0.1.0] — 2026-05-06

Primeiro release citável. Fundação analítica completa para o produto **HEX-EDU**.

### Achado central

**66% da desigualdade educacional do Rio Municipal está dentro das RAs**, não entre elas (média 2007–2023). Robusto a:

- Etapa escolar (ANOS_INICIAIS 5º ano e ANOS_FINAIS 9º ano).
- Ponderação por matrículas (nos 2 anos com overlap, 2011 e 2013).
- Substituição do IDEB pelos componentes Aprovação (%) e Média SAEB.

Justificativa quantitativa direta para o produto visual HEX-EDU (mapa H3 em granularidade de bairro substituindo o coroplético tradicional por RA).

### Adicionado (relatórios)

- 01 — EDA do manifest do Grupo Educação (186 itens, 4 owners, janela 2017–2026).
- 02 — Probe de ingestão da API ArcGIS Hub (5/5 itens HTTP 200).
- 03 — Catálogo empírico dos 127 Excels (12.3 MiB total; 126/127 são `.xls` legacy, não `.xlsx`).
- 04 — Auditoria do shortlist (8 USE / 3 NEEDS_CLEANING / 1 SKIP de 12 candidatos).
- 05 — Corpus dos 35 PDFs (4 coleções IPP, 717 páginas, 25/35 com texto extraível).
- 06 — Decomposição Theil-T do IDEB séries iniciais por bairro (1991–2023).
- 06b — Theil ponderado por matrículas (2011, 2013).
- 07 — HEX-EDU mapa estático (4 anos × RA vs H3 res 8).
- 08 — HEX-EDU mapa interativo Folium (9 anos com seletor).
- 09 — IDEB séries finais (9º ano) — replicação do achado central.
- 10 — Replicação metodológica em sub-componentes (Aprovação, SAEB, IDEB).
- Paper draft v0.1 consolidando os achados.

### Adicionado (infraestrutura)

- Site MkDocs Material publicado em <https://freirelucas.github.io/rio-edu-lab/>.
- Workflow `pages` (deploy automático em push para `main`).
- Workflow `ci` (pytest + ruff em todo push/PR).
- 19 testes unitários e de integração para a decomposição Theil; o achado central virou um teste.
- `analysis/_theil.py` — implementação canônica testável.
- 17 scripts em `analysis/` reproduzíveis ponta-a-ponta com `pip install -r requirements.txt`.

### Dados derivados versionados em `data/processed/`

- `manifest_enriched.csv` (186 itens × heurísticas)
- `excel_catalog.csv` + `excel_sheets.csv` (127 × 630)
- `pdf_catalog.csv` (35)
- `shortlist_audit.csv` (12)
- `ideb_bairros.csv` + `ideb_anos_finais.csv` (long format)
- `theil_ideb_anos_iniciais.csv` + `theil_ideb_anos_finais.csv`
- `theil_ideb_weighted.csv` (2 anos com matrícula)
- `theil_components.csv` (3 componentes × 9 anos)
- `theil_iniciais_vs_finais.csv` (side-by-side)
- `matriculas_bairros.csv` (4 anos)
- `ideb_components_long.csv` (3924 obs)
- `h3_grid.geojson` + `hex_to_bairro.csv` + `bairros_aliases.csv`
- `hex_ideb_panel.csv` (1593 hexes × 4 anos)

### Limitações conhecidas (não-objetivos da v0.1)

- Streamlit hospedado — Folium estático embebido no MkDocs serve para v1.
- Replicação numérica direta de "Pereira et al. (2019)" — paper-base citado no README do ACEC-Hub mas sem título/DOI; replicação numérica fica como backlog. Em vez disso, fizemos replicação metodológica nos sub-componentes do IDEB (Relatório 10).
- OCR dos 10 PDFs scanned do Relatório 05.
- Refatoração para package Python instalável.
- THESHA-Rio, PM-12, FUN-Rio (outros produtos do roadmap MVP-1 do ACEC-Hub).

### DOI Zenodo

- **Concept DOI** (sempre aponta para a última versão): <https://doi.org/10.5281/zenodo.20060620>
- Emitido em 2026-05-06 a partir do GitHub Release v0.5.0 (que englobou também o conteúdo da v0.1.0). Webhook ativado em <https://zenodo.org/account/settings/github/>.
