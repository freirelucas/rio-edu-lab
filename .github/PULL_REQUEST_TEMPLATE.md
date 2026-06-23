<!-- Obrigado por contribuir pro rio-edu-lab! 🎉 -->

## O que muda

<!-- 1-3 frases. Tipo: "Adiciona paper X ao catálogo + replica método Y" ou
     "Fix bug Z em _match.py" ou "Atualiza taxonomy categoria W". -->

## Tipo

- [ ] 📚 Novo paper no catálogo
- [ ] 🔬 Replicação (paper status pending → full|partial)
- [ ] 🐛 Bug fix
- [ ] 📊 Nova análise/produto
- [ ] 🏗️ Mudança arquitetural (atinge skills VSM)
- [ ] 📖 Documentação
- [ ] ⚙️ Infra (CI, drift checks, tooling)

## Checklist obrigatório

- [ ] Drift renderers rodaram: `25, 41, 51, 56` se mudou funnel; `32, 41` se mudou catalog; `60, 63, 64` se mudou produto
- [ ] `pytest tests/` verde
- [ ] `mkdocs build --strict` verde
- [ ] `ruff check analysis/ tests/` sem novos errors
- [ ] Schema YAML backward-compat (nenhum campo removido)
- [ ] Se LLM usado: `MAX_LLM_BUDGET_USD` respeitado (custo declarado abaixo)

## Checklist replicação (se aplicável)

- [ ] `data_availability_statement` populado no catalog entry
- [ ] `provenance` (data manifest hash + code commit + replication date + replicator)
- [ ] `controlled_randomness` (seeds usados, ou `[]` se determinístico)
- [ ] `runtime` estimado
- [ ] TOP scorecard re-rodado (`python3 analysis/60_top_scorecard.py`)
- [ ] Provenance trail re-rodado (`python3 analysis/63_provenance_trail.py`)
- [ ] Issue de claim referenciada (`closes #XXX`)

## Custo LLM (se aplicável)

```
Provider: anthropic|rio
Tokens: X input / Y output
Cost: $Z.ZZ USD
```

## Como verificar localmente

```bash
# Comandos pra reviewer rodar e validar
```

---

🤖 _PR template versionado em `.github/PULL_REQUEST_TEMPLATE.md`. Sugestões de melhoria via issue `[enhancement]`._
