# Changelog

Formato adaptado de [Keep a Changelog](https://keepachangelog.com/) e [SemVer](https://semver.org/lang/pt-BR/).

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

### Ativação manual do DOI no Zenodo

Para que este release receba DOI:

1. Habilitar webhook em <https://zenodo.org/account/settings/github/>, ativando a sincronização do repo `freirelucas/rio-edu-lab`.
2. Criar o release `v0.1.0` no GitHub (ou re-criar se já existir antes da ativação).
3. Zenodo emite o DOI automaticamente. Substituir o placeholder no `README.md` pelo DOI real.
