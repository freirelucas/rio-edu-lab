# Changelog

Formato adaptado de [Keep a Changelog](https://keepachangelog.com/) e [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased — v0.6 in progress]

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
