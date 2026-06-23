---
name: 💡 Sugerir nova fonte de papers
about: O funil vai além OpenAlex. SciELO, Crossref, HF Papers, repositórios institucionais — sugira aqui.
title: "[source] <nome da fonte>"
labels: ["enhancement", "discovery-source"]
assignees: []
---

## Fonte

- **Nome**:
- **URL principal**:
- **API/SDK disponível?**: (sim/não, link pra docs)
- **Licença dos metadados**:
- **Cobertura estimada de papers de política pública educacional**:

## Por quê adicionar

<!-- Que gap preenche? Hoje temos OpenAlex (250M) + Semantic Scholar.
     Sua fonte traz o que esses não trazem? -->

## Custos

- **Auth requerida?** (API key, email, etc.)
- **Rate limit conhecido**:
- **Custo monetário** (se aplicável):

## Schema mapping

<!-- Que campos da sua fonte mapeiam pra: openalex_id, doi, title, abstract,
     citations, year, referenced_works, type? Ou tem campos novos relevantes? -->

## Já existe adapter no lab?

<!-- Check `analysis/_*.py` — adapters atuais: _openalex, _semanticscholar,
     _github, _anthropic, _rio. -->

---

**Pra curador:** se aprovado, segue padrão `analysis/_<source>.py` espelhando
shape de `_openalex.py` (cache filesystem TTL 30d, polite throttle, retry
backoff exponencial). Inclui tests mockados.
