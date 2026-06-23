---
name: 📚 Sugerir paper pro catálogo
about: Conhece um paper de política pública educacional que deveria estar no rio-edu-lab? Use este template.
title: "[paper] Autor Ano — Título resumido"
labels: ["paper-suggestion", "needs-curation"]
assignees: []
---

## Paper

- **Título completo**:
- **Autores**:
- **Ano**:
- **DOI ou URL canônico**:
- **OpenAlex ID** (se souber, formato `W123...`):

## Por quê este paper

<!-- 1-2 parágrafos. Onde o método é canônico? Quem cita? -->

## Dados necessários (best guess)

<!-- O que o método precisaria pra rodar? Lista informal. Exemplos:
     - desempenho por escola (tipo IDEB)
     - SES por bairro
     - geometria de escolas
     - série temporal de matrículas
     - ...
     Não precisa ser exato — o pipeline mapeia depois contra a taxonomy.
-->

## Aplicabilidade ao Rio

<!-- O método rodaria contra os 9.855 itens do data.rio? Tem item óbvio? -->

## Já tem implementação pública?

<!-- Link pra repo se conhecer. Ex:
     - GitHub: ...
     - Zenodo: ...
     - CRAN/PyPI: ...
-->

---

**Pra curador (Lucas):** Decisão de promoção segue critérios em [`docs/qualidade.md`](https://freirelucas.github.io/rio-edu-lab/qualidade/) + score automático via `analysis/65_curatorial_inbox.py`. Não há SLA prometido; PR direto com a entrada do catálogo acelera.
