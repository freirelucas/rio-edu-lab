# TOP Guidelines Scorecard

Auto-gerado por `analysis/60_top_scorecard.py` a partir de `data/papers_catalog.yml`.

**TOP Guidelines** (Center for Open Science) define 8 padrões de transparência, cada um em 4 níveis:

- **0** — Not implemented
- **1** — Disclosed (declarado)
- **2** — Required (dados/código compartilhados + citados)
- **3** — Verified (replicação independente confirmou)

Score do rio-edu-lab por paper:

| paper | status | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | total | % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pereira-2019-ipea | partial | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 1 | 11 | 68% |
| reardon-2011-whither | partial | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 1 | 11 | 68% |
| theil-1967-economics | full | 1 | 2 | 2 | 1 | 2 | 1 | 1 | 2 | 12 | 75% |
| soares-andrade-2006 | pending | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| alves-soares-2013 | pending | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| coleman-1966-eeo | pending | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| hanushek-1986-jel | pending | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| reardon-owens-2014 | pending | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| becker-1964-human-capital | unfeasible | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| cunha-heckman-2007 | unfeasible | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| hoxby-2000-aer | pending | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| card-krueger-1992-jpe | unfeasible | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 3 | 18% |
| coleman-1982-high | pending | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 12% |
| dupriez-2006-inequalities | pending | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 18% |
| schwartz-2011-housing | pending | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 12% |

## Legenda dos standards

- **S1** — Citation Standards
- **S2** — Data Transparency
- **S3** — Code Transparency
- **S4** — Materials Transparency
- **S5** — Design + Analysis Transparency
- **S6** — Study Preregistration
- **S7** — Analysis Plan Preregistration
- **S8** — Replication

## Heurísticas de scoring

Veja docstring em `analysis/60_top_scorecard.py` pra fórmulas exatas. Em resumo:

- S1 (Citation): DOI + OpenAlex ID populados
- S2 (Data): `data_availability_statement.summary == public` + sources[]
- S3 (Code): `scripts[]` + replication_status ∈ {full, partial}
- S4 (Materials): `report_ids[]` populated (mini-pages renderizados)
- S5 (Design+Analysis): data_requirements + method + controlled_randomness declarados
- S6 (Study Prereg): cap em 1 pra retrospective replications (impossível pre-registrar paper já publicado)
- S7 (Analysis Plan): `preregistration.osf_url` populated
- S8 (Replication): full=2, partial=1

**Total possível**: 8 standards × 2 levels = 16
