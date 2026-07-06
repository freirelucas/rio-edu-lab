---
title: 🛰️ Sala de Operação
description: Estado vivo da corporação cibernética do rio-edu-lab — funil, órgãos autônomos, fila curatorial, transparência e auditabilidade. Pública por design (transparência ativa).
---

# 🛰️ Sala de Operação

> **Cybersyn moderno.** Esta tela mostra o estado vivo da [corporação cibernética](corporacao.md). É **pública por design** — transparência ativa é a missão. O *controle* (aprovar, pausar, disparar) acontece no GitHub, que já autentica você.

!!! info "Observar vs. Agir"
    **Observar** (todos, aqui): ver o estado. · **Agir** (só o curador, no GitHub): mergear PR = aprovar · desabilitar workflow = pausar · `workflow_dispatch` = disparar. O login do GitHub já é o gate de controle.

## 📊 Funil de descoberta

<div class="grid cards" markdown>

- :material-magnify:{ .lg .middle } __2266__ candidates descobertos
- :material-filter:{ .lg .middle } __482__ com requisitos (Stage 2)
- :material-book-open-variant:{ .lg .middle } __18__ no catálogo
- :material-check-decagram:{ .lg .middle } __1 full · 2 partial__ replicados end-to-end

</div>

**data.rio**: 4 itens ativos · 9851 órfãos · 9855 total.

<div data-chart="_assets/charts/funnel.json"></div>

## 🫀 Órgãos da corporação

Status **ao vivo** (badges nativos do GitHub Actions — sempre atuais):

| Órgão | VSM | Função | Cadência | Status ao vivo |
|---|:--:|---|---|---|
| `ci.yml` | S2 | Coordenação — drift checks anti-oscilação | cada push | [![status](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/ci.yml) |
| `pages.yml` | S1.f | Hotsite — deploy do site | cada push | [![status](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/pages.yml) |
| `algedonic-alert.yml` | — | Canal algedônico — emergência | CI falha | [![status](https://github.com/freirelucas/rio-edu-lab/actions/workflows/algedonic-alert.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/algedonic-alert.yml) |
| `s3star-audit.yml` | S3* | Auditoria — drift interno esporádico | mensal | [![status](https://github.com/freirelucas/rio-edu-lab/actions/workflows/s3star-audit.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/s3star-audit.yml) |
| `s4-scout.yml` | S4 | Inteligência — gaps + oportunidades externas | mensal | [![status](https://github.com/freirelucas/rio-edu-lab/actions/workflows/s4-scout.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/s4-scout.yml) |
| `snowball.yml` | S1.a | Descoberta — snowball multi-fonte | semanal 💤 | [![status](https://github.com/freirelucas/rio-edu-lab/actions/workflows/snowball.yml/badge.svg)](https://github.com/freirelucas/rio-edu-lab/actions/workflows/snowball.yml) |

💤 = dormente (espera secret). 🔒 Os órgãos autônomos (audit, scout, keepalive, snowball) só disparam com a chave-mestra `CORP_ACTIVE=true` — **desligados por padrão**. Ver [ativação + garantias anti-loop](corporacao.md).

## 📋 Fila curatorial (inbox)

**50 candidates** aguardando decisão (9 🇧🇷). Comunidade pode [reivindicar replicação](https://github.com/freirelucas/rio-edu-lab/issues/new?template=replication-claim.md).

| # | 🇧🇷 | Cit | Score | Paper |
|--:|:--:|--:|--:|---|
| 1 |  | 2,933 | 28.6 | Teacher Turnover and Teacher Shortages: An Organization… |
| 2 |  | 408 | 24.32 | Teacher Turnover, Teacher Shortages, and the Organizati… |
| 3 |  | 30,835 | 24.13 | The central role of the propensity score in observation… |
| 4 |  | 17,030 | 23.75 | Convergent and discriminant validation by the multitrai… |
| 5 |  | 8,268 | 23.28 | The New Meaning of Educational Change |
| 6 |  | 4,502 | 22.88 | The Economic Costs of Conflict: A Case Study of the Bas… |
| 7 |  | 4,382 | 22.86 | Teachers, Schools, and Academic Achievement |
| 8 | 🇧🇷 | 200 | 22.85 | Três gerações de avaliação da educação básica no Brasil… |
| 9 |  | 4,092 | 22.82 | Identification and Estimation of Local Average Treatmen… |
| 10 |  | 4,053 | 22.81 | The Bell Curve: Intelligence and Class Structure in Ame… |

_(top 10 de 50 — fila completa em [inbox](inbox.md))_

## 🔬 Transparência (TOP Guidelines)

Score médio de transparência: **4.5/16** (~28%) sobre 15 papers. Detalhe por standard em [TOP scorecard](top-scorecard.md).

## 🔗 Auditabilidade (provenance chains)

**2/3 papers** com cadeia de proveniência completa (paper DOI → dados → código → resultados, verificável um-clique):

| Paper | Cadeia | Fontes | Scripts | Outputs |
|---|:--:|--:|--:|--:|
| [pereira-2019-ipea](provenance/pereira-2019-ipea.md) | ⚠️ | 3 | 3 | 0 |
| [reardon-2011-whither](provenance/reardon-2011-whither.md) | ✅ | 2 | 3 | 1 |
| [theil-1967-economics](provenance/theil-1967-economics.md) | ✅ | 2 | 4 | 3 |

## 🧬 Paper↔dataset (sinal declarativo)

**2 papers** citam DOI de dataset declaradamente (precisão ~100%). Ver [detalhe](produtos/paper_dataset_links.md).

## 🎛️ Como agir (control room)

O GitHub é a sala de controle autenticada. Você (curador) age assim:

- **Aprovar** promoção/mudança → mergear o [PR](https://github.com/freirelucas/rio-edu-lab/pulls)
- **Pausar** um órgão → desabilitar o workflow na [aba Actions](https://github.com/freirelucas/rio-edu-lab/actions)
- **Disparar** manualmente → `Run workflow` ([workflow_dispatch](https://github.com/freirelucas/rio-edu-lab/actions))
- **Emergência** → issues com label [`priority:critical`](https://github.com/freirelucas/rio-edu-lab/labels/priority%3Acritical)

---

_Auto-gerado por `analysis/67_render_sala.py` a partir de estado committado. Badges de órgãos são ao vivo. Drift-checked no CI. Pública — transparência ativa._