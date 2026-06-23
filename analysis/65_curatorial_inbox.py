"""Curatorial inbox — top-N candidates do funil pra comunidade votar.

Sprint v0.19 (autopilot expansion) — entrega #2. Render `docs/inbox.md`
com queue priorizada pra próximas replicações: score composite (match
enriched) × citation × dataset_refs × is_brazilian.

Mecanismo público de crítica: cada paper aqui tem link pra "Claim"
(issue template) + "Sugerir paper diferente" (issue template). Reduz
gargalo curatorial de Lucas.

Drift-checked no CI (drift #16).

Filtra:
- já no catálogo (não duplicar)
- coverage `available` (parcial ou full)
- score significativo (composite ≥ 5 OR n_dataset_refs ≥ 1 OR is_brazilian)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
OUT_MD = ROOT / "docs" / "inbox.md"
OUT_JSON = ROOT / "data" / "processed" / "curatorial_inbox.json"


def load_catalog_ids(catalog_path: Path) -> set[str]:
    """OpenAlex IDs já no catalog → não promover."""
    if not catalog_path.exists():
        return set()
    cat = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    ids = set()
    for p in cat.get("papers") or []:
        oid = p.get("openalex_id") or ""
        if oid:
            ids.add(oid.split("/")[-1])
    return ids


def compute_priority_score(c: dict) -> float:
    """Composite priority score pra ranking inbox.

    Componentes:
    - composite máximo entre coverage rows (match enriched)
    - log10(citations + 1)
    - n_dataset_refs (paper↔dataset declarado, gold)
    - bonus is_brazilian (+2)
    """
    import math

    cov = c.get("coverage") or []
    composites = [
        (r.get("match_detail") or {}).get("composite") or 0
        for r in cov
    ]
    max_composite = max(composites) if composites else 0

    citations = c.get("citations") or 0
    cit_score = math.log10(citations + 1)

    n_ds = len(c.get("dataset_refs") or [])
    br_bonus = 2.0 if c.get("is_brazilian") else 0

    # Weights subjetivos — composite domina, cit log + dataset linkage + BR
    return max_composite * 2.0 + cit_score * 1.5 + n_ds * 3.0 + br_bonus


def is_inbox_eligible(c: dict, catalog_ids: set[str]) -> bool:
    """Critérios pra entrar no inbox."""
    oid_full = c.get("openalex_id") or ""
    oid = oid_full.split("/")[-1] if oid_full else ""
    if oid and oid in catalog_ids:
        return False  # já no catálogo

    cov = c.get("coverage") or []
    has_available = any((r.get("status") == "available") for r in cov)
    if not has_available:
        return False

    composites = [
        (r.get("match_detail") or {}).get("composite") or 0
        for r in cov
    ]
    max_comp = max(composites) if composites else 0

    n_ds = len(c.get("dataset_refs") or [])
    br = bool(c.get("is_brazilian"))

    return max_comp >= 5.0 or n_ds >= 1 or br


def collect_inbox_rows(candidates: list[dict], catalog_ids: set[str], top_n: int = 50) -> list[dict]:
    rows = []
    for c in candidates:
        if not is_inbox_eligible(c, catalog_ids):
            continue
        oid = (c.get("openalex_id") or "").split("/")[-1]
        cov = c.get("coverage") or []
        composites = [(r.get("match_detail") or {}).get("composite") or 0 for r in cov]
        rows.append({
            "openalex_id": oid,
            "title": (c.get("title") or "")[:120],
            "year": c.get("year"),
            "citations": c.get("citations") or 0,
            "is_brazilian": bool(c.get("is_brazilian")),
            "doi": c.get("doi"),
            "max_composite": round(max(composites) if composites else 0, 2),
            "n_dataset_refs": len(c.get("dataset_refs") or []),
            "n_coverage": len(cov),
            "priority_score": round(compute_priority_score(c), 2),
        })
    rows.sort(key=lambda r: -r["priority_score"])
    return rows[:top_n]


def render_markdown(rows: list[dict], n_total_funnel: int, n_catalog: int) -> str:
    lines = []
    lines.append("---")
    lines.append("title: 📋 Inbox curatorial — papers candidatos a próxima replicação")
    lines.append("description: Fila priorizada de papers do funil pra próxima replicação. Comunidade pode reivindicar (claim) ou sugerir alternativas via GitHub issues.")
    lines.append("---")
    lines.append("")
    lines.append("# 📋 Inbox curatorial")
    lines.append("")
    lines.append(f"**{n_total_funnel} candidates no funil**, **{n_catalog} no catálogo**. ")
    lines.append("Esta página lista os papers que **deveriam entrar próximo**, priorizados por:")
    lines.append("")
    lines.append("- `match_enriched.composite` (sinal estruturado paper↔data.rio)")
    lines.append("- `dataset_refs` (citação declarada de DOI dataset — sinal forte ~100% precisão)")
    lines.append("- `citations` (log-escala) + bônus BR")
    lines.append("")
    lines.append("## Como contribuir")
    lines.append("")
    lines.append('1. **Quer replicar?** Abra issue [`🔬 Claim`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=replication-claim.md) com o paper-id. PwC-style — primeiro a reivindicar trabalha (30d timeout).')
    lines.append('2. **Conhece um paper melhor?** [`📚 Sugerir paper`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=sugerir-paper.md).')
    lines.append('3. **Conhece outra fonte além OpenAlex?** [`💡 Sugerir source`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=sugerir-source.md).')
    lines.append('4. **Bug ou data quebrado?** [`🐛 Bug report`](https://github.com/freirelucas/rio-edu-lab/issues/new?template=bug-report.md).')
    lines.append("")
    lines.append("[💬 Discussão geral nos GitHub Discussions](https://github.com/freirelucas/rio-edu-lab/discussions)")
    lines.append("")

    if not rows:
        lines.append("!!! info")
        lines.append("    Inbox vazio. Rode `python3 analysis/47_check_coverage.py --force` + ")
        lines.append("    `python3 analysis/45d_dataset_refs.py` pra popular sinais.")
        lines.append("")
        return "\n".join(lines)

    lines.append(f"## Top {len(rows)} candidatos")
    lines.append("")
    lines.append("| # | Score | BR? | Cit | Comp | Datasets | Year | Title | Action |")
    lines.append("|--:|--:|:-:|--:|--:|--:|--:|---|:--:|")
    for i, r in enumerate(rows, 1):
        br = "🇧🇷" if r["is_brazilian"] else " "
        title = r["title"][:60]
        year = r["year"] or "?"
        cit = r["citations"]
        comp = r["max_composite"]
        n_ds = r["n_dataset_refs"]
        oid = r["openalex_id"]
        claim_url = f"https://github.com/freirelucas/rio-edu-lab/issues/new?template=replication-claim.md&title=[claim]+{oid}"
        action = f"[Claim]({claim_url})"
        lines.append(f"| {i} | **{r['priority_score']}** | {br} | {cit:,} | {comp} | {n_ds} | {year} | {title} | {action} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Auto-gerado por `analysis/65_curatorial_inbox.py`. Drift-checked no CI._")
    return "\n".join(lines)


def main() -> int:
    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML}", file=sys.stderr)
        return 1
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    n_total = len(candidates)
    print(f"loaded {n_total} candidates", file=sys.stderr)

    catalog_ids = load_catalog_ids(CATALOG_YML)
    print(f"catalog has {len(catalog_ids)} papers (excluindo do inbox)", file=sys.stderr)

    rows = collect_inbox_rows(candidates, catalog_ids, top_n=50)
    print(f"  {len(rows)} candidates no inbox", file=sys.stderr)

    md = render_markdown(rows, n_total, len(catalog_ids))
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(ROOT)}", file=sys.stderr)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
