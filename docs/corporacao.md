---
title: Corporação Cibernética — arquitetura de trabalho autônomo
description: Como o rio-edu-lab vira uma "corporação cibernética" (VSM de Stafford Beer ligado a automação real) que leva o produto de v0.19 → v1.0 com autonomia segura. Cybersyn moderno — humano fica em S5 (policy), máquina faz S1-S4.
---

# 🏢 Corporação Cibernética

> **Tese:** O rio-edu-lab já tem o *blueprint* (VSM em [arquitetura.md](arquitetura.md) + 6 skills). A "corporação cibernética" não é algo novo a inventar — é **ligar o VSM ao substrato durável certo**, com o **humano fixo em S5 (policy/identity)** e a máquina fazendo S1-S4. Cybersyn (Beer, Chile 1971) feito com GitHub Actions + Claude + task backlog versionado.

[← Arquitetura VSM](arquitetura.md){ .md-button }

## 1. Por que "corporação" e não "script"

Um script roda quando você o chama. Uma **corporação cibernética** continua trabalhando — varre o ambiente, detecta drift, abre PRs, triagem da comunidade — *sem você no loop a cada passo*, mas **parando nos pontos onde decisão é sua**.

A diferença não é "mais automação". É **estrutura recursiva viável**: cada sub-unidade tem seu próprio mecanismo de auto-regulação (S2 anti-oscilação, S3 gates, S3* audit), e o todo tem um canal de emergência (algedônico) e uma identidade que não se automatiza (S5).

Stafford Beer construiu isto para a economia chilena com 1971-tech (telex + 1 mainframe). Hoje temos GitHub Actions (cron real, permissions scoping), Claude (córtex cognitivo invocável), e task backlog versionado. **O hardware finalmente alcançou o modelo.**

## 2. Os três substratos

A corporação vive em três camadas, cada uma com durabilidade e função distintas:

| Substrato | É o quê no VSM | Durabilidade | Risco |
|---|---|---|---|
| **GitHub Actions** | O *corpo* — S1-S4 como workflows agendados | Permanente (roda sem REPL vivo, cron real) | Baixo (permissions scoping, PRs precisam review) |
| **Claude Code (eu)** | O *córtex* — raciocínio invocado pelos workflows ou por você | Efêmero (por-sessão) | Médio (gasta tokens; resource bargain limita) |
| **Task backlog + Issues** | A *memória organizacional* — S2 coordination | Versionado em git / GitHub | Nenhum (dados, não ações) |

**Decisão de design crítica**: o cron do Claude Code (`CronCreate`) é *session-only* (morre quando a sessão fecha, expira em 7 dias, só dispara com REPL idle). **Não serve de substrato durável.** O corpo permanente da corporação é **GitHub Actions** — Claude é invocado *por* ele, não o contrário.

## 3. Mapeamento VSM → mecanismo concreto

| Sistema | Função | Mecanismo durável (hoje / a construir) | Autonomia |
|---|---|---|---|
| **S1.a Discovery** | snowball multi-source | `snowball.yml` (cron semanal) → PR | ✅ abre PR, humano merge |
| **S1.b Match** | scoring + coverage | roda dentro do snowball workflow | ✅ mecânico |
| **S1.d Curation** | inbox priorizado | `65_curatorial_inbox.py` no CI → drift | ✅ render; humano promove |
| **S1.f Hotsite** | publicação | `pages.yml` (push → deploy) | ✅ idempotente |
| **S1.h Audit trail** | chat → issue | SessionEnd hook (opt-in) | ✅ opt-in |
| **S2 Coordination** | anti-oscilação | 16 drift checks no CI + task backlog | ✅ automático |
| **S3 Allocation** | gates + budget | pytest/ruff/mkdocs/schema no CI + `MAX_LLM_BUDGET_USD` | ✅ enforça |
| **S3\* Audit** | auditoria esporádica | `62_s3star_audit.py` → **novo workflow cron mensal** | ✅ abre issue se RED |
| **S4 Intelligence** | scan venues/modelos | `vsm-s4-scout` skill → **novo workflow cron** | ✅ abre issue com achados |
| **S5 Policy/Identity** | ética, missão, merge, promoção | **VOCÊ. Nunca automatizado.** | ❌ humano |
| **Canal algedônico** | emergência | `algedonic-alert.yml` (CI falha → issue) | ✅ existe |

A maior parte já existe. O que falta pra "corporação viva": **2 workflows novos** (S3* auditor mensal, S4 scout) + **ativar os dormentes** (snowball.yml precisa secret).

## 4. Os três perigos da autonomia — e por que o VSM já os resolve

Autonomia que gasta dinheiro, escreve em `main`, e toma decisões curatoriais é perigosa. O VSM que construímos **já tem os freios embutidos**:

### Perigo 1 — Custo descontrolado (runaway tokens)

- **Freio existente**: `MAX_LLM_BUDGET_USD` + `MAX_TOKENS_PER_PAPER` enforçados em *todos* os call sites LLM (commit `54ef543`). Hard stop, não advisory.
- **Freio adicional na corporação**: cada workflow declara um budget cap. CI falha se exceder. GitHub Actions tem timeout por job.
- **Resultado**: impossível um agente autônomo gastar além do teto sem você unsetar a env var.

### Perigo 2 — Escrita direta em `main` (mudança irreversível sem review)

- **Princípio**: a corporação **NUNCA faz push direto em `main`**. Sempre abre PR.
- **Freio**: branch protection (você liga em Settings → Branches). Require PR review + status checks.
- **Resultado**: o humano (S5) é o gate de merge. A corporação propõe, você dispõe. Cybersyn-fiel — a Operations Room *mostrava* o estado, decisões eram humanas.

### Perigo 3 — Auto-promoção curatorial (diluir o catálogo)

- **Freio existente**: `vsm-s5-constitution` skill declara *"decisão curatorial é humana; AI sugere, nunca auto-promove"*.
- **Mecânica**: a corporação popula o **inbox** (`docs/inbox.md`) com score de prioridade. Você (ou a comunidade via `claim`) decide o quê promover.
- **Resultado**: escala sem perder curadoria. A máquina enche a fila; humanos escolhem.

## 5. Espectro de autonomia — você escolhe o nível

| Nível | A corporação pode... | Risco | Recomendado pra |
|---|---|---|---|
| **1 — Suggest-only** | Abrir issues + PRs. Você revisa e mergeia tudo. | Mínimo | Começar. MVP. |
| **2 — Auto-merge mecânico** | Auto-mergear PRs *puramente mecânicos* que passam CI (drift re-render, dep bumps). Tudo cognitivo/curatorial espera você. | Baixo | Quando confiar nos drift checks |
| **3 — Auto-merge amplo** | Mergear tudo que passa CI; você audita post-hoc via S3*. | Médio-alto | Só com gold-set provando precisão |

**Recomendação pra levar v0.19 → v1.0 com segurança: Nível 1, migrando pra 2 conforme confiança.** O trabalho mecânico (snowball, drift, render, triagem) roda sozinho e abre PRs; você aprova os merges. As decisões que importam (promover paper, declarar v1.0, gastar acima de budget) ficam em S5 — você.

## 6. MVP da corporação (o que ligar primeiro, de forma segura)

Ordem por leverage × segurança:

1. **Memória organizacional** ✅ *(feito nesta sessão)* — backlog v1.0 como tasks rastreáveis (7 tasks, release bloqueada pelos tier-1).
2. **S3\* Auditor mensal** — workflow cron que roda `62_s3star_audit.py`, abre issue se verdict RED. Suggest-only, zero risco.
3. **S4 Scout** — workflow cron que escaneia venues/modelos novos, abre issue com achados pra você triar.
4. **Ativar S1 Discovery** — `snowball.yml` weekly (precisa `OPENALEX_EMAIL` secret). Abre PR; você mergeia.
5. **Branch protection** — você liga. Vira o gate S5 formal.

Nenhum desses passos dá à corporação poder de gastar descontrolado ou escrever em `main` sem você. **Todos são suggest-only ou PR-gated.**

## 7. O que NUNCA se automatiza (a constituição da corporação)

S5 é a identidade. Estes atos são **sempre humanos**, por design, não por limitação técnica:

- **Merge em `main`** — você é o gate
- **Promover paper ao catálogo** — curadoria humana ([`vsm-s5-constitution`](https://github.com/freirelucas/rio-edu-lab/blob/main/.claude/skills/vsm-s5-constitution.md))
- **Declarar v1.0 / release** — compromisso reputacional
- **Mudar a missão** — "traduzir academia pra dado brasileiro" é a constituição
- **Gastar acima de budget** — requer unset explícito de env var
- **Ética curatorial** — incluir/excluir paper sobre população vulnerável, LGPD, atribuição

> Beer: *"o propósito de um sistema é o que ele faz"*. A corporação faz o trabalho mecânico de traduzir 1000s de papers em insights contra dados do Rio. O **propósito** — o porquê, o ethos, o gosto curatorial — fica com o humano. Essa é a fronteira que torna a autonomia segura.

## 8. Como isto leva v0.19 → v1.0

A corporação executa o backlog (§6 task list) nas camadas certas:

- **Trabalho mecânico autônomo** (DAS estendido, match ranker, drift, render) → corporação abre PRs, você mergeia
- **Trabalho que precisa de você** (OSF recipes, gold-set labeling, escolha de qual paper replicar, declarar v1.0) → fica em S5, a corporação só *lembra* via task backlog + issues
- **Trabalho gated em externalidades** (45d/429, Censo 2022, Rio endpoint) → corporação monitora (S4) e avisa quando destravar

Resultado: você atua como **CEO/curador**, não como operário. A corporação carrega o peso mecânico da escala; você decide direção e aprova saída.

## 9. 🔌 Ativação — guia passo a passo (custo confirmado: $0)

Pesquisa (jun/2026) confirmou: **repo público → GitHub Actions ilimitado e grátis**. A corporação roda a custo zero. O único gasto possível (Claude autônomo em CI) é opt-in *e* pode ser **$0 via assinatura** (não a API paga).

### Passo 0 — A chave-mestra `CORP_ACTIVE` (a corporação nasce DESLIGADA)

Os órgãos autônomos (`s3star-audit`, `s4-scout`, `keepalive`, `snowball`) **não rodam sozinhos até você ligar**. Cada um checa uma variável de repo:

```
Settings → Secrets and variables → Actions → Variables → New repository variable
  Name:  CORP_ACTIVE
  Value: true
```

- **Sem essa variável (default)**: crons **não disparam**. A corporação fica montada mas inerte. Merge do código não liga nada.
- **`CORP_ACTIVE = true`**: crons passam a rodar no schedule.
- **`CORP_ACTIVE = false`** (ou apagar): **big red button** — para tudo instantaneamente no próximo tick.
- **Dispatch manual** (`Run workflow`) sempre funciona, independente da chave — pra você testar um órgão sob demanda.

Isso responde direto ao medo de "rodar em loop consumindo recursos": **nada autônomo acontece sem essa chave**, e ela desliga tudo de uma vez.

### Passo 1 — Secrets (Settings → Secrets and variables → Actions)

| Secret | Ativa | Sensível? | Necessário? |
|---|---|---|---|
| `OPENALEX_EMAIL` = `lucasfreire@gmail.com` | `snowball.yml` weekly (descoberta) | não (polite-pool ID) | pra ligar discovery |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude autônomo em CI (triagem/auto-fix) | **sim** | opcional |
| `RIO_API_BASE` / `RIO_API_KEY` | Path D (LLM soberano) | sim | quando endpoint existir |

Os órgãos determinísticos (`s3star-audit`, `s4-scout`, `keepalive`) **já funcionam sem secret nenhum**.

### Passo 2 — Claude em CI sem custo por token (opcional)

A `anthropics/claude-code-action@v1` aceita **`claude_code_oauth_token`** gerado da sua assinatura Claude Pro/Max (`claude setup-token` local). Isso roda Claude autônomo em CI **usando sua assinatura, não a API paga** — dentro dos limites dela. Alternativa: `ANTHROPIC_API_KEY` (paga por token) com cap via `claude_args: "--max-turns 5 --model claude-sonnet-4-6"`.

### Passo 3 — Labels (Settings → Labels)

Os workflows usam: `s3star-audit`, `s4-scout`, `algedonic-alert`, `priority:critical`, `discovery-source`, `paper-suggestion`, `replication-claim`. Crie-os pra os órgãos poderem etiquetar issues.

### Passo 4 — Keepalive (já resolvido no código)

⚠️ Pegadinha que a pesquisa achou: **crons auto-desativam após 60 dias sem commit** em repo público (tag/release não conta). O `.github/workflows/keepalive.yml` faz heartbeat a cada 20 dias com `[skip ci]` — resolve automaticamente. É a única exceção ao "corporação só abre PR" (mecânico, não-curatorial, precisa ser autônomo).

### Passo 5 — Nível de autonomia (você decide)

Default seguro: **N1 suggest-only** (corporação abre issues/PRs, você mergeia). Suba pra N2 (auto-merge mecânico) quando confiar nos drift checks. Ver §5.

### 🛡️ Garantias anti-runaway (por que não vai loopar nem torrar recurso)

Auditoria do grafo de disparos (jun/2026) — a corporação é **estruturalmente incapaz de loopar**:

1. **Nenhum órgão se auto-dispara.** Grafo de triggers é acíclico: crons disparam por relógio, não por output de outro órgão. `algedonic-alert` dispara em CI-falha, mas abrir issue não dispara CI → sem ciclo.
2. **Zero auto-merge.** Tudo espera merge humano (N1). PR aberto não vira código sozinho.
3. **Zero LLM nos órgãos atuais.** `s3star-audit`, `s4-scout`, `keepalive`, `snowball` são Python puro determinístico. Nenhuma chamada paga. (Claude-em-CI é opt-in futuro, capado por `--max-turns` + OAuth de assinatura.)
4. **Kill switch `CORP_ACTIVE`** — off por padrão; um toggle para tudo.
5. **`concurrency: cancel-in-progress`** em cada órgão — um run novo cancela o anterior, nunca empilha.
6. **`timeout-minutes`** em cada job (5–60 min) — nada roda pra sempre. GitHub também mata em 6h.
7. **`keepalive` usa `[skip ci]`** — o heartbeat não dispara a suíte inteira.
8. **Repo público = Actions grátis ilimitado** — mesmo no pior caso, custo monetário = $0.

Pior cenário realista: um órgão roda até o timeout uma vez e para. Sem cascata, sem gasto.

### O que NÃO precisa

- **Login/auth separado** — a [Sala de Operação](sala.md) é pública (transparência ativa); o *controle* já é autenticado pelo GitHub (merge/dispatch/disable pedem sua identidade). "Security through obscurity" sobre dados públicos não protege nada.
- **Hosting pago** — GitHub Pages (site) + badges live = $0.
- **Branch protection** é recomendado (gate S5 formal) mas não bloqueia a corporação.

## 10. Riscos residuais (honestos)

- **GitHub Actions cron drift** — crons do GH não são pontuais (podem atrasar minutos). Aceitável pra trabalho não-realtime.
- **Claude-em-CI custo** — invocar Claude via `claude-code-action` em cada issue gasta. Mitigar: só em issues com label específica + budget cap.
- **Comunidade adversarial** — issues/PRs externos podem tentar injetar conteúdo malicioso. Mitigar: a corporação trata input externo como não-confiável (já no system prompt do Claude Code); merge sempre humano.
- **Over-automation** — ligar nível 3 cedo demais. Mitigar: começar nível 1, subir com evidência (gold-set).
- **Modelo Rio em prod** — Path D dormente; quando ligar, re-validar budget (self-hosted muda economia).

---

_Este documento é a constituição operacional da corporação. Versionado em `docs/corporacao.md`. Mudanças estruturais invocam [`vsm-s5-constitution`](https://github.com/freirelucas/rio-edu-lab/blob/main/.claude/skills/vsm-s5-constitution.md)._
