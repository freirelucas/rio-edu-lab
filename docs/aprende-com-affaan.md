---
title: Aprende com affaan-m — scout de agent-harness
description: Relatório S4 (VSM Intelligence) que estuda o ecossistema de agentic tooling de Affaan Mustafa (ECC, agentshield, claude-swarm) e mapeia aprendizados aplicáveis à corporação cibernética do rio-edu-lab. Suggest-only — curador decide.
---

# Aprende com `affaan-m`

!!! abstract "O que é este documento"
    Relatório do canal **S4 — Intelligence** (ver [skill `vsm-s4-scout`](arquitetura.md)). O S4 olha pra fora e pro futuro; aqui a varredura foi de um **peer maintainer de agentic tooling** — [Affaan Mustafa (`@affaan-m`)](https://github.com/affaan-m) — e não do ambiente acadêmico usual.

    **Snapshot dos READMEs públicos em 2026-08-10.** Métricas de popularidade foram omitidas de propósito (voláteis e não-auditáveis num snapshot). O que importa aqui são os **conceitos de engenharia de harness**, não números.

    **Suggest-only.** Nenhum item abaixo é auto-promovido. Cada aprendizado vem com esforço/risco/recomendação; o curador (Lucas) decide quais viram PR — igual a qualquer output de S4 (regra 4 do `AGENTS.md`: *decisões curatoriais → humano decide, AI sugere*).

## Por que estudar este perfil

O rio-edu-lab não é só um pipeline de dados: desde a v0.20 é uma **[corporação cibernética](corporacao.md)** — agentes S1–S5 mapeados no [Viable System Model](arquitetura.md), com kill switch, travas anti-runaway e cost-guard. Isso faz do *próprio harness de agentes* uma superfície de engenharia (e de ataque) que precisa ser otimizada e auditada.

`@affaan-m` trabalha exatamente nessa camada — "otimizar o sistema em volta do modelo, não só os prompts dentro dele". Três repos dele resolvem problemas que já estão no nosso roadmap (auditoria de config, memória persistente, orquestração multi-agente), então é fonte de aprendizado direto e não teórico.

## O que ele constrói

| Repo | Conceito | Relevância pra nós |
|---|---|---|
| **[ECC](https://github.com/affaan-m/ECC)** | "Agent harness OS" pro Claude Code. Ciclo `plan → test → implement → review → verify → remember → improve`. Separa **rules** (sempre carregadas) de **skills** (on-demand), **agents** (escopo isolado) e **hooks** (fora do contexto do modelo). Camada **instincts** = padrões aprendidos com confidence score. | Nós já temos skills on-demand (6 VSM) + `AGENTS.md` sempre-carregado. Falta a camada de **memória/aprendizado** e o uso de **hooks** fora de contexto. |
| **[agentshield](https://github.com/affaan-m/agentshield)** | Static analyzer que escaneia `CLAUDE.md`, `settings.json`, hooks, MCP configs e agent defs. 5 categorias: **secrets, permissions, hooks, MCP, agent config**. Nota A–F, saída SARIF/JSON/HTML, `--fix`, GitHub Action, pipeline adversarial opt-in (red/blue/auditor). | Ataca *exatamente* os arquivos que temos (`.claude/`, `AGENTS.md`). Preenche o TODO "gitleaks pre-commit (v0.17+)" e casa com a skill [`vsm-s3star-auditor`](arquitetura.md). |
| **[claude-swarm](https://github.com/affaan-m/claude-swarm)** | Orquestração multi-agente em 3 fases: (1) planner decompõe em **grafo de dependências**; (2) agentes rodam em paralelo com **file locking** + **budget tracking** + retry; (3) **quality gate** revisa todos os outputs juntos. Model tiering: modelo forte planeja/revisa, modelo barato executa. | Espelho quase 1:1 da nossa corporação (S3 aloca, S1 executa, S2 anti-oscilação). Valida nossas travas e sugere grafo-de-dependências + file locking pra quando rodarmos S1s em paralelo. |
| **[JARVIS](https://github.com/affaan-m/JARVIS)** | Plataforma de coleta contínua de intel (web scraping / OSINT autônomo). | Valida a ambição do S4: *sensing contínuo* do ambiente via automação, não varredura manual reativa. |

## Mapeamento VSM — aprendizado ↔ órgão existente

```
S5 constitution  ── portabilidade vendor-neutral (AGENTS.md ✓ já adotado)
S4 scout         ── automatizar sensing (JARVIS / cron)         → A6
S3 allocator     ── model tiering + budget/grafo (claude-swarm)  → A4, A5
S3* auditor      ── config self-audit (agentshield)             → A1
S2 coordinator   ── file locking anti-colisão (claude-swarm)     → A4
S1 runner        ── ciclo plan→…→verify (ECC)                    → (já mapeado)
   └ memória     ── instincts / memory vault (ECC)              → A3  ← órgão faltante
```

O achado estrutural: nossa corporação tem S1–S5, mas **não tem um órgão de memória/aprendizado persistente** além dos docs. ECC chama isso de *instincts*; é a peça que falta pra fechar o ciclo `…→ remember → improve`.

## Backlog de aprendizados (suggest-only)

| # | Aprendizado | Esforço | Risco | Recomendação |
|---|---|---|---|---|
| **A1** | Config self-audit estilo agentshield como drift/CI check | Médio | Baixo | **Incluir** (v0.17 — casa com gitleaks TODO) |
| **A2** | Context economics: rules-sempre vs skills-on-demand vs hooks-fora-de-contexto | Baixo | Baixo | **Incluir** (higiene barata) |
| **A3** | Órgão de memória (instincts) fechando `remember→improve` | Alto | Médio | **Parquear** — exige design S5 |
| **A4** | Grafo de dependências + file locking na corporação | Médio | Médio | **Parquear** — só quando ≥2 S1 paralelos |
| **A5** | Model tiering (Opus planeja / Haiku executa) | Baixo | Baixo | **Incluir** (extraction já usa Haiku) |
| **A6** | Automatizar S4 scout via GitHub Action mensal | Baixo | Baixo | **Incluir** (fecha lacuna conhecida do s4-scout) |

### A1 — Config self-audit (agentshield) · **Incluir**

O `AGENTS.md` já tem seção **Segurança** com NEVER/ALWAYS e promete "gitleaks pre-commit (v0.17+)". agentshield mostra que dá pra ir além de secrets: auditar **permissões wildcard** em `settings.json`, **injeção em hooks** (`${var}` interpolado), e **risco de MCP** (`npx -y` auto-install, bind `0.0.0.0`). Como a corporação nasce DESLIGADA e determinística, um scanner é aliado natural do [`vsm-s3star-auditor`](arquitetura.md).

- **Opção leve:** adicionar o GitHub Action `affaan-m/agentshield@v1` como job warn-only no CI (mesmo padrão dos 11 drift checks). Custo ~zero, dependência externa isolada no CI.
- **Opção soberana:** portar as regras mais relevantes num `analysis/60_*`-style audit stdlib-only (alinhado à nossa preferência por stdlib + idempotência + auditabilidade um-clique). Mais trabalho, zero dependência de terceiros.
- **Guard:** validar contra `.claude/settings.example.json` (não há `settings.json` real commitado — o que já é boa prática que o scanner confirmaria).

### A2 — Context economics · **Incluir**

ECC formaliza o que já fazemos por instinto: **rules sempre-carregadas** (nosso `AGENTS.md`), **skills on-demand** (6 VSM), **hooks fora do contexto**. Dois ajustes baratos:

1. O `AGENTS.md` está crescendo. Manter nele só o *sempre-necessário* e empurrar detalhe operacional pras skills preserva janela de contexto (filosofia ECC: "optimize the context window, persist everything else").
2. **Hooks ainda não são usados.** Checks que hoje pedem lembrança ("rode 25/41/51/56 após mudar funil") são candidatos naturais a hook `PostToolUse` — sai do contexto do modelo e vira garantia, não lembrete.

### A3 — Órgão de memória / instincts · **Parquear**

O ciclo ECC termina em `remember → improve`: sessões destilam padrões com confidence score, recuperáveis depois. Nós temos o embrião disso planejado — `analysis/60_session_to_issue.py` (audit trail v0.16+) — mas não uma **memória viva** que realimente decisões. É o órgão faltante da corporação. Risco médio (o que persistir? como evitar viés acumulado?) → exige design via [`vsm-s5-constitution`](arquitetura.md) antes, conforme regra 3 do `AGENTS.md`. Parquear como proposta de arquitetura, não implementar direto.

### A4 — Grafo de dependências + file locking · **Parquear**

claude-swarm decompõe em grafo de dependências e usa **file locking pessimista** pra rodar agentes em paralelo sem colisão, com budget tracking e retry. Nossa corporação já tem cost-guard (`--limit`, `--dry-run`), kill switch e travas anti-runaway — mas roda serial. Só vale adotar grafo+lock **quando** houver ≥2 unidades S1 executando em paralelo de fato. Parquear até esse cenário existir (evita complexidade sem uso — mesma disciplina de escopo que mantém o `requirements.txt` mínimo).

### A5 — Model tiering · **Incluir**

claude-swarm usa modelo forte pra planejar/revisar e barato pra executar. Nós já fazemos metade: extraction roda em **Haiku 4.5** (`_anthropic.py`, ~$0.001/paper). O aprendizado é tornar o tiering **explícito na corporação**: S3/S4 (planejamento, auditoria) podem justificar um tier mais forte; S1 (execução mecânica) fica no barato. Documentar a política de tier em [`corporacao.md`](corporacao.md); custo de adoção baixíssimo.

### A6 — Automatizar o S4 scout · **Incluir**

A própria skill `vsm-s4-scout` lista como **lacuna conhecida**: "hoje scout é manual + reativo; em v0.18 automatizar via GitHub Actions com cron mensal que abre issue com relatório". JARVIS (sensing contínuo) valida a direção. Concretamente: Action mensal que roda o checklist do scout e abre uma issue com o relatório — mantendo o princípio suggest-only (a issue é sugestão; o curador decide). Este próprio documento é o primeiro output manual desse canal.

## O que **não** copiar

S4 também filtra ruído. Boa parte do perfil é fora do nosso escopo e **não** deve virar dependência ou inspiração de feature:

- **Trading bots autônomos** (stoictradingAI, dprc-autotrader, HyperMamba) — domínio financeiro, sem relação com política pública educacional.
- **OSINT via smart glasses / scraping agressivo** (JARVIS na forma literal) — conflita com nossa postura **LGPD-first** ("dados já vêm agregados do IPP; não desanonimizar"). Aproveitar só a *ideia* de sensing contínuo, nunca a coleta invasiva.
- **`npx -y` auto-install de MCP** — o próprio agentshield sinaliza como risco de supply chain; manteremos dependências pinadas e opt-in.

O filtro aqui é o mesmo da nossa constituição (S5): adotamos **padrões de engenharia de harness**, não o domínio de aplicação nem os atalhos de conveniência.

## Próximo passo curatorial

1. Curador revisa este relatório e marca A1/A2/A5/A6 como candidatos a PR (os "Incluir").
2. A3/A4 ficam parqueados como propostas de arquitetura (invocar [`vsm-s5-constitution`](arquitetura.md) antes de qualquer implementação).
3. `@affaan-m` entra na lista **Comunidade no ecosystem** do `AGENTS.md` como peer de agentic tooling (feito neste mesmo PR).

!!! note "Criticável"
    Este é output de S4, não verdade estabelecida. Discordância sobre prioridade, esforço ou risco de qualquer item é bem-vinda — abra issue ou comente no [inbox curatorial](inbox.md).
