---
title: "Qualidade do match"
description: "Precision/recall por categoria + confusion matrix sobre gold-set de ~50 pairs etiquetados à mão."
---

# Qualidade do match (paper → categoria)

_Relatório gerado por `analysis/51_match_quality_report.py` sobre `data/match_quality_gold.yml` (sample do funnel commit `1eda168b8f11`)._

## Cobertura do labeling

- **Total de labels no sample:** 50
- **Decididos (correct + wrong):** 0
- **Corretos:** 0
- **Errados:** 0
- **Unsure:** 0 (0% — needs-second-opinion)
- **Não preenchidos:** 50


!!! note
    Nenhum label decidido ainda — preencha `is_correct` em `data/match_quality_gold.yml` (true/false/"unsure") e rerode `python3 analysis/51_match_quality_report.py`.
