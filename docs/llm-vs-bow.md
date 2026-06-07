---
title: "LLM vs bag-of-words: comparação"
description: "Agreement, disagreement e taxonomy-gap rate entre o IDF lexical (v2) e o LLM extraction (v3) sobre o mesmo funil."
---

# LLM (v3) vs bag-of-words IDF (v2) — comparação

_Gerado por `analysis/56_llm_vs_bow_compare.py` sobre os candidatos do funil que têm ambos os signals (bow do `46` e llm do `55`)._

## Cobertura

- **Total no funil:** 2080
- **Com bow signal:** 394
- **Com llm signal:** 0
- **Com ambos (= sample da comparação):** 0

!!! note
    Nenhum candidate tem ambos signals ainda. Rode `55_llm_extract_requirements.py` pra popular llm_* em alguns candidates, depois re-rode este script.
