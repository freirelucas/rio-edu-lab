---
name: vsm-s3star-auditor
description: Sporadic audit independent of routine reports. Maps to VSM System 3* — Audit (vertical channel that verifies ground truth, bypassing System 2 routine reporting). Use to detect silent drift between stages, validate idempotency under cold cache, sample-recompute matching/coverage, or spot-check LLM extraction quality. NOT a regular CI gate — invoke sporadically when trust in pipeline output is in question.
---

# VSM S3* Auditor — auditoria esporádica

Skill que reproduz o **canal vertical S3* do VSM**: auditoria não-roteirizada, independente dos relatórios de rotina (drift checks no CI, pytest). Existe pra detectar **drift silencioso** — quando tudo passa mas a realidade no chão divergiu.

## Quando invocar

- Suspeita de drift silencioso (drift checks passando mas resultado parece estranho)
- Após mudança grande em `_match.py` ou `47_check_coverage.py`
- Antes de release v0.X.0 — auditoria final
- User pede "confirme que isso está certo"
- 1× por mês como rotina (não diária — auditoria é esporádica por design)

## Procedure (cold-cache + random sample)

### 1. Cold cache recompute

```bash
# Snapshot do estado atual
git stash
# Limpar cache forçar re-fetch
mv data/cache /tmp/cache_backup_$(date +%s)
mkdir data/cache
# Re-rodar Stage 2-3 com force
python3 analysis/46_extract_requirements.py --force
python3 analysis/47_check_coverage.py --force
# Diff vs snapshot
git diff --stat data/papers_funnel.yml
git stash pop
```

**Esperado**: zero diff se pipeline determinístico. Diff inesperado → investigar.

### 2. Sample random recompute

```bash
# 20 candidates random (seed fixo pra reprodutibilidade)
python3 -c "
import yaml, random
random.seed(42)
c = yaml.safe_load(open('data/papers_funnel.yml'))['candidates']
sample = random.sample(c, 20)
for p in sample:
    print(p['openalex_id'], p['title'][:60])
"
```

Inspecionar manualmente: o match_detail composite faz sentido? O suggested_requirements top-1 está correto? O coverage status é honesto?

### 3. LLM sampling (se aplicável)

Se v3 LLM extraction tiver sido populado em ≥ 50 candidates:

```bash
python3 analysis/56_llm_vs_bow_compare.py
```

Inspecionar `data/processed/llm_vs_bow_comparison.json`:
- Agreement rate ≥ 70%? Se < 50%, IDF ou LLM está errado
- Disagreement examples — qual está certo na sua leitura?
- Taxonomy gap rate ≤ 5%? Se > 10%, taxonomy precisa expansão

### 4. Gold-set spot check

```bash
# Re-run match-quality report
python3 analysis/51_match_quality_report.py
```

Se ≥ 30 labels decididos:
- Precision per category: razoável (≥ 0.7)?
- Recall per category: razoável (≥ 0.5)?
- Categorias com baixa precision → próxima rodada de melhoria

### 5. Bootstrap Theil regression

```bash
python3 analysis/35_bootstrap_theil_ci.py
git diff data/processed/theil_bootstrap_ci.csv
```

Determinístico (seed=42). **Qualquer diff = bug em `acec.stats.theil_decompose`**.

## Critério de sucesso

- Cold cache recompute: zero drift inesperado
- Sample 20 candidates: inspeção visual aprova
- Bootstrap Theil: byte-equal
- Se LLM populado: agreement ≥ 70%, gap ≤ 5%

## Falha → ação

- Drift silencioso: investigar fonte (cache poisoned? schema migration? ordem de operações?)
- Sample errado: revisar `_match.py` ou taxonomy
- Bootstrap diff: bug em primitiva acec

## Outputs

- Relatório markdown salvo em `data/processed/audit_<date>.md`
- Lista de discrepâncias encontradas
- Recomendação: status pipeline (verde / amarelo / vermelho)

## NÃO fazer

- Rodar diariamente — é S3*, não S3. Esporádico por design.
- Substituir drift checks no CI — esses são S2 (anti-oscilação rotineira).
