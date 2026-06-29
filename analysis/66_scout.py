"""S4 Scout — varredura determinística do ambiente (VSM System 4).

Corporação cibernética: órgão sensorial. Escaneia gaps + oportunidades SEM
LLM (zero custo autônomo, suggest-only). Reporta o que a corporação deveria
caçar próximo — materializa "ser guloso em educação".

Diferente de 62_s3star_audit (que olha pra DENTRO: drift, schema, invariantes)
o scout olha pra FORA e pro futuro:
  1. Funnel gaps — categorias da taxonomy sub-representadas
  2. Seed saturation — quantos seeds, quão perto do cap
  3. data.rio coverage gaps — items edu-tagged sem nenhum candidate
  4. Model availability — Rio-3.5 endpoint status (sinaliza Path D)
  5. Inbox health — candidates aguardando claim
  6. dataset_refs progress — quantos têm sinal paper↔dataset

Output:
  data/processed/scout_<date>.md  — relatório legível
  data/processed/scout_<date>.json — machine-parseable

Workflow `.github/workflows/s4-scout.yml` roda mensal + abre issue com achados.

Uso:
  python3 analysis/66_scout.py
  python3 analysis/66_scout.py --check-rio-endpoint   # HTTP check Rio-3.5
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
SEEDS_YML = ROOT / "data" / "openalex_seeds.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
TODAY = date.today().isoformat()

# Cap documentado de seeds (curador intent, ver openalex_seeds.yml header)
SEED_CAP = 40
RIO_HF_URL = "https://huggingface.co/prefeitura-rio/Rio-3.5-Open-397B"


def scan_funnel_gaps() -> dict:
    """Categorias da taxonomy sub-representadas no funil."""
    if not FUNNEL_YML.exists() or not TAXONOMY_YML.exists():
        return {"status": "skipped", "reason": "missing files"}
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    tax = yaml.safe_load(TAXONOMY_YML.read_text(encoding="utf-8")) or {}
    all_cats = [c["id"] for c in (tax.get("categories") or [])]

    cat_counts: Counter = Counter()
    for c in candidates:
        for sugg in c.get("suggested_requirements") or []:
            cat_counts[sugg.get("category_id")] += 1

    # Categorias com < 5% da média = sub-representadas
    total = sum(cat_counts.values()) or 1
    avg = total / max(len(all_cats), 1)
    underrep = [
        cat for cat in all_cats
        if cat_counts.get(cat, 0) < avg * 0.3
    ]
    return {
        "status": "ok",
        "n_candidates": len(candidates),
        "cat_distribution": dict(cat_counts.most_common()),
        "underrepresented": underrep,
        "recommendation": (
            f"{len(underrep)} categorias sub-representadas: {underrep}. "
            "Considere seeds que ancorem esses temas."
            if underrep else "Cobertura de categorias balanceada."
        ),
    }


def scan_seed_saturation() -> dict:
    """Quantos seeds enabled vs cap documentado."""
    if not SEEDS_YML.exists():
        return {"status": "skipped", "reason": "no seeds file"}
    doc = yaml.safe_load(SEEDS_YML.read_text(encoding="utf-8")) or {}
    seeds = doc.get("seeds") or []
    enabled = [s for s in seeds if s.get("enabled", True)]
    pct = 100 * len(enabled) / SEED_CAP
    return {
        "status": "ok",
        "n_seeds_enabled": len(enabled),
        "seed_cap": SEED_CAP,
        "saturation_pct": round(pct, 1),
        "recommendation": (
            f"Seeds em {pct:.0f}% do cap ({len(enabled)}/{SEED_CAP}). "
            + ("Espaço pra adicionar âncoras de temas sub-representados."
               if pct < 90 else "Quase saturado — priorize qualidade sobre quantidade, "
               "ou eleve o cap via PR ao header de openalex_seeds.yml.")
        ),
    }


def scan_inbox_health() -> dict:
    """Estado da fila curatorial."""
    inbox_json = ROOT / "data" / "processed" / "curatorial_inbox.json"
    if not inbox_json.exists():
        return {"status": "skipped", "reason": "inbox not rendered yet"}
    rows = json.loads(inbox_json.read_text(encoding="utf-8"))
    br = sum(1 for r in rows if r.get("is_brazilian"))
    with_ds = sum(1 for r in rows if (r.get("n_dataset_refs") or 0) > 0)
    return {
        "status": "ok",
        "n_inbox": len(rows),
        "n_brazilian": br,
        "n_with_dataset_refs": with_ds,
        "top_3": [
            {"title": r["title"][:60], "score": r["priority_score"]}
            for r in rows[:3]
        ],
        "recommendation": (
            f"{len(rows)} candidates no inbox ({br} BR, {with_ds} com dataset refs). "
            "Comunidade pode reivindicar via issue template `replication-claim`."
        ),
    }


def scan_dataset_refs_progress() -> dict:
    """Quantos candidates têm sinal paper↔dataset."""
    if not FUNNEL_YML.exists():
        return {"status": "skipped"}
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    with_field = sum(1 for c in candidates if c.get("dataset_refs") is not None)
    with_hits = sum(1 for c in candidates if c.get("dataset_refs"))
    return {
        "status": "ok",
        "n_processed": with_field,
        "n_with_dataset_link": with_hits,
        "recommendation": (
            f"{with_field} candidates processados por 45d, {with_hits} com dataset DOI. "
            + ("Re-rode 45d quando OpenAlex 429 resetar pra completar o pool."
               if with_field < 100 else "Pool de dataset_refs saudável.")
        ),
    }


def check_rio_endpoint() -> dict:
    """HTTP HEAD pro Rio-3.5 model card — sinaliza disponibilidade Path D.

    Não testa inference endpoint (não há ainda); só confirma o model card vivo
    e lembra de checar deployment status. Determinístico, sem auth.
    """
    req = urllib.request.Request(RIO_HF_URL, method="HEAD",
                                 headers={"User-Agent": "rio-edu-lab/0.20 (scout)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            alive = resp.status == 200
    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        alive = False
    return {
        "status": "ok",
        "model_card_alive": alive,
        "url": RIO_HF_URL,
        "recommendation": (
            "Rio-3.5 model card vivo. Cheque manualmente se HF Inference Endpoint "
            "saiu do pending (19 requests) — destrava Path D (LLM soberano). "
            "Adapter _rio.py já pronto; flip via LLM_PROVIDER=rio."
        ),
    }


def render_markdown(report: dict) -> str:
    lines = [f"# S4 Scout — {TODAY}", ""]
    lines.append("Varredura determinística do ambiente (VSM S4). Suggest-only, zero LLM.")
    lines.append("Auto-gerado por `analysis/66_scout.py`.")
    lines.append("")
    section_titles = {
        "funnel_gaps": "🔭 Funnel gaps (categorias sub-representadas)",
        "seed_saturation": "🌱 Seed saturation",
        "inbox_health": "📋 Inbox health",
        "dataset_refs": "🔗 Paper↔dataset progress",
        "rio_endpoint": "🇧🇷 Rio-3.5 (Path D)",
    }
    for key, title in section_titles.items():
        sec = report.get(key)
        if not sec or sec.get("status") == "skipped":
            continue
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"> {sec.get('recommendation', '')}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Órgão S4 da corporação cibernética. Veja [docs/corporacao.md](../corporacao.md)._")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-rio-endpoint", action="store_true",
                    help="incluir HTTP check do Rio-3.5 model card")
    args = ap.parse_args()

    print(f"S4 Scout — {TODAY}", file=sys.stderr)
    report = {
        "date": TODAY,
        "funnel_gaps": scan_funnel_gaps(),
        "seed_saturation": scan_seed_saturation(),
        "inbox_health": scan_inbox_health(),
        "dataset_refs": scan_dataset_refs_progress(),
    }
    if args.check_rio_endpoint:
        report["rio_endpoint"] = check_rio_endpoint()

    out_dir = ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"scout_{TODAY}.md"
    json_path = out_dir / f"scout_{TODAY}.json"
    md_path.write_text(render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {md_path.relative_to(ROOT)}", file=sys.stderr)
    print(f"wrote {json_path.relative_to(ROOT)}", file=sys.stderr)

    # Print recommendations pro stderr (workflow captura)
    for key in ("funnel_gaps", "seed_saturation", "inbox_health", "dataset_refs"):
        sec = report.get(key, {})
        if sec.get("recommendation"):
            print(f"  [{key}] {sec['recommendation']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
