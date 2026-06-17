---
name: vsm-s5-constitution
description: Validate work against the lab's identity, ethos, and policy. Maps to VSM System 5 — Policy (identity arbitration between S3 inside-now and S4 outside-then). Use before merging significant changes, when a PR touches multiple stages, when a curatorial decision needs ethical review, or when there's tension between operational efficiency and mission. NOT a routine gate — invoke when policy/identity is at stake.
---

# VSM S5 Constitution — identidade e ethos

Skill que reproduz o **canal S5 do VSM**: identidade. Arbitra a tensão entre S3 (run / preservar o presente) e S4 (change / explorar o futuro). Garante que decisões respeitam a missão do lab.

## Quando invocar

- PR grande mudando estrutura (novo adapter, nova stage, mudança schema)
- Decisão curatorial polêmica (promover paper X ao catálogo? incluir paper de domínio Y?)
- Tensão S3 vs S4 (ex: bug fix urgente vs implementar fonte nova de papers)
- Antes de release maior (v0.X.0)
- User pede "isso está alinhado com a missão?"

## Constituição do lab (a versionar — v0.16 sprint)

Identidade declarada em `docs/sobre.md`:

1. **Missão**: "Traduzir academia gringa pra dado brasileiro" — ponte entre cânone metodológico internacional e granularidade pública do Rio
2. **Pipeline reproduzível ponta-a-ponta** — não claim de causalidade, só replicação literal de método publicado contra dado público
3. **Open science**: AEA + OSF + TOP padrão. CITATION.cff. DOI Zenodo. CC-BY-4.0 dados + MIT código
4. **Transparência ativa**: chat → issue como audit trail; provenance completa; dados crus + intermediários acessíveis
5. **Soberania de modelo**: Rio-3.5 preparado (Path D), Claude operacional. Quando endpoint sair, flip via env var
6. **Auditabilidade um-clique**: cada paper replicado → Binder badge + AEA README + OSF Replication Recipe
7. **Curatoria humana central**: LLM e ferramentas assistem; decisão final é humana (Lucas + community via PR)
8. **Funil global, catálogo Rio**: descoberta absorve academia + policy + econ global; catálogo replica contra data.rio

## Checks por categoria

### Mudanças no pipeline

- A mudança preserva backward-compat?
- Adiciona drift check no CI?
- Tem teste invariante?
- Documenta em `docs/`?

### Mudanças no catálogo

- Paper tem `data_availability_statement`?
- Paper tem `provenance` (DOI + commit + replication_date)?
- Paper tem `controlled_randomness` se rodou stochastic?
- Paper aparece no scorecard TOP?
- Paper foi pré-registrado via OSF Replication Recipe?

### Mudanças no LLM provider

- Mantém fallback automático?
- Custo per-paper documentado?
- Teste comparativo com gold-set existe?
- `_provider` tag persistido em audit trail?

### Mudanças na taxonomy/seeds

- Novo seed tem citation count justificável?
- Nova categoria respeita os 10 cats fechados ou expande explicitamente?
- Domain signal (`edu + policy`) ainda funciona?

### Decisões éticas curatoriais

- Paper viola ética acadêmica (plágio, fabricação)?
- Paper sobre população vulnerável: respeita LGPD + anonimização?
- Replicação revela info confidencial? (não esperado pra data.rio public)
- Atribuição correta dos autores originais?

## Algedonic alert (canal de emergência)

Se algum dos seguintes ocorrer, **PARAR EXECUÇÃO** e escalar pro usuário:
- Teste `tests/test_theil.py::test_share_within_range_narrative` falha (achado central do lab quebrou)
- mkdocs build --strict falha em `main` push
- ANTHROPIC_API_KEY exposto em commit ou log
- Schema migration sem rollback
- Funnel YAML cresce > 50% numa única run inesperadamente
- Drift check falha sem mudança de código (bug em determinismo)

## Output esperado

- Status: ✓ alinhado / ⚠ tensão (especificar) / ✗ violação (especificar)
- Recomendação: prosseguir / pausar pra discussão / rejeitar
- Se tensão S3↔S4: qual lado pesar? (preservar vs explorar)

## NÃO fazer

- Tomar decisão curatorial final sem human-in-loop
- Bloquear PR rotineiro (esse é S3)
- Confundir com S3 (S3 = otimizar o presente; S5 = definir o porquê)
