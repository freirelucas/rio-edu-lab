"""Gera artefatos de visualização do estado atual do funil de replicação.

Lê o estado canônico em:
  - data/papers_funnel.yml      (Stages 1-3: snowball, scoring, coverage)
  - data/papers_catalog.yml     (Stage 4: catálogo curado)
  - data/manifest.json          (substrato data.rio: 9.855 itens)
  - data/requirements_taxonomy.yml  (10 categorias canônicas de dado)

Escreve:
  - docs/_assets/charts/funnel.json           Plotly Funnel (4 estágios)
  - docs/_assets/charts/data_rio_coverage.json Plotly Donut (ativos vs órfãos)
  - docs/_assets/charts/themes.json           Plotly Bar (papers por categoria)
  - data/processed/funnel_state.json          métricas flat para inclusão markdown

Determinístico, idempotente, CI-friendly. Reroda sem efeitos colaterais.

Uso:
  python3 analysis/25_funnel_state.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"

CHARTS_DIR = ROOT / "docs" / "_assets" / "charts"
STATE_JSON = ROOT / "data" / "processed" / "funnel_state.json"
INDEX_MD = ROOT / "docs" / "index.md"

# Funil analítico: os números do funil na landing são derivados do estado, não
# hardcoded. 25 reescreve o bloco entre estes marcadores em docs/index.md.
BIGNUMS_START = "<!-- funnel:bignums:start (gerado por analysis/25_funnel_state.py) -->"
BIGNUMS_END = "<!-- funnel:bignums:end -->"

PLOTLY_FONT = {"family": "Inter, system-ui, sans-serif", "size": 14}


def compute_state() -> dict:
    funnel = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8"))
    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8"))
    taxonomy = yaml.safe_load(TAXONOMY_YML.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))

    candidates = funnel.get("candidates", [])
    papers = catalog.get("papers", [])
    categories = taxonomy.get("categories", [])
    items = manifest.get("items", [])

    stage1 = len(candidates)
    stage2 = sum(1 for c in candidates if c.get("suggested_requirements"))
    stage4 = len(papers)
    replicated = sum(
        1 for p in papers if p.get("replication_status") in ("full", "partial")
    )

    status_breakdown = Counter(p.get("replication_status") for p in papers)

    # "Ativados" = itens do data.rio usados por papers REPLICADOS (full/partial).
    # Coberturas de papers `pending` são sugestões provisórias do matching IDF
    # (validadas só na replicação real), então não contam como ativadas — senão
    # promover candidatos infla o número sem nenhuma replicação nova.
    active_items = set()
    for p in papers:
        if p.get("replication_status") not in ("full", "partial"):
            continue
        for cov in p.get("data_rio_coverage") or []:
            iid = cov.get("item_id")
            if iid:
                active_items.add(iid)

    total_items = len(items)
    n_active = len(active_items)
    n_orphan = total_items - n_active

    candidates_per_category: Counter = Counter()
    for c in candidates:
        for sr in c.get("suggested_requirements") or []:
            if isinstance(sr, dict):
                cid = sr.get("category_id")
                if cid:
                    candidates_per_category[cid] += 1

    catalog_per_category: Counter = Counter()
    for p in papers:
        for cov in p.get("data_rio_coverage") or []:
            cid_or_label = cov.get("category_id") or cov.get("requirement", "")
            if cid_or_label:
                catalog_per_category[cid_or_label] += 1

    type_dist = Counter(it.get("type", "Outros") for it in items)

    conversion_rate = round(stage4 / stage1 * 100, 1) if stage1 else 0.0
    replication_rate = round(replicated / stage4 * 100, 1) if stage4 else 0.0
    coverage_pct = round(n_active / total_items * 100, 2) if total_items else 0.0

    return {
        "stage1_candidates": stage1,
        "stage2_with_requirements": stage2,
        "stage4_catalog": stage4,
        "replicated_total": replicated,
        "status_breakdown": dict(status_breakdown),
        "data_rio_total": total_items,
        "data_rio_active": n_active,
        "data_rio_orphan": n_orphan,
        "coverage_pct": coverage_pct,
        "conversion_rate_pct": conversion_rate,
        "replication_rate_pct": replication_rate,
        "categories": [
            {
                "id": c["id"],
                "label": c.get("label_pt", c["id"]),
                "n_funnel": candidates_per_category.get(c["id"], 0),
            }
            for c in categories
        ],
        "type_top10": [{"type": t, "n": n} for t, n in type_dist.most_common(10)],
    }


def render_funnel_chart(state: dict) -> dict:
    """Plotly Funnel: 4 stages with real numbers."""
    return {
        "data": [
            {
                "type": "funnel",
                "y": [
                    "candidatos",
                    "tema relevante",
                    "catálogo",
                    "replicados",
                ],
                "x": [
                    state["stage1_candidates"],
                    state["stage2_with_requirements"],
                    state["stage4_catalog"],
                    state["replicated_total"],
                ],
                "textinfo": "value+percent initial",
                "marker": {
                    "color": ["#d8d8d8", "#a8a8a8", "#6f6f6f", "#1a9850"],
                },
                "connector": {"line": {"color": "#ddd", "width": 1}},
            }
        ],
        "layout": {
            "margin": {"l": 110, "r": 30, "t": 20, "b": 20},
            "height": 320,
            "font": PLOTLY_FONT,
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
        },
        "config": {"displayModeBar": False, "responsive": True},
    }


def render_coverage_chart(state: dict) -> dict:
    """Plotly Donut: data.rio items ativos vs órfãos."""
    return {
        "data": [
            {
                "type": "pie",
                "values": [state["data_rio_active"], state["data_rio_orphan"]],
                "labels": [
                    f"Ativos ({state['data_rio_active']})",
                    f"Inexplorados ({state['data_rio_orphan']:,})".replace(",", "."),
                ],
                "hole": 0.6,
                "marker": {"colors": ["#1a9850", "#e8e8e8"]},
                "textinfo": "label",
                "textposition": "outside",
                "showlegend": False,
                "sort": False,
            }
        ],
        "layout": {
            "margin": {"l": 20, "r": 20, "t": 20, "b": 20},
            "height": 280,
            "font": PLOTLY_FONT,
            "annotations": [
                {
                    "text": f"<b>{state['coverage_pct']}%</b><br>cobertura",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 18},
                }
            ],
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
        },
        "config": {"displayModeBar": False, "responsive": True},
    }


def render_themes_chart(state: dict) -> dict:
    """Plotly horizontal bar: candidatos do funil por categoria taxonômica."""
    cats = sorted(state["categories"], key=lambda c: c["n_funnel"])
    labels = [c["label"] for c in cats]
    values = [c["n_funnel"] for c in cats]
    return {
        "data": [
            {
                "type": "bar",
                "orientation": "h",
                "y": labels,
                "x": values,
                "text": [str(v) if v else "" for v in values],
                "textposition": "outside",
                "marker": {"color": "#6f6f6f"},
            }
        ],
        "layout": {
            "margin": {"l": 280, "r": 40, "t": 20, "b": 30},
            "height": 360,
            "font": PLOTLY_FONT,
            "xaxis": {"title": "candidatos no funil"},
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
        },
        "config": {"displayModeBar": False, "responsive": True},
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def render_bignums(state: dict) -> str:
    """The 4-stage big-num grid for the landing, sourced from funnel state."""
    cells = [
        (state["stage1_candidates"], "candidatos no funil (snowball bibliométrico)"),
        (state["stage2_with_requirements"], "com tema educacional relevante"),
        (state["stage4_catalog"], "papers no catálogo curado"),
        (state["replicated_total"], "replicados publicados"),
    ]
    lines = ['<div class="big-num-grid">']
    for num, label in cells:
        lines.append(
            f'  <div class="big-num"><span class="num">{num}</span>'
            f'<span class="label">{label}</span></div>'
        )
    lines.append("</div>")
    return "\n".join(lines)


def inject_block(path: Path, start: str, end: str, content: str) -> bool:
    """Replace the text between `start` and `end` markers with `content`.

    Returns True if the file changed. Raises if markers are absent (so a
    renamed/removed marker fails loudly in CI instead of silently no-op'ing).
    """
    text = path.read_text(encoding="utf-8")
    block = f"{start}\n{content}\n{end}"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pat.search(text):
        raise SystemExit(f"markers not found in {path.relative_to(ROOT)}: {start!r}")
    new = pat.sub(lambda _m: block, text)
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    for required in (FUNNEL_YML, CATALOG_YML, TAXONOMY_YML, MANIFEST_JSON):
        if not required.exists():
            print(f"missing: {required.relative_to(ROOT)}", file=sys.stderr)
            return 1

    state = compute_state()

    write_json(CHARTS_DIR / "funnel.json", render_funnel_chart(state))
    write_json(CHARTS_DIR / "data_rio_coverage.json", render_coverage_chart(state))
    write_json(CHARTS_DIR / "themes.json", render_themes_chart(state))
    write_json(STATE_JSON, state)

    if INDEX_MD.exists() and inject_block(INDEX_MD, BIGNUMS_START, BIGNUMS_END, render_bignums(state)):
        print(f"updated big-nums in {INDEX_MD.relative_to(ROOT)}")

    print(
        f"funnel: {state['stage1_candidates']} → {state['stage2_with_requirements']} → "
        f"{state['stage4_catalog']} → {state['replicated_total']} "
        f"({state['conversion_rate_pct']}% end-to-end)"
    )
    print(
        f"data.rio: {state['data_rio_active']} ativos / "
        f"{state['data_rio_orphan']:,} órfãos / {state['coverage_pct']}% cobertura".replace(",", ".")
    )
    print(f"wrote {CHARTS_DIR.relative_to(ROOT)}/{{funnel,data_rio_coverage,themes}}.json")
    print(f"wrote {STATE_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
