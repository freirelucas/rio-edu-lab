---
name: 🐛 Reportar problema (dado, código, ou análise)
about: Algo está errado num replicado, ou um item do data.rio mudou? Documenta aqui.
title: "[bug] <componente> — descrição curta"
labels: ["bug", "needs-triage"]
assignees: []
---

## Tipo do problema

- [ ] Erro de cálculo em paper replicado
- [ ] Dado do data.rio quebrou (404, schema mudou, valores estranhos)
- [ ] Provenance hash não bate
- [ ] Bug em script `analysis/NN_*.py`
- [ ] Drift check no CI falhou mas não sei por quê
- [ ] Outro

## Onde

<!-- Caminho específico: paper_id, script, arquivo, URL data.rio... -->

## Como reproduzir

```bash
# Comandos pra reproduzir o bug
```

## Esperado vs observado

**Esperado:**

**Observado:**

## Ambiente

- Sistema operacional:
- Python version:
- Branch / commit:

## Logs / output

<details>
<summary>Click pra expandir</summary>

```
(cole logs aqui)
```

</details>

---

**Pra curador:** triagem rápida:
- Bug crítico (achado quebrou) → label `priority:critical` + close imediato algedônico (issue auto via `.github/workflows/algedonic-alert.yml`)
- Bug dado externo (data.rio) → label `external-dep` + abrir issue downstream se aplicável
- Bug código → label `bug` + PR direto preferível
