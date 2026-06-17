---
title: Arquitetura v0.16 — VSM, soberania, ciência aberta
description: Modelo VSM de Stafford Beer aplicado ao rio-edu-lab. Roadmap v0.16+ pra LLM soberano (Rio-3.5), reprodutibilidade one-click, chat→issue audit, AEA/OSF/TOP open science. Honesto sobre custos e riscos.
---

# Arquitetura v0.16 — VSM, soberania, ciência aberta

> **Pra navegantes apressados:** este documento aplica o **Viable System Model** (Stafford Beer) ao rio-edu-lab como espinha arquitetural. Define o que é S1-S5, mapeia funções críticas pra skills do Claude Code, e estabelece o roadmap v0.16+ centrado em (a) LLM soberano Rio-3.5-Open-397B, (b) one-click reprodutibilidade, (c) chat → GitHub issue como audit trail, (d) padrões AEA + OSF + TOP de ciência aberta.

[← Voltar à página Sobre](sobre.md){ .md-button }

## 1. Por quê VSM agora

O lab cresceu de 3 estágios (descoberta → match → coverage) pra 6+ (incluindo curatoria, replicação, hotsite, audit, LLM extraction opcional, code_signal, multi-source snowball). O auditor arquitetural identificou 3 sinais de inflexão futura: funnel YAML escala mal acima de 10k papers; adapters de novas fontes exigem 7+ pontos de toque; análises "vivas" misturam com infra do pipeline.

**Diagnóstico**: o lab precisa de uma teoria de *divisão e síntese* do trabalho algorítmico — não mais uma camada de scripts numerados. VSM oferece exatamente isso: 5 sistemas + 4 canais que descrevem qualquer organização viável, recursivamente.

**Referências canônicas**: Beer (1972) *Brain of the Firm*; Beer (1979) *Heart of Enterprise*; Beer (1985) *Diagnosing the System*; Espejo & Reyes (2011) *Organizational Systems*; Pickering (2010) *The Cybernetic Brain*; Medina (2011) *Cybernetic Revolutionaries* (Cybersyn Chile). Aplicações recentes: Cadena (2024 INCOSE — SAFe pela lente VSM); Fearne (2024 — VSM para AI agent orchestration); [vsm-docs Elixir](https://viable-systems.github.io/vsm-docs/) (Actor Model + Event Sourcing implementando VSM).

## 2. VSM mapeado ao rio-edu-lab

### S1 — Operations (o que faz o trabalho)

Sub-unidades S1, cada uma um VSM recursivo aninhado:

| Sub-unidade | Função | Scripts hoje |
|---|---|---|
| **S1.a Discovery** | Snowball bibliométrico OpenAlex + Semantic Scholar + GitHub | `45_bulk_discover.py`, `_openalex.py`, `_semanticscholar.py`, `45c_apply_code_signals.py` |
| **S1.b Match** | Filtro temático + scoring IDF + code_book bonus + match_detail | `46_extract_requirements.py`, `_match.py`, `49b_apply_codebook_overrides.py` |
| **S1.c Coverage** | Cobertura paper→data.rio item, status + match_detail | `47_check_coverage.py` |
| **S1.d Curation** | Promove funil → catálogo, gold-set, decisão accept/reject | `48_promote_funnel.py`, `50_sample_gold_set.py`, `51_match_quality_report.py` |
| **S1.e Replication** | Análises Stage 4 vivas (Theil, Pereira, VULN-EDU, FUN-Rio, PM-12, HEX-EDU, THESHA, Moran-LISA) | `10_*` a `37_*` |
| **S1.f Hotsite** | Publicação mkdocs com insights + reprodutibilidade one-click | `docs/`, `mkdocs.yml`, charts em `docs/_assets/` |
| **S1.g LLM extraction** | v3 — paper → tool-use structured output | `_anthropic.py`, `_rio.py`, `_llm.py`, `49_codebook_backfill.py`, `55_llm_extract_requirements.py` |
| **S1.h Audit trail** | (novo v0.16) chat → GitHub issue, provenance trail | a construir |

### S2 — Coordination (anti-oscilação entre S1)

Infraestrutura que evita colisão entre sub-unidades S1 que compartilham recursos:

- **Schemas YAML versionados** (funnel, catalog, manifest, codebook_overrides, code_signals, papers_funnel) — single source of truth por estágio
- **Cache filesystem por ID** (`data/cache/openalex/`, `data/cache/semscholar/`, `data/cache/github/`, `data/cache/anthropic/`) — evita refetch redundante
- **Drift checks no CI** (11 hoje): re-render → `git diff --quiet` → falha. Previne S1.f (hotsite) ficar dessincronizado de S1.b (match) ou S1.c (coverage)
- **Idempotent appliers** (`49b`, `45c`) — mesma operação 2× é noop, não duplica estado

**Lacuna**: falta **registry de contratos entre stages**. Hoje cada stage assume implícitamente shape do anterior. Vir-se v0.17 com JSON Schema validation por artefato.

### S3 — Operational management (controle inside-and-now)

Gates de qualidade que decidem se o pipeline pode rodar:

- **pytest invariants** (296 testes): Theil bootstrap determinístico, match enriched, code_book, etc.
- **ruff lint** (warn-only hoje; tighten em v0.17)
- **mkdocs build --strict**: docs precisam compilar
- **Schema validation** (`31_build_paper_catalog.py --validate-funnel`)

**Lacuna**: falta **resource bargain explícito** — quanto compute/tempo/tokens cada stage pode consumir. Documentar via env vars (`MAX_TOKENS_PER_PAPER`, `MAX_LLM_BUDGET_USD`) na v0.17.

### S3* — Audit (canal vertical esporádico)

Auditoria não-roteirizada, independente dos relatórios de rotina:

- **Gold-set labeling** + match-quality report (`51_match_quality_report.py`)
- **LLM vs BoW comparison** (`56_llm_vs_bow_compare.py`)
- **Theil bootstrap CI** (`35_bootstrap_theil_ci.py`)
- **Moran's I + LISA** (`37_moran_lisa.py`)

**Lacuna crítica**: re-execução com **cache cold** sobre amostra aleatória pra detectar drift silencioso. Skill `vsm-s3star-audit` resolve.

### S4 — Intelligence (outside-and-then)

Varredura do ambiente externo:

- **Snowball seed expansion** (39 seeds em `data/openalex_seeds.yml`)
- **Code signals** (GitHub + future Zenodo + DataCite)
- **Community signal** (`docs/dados.md` — prefeitura-rio, basedosdados, UFPB-Squad, r5py, cran/OasisR)
- **Model availability scan** (Rio-3.5 endpoints, novos APIs)
- **Data.rio item additions** (manifest snapshot)

**Lacuna**: scan automatizado de novos venues acadêmicos (Stata Journal, AEA RCT Registry, IPEA TDs) + RSS dos achados. Skill `vsm-s4-scout` operacionaliza.

### S5 — Policy / Identity (o ethos)

Identidade, missão, ética:

- "Traduzir academia gringa pra dado brasileiro" (`docs/sobre.md`)
- Open science + transparência + reprodutibilidade + auditabilidade
- LLM soberano (Rio-3.5 Path D preparado)
- MIT + CC-BY-4.0
- DOI Zenodo (10.5281/zenodo.20060620)

**Lacuna**: **constituição versionada** — pledge formal de ética de extração, atribuição, fair use. Skill `vsm-s5-constitution` redige.

### 4 canais verticais

| Canal | Função | Status |
|---|---|---|
| **Command** | S3 → S1 (regras operacionais) | ✓ via CI gates |
| **Resource bargain** | S1 → S3 ↔ "trabalho em troca de recursos" | ✗ implícito |
| **Accountability (S3*)** | S1 → S3* (audit esporádico) | ⚠ parcial (só análises) |
| **Algedonic alert** | bypass de emergência (S1 → S5) | ✗ não existe |

Canal algedônico ausente = falhas silenciosas até quebrar. v0.16 cria via webhook GitHub Actions que pinga issue de emergência quando teste invariante crítico falha.

## 3. Funções críticas → skills do Claude Code

Cada função S1-S5 vira uma skill especializada em `.claude/skills/`:

| Skill | Sistema | Função crítica |
|---|---|---|
| `vsm-s1-runner` | S1 | Executa 1 stage com contrato I/O explícito |
| `vsm-s2-coordinator` | S2 | Detecta colisão de schema/cadência; arbitra |
| `vsm-s3-allocator` | S3 | Enforce gates + budget compute/tokens |
| `vsm-s3star-auditor` | S3* | Amostra random + cold cache + diff semântico |
| `vsm-s4-scout` | S4 | Scan venues, modelos novos, drift baseline |
| `vsm-s5-constitution` | S5 | Valida PR contra carta ética; arbitra S3↔S4 |

Veja [`.claude/skills/`](https://github.com/freirelucas/rio-edu-lab/tree/main/.claude/skills) pra invocação concreta.

## 4. Roadmap v0.16+ — 4 frentes

### Frente 1 — LLM soberano (Path D refinada)

**Estado do modelo Rio-3.5-Open-397B** (verificado): É um **merge** de Qwen3.5-397B-A17B + Nex-N2-Pro com on-policy distillation, não treinamento do zero. IplanRIO publicou erratum sobre upload errado. Benchmarks são "model-card-only" — sem reprodução independente. 397B params, ~17B active, 512 experts, contexto 262k (1M YaRN), multimodal + tool calling herdados de Qwen3.5 base.

**Economia honesta** (custos verificados 2026):

| Caminho | Hardware | Custo mensal 24/7 | Adapter pronto? |
|---|---|---:|:---:|
| HF Inference Endpoints dedicado | 4×H100 80GB | US$ 13-43k | ✓ |
| vLLM self-host AWS/GCP | 4×H100 rental | US$ 4-20k | ✓ |
| Hardware compra | 4×H100 PCIe | ~US$ 120k one-time | ✓ |
| Modal serverless | pay-per-execution | US$ 11-16k | ✓ |
| Together dedicated | 4×H100 | ~US$ 19k | ✓ |
| Ollama Q4 (M3 Max 128GB) | local workstation | US$ 0 marginal, 3-6 tok/s | ✓ |
| **Claude Haiku 4.5 (hoje)** | API serverless | **~US$ 30 pro funnel inteiro** | ✓ |
| LNCC Santos Dumont (RNP) | 8×V100, sovereign | aplicação acadêmica grátis | ✓ |

**Break-even**: Rio self-hosted só vence Haiku acima de ~10-50M tokens/dia. Nosso funnel atual usa ~8M tokens/run inteira. **Claude continua mais barato pra extração estruturada bulk**.

**Estratégia híbrida v0.16**:
1. Claude Haiku 4.5 default pra tool calling crítico + bulk extraction (custo + latência + tool stability)
2. Rio-3.5 opt-in via Modal serverless pra: (a) tarefas PT-BR específicas, (b) multimodal PDF parsing (tabelas/figuras), (c) reprocessing nightly quando volume justificar
3. **`_llm.py` dispatcher já isola** — env `LLM_PROVIDER=rio` flip total quando endpoint estabilizar; fallback automático pra Haiku em error/timeout
4. **Sovereign goal**: aplicar em LNCC/RNP via SINAPAD pra acesso V100 acadêmico — caminho real de soberania, não política

**Benchmarks obrigatórios antes de migrar**: gold-set de 100 papers validados Haiku → comparar Rio em (a) campos corretos, (b) US$/paper, (c) p50/p99 latency, (d) tool calls bem-formados. Sem isso, migrar é apostar em claims do model card não reproduzidas.

### Frente 2 — One-click reprodutibilidade + hotsite

**Stack escolhida** (das 10 plataformas avaliadas):

- **Jupyter Book v2** ([next.jupyterbook.org](https://next.jupyterbook.org)) — MyST Document Engine, JEP 122, launch buttons nativos Binder/Colab/JupyterLite/Deepnote. Free, MIT, self-hosted via static HTML.
- **Quarto 2** alternativa (Rust rewrite late-2026) se priorizar publicação polida sobre executable books.
- **Binder badge** ([mybinder.org](https://mybinder.org)) — free, 1GB-2GB RAM, 6h sessions, sem GPU. Suficiente pra rerodar Theil + Pereira + VULN-EDU. Self-host BinderHub via K8s/Helm se virar gargalo.
- **Google Colab badge** complementar — destination opcional pra leitores com GPU.

**NÃO escolhidos**: Code Ocean (closed-source, custo opaco); Whole Tale (largamente defunct em 2026, dashboard down); Renku 2 (excelente mas K8s pesado pra curador solo); REANA (MIT + Snakemake, melhor pra workflows complexos — manter como fallback).

**Bundle reprodutível por paper**:
- `pyproject.toml` + `uv.lock` (commitado) — uv é 10-100x mais rápido que Poetry, lockfile cross-platform com hashes
- `Dockerfile` rodando `uv sync --frozen` — funciona em Binder, Codespaces, CI, local
- `.devcontainer/devcontainer.json` referenciando mesmo Dockerfile (IDE parity)
- DVC + Hugging Face datasets pra data > 50MB
- Zenodo + Software Heritage SWHID (ISO/IEC 18670, abril 2025) pra DOI software permanente
- `CITATION.cff` no root — auto-renderiza badge "Cite this repository" no GitHub

### Frente 3 — Chat → GitHub issue como audit trail

**Achado**: Anthropic não ship export oficial além de `/export` (plaintext). JSONL fica em `~/.claude/projects/<proj>/<session>.jsonl`. Auto-removed após 30 dias (configurável via `cleanupPeriodDays`).

**Stack escolhida**:

- **SessionEnd hook** (`code.claude.com/docs/en/hooks`) — recebe `transcript_path`. Executar script Python que:
  1. Parsea JSONL (schema: `type`, `uuid`, `parentUuid`, `timestamp`, `message`, `toolUseResult`)
  2. Renderiza Markdown via [cc2md](https://github.com/magarcia/cc2md) ou [claude-code-log](https://github.com/daaain/claude-code-log) ou DIY simples
  3. `gh issue create` com body Markdown + label `audit-trail/session-{date}`
- **Langfuse MIT self-hosted** ([langfuse.com](https://langfuse.com)) — opcional pra observability rica via OpenLLMetry instrumentation. Annotation queues = "human reviewer audits trace" → casa com auditabilidade.
- **Gitleaks pre-commit + TruffleHog CI** — redação antes de commit chat log (paths, secrets, PII).
- **AGENTS.md** ([agents.md](https://agents.md/) — Linux Foundation Agentic AI track) — symlink `CLAUDE.md → AGENTS.md` pra cross-vendor compat (OpenAI Codex, Cursor, Aider, Google Jules, GitHub Copilot agent, Cline, Devin, Junie etc.).

**Privacy budget**: chat contém código + working dir + às vezes nomes próprios. SessionEnd hook deve **redatar absolute paths** (`/home/user/...` → `~/`), filtrar tool results > 5KB, e flag PII via regex. GDPR aplica retenção ≤ 90 dias.

### Frente 4 — Open Science stack (AEA + OSF + TOP)

**Adoção concreta** (das 5 alternativas):

- **AEA Data Editor README template** ([Vilhuber](https://social-science-data-editors.github.io/template_README/template-README.html)) — testado em 500+ papers AEA desde 2019. Seções obrigatórias: Overview, DAS, Computational Requirements, Description of Programs/Code, Instructions to Replicators, List of Tables/Programs, References.
- **OSF Replication Recipe** ([osf.io/p4fse](https://osf.io/p4fse/)) — lab REPLICA (não gera), então o análogo do pre-registration é declarar critério de "sucesso de replicação" ANTES de rodar o código.
- **WWC Standards Handbook v5.0** (IES) — rubric pros 15 papers do catálogo: rating "Meets WWC Standards" / "with reservations" / "does not meet".
- **TOP Guidelines** ([Center for Open Science](https://www.cos.io/initiatives/top-guidelines)) — 7 práticas × 3 níveis (Disclosed / Shared+Cited / Certified). Scorecard auto-renderizado por paper.
- **SciELO open science badges** — só 1 journal BR usa hoje, oportunidade de liderança brasileira.
- **4 badges OSF** por paper replicado: Open Data, Open Materials, Open Analytic Code, Preregistered.

**Schema YAML estendido por paper** (v0.16):

```yaml
data_availability_statement:
  summary: "public"  # public | restricted | confidential
  sources:
    - name: "INEP Censo Escolar 2019"
      url: "https://gov.br/inep/..."
      access_date: "2024-03-15"
      license: "Dados Abertos gov.br"
      sha256: "abc123..."
controlled_randomness:
  seeds: [42, 1234]
runtime: "12min @ 4-core CPU"
preregistration:
  type: "retrospective_replication_recipe"
  osf_url: "https://osf.io/xxxx"
provenance:
  paper_doi: "10.xxxx/yyyy"
  data_manifest_hash: "sha256:..."
  code_commit: "abc1234"
  replication_date: "2024-11-01"
  replicator: "Lucas Freire"
```

## 5. Cronograma realista (3 sprints)

**Sprint v0.16 — Open science stack + AGENTS.md + bug fix related_works (~1 semana)**
- Fix bug `related_works` → `referenced_works` em `_openalex.py:parse_work` (P0 confirmado por 5 agentes)
- AGENTS.md cross-vendor + symlink CLAUDE.md
- Schema YAML estendido (DAS + provenance + controlled_randomness) no catálogo dos 15 papers
- CITATION.cff no root
- TOP scorecard renderizado por paper (auto via novo `analysis/60_top_scorecard.py`)
- 6 skills `.claude/skills/vsm-*.md` (este commit)

**Sprint v0.17 — Hotsite reprodutível + chat audit (~2-3 semanas)**
- Migração mkdocs → Jupyter Book v2 OU adoção Quarto (a decidir conforme estado v2 em produção)
- Binder badge + `Dockerfile` + `pyproject.toml` + `uv.lock` por paper replicável
- SessionEnd hook → cc2md/ccexport → `gh issue create` template
- Gitleaks + TruffleHog em pre-commit + CI
- OSF project + Replication Recipe retroativo nos 3 papers replicados

**Sprint v0.18 — Sovereign LLM + S3* audit + canais VSM (~3-4 semanas)**
- Aplicação LNCC/RNP/SINAPAD pra V100 acadêmico (caminho sovereign real)
- Modal serverless validation: 100 papers gold-set Rio vs Haiku (custo + qualidade + latência)
- Algedonic alert: webhook GitHub Action pra invariante crítica
- `vsm-s3star-auditor` skill operacional: random sample + cold cache + diff
- Resource bargain explícito (env vars `MAX_TOKENS_PER_PAPER`, `MAX_LLM_BUDGET_USD`)

## 6. Riscos honestos

1. **Rio-3.5 ainda em erratum** — IplanRIO admitiu upload errado da merge vs distilada. Wait-and-see antes de migração total.
2. **VSM como org-chart**: ele não é hierarquia, é função. Curador solo (Lucas) ocupa S1+S3+S4+S5 simultaneamente — pitfall #1 de Beer.
3. **Over-engineering S2**: anti-oscilação só importa quando há contenção real. Não construir registry de contratos se nada está colidindo.
4. **Recursão infinita**: cada sub-script como VSM completo gera atrito. Parar quando S1 é trivial.
5. **Privacy de chat trail**: caminhos absolutos, nomes próprios, tool results vazam. Redação obrigatória antes de issue.
6. **Custos cloud GPU variam 3× entre providers** (AWS US$4,50/h vs GCP US$10-80/h pra H100). Monitor mensal.
7. **Sustainability de plataformas**: Whole Tale defunct (lição), Copilot Workspace V1 sunset May 2025 (lição), Renku Legacy descontinuado. Não acoplar a stack monocultural.

## 7. Pitfalls do VSM (Stafford Beer warning)

(i) **Confundir S3 com S5** — S3 otimiza o presente, S5 define o "porquê". Curador solo tende a colapsar tudo em S5 e perder controle operacional. (ii) **VSM como dogma** — ele descreve viabilidade, não prescreve organização ideal. Algumas estruturas precisam ser irreverentemente quebradas. (iii) **Ignorar algedônico** — sem bypass de emergência, falhas críticas viram silenciosas até quebrar o pipeline.

## 8. Continue

<div class="grid cards" markdown>

- [:material-account-tie: Sobre o lab](sobre.md)
- [:material-database: Dados do data.rio](dados.md)
- [:material-file-document: Papers do catálogo](papers/index.md)
- [:material-check-circle: Qualidade do match](match-quality.md)

</div>
