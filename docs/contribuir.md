---
title: Contribuir
description: Como contribuir pro rio-edu-lab — paper suggestions, claim de replicações, sources novas, bug reports.
---

# 🤝 Contribuir

O rio-edu-lab é **operado por um curador solo** (Lucas Freire) mas **escala via comunidade**. A escala do desafio — traduzir 1000s de papers de política pública educacional contra dados brasileiros — não fecha sem ajuda externa.

## Canais

### 💬 Discussions — pra conversar

[GitHub Discussions](https://github.com/freirelucas/rio-edu-lab/discussions) é pra:

- Dúvidas conceituais ("o método X funciona pra Rio?")
- Contexto histórico ("por que escolheram Theil?")
- Brainstorming aberto
- Mostrar trabalho relacionado seu

### 🎯 Issues — pra trabalho acionável

Cada issue tem **template específico**:

- **[📚 Sugerir paper](https://github.com/freirelucas/rio-edu-lab/issues/new?template=sugerir-paper.md)** — paper que deveria estar no catálogo
- **[🔬 Claim — vou replicar](https://github.com/freirelucas/rio-edu-lab/issues/new?template=replication-claim.md)** — reserve trabalho de replicação (PwC-style)
- **[💡 Sugerir source](https://github.com/freirelucas/rio-edu-lab/issues/new?template=sugerir-source.md)** — fonte de papers além OpenAlex/Semantic Scholar
- **[🐛 Bug report](https://github.com/freirelucas/rio-edu-lab/issues/new?template=bug-report.md)** — algo quebrou

### 🚀 Pull Requests

PRs diretos são bem-vindos. Template em `.github/PULL_REQUEST_TEMPLATE.md` lista checklist:

- Drift renderers rodados (25, 41, 51, 56, 60, 63, 64, 65)
- pytest verde
- mkdocs build --strict verde
- ruff sem novos erros
- DAS + provenance se for replicação (veja [TOP scorecard](top-scorecard.md))

## Fluxo recomendado pra contribuidores

### Quero sugerir um paper

1. Verifique [Inbox](inbox.md) — pode já estar lá
2. Verifique [catálogo](papers/index.md) — pode já estar replicado
3. Abre [`📚 Sugerir paper`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=sugerir-paper.md)
4. Curador (Lucas) responde em ~1 semana

### Quero replicar um paper do inbox

1. Vê [Inbox](inbox.md), escolhe paper top-priority
2. Abre [`🔬 Claim`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=replication-claim.md) com paper-id
3. Espera curador aprovar (~3 dias) — evita duplicar trabalho
4. Faz fork + PR seguindo template

**Convenção PwC-style**: claim ativo por 30 dias. Após, se sem update, qualquer um pode pegar.

### Quero adicionar uma fonte (SciELO, Crossref, HF Papers, etc.)

1. Abre [`💡 Sugerir source`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=sugerir-source.md)
2. Padrão de adapter: espelhar shape de `analysis/_openalex.py` (cache filesystem, polite throttle, retry backoff)
3. PR com `analysis/_<source>.py` + tests + integração com `analysis/45_bulk_discover.py`

### Quero reportar um bug

1. Abre [`🐛 Bug report`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=bug-report.md)
2. Bug crítico (achado quebrou) → automaticamente vira algedônico (canal VSM emergency) via `.github/workflows/algedonic-alert.yml`
3. Bug em dado externo (data.rio) → label `external-dep`, talvez issue downstream

## Princípios

### Open Science non-negotiable

- **MIT** (código) + **CC-BY-4.0** (dados derivados)
- Tudo replicável end-to-end via `analysis/NN_*.py`
- DOI Zenodo + provenance trail per paper replicado ([padrão TOP](top-scorecard.md))
- DAS (Data Availability Statement) em todo paper full/partial

### Curatorial humano-on-loop

- LLM assiste (extraction, classification, scoring)
- Decisão final **sempre humana**
- Nada é auto-promovido ao catálogo

### Auditabilidade um-clique

- Provenance trails auto-gerados ([`docs/provenance/`](https://github.com/freirelucas/rio-edu-lab/tree/main/docs/provenance))
- Chat → GitHub issue audit (via `analysis/61_session_to_issue.py`)
- Drift checks no CI (15+ gates)
- Algedônico alert se invariante crítica quebrar

## Comunidade no ecosystem

Repos peer que valem conhecer (mais em [`docs/dados.md`](dados.md)):

- **[prefeitura-rio/pipelines](https://github.com/prefeitura-rio/pipelines)** — engenharia oficial do data.rio
- **[basedosdados/pipelines](https://github.com/basedosdados/pipelines)** — canônico BR de dados abertos
- **[Mcp-Brasil/mcp-brasil](https://github.com/Mcp-Brasil/mcp-brasil)** — MCP server INEP/SAEB
- **[UFPB-Squad-Team/odin-api](https://github.com/UFPB-Squad-Team/odin-api)** — paralelo conceitual ao rio-edu-lab pra outras cidades

## Contato

- Lucas Freire (`@freirelucas`) — `lucasfreire@gmail.com`
- Issues + PRs são preferidos a email pra trabalho público
- Email ok pra colaboração privada / proposal acadêmico

---

_Este documento segue [`CONTRIBUTING.md` convention](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors). Versionado em `docs/contribuir.md` + symlink `CONTRIBUTING.md` na raiz._
