---
name: vsm-s3-allocator
description: Enforce quality gates and resource budgets. Maps to VSM System 3 — Operational Management (inside-and-now control). Use before merging to main, before running expensive LLM extraction, or when ensuring invariants hold. Runs pytest, ruff, mkdocs strict, schema validation, and enforces token/budget caps.
---

# VSM S3 Allocator — gates de qualidade + resource bargain

Skill que reproduz o **canal S3**: regula o presente operacional. Aloca recursos (compute, tokens, tempo) e enforce regras (testes, lint, schema).

## Quando invocar

- Antes de `git commit` em main
- Antes de rodar batch LLM extraction (49 com `--limit` grande, 55 com `--all`)
- Suspeita de regressão (teste verde mas comportamento mudou)
- Quando user pede "está tudo verde?"

## Gates obrigatórios

Executar **em paralelo quando possível**:

1. **pytest** (296 testes esperados):
   ```bash
   python3 -m pytest tests/ -q --ignore=tests/test_pereira_simple.py
   ```
   Critério: 100% verde. Falha → investigar imediatamente.

2. **ruff check** (lint):
   ```bash
   python3 -m ruff check analysis/ tests/
   ```
   Hoje warn-only no CI; tighten em v0.17. Mas reportar erros mesmo assim.

3. **mkdocs build --strict** (docs sintaxe + links):
   ```bash
   python3 -m mkdocs build --strict
   ```
   Critério: zero warnings.

4. **Schema validation**:
   ```bash
   python3 analysis/31_build_paper_catalog.py --validate-funnel
   ```
   Critério: zero invalid entries.

5. **Theil invariants** (replication safeguard):
   - `acec.stats.theil_decompose` deve obedecer t = tb + tw exato
   - `share_within ∈ [0.59, 0.73]` (range narrativo)

## Resource bargain (a documentar v0.17)

Env vars que limitam consumo por stage:

- `MAX_TOKENS_PER_PAPER` — cap de tokens LLM por paper extraction (sugestão: 4000 in + 1000 out)
- `MAX_LLM_BUDGET_USD` — cap diário de custo LLM (sugestão: $5)
- `MAX_SNOWBALL_DEPTH` — cap de profundidade (default já está em `--depth 2`)
- `MAX_NEW_CANDIDATES` — cap por run de snowball (default 1500)

Sem estes vars, batch grande pode escapar do controle. Skill alerta se ausentes.

## Critério de sucesso

Todos gates verdes + resource budgets respeitados.

## Falha → ação

- pytest falha: rode `pytest -v <test_arquivo>` pra detalhe, investigue regressão
- ruff falha: rode `python3 -m ruff check --fix` pra auto-fix
- mkdocs falha: investigue link quebrado ou syntax error
- schema falha: artefato YAML inválido, identifique entrada problemática

## Outputs

- Tabela: gate | status | tempo | observação
- Resumo: pronto pra merge? ✓/✗
- Próximo passo se falhou
