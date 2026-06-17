---
name: vsm-s2-coordinator
description: Detect schema collisions, drift, or stale state between pipeline stages. Maps to VSM System 2 — Coordination (anti-oscillation). Use when artifacts may have diverged (funnel after manual edit, manifest after refresh, catalog after promotion), before commit/push, or when CI drift check fails. Runs all drift renderers (25, 41, 51, 56) and reports inconsistencies.
---

# VSM S2 Coordinator — anti-oscilação entre stages

Skill que reproduz o **canal S2 do VSM**: evita que sub-unidades S1 (discovery, match, coverage, curation, hotsite) entrem em conflito quando compartilham recursos (YAML state, cache, manifest, charts).

## Quando invocar

- Antes de `git commit` quando mudou um artefato YAML
- Após editar manualmente `data/manifest.json`, `data/papers_funnel.yml`, `data/papers_catalog.yml`
- CI falhou em drift check
- Suspeita de divergência entre funil + landing page numbers

## Checks coordenados

Executar **EM ORDEM** (cada um depende do anterior):

1. **Funnel state** (`analysis/25_funnel_state.py`):
   - Recompute big-nums em `docs/index.md`
   - Recompute `docs/_assets/charts/funnel.json`, `themes.json`, `data_rio_coverage.json`
   - Recompute `data/processed/funnel_state.json`

2. **Papers ↔ data.rio reverse link** (`analysis/41_match_requirements.py`):
   - Recompute `docs/papers-by-data-rio.md`

3. **Match quality report** (`analysis/51_match_quality_report.py`):
   - Recompute `data/processed/match_quality_summary.json` + `docs/match-quality.md`

4. **LLM vs BoW comparison** (`analysis/56_llm_vs_bow_compare.py`):
   - Recompute `data/processed/llm_vs_bow_comparison.json` + `docs/llm-vs-bow.md`

5. **Theil bootstrap CI** (`analysis/35_bootstrap_theil_ci.py`):
   - Determinístico (seed=42 fixo + year offset)
   - Recompute `data/processed/theil_bootstrap_ci.csv`

6. **mkdocs build --strict**:
   - Confirma sem links quebrados, sem warnings

7. **`git diff --stat`** final:
   - Lista artefatos modificados
   - Distinguir intencional (mudança esperada) vs drift (precisa investigar)

## Critério de sucesso

- Todos drift renderers exit 0
- `mkdocs build --strict` exit 0
- Diff só contém: artefato editado pelo usuário + drift renderers downstream esperados
- **Inesperado** = parar e investigar antes de commitar

## Lacunas conhecidas (não cobertas)

- **Schema registry**: não há JSON Schema validation entre stages. Apenas runtime checks via pytest.
- **Resource bargain explícito** (S3 também): tokens/compute por stage não tem cap.

## Outputs

- ✓ Verde se tudo passar
- ✗ Lista de drifts inesperados com path:linha
- Sugestão: re-rodar Stage X se artefato Y mudou
