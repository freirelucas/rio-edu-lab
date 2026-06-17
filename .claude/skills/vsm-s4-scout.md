---
name: vsm-s4-scout
description: Scan external environment for new papers, methods, datasets, models, venues. Maps to VSM System 4 — Intelligence (outside-and-then). Use to find new seeds for snowball expansion, scan academic venues for relevant papers, detect new model releases (Rio-3.5 endpoint availability), audit data.rio for new items, monitor community ecosystem (basedosdados, prefeitura-rio, UFPB). Returns prioritized list of additions for human review.
---

# VSM S4 Scout — varredura do ambiente externo

Skill que reproduz o **canal S4 do VSM**: olha pra fora e pro futuro. Identifica oportunidades de expansão (seeds novos, métodos canônicos, modelos novos, items data.rio recém-publicados).

## Quando invocar

- 1× por mês como rotina
- Após anúncio público (modelo novo, dataset novo, venue novo)
- Antes de release maior (v0.16, v0.17, etc.) pra atualizar landscape
- User pede "tem alguma coisa nova que devíamos olhar?"

## Scan checklist

### 1. Seeds candidatos (OpenAlex)

```bash
# Top papers recentes em educação + policy
# (via OpenAlex API ou Semantic Scholar)
```

Buscar:
- Papers > 100 cit publicados nos últimos 2 anos
- Filtrar por filter: edu OR policy keywords
- Não-já-em `openalex_seeds.yml`
- Reportar top 10 por (citações × FWCI)

### 2. Venue scan

Venues acadêmicos pra monitorar:
- **AEA RCT Registry** (socialscienceregistry.org) — pre-registrations novos
- **NBER Working Papers** (nber.org/papers) — pre-prints econ
- **IZA Discussion Papers** (iza.org) — labor + edu
- **IPEA Textos para Discussão** (ipea.gov.br) — BR policy
- **AEA Papers and Proceedings** — annual
- **Journal of Public Economics**
- **Economics of Education Review**
- **AEJ Applied** + **AEJ Policy**
- **AERA Open** — education methodology
- **SciELO Education BR**

Pra cada venue: tem RSS/atom feed? Quanto sai por mês? Filtros por temática?

### 3. Modelos LLM disponíveis

- **Rio-3.5-Open-397B** — HF Inference Endpoint deploy? 19 requests pending — STATUS?
- **Qualquer quant do Rio-3.5** publicado por comunidade no HF?
- **Provedores comerciais** hospedam Rio-3.5? (Together / Replicate / Modal / Fireworks / Groq)
- **Modelos PT-BR nativos novos** com tool calling?
- **Claude updates** (Haiku 5? Sonnet 5?)

Reportar: status, custo estimado, esforço migração.

### 4. data.rio novos items

```bash
# Re-fetch manifest e diff
python3 analysis/00_fetch_manifest.py  # se existir, OU manualmente
diff data/manifest.json data/manifest.json.previous
```

Reportar: items adicionados (foco em tags edu), items removidos, items modificados.

### 5. Community ecosystem

Repos pra monitorar (já documentados em `docs/dados.md` seção "Comunidade no GitHub"):
- `prefeitura-rio/pipelines` — releases novos?
- `basedosdados/pipelines` — datasets edu novos?
- `Mcp-Brasil/mcp-brasil` — INEP/SAEB updates?
- `UFPB-Squad-Team/odin-api` — features novas?
- `r5py/r5py` — versão nova relevante pra Pereira?
- `cran/OasisR` — atualizações Reardon ordinal segregation?

### 6. Padrões emergentes

Buscar em arXiv / Twitter / Hacker News / r/MachineLearning:
- Novos métodos de matching paper↔dados/código
- Open science standards updates (FAIR/TRUST/TOP novos)
- AEA Data Editor template updates
- Anthropic / Claude Code novidades (skills, hooks, MCP)
- VSM applications novas em ciência aberta

## Output esperado

Relatório `data/processed/scout_<date>.md` com seções:
- 5 seeds candidatos top
- 3 venues com novidade
- Status modelos LLM
- Items data.rio novos (delta)
- 3 updates de community ecosystem
- 2 padrões emergentes notáveis

Cada item com:
- Esforço de adoção (baixo/médio/alto)
- Risco
- Recomendação (incluir / parquear / ignorar)

## Critério de sucesso

Curador (Lucas) revisa e decide quais virar PR. Skill NÃO promove automaticamente — é S4 (intelligence), não S1 (execução).

## Lacuna conhecida

Hoje scout é manual + reativo. Em v0.18, automatizar via GitHub Actions com cron mensal que abre issue com relatório.
