# AGENTS.md — guidance pra AI agents no rio-edu-lab

Este arquivo segue a [convenção AGENTS.md](https://agents.md/) ([Linux Foundation Agentic AI track](https://agents.md/)) — instruções declarativas pra AI agents (Claude Code, OpenAI Codex, Cursor, Aider, Google Jules, GitHub Copilot agent, Cline, Devin, JetBrains Junie, Windsurf, etc.) operando neste repositório.

`CLAUDE.md` é symlink pra `AGENTS.md` — convention para cross-vendor compat.

## Visão de 30 segundos

**rio-edu-lab** é um pipeline aberto de identificação de papers sobre política pública educacional → match contra os 9.855 itens do data.rio (Instituto Pereira Passos, Rio de Janeiro) → replicação reproduzível com transparência total.

**Missão** (de `docs/sobre.md`): traduzir academia gringa pra dado brasileiro com auditabilidade um-clique. Catálogo é Rio-edu-foco; funil v0.15+ absorve public policy + economics global.

**Arquitetura** (de `docs/arquitetura.md`): Viable System Model (Stafford Beer). Veja skills VSM em `.claude/skills/vsm-*.md`.

## Como rodar

### Pipeline básico (Stage 1-3)

```bash
# Discovery (snowball OpenAlex; precisa OPENALEX_EMAIL)
OPENALEX_EMAIL=lucasfreire@gmail.com python3 analysis/45_bulk_discover.py --depth 1

# Stage 2 — filter + IDF + code_book scoring
python3 analysis/46_extract_requirements.py --force

# Stage 3 — coverage data.rio + match_detail composite
python3 analysis/47_check_coverage.py --force

# Drift renderers (rode SEMPRE após mudança em funil)
python3 analysis/25_funnel_state.py
python3 analysis/41_match_requirements.py
python3 analysis/51_match_quality_report.py
python3 analysis/56_llm_vs_bow_compare.py
```

### Testes

```bash
# Full suite (296 tests esperados)
python3 -m pytest tests/ -q --ignore=tests/test_pereira_simple.py

# Linting (warn-only no CI; tighten v0.17)
python3 -m ruff check analysis/ tests/

# Docs (deve ser estrito)
python3 -m mkdocs build --strict
```

### LLM extraction (opt-in)

Default provider é Anthropic Claude Haiku 4.5 via `_anthropic.py`. Migração Path D pra Rio-3.5-Open-397B preparada via `_rio.py` + dispatcher `_llm.py`:

```bash
# Anthropic (default)
ANTHROPIC_API_KEY=sk-... python3 analysis/55_llm_extract_requirements.py --limit 10

# Rio-3.5 (quando endpoint disponível)
LLM_PROVIDER=rio RIO_API_BASE=https://<endpoint>/v1 RIO_API_KEY=hf_... \
    python3 analysis/55_llm_extract_requirements.py --limit 10

# Ollama local (default RIO_API_BASE=http://localhost:11434/v1)
LLM_PROVIDER=rio python3 analysis/55_llm_extract_requirements.py --limit 10
```

## Padrões de código

### Stack

- **Python 3.10+** (3.12 testado em CI; 3.10/3.11 alegado backward-compat)
- **Stdlib + opt-in deps**: `requirements.txt` mínimo (PyYAML, geopandas, plotly, mkdocs-material). Anthropic SDK e `requests` são opt-in.
- **YAML como state** — funnel, catalog, manifest. Idempotent appliers (`49b`, `45c`) merge into.
- **Filesystem cache por ID** — `data/cache/*/` gitignored, TTL 30d.
- **Drift checks no CI** — 11 hoje. Re-render + `git diff --quiet`. Falha em drift = curador precisa rodar generator.

### Naming

- **Scripts numerados**: `01_*.py` a `60_*.py` em `analysis/`. Convenção:
  - `01-09` setup / inventory
  - `10-37` análises Stage 4 (replicações vivas: Theil, Pereira, VULN-EDU, FUN-Rio, etc.)
  - `40-49` Stage 1-2 discovery + matching
  - `50-56` Stage 3 quality + LLM
  - `60+` audit trail (v0.16+)
- **Underscore prefix**: `_match.py`, `_openalex.py`, `_rio.py`, `_llm.py` → adapters/helpers, não rodam como entry-point
- **Testes**: `tests/test_<module>.py` espelhando `analysis/`

### Convenções

- **Idempotência primeiro**: 2ª chamada deve ser noop. Tests obrigatórios.
- **Backward-compat de schema YAML**: NUNCA remover campo existente. Adicionar é OK.
- **Drift renderer downstream**: SE mudou funnel → rode `25, 41, 51, 56`. SE mudou catalog → rode `32, 41`. SE mudou code → rode pytest + mkdocs.
- **Cache invalidation**: `--refresh` ou `--force` flag respeitado. NÃO mute cache silenciosamente.

## Segurança

### NEVER

- Commitar `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `OPENALEX_EMAIL` em código
- Reescrever histórico em `main`
- `git push --force` em main
- Removerl drift check sem PR + review

### ALWAYS

- Rodar `gitleaks pre-commit` antes de commitar chat trail (v0.17+)
- Redatar absolute paths (`/home/user/...` → `~/`) em chat trails publicados
- Filtrar tool results > 5KB no audit trail
- Respeitar `cleanupPeriodDays` pra `~/.claude/projects/*.jsonl`
- LGPD: dados de população (alunos, escolas) já vêm agregados do IPP — não desanonimizar

## Skills do Claude Code

6 skills VSM-mapeadas em `.claude/skills/`:

- **`vsm-s1-runner`** — executa stage com contrato I/O explícito
- **`vsm-s2-coordinator`** — anti-oscilação entre stages, rode antes de commit
- **`vsm-s3-allocator`** — gates de qualidade + resource budget
- **`vsm-s3star-auditor`** — auditoria esporádica (cold cache, sample, drift silent)
- **`vsm-s4-scout`** — varredura ambiente externo (seeds, modelos, items data.rio)
- **`vsm-s5-constitution`** — identidade + ethos arbitration

Veja `docs/arquitetura.md` pra contexto VSM completo.

## Comunidade no ecosystem

Repos peer que valem linkar (mais em `docs/dados.md`):

- **[prefeitura-rio/pipelines](https://github.com/prefeitura-rio/pipelines)** — engenharia oficial do data.rio
- **[basedosdados/pipelines](https://github.com/basedosdados/pipelines)** — canônico BR
- **[Mcp-Brasil/mcp-brasil](https://github.com/Mcp-Brasil/mcp-brasil)** — MCP server INEP/SAEB
- **[r5py/r5py](https://github.com/r5py/r5py)** — stack Pereira accessibility
- **[cran/OasisR](https://github.com/cran/OasisR)** — Reardon ordinal segregation R package

Peer de **agentic tooling / agent-harness** (estudo em [`docs/aprende-com-affaan.md`](docs/aprende-com-affaan.md)):

- **[affaan-m/ECC](https://github.com/affaan-m/ECC)** — agent harness OS pro Claude Code (rules/skills/agents/hooks/instincts)
- **[affaan-m/agentshield](https://github.com/affaan-m/agentshield)** — static analyzer de config de agente (secrets/perms/hooks/MCP) → A1 do scout
- **[affaan-m/claude-swarm](https://github.com/affaan-m/claude-swarm)** — orquestração multi-agente (grafo de deps + file locking + budget)

## Contato

- Author: Lucas Freire (`@freirelucas` no GitHub) — `lucasfreire@gmail.com`
- License: MIT (código) + CC-BY-4.0 (dados derivados)
- DOI: [10.5281/zenodo.20060620](https://doi.org/10.5281/zenodo.20060620)
- Lab site: https://freirelucas.github.io/rio-edu-lab/

## Pra AI agents (instruções declarativas)

1. **Antes de mudar**: leia `docs/arquitetura.md` + `docs/sobre.md`. Entenda o VSM mapping.
2. **Pequenas mudanças**: PR direto, drift renderers rodados, testes verdes.
3. **Mudanças grandes (novo adapter, nova stage)**: invoque skill `vsm-s5-constitution` antes; documente em `docs/arquitetura.md`.
4. **Decisões curatoriais** (promover paper, incluir seed): humano decide, AI sugere. Nunca auto-promover.
5. **LLM cost-guard**: respeite `--dry-run` mode, `--limit` cap. NUNCA disparar `--all` sem confirmação humana.
6. **Sessions JSONL**: pode ser exportado pra issue audit trail (futuro `analysis/60_session_to_issue.py`). Redação obrigatória.
