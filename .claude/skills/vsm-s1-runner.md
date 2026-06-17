---
name: vsm-s1-runner
description: Execute a single Stage 1-3 pipeline operation (Discovery, Match, Coverage, Curation, Replication, Hotsite, LLM extraction) with explicit input/output contract. Maps to VSM System 1 — Operations. Use when running 45_bulk_discover, 46_extract_requirements, 47_check_coverage, 48_promote_funnel, 49b_apply_codebook_overrides, 45c_apply_code_signals, or any numbered analysis script. Verifies inputs exist, idempotency, and writes back to canonical YAML.
---

# VSM S1 Runner — execute uma operação do pipeline

Skill que reproduz o **contrato explícito de input/output** pra cada sub-unidade S1 do rio-edu-lab. Atua como "S1 viable system aninhado": cada stage é por si só um VSM completo (recursivo), com seus próprios input/state/output.

## Quando invocar

- Usuário diz "rode o snowball" / "rode 46" / "atualize coverage" / "promova candidate X ao catálogo"
- Necessidade de re-rodar Stage 2 ou 3 após mudança de match/`code_book`
- Necessidade de rodar análise Stage 4 (Theil, Pereira, VULN-EDU, etc.) end-to-end

## Contrato por sub-unidade

| S1 | Script | Input (artefatos) | Output (artefatos) | Idempotente? |
|---|---|---|---|---|
| S1.a Discovery | `45_bulk_discover.py` | `openalex_seeds.yml` + cache | `papers_funnel.yml` (cresce) | sim (`--refresh` força) |
| S1.b Match | `46_extract_requirements.py` | funil + `requirements_taxonomy.yml` | funil (`+suggested_requirements`) | sim (`--force`) |
| S1.c Coverage | `47_check_coverage.py` | funil + `manifest.json` | funil (`+coverage[]` + `match_detail`) | sim (`--force`) |
| S1.d Curation | `48_promote_funnel.py` | funil | `papers_catalog.yml` | sim |
| S1.e Replication | `10-37_*.py` | catálogo + raw data | `data/processed/*.csv`, `docs/reports/*.md` | sim (cache) |
| S1.f Hotsite | `mkdocs build --strict` | `docs/**`, charts | `site/**` | sim |
| S1.g LLM ext | `49_codebook_backfill.py`, `55_*` | manifest/funil + LLM | funnel (`+llm_*`) ou manifest (`+code_book`) | sim (cache) |
| S1.h Audit (futuro) | `60_session_to_issue.py` | `~/.claude/projects/*.jsonl` | GitHub issue | sim |

## Pré-condições obrigatórias

Antes de executar:
1. **Verificar dependências** — não rodar 47 sem rodar 46 antes; não rodar 48 sem 46+47
2. **Working tree clean** se for batch run (commit pendente?)
3. **Cache válido** — se `--no-cache` ou `--refresh`, avisar custo (API calls)

## Execução

1. `git status --short` (alertar se uncommitted)
2. Rodar o script com flags apropriadas
3. Verificar exit code = 0
4. Diff de artefato (`git diff --stat data/papers_funnel.yml`) pra confirmar mudança
5. Rodar drift renderers downstream se relevante (25, 41, 51, 56)
6. NÃO commitar automaticamente — usuário decide

## Padrões a respeitar

- **Backward-compat**: se modificar schema YAML, manter campos antigos
- **Idempotência primeiro**: 2ª chamada deve ser noop (test esperado)
- **Drift checks**: re-rodar 25/51/56/41 quando funil mudar; checar nada commitable além das mudanças intencionais

## Outputs esperados ao usuário

- Resumo do diff (n candidates mudados, deltas)
- Próximo passo sugerido (drift, commit)
- Custo se LLM extraction envolvida (~$0.001/paper Claude Haiku)
