"""Render paper_dataset_links.md — papers do funil que citam DOI dataset.

Sprint v0.18 — entrega #2. Consome `dataset_refs` populado por
`analysis/45d_dataset_refs.py` e renderiza tabela navegável no hotsite.

Sinal: paper que CITA dataset com DOI (via OpenAlex referenced_works
filtered por type=dataset) é declarativo pelo autor — ~100% precisão.
Diferente de IDF lexical (probabilístico), aqui é "fato" de bibliografia.

Drift-checked: re-roda em CI se data/papers_funnel.yml mudar.

Uso:
  python3 analysis/64_render_paper_dataset_links.py
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _safe_md import sanitize_cell  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
OUT_MD = ROOT / "docs" / "produtos" / "paper_dataset_links.md"
OUT_JSON = ROOT / "data" / "processed" / "paper_dataset_links.json"


def collect_links(candidates: list[dict]) -> list[dict]:
    """Pra cada candidate com dataset_refs não-vazio, retorna row pra tabela."""
    rows = []
    for c in candidates:
        refs = c.get("dataset_refs") or []
        if not refs:
            continue
        oid = (c.get("openalex_id") or "").split("/")[-1]
        rows.append({
            "openalex_id": oid,
            "title": (c.get("title") or "")[:100],
            "citations": c.get("citations") or 0,
            "year": c.get("year"),
            "is_brazilian": bool(c.get("is_brazilian")),
            "doi": c.get("doi"),
            "n_dataset_refs": len(refs),
            "dataset_refs": refs[:5],  # top-5 pra display
        })
    # Sort: BR first, then n_dataset_refs desc, then citations desc
    rows.sort(key=lambda r: (
        -int(r["is_brazilian"]),
        -r["n_dataset_refs"],
        -r["citations"],
    ))
    return rows


def render_markdown(rows: list[dict], n_total_funnel: int) -> str:
    lines = []
    lines.append("---")
    lines.append("title: Papers que citam datasets com DOI declarado")
    lines.append("description: Sinal declarativo paper↔dataset via OpenAlex referenced_works filtered por type=dataset. Não inferência IDF — fato bibliográfico.")
    lines.append("---")
    lines.append("")
    lines.append("# Papers que citam datasets com DOI declarado")
    lines.append("")
    lines.append(
        "Resultado do `analysis/45d_dataset_refs.py` (v0.17.f). Pra cada candidate "
        "do funil, OpenAlex `referenced_works` foi filtrado por `type=dataset` — "
        "ou seja, papers que **declararam citar** um dataset com DOI canônico. "
        "Sinal de ~100% precisão (declaração do autor, não inferência semântica)."
    )
    lines.append("")
    lines.append(f"**Estado**: {len(rows)} papers com ≥1 dataset ref de {n_total_funnel} candidates no funil.")
    lines.append("")
    if not rows:
        lines.append("!!! info")
        lines.append("    Nenhum candidate tem `dataset_refs` populated ainda.")
        lines.append("    Rode `OPENALEX_EMAIL=... python3 analysis/45d_dataset_refs.py --limit 100`")
        lines.append("    pra popular o sinal.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Top papers por sinal dataset")
    lines.append("")
    lines.append("| BR? | n_refs | citações | Year | Paper | Dataset DOIs |")
    lines.append("|---|---:|---:|---|---|---|")
    for r in rows[:50]:  # cap visual em 50
        br = "🇧🇷" if r["is_brazilian"] else " "
        title = sanitize_cell(r["title"], max_len=60)
        year = r["year"] or "?"
        cit = r["citations"]
        n = r["n_dataset_refs"]
        # Render top-3 dataset titles
        ds_titles = []
        for d in r["dataset_refs"][:3]:
            t = sanitize_cell(d.get("title") or "?", max_len=40)
            doi = d.get("doi")
            if doi:
                ds_titles.append(f"[{t}](https://doi.org/{doi})")
            else:
                ds_titles.append(t)
        ds_str = "<br>".join(ds_titles)
        lines.append(f"| {br} | {n} | {cit} | {year} | {title} | {ds_str} |")
    lines.append("")
    if len(rows) > 50:
        lines.append(f"_(mostrando 50 de {len(rows)}; dataset completo em [`data/processed/paper_dataset_links.json`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/processed/paper_dataset_links.json))_")
        lines.append("")
    lines.append("## Como funciona")
    lines.append("")
    lines.append("O OpenAlex captura o campo `referenced_works` de cada paper — IDs OpenAlex das obras CITADAS (não similaridade). Pra cada paper do priority pool (fully-covered + BR + top-cit), `analysis/45d_dataset_refs.py` faz batch-lookup dos refs e filtra `type ∈ {dataset, software-source-code, software, supplementary-materials}`.")
    lines.append("")
    lines.append("Recomendação dos 5 agentes especialistas v0.16: este é o sinal **mais forte** pra paper↔dataset linkage (precisão ~100%) — autor declarou no manuscript que cita o dataset com DOI.")
    return "\n".join(lines)


def main() -> int:
    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML}", file=sys.stderr)
        return 1
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    n_total = len(candidates)
    print(f"loaded {n_total} candidates", file=sys.stderr)

    rows = collect_links(candidates)
    print(f"  {len(rows)} candidates com ≥1 dataset ref", file=sys.stderr)

    md = render_markdown(rows, n_total)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_MD.relative_to(ROOT)}", file=sys.stderr)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
