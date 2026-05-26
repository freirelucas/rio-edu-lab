---
title: Propósito e critérios de qualidade do pipeline — rio-edu-lab
description: O que cada etapa do pipeline faz (propósito final) e como se sabe que a saída é confiável (critérios de qualidade), no backend (analysis/ → data/) e no front (site MkDocs).
---

# Propósito e critérios de qualidade do pipeline

Esta página torna explícito, para gestores e cientistas, **o que cada etapa do pipeline faz** (propósito final) e **como se sabe que a saída é confiável** (critérios de qualidade).

O `rio-edu-lab` não tem um front/back web literal:

- **Backend** = o pipeline de dados — scripts numerados `analysis/NN_*.py` que leem `data/raw/`, escrevem `data/processed/` e emitem relatórios; mais o pacote instalável `acec` (estatística canônica com invariantes).
- **Front** = a camada de publicação — fonte em `docs/` renderizada por `mkdocs build` e publicada no [site](index.md) via GitHub Pages.

!!! note "Ordem real do fluxo de papers"
    As etapas estão na ordem em que costumam ser pensadas, mas o fluxo de papers é **descoberta (1) → funil (3) → catálogo (2)**: o funil é quem alimenta o catálogo. Veja também os [4 estágios](sobre.md) e a [taxonomia de 10 categorias](dados.md).

## 1. Exploração de papers de educação

**Propósito final.** Varrer a literatura seminal de educação e expandir por citações (snowball via OpenAlex) a partir de papers-semente, montando o universo de candidatos a replicar no contexto do Rio. Roadmap: 12 → 100 papers.

**Backend.** `34_fetch_openalex.py`, `40_openalex_discover.py`, `45_bulk_discover.py` + helper `_openalex.py`; sementes versionadas em `data/openalex_seeds.yml`; cache de respostas em `data/processed/openalex_citations.json`.

**Front.** Sem página própria — o universo descoberto vira métrica no funil (etapa 3).

**Critérios de qualidade.**

- Descoberta parte de sementes **explícitas e versionadas** (não aleatória) → reprodutível.
- Deduplicação por `openalex_id`.
- Respostas brutas persistidas → reexecução **idempotente**, sem rebater a API.

## 2. Catalogação

**Propósito final.** Transformar os papers selecionados num **catálogo público canônico** (`data/papers_catalog.yml`) — cada entrada mapeia requisitos de dados → itens data.rio disponíveis → status de replicação + insight para gestores. É o **produto primário** do lab.

**Backend.** `31_build_paper_catalog.py` (monta mapeamentos + valida schema); saídas `data/processed/papers_catalog_summary.json`, `paper_data_mapping.csv`.

**Front.** `32_render_papers_pages.py` renderiza as mini-páginas `docs/papers/*.md` + o [índice de papers](papers/index.md).

**Critérios de qualidade.**

- *Hard-fail no CI:* `id`, `year`, `replication_status` válidos + invariante de `report_ids`.
- Vocabulário **fechado** de status: `replication_status ∈ {full, partial, pending, unfeasible}`; `data_rio_coverage.status ∈ {available, partial, external, missing}`.
- **Drift check:** o CI reroda o gerador e faz `git diff --quiet docs/papers/`, falhando se as páginas divergirem do commitado (obriga regenerar).
- Caveats metodológicos explícitos por entrada (MAUP, comparabilidade, mudanças INEP/IBGE).

## 3. Funil de papers

**Propósito final.** Triagem **reprodutível** dos candidatos até o catálogo: extrair requisitos de dados de cada paper, casá-los com o que o data.rio oferece, medir cobertura e **promover** (decisão curatorial) os aprovados de `papers_funnel.yml` (staging) → `papers_catalog.yml`. Dá rastreabilidade "universo descoberto → catalogado".

**Backend.** `46_extract_requirements.py`, `41_match_requirements.py`, `47_check_coverage.py`, `48_promote_funnel.py` + helper `_match.py`; staging `data/papers_funnel.yml`; taxonomia `data/requirements_taxonomy.yml`; saídas `funnel_state.json`, `data_rio_match_suggestions.csv`, `data_rio_reverse_links.json`.

**Front.** `25_funnel_state.py` gera métricas + `docs/_assets/charts/funnel.json` (hero "9.855 itens…"); `41_match_requirements.py` gera `docs/papers-by-data-rio.md` (índice reverso paper ↔ item).

**Critérios de qualidade.**

- Schema **estrito** do funil (`31_build_paper_catalog.py --validate-funnel`): sem `openalex_id` duplicado, `decision` válida, `category_ids` ∈ taxonomia fechada de 10 categorias.
- **Matching com limiar explícito** (score **IDF-weighted** ≥ 5,0 = `available`) → auditável, não subjetivo.
- **Drift check** do índice reverso (CI reroda `41` e diffa a página).

## 4. Análise dos dados disponíveis em toda a API do data.rio

**Propósito final.** Inventariar/ativar o acervo público (9.855 itens; 186 de educação; **4 ativados**) e produzir os achados substantivos replicando papers: o achado-central (**66% da desigualdade do IDEB está *dentro* das RAs**), [HEX-EDU](produtos/hex_edu.md) (Theil em grid H3 + acessibilidade estilo Pereira) e [VULN-EDU](produtos/vuln_edu.md) (IDS × IDEB).

**Backend (aquisição + inventário).** `00_fetch_manifest.py` (snapshot canônico `manifest.json`), `01_manifest_eda.py`, `02_ingestion_probe.py` (valida endpoints → `data/raw/probe/*`), `03/04/05` (Excel), `06_shortlist_audit.py`, `07/08/09` (PDF).

**Backend (análise).** Theil: `10`, `15`, `16`, `17` + helper `_theil.py` e pacote `acec.stats` (`theil_t`, `theil_decompose[_nested]`, `pearson`, `spearman`, `ols_simple`, `quintile_grid`); HEX-EDU: `11`–`14`, `26`; VULN-EDU: `28`, `29`; outros: `18`, `19`, `20`.

**Front.** [`data-rio-api.md`](data-rio-api.md) (endpoints validados), [`dados.md`](dados.md) (escopo + taxonomia), os relatórios `docs/reports/01`–`15`, [HEX-EDU](produtos/hex_edu.md), [VULN-EDU](produtos/vuln_edu.md), [achados](achados.md), [bairros prioritários](bairros-prioritarios.md).

**Critérios de qualidade.**

- **Snapshot canônico** (`manifest.json`) → análises partem de estado fixo, não de chamada ao vivo.
- **Probe valida endpoints** antes do uso; **provenance** em `data/raw/geo/_provenance.json` (origem + data) → rastreabilidade da fonte.
- **Identidade Theil exata** (teste *hard*, `tests/test_theil.py`): `T_b + T_w == T` dentro de `1e-6` em toda linha; `T = 0` na igualdade perfeita; pacote `acec` com invariantes incl. **identidade aditiva de 3 níveis**.
- **Sanity do achado-headline** (*hard-fail*): `share_within ∈ [59%, 73%]` (média 66%) — regressão no pipeline quebra o teste; robusto em **6 séries**.
- **Honestidade estatística:** VULN-EDU reporta Pearson +0,40 / R² = 0,16 e "39% de bairros não-concordantes" — efeito modesto declarado, não inflado; acessibilidade Pereira com distância haversine e critério de elegibilidade explícito (1022 escolas).
- Relatórios numerados em ordem cronológica (trilha auditável); status de cobertura rotulado por item.

## 5. Deploy de visualizações

**Propósito final.** Publicar os achados como gráficos interativos e mapas (Plotly + H3/folium) de forma **automática e reprodutível**, para gestores e cientistas explorarem.

**Backend (geração dos artefatos).** `21_build_tour_charts.py`, `25_funnel_state.py`, `27_accessibility_charts.py`, `30_vuln_edu_charts.py` exportam Plotly como JSON em `docs/_assets/charts/*.json`; `14_hex_edu_folium.py` gera o mapa interativo; `acec.viz` (palette + `write_json`).

**Front (render + deploy).** `docs/javascripts/charts.js` carrega o JSON via `Plotly.newPlot()`; markers `<div data-chart="…">`; o [mapa interativo](mapa.md); deploy `.github/workflows/pages.yml` em push para `main`.

**Critérios de qualidade.**

- JSON dos charts **versionado** + **drift check** (CI reroda geradores e diffa).
- Colorway canônico (`RIO_COLORWAY`) aplicado quando o layout não sobrescreve → consistência visual.
- **`mkdocs build --strict`** falha em link quebrado / arquivo não referenciado.
- Plotly **pinado** em 2.35.0 (render determinístico); deploy idempotente automático.

## 6. Documentação replicável para cientistas

**Propósito final.** Garantir que qualquer cientista reproduza o lab ponta-a-ponta (["reproduzível em 4 minutos"](reproduzir.md)), entenda a trilha de auditoria e **cite** o trabalho — a reprodutibilidade é tratada como produto, não como extra.

**Front (docs).** [`reproduzir.md`](reproduzir.md) (ordem do pipeline + comandos + *sanity assertion* final), [`investigacao.md`](investigacao.md) (trilha cronológica em 5 capítulos, "auditoria pé-a-pé 01→15"), [`sobre.md`](sobre.md), `README.md`; `CITATION.cff` + DOI Zenodo; licenças MIT (código) / CC BY 4.0 (dados derivados).

**Backend (suporte).** Núcleo **sem dependências externas** (stdlib Python 3.10+); scripts numerados em ordem determinística; `24_append_report_footers.py` (rodapés de proveniência nos relatórios).

**Critérios de qualidade.**

- **Auditabilidade por design:** relatórios 01→15; cada produto cita o paper-base e replica o método antes de estender ("paper-driven").
- **Reprodutibilidade testável:** suíte verde (26 testes do lab + 20 do `acec`); sanity do `share_within`; build estrito.
- Proveniência/licenciamento creditados; DOI Zenodo preservado entre releases.

## Portões transversais

Valem para todo o pipeline e são aplicados no CI (`.github/workflows/{ci,pages}.yml`):

| Portão | O que garante |
|---|---|
| `pytest` (26 lab + 20 `acec`) | Invariantes do Theil (2 e 3 níveis), primitivas do matching IDF, e o achado `share_within` como *hard-fail* |
| `ruff` | Lint (hoje *warn-only*; a apertar) |
| Validação de schema | Catálogo e funil (`31_build_paper_catalog.py [--validate-funnel]`) |
| Drift checks | Páginas geradas == commitadas (papers, índice reverso, charts) |
| `mkdocs build --strict` | Sem link quebrado / arquivo não referenciado |
| Deploy | Automático em push para `main` (idempotente) |

## Continue

<div class="grid cards" markdown>

-   [:material-run-fast: Reproduzir em 4 minutos](reproduzir.md)
-   [:material-history: Histórico técnico](investigacao.md)
-   [:material-database: Dados e taxonomia](dados.md)

</div>
