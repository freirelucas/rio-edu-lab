"""Render docs/sala.md — a Sala de Operação pública da corporação cibernética.

Cybersyn moderno: uma tela que mostra o estado vivo da corporação. PÚBLICA
por design (transparência ativa é a missão). O controle (aprovar, pausar,
disparar) fica no GitHub nativo, que já autentica.

Lê JSONs committados (determinístico → drift-checked) + embute badges de
status LIVE dos workflows (imagens nativas do GitHub Actions, sempre atuais).

Camadas:
- OBSERVAR (esta página, pública): funnel, órgãos, inbox, transparência, audit
- AGIR (GitHub, autenticado): merge PR = aprovar; disable workflow = pausar;
  workflow_dispatch = disparar

Fontes (todas committadas, não-gitignored):
  data/processed/funnel_state.json
  data/processed/papers_catalog_summary.json
  data/processed/curatorial_inbox.json
  data/processed/top_summary.json
  data/processed/provenance_summary.json
  data/processed/paper_dataset_links.json

Uso:
  python3 analysis/67_render_sala.py

Drift check no CI: re-roda + diffa docs/sala.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _safe_md import sanitize_cell  # noqa: E402  — sanitiza títulos não-confiáveis

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
OUT_MD = ROOT / "docs" / "sala.md"

GH = "https://github.com/freirelucas/rio-edu-lab"
GH_ACTIONS = f"{GH}/actions/workflows"

# Órgãos da corporação → (arquivo do workflow, sistema VSM, descrição, cadência)
ORGAOS = [
    ("ci.yml", "S2", "Coordenação — drift checks anti-oscilação", "cada push"),
    ("pages.yml", "S1.f", "Hotsite — deploy do site", "cada push"),
    ("algedonic-alert.yml", "—", "Canal algedônico — emergência", "CI falha"),
    ("s3star-audit.yml", "S3*", "Auditoria — drift interno esporádico", "mensal"),
    ("s4-scout.yml", "S4", "Inteligência — gaps + oportunidades externas", "mensal"),
    ("snowball.yml", "S1.a", "Descoberta — snowball multi-fonte", "semanal 💤"),
]


def _load(name: str):
    p = PROCESSED / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def render() -> str:
    funnel = _load("funnel_state.json") or {}
    catalog = _load("papers_catalog_summary.json") or {}
    inbox = _load("curatorial_inbox.json") or []
    top = _load("top_summary.json") or {}
    prov = _load("provenance_summary.json") or []
    ds_links = _load("paper_dataset_links.json") or []

    L: list[str] = []
    L.append("---")
    L.append("title: 🛰️ Sala de Operação")
    L.append("description: Estado vivo da corporação cibernética do rio-edu-lab — funil, órgãos autônomos, fila curatorial, transparência e auditabilidade. Pública por design (transparência ativa).")
    L.append("---")
    L.append("")
    L.append("# 🛰️ Sala de Operação")
    L.append("")
    L.append("> **Cybersyn moderno.** Esta tela mostra o estado vivo da [corporação cibernética](corporacao.md). "
             "É **pública por design** — transparência ativa é a missão. O *controle* (aprovar, pausar, disparar) "
             "acontece no GitHub, que já autentica você.")
    L.append("")
    L.append("!!! info \"Observar vs. Agir\"")
    L.append("    **Observar** (todos, aqui): ver o estado. · **Agir** (só o curador, no GitHub): "
             "mergear PR = aprovar · desabilitar workflow = pausar · `workflow_dispatch` = disparar. "
             "O login do GitHub já é o gate de controle.")
    L.append("")

    # ── KPI grid — funil ──────────────────────────────────────────────────
    L.append("## 📊 Funil de descoberta")
    L.append("")
    s1 = funnel.get("stage1_candidates", "—")
    s2 = funnel.get("stage2_with_requirements", "—")
    # Catálogo/replicados: preferir papers_catalog_summary (fonte canônica,
    # mais fresca que funnel_state que só re-roda no 25).
    s4 = catalog.get("n_papers", funnel.get("stage4_catalog", "—"))
    _by_status = catalog.get("by_replication_status") or {}
    _full = _by_status.get("full", 0)
    _partial = _by_status.get("partial", 0)
    rep = f"{_full} full · {_partial} partial" if _by_status else funnel.get("replicated_total", "—")
    L.append('<div class="grid cards" markdown>')
    L.append("")
    L.append(f"- :material-magnify:{{ .lg .middle }} __{s1}__ candidates descobertos")
    L.append(f"- :material-filter:{{ .lg .middle }} __{s2}__ com requisitos (Stage 2)")
    L.append(f"- :material-book-open-variant:{{ .lg .middle }} __{s4}__ no catálogo")
    L.append(f"- :material-check-decagram:{{ .lg .middle }} __{rep}__ replicados end-to-end")
    L.append("")
    L.append("</div>")
    L.append("")
    # data.rio coverage
    dr_total = funnel.get("data_rio_total", "—")
    dr_active = funnel.get("data_rio_active", "—")
    dr_orphan = funnel.get("data_rio_orphan", "—")
    L.append(f"**data.rio**: {dr_active} itens ativos · {dr_orphan} órfãos · {dr_total} total.")
    L.append("")
    # Embed funnel chart if present
    if (ROOT / "docs" / "_assets" / "charts" / "funnel.json").exists():
        L.append('<div data-chart="_assets/charts/funnel.json"></div>')
        L.append("")

    # ── Órgãos da corporação (badges live) ────────────────────────────────
    L.append("## 🫀 Órgãos da corporação")
    L.append("")
    L.append("Status **ao vivo** (badges nativos do GitHub Actions — sempre atuais):")
    L.append("")
    L.append("| Órgão | VSM | Função | Cadência | Status ao vivo |")
    L.append("|---|:--:|---|---|---|")
    for wf, vsm, desc, cad in ORGAOS:
        badge = f"[![status]({GH_ACTIONS}/{wf}/badge.svg)]({GH_ACTIONS}/{wf})"
        L.append(f"| `{wf}` | {vsm} | {desc} | {cad} | {badge} |")
    L.append("")
    L.append("💤 = dormente (espera secret). 🔒 Os órgãos autônomos (audit, scout, keepalive, snowball) "
             "só disparam com a chave-mestra `CORP_ACTIVE=true` — **desligados por padrão**. "
             "Ver [ativação + garantias anti-loop](corporacao.md).")
    L.append("")

    # ── Fila curatorial ───────────────────────────────────────────────────
    L.append("## 📋 Fila curatorial (inbox)")
    L.append("")
    n_inbox = len(inbox)
    n_br = sum(1 for r in inbox if r.get("is_brazilian"))
    L.append(f"**{n_inbox} candidates** aguardando decisão ({n_br} 🇧🇷). "
             f"Comunidade pode [reivindicar replicação]({GH}/issues/new?template=replication-claim.md).")
    L.append("")
    L.append("| # | 🇧🇷 | Cit | Score | Paper |")
    L.append("|--:|:--:|--:|--:|---|")
    for i, r in enumerate(inbox[:10], 1):
        br = "🇧🇷" if r.get("is_brazilian") else ""
        cit = f"{r.get('citations', 0):,}"
        score = r.get("priority_score", "—")
        title = sanitize_cell(r.get("title"), max_len=55)
        L.append(f"| {i} | {br} | {cit} | {score} | {title} |")
    L.append("")
    if n_inbox > 10:
        L.append(f"_(top 10 de {n_inbox} — fila completa em [inbox](inbox.md))_")
        L.append("")

    # ── Transparência (TOP scorecard) ─────────────────────────────────────
    L.append("## 🔬 Transparência (TOP Guidelines)")
    L.append("")
    n_p = top.get("n_papers", "—")
    mean = top.get("mean_total_score")
    maxp = top.get("max_possible", 16)
    if isinstance(mean, (int, float)):
        pct = int(100 * mean / maxp) if maxp else 0
        L.append(f"Score médio de transparência: **{mean:.1f}/{maxp}** (~{pct}%) sobre {n_p} papers. "
                 f"Detalhe por standard em [TOP scorecard](top-scorecard.md).")
    else:
        L.append(f"TOP scorecard sobre {n_p} papers — ver [detalhe](top-scorecard.md).")
    L.append("")

    # ── Auditabilidade (provenance) ───────────────────────────────────────
    L.append("## 🔗 Auditabilidade (provenance chains)")
    L.append("")
    n_complete = sum(1 for p in prov if p.get("audit_chain_complete"))
    L.append(f"**{n_complete}/{len(prov)} papers** com cadeia de proveniência completa "
             "(paper DOI → dados → código → resultados, verificável um-clique):")
    L.append("")
    L.append("| Paper | Cadeia | Fontes | Scripts | Outputs |")
    L.append("|---|:--:|--:|--:|--:|")
    for p in prov:
        chain = "✅" if p.get("audit_chain_complete") else "⚠️"
        pid = p.get("paper_id", "?")
        L.append(f"| [{pid}](provenance/{pid}.md) | {chain} | "
                 f"{p.get('n_data_sources', 0)} | {p.get('n_scripts', 0)} | {p.get('n_processed_outputs', 0)} |")
    L.append("")

    # ── Paper↔dataset ─────────────────────────────────────────────────────
    if ds_links:
        L.append("## 🧬 Paper↔dataset (sinal declarativo)")
        L.append("")
        L.append(f"**{len(ds_links)} papers** citam DOI de dataset declaradamente (precisão ~100%). "
                 f"Ver [detalhe](produtos/paper_dataset_links.md).")
        L.append("")

    # ── Como agir ─────────────────────────────────────────────────────────
    L.append("## 🎛️ Como agir (control room)")
    L.append("")
    L.append("O GitHub é a sala de controle autenticada. Você (curador) age assim:")
    L.append("")
    L.append(f"- **Aprovar** promoção/mudança → mergear o [PR]({GH}/pulls)")
    L.append(f"- **Pausar** um órgão → desabilitar o workflow na [aba Actions]({GH}/actions)")
    L.append(f"- **Disparar** manualmente → `Run workflow` ([workflow_dispatch]({GH}/actions))")
    L.append(f"- **Emergência** → issues com label [`priority:critical`]({GH}/labels/priority%3Acritical)")
    L.append("")
    L.append("---")
    L.append("")
    L.append("_Auto-gerado por `analysis/67_render_sala.py` a partir de estado committado. "
             "Badges de órgãos são ao vivo. Drift-checked no CI. Pública — transparência ativa._")
    return "\n".join(L)


def main() -> int:
    md = render()
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
