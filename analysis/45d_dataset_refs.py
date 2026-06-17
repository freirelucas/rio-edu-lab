"""Filter referenced_works por type=dataset/software — paper↔dataset linkage.

Sprint v0.17.f — implementação da recomendação dos 5 agentes (v0.16 audit).
Agora destravada pelo bug fix v0.16 que separou referenced_works (citações
reais) de related_works (similaridade do OpenAlex).

Estratégia (Agente 1 + Agente 3):

  Pra cada candidate com referenced_works populado:
    1. Pegar os W-IDs dos refs (citações declaradas pelo autor)
    2. Batch-lookup via OpenAlex (filter=openalex_id:W1|W2|… +
       select=id,doi,title,type) — usa cache existing
    3. Filtrar refs com type ∈ {dataset, software-source-code, software,
       version-of-record}
    4. Persistir como `dataset_refs: [{openalex_id, doi, title, type}]`
       no candidate

Sinal: paper que CITA dataset com DOI é a forma mais confiável (declarativa
pelo autor, ~100% precisão) de inferir paper→dataset linkage. Cobertura
realística (Agente 3): 15-25% dos candidates pós-2010 terão ≥1 dataset
referenced. Pre-2010 quase zero (cultura de DOI dataset emergiu ~2015+).

OpenAlex `type` taxonomy (https://docs.openalex.org/api-entities/works/work-object#type):
  article, book, book-chapter, dataset, dissertation, editorial, erratum,
  letter, paratext, peer-review, reference-entry, report, retraction,
  standard, supplementary-materials, other

Filtramos `dataset` (gold pra nosso uso). Software NÃO é tipo nativo no
OpenAlex hoje (gap conhecido — vem só via DataCite ingest); manter no enum
pra forward-compat.

Uso:
  OPENALEX_EMAIL=lucasfreire@gmail.com python3 analysis/45d_dataset_refs.py
  python3 analysis/45d_dataset_refs.py --limit 50    # smoke test
  python3 analysis/45d_dataset_refs.py --refresh     # re-query missing types
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from _openalex import fetch_works_batch  # noqa: E402

FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"

# Tipos OpenAlex que sinalizam "dataset/software" — uso declarativo pra
# paper↔dataset link. `dataset` é canônico; software é gap conhecido (OpenAlex
# não tipo nativo) mas mantemos pra forward-compat (DataCite ingest pode
# começar a popular).
DATASET_TYPES = frozenset({
    "dataset",
    "software-source-code",
    "software",
    "supplementary-materials",  # às vezes datasets vêm como supplementary
})


def priority_pool(candidates: list[dict]) -> list[int]:
    """Ordena candidates por prioridade pra dataset_refs lookup:
    Tier 1: fully-covered (data.rio match) + tem referenced_works
    Tier 2: BR + tem referenced_works
    Tier 3: top 200 por citação + tem referenced_works
    """
    tier1, tier2, tier3 = [], [], []
    for i, c in enumerate(candidates):
        refs = c.get("referenced_works") or []
        if not refs:
            continue  # sem refs = sem nada pra lookup
        cov = c.get("coverage") or []
        statuses = [(x or {}).get("status") for x in cov]
        if statuses and all(s == "available" for s in statuses):
            tier1.append(i)
        elif c.get("is_brazilian"):
            tier2.append(i)
        else:
            tier3.append(i)
    # Sort cada tier por cit desc
    def by_cit(idx):
        return -(candidates[idx].get("citations") or 0)
    tier1.sort(key=by_cit)
    tier2.sort(key=by_cit)
    tier3.sort(key=by_cit)
    # Tier 3 cap pra 200 (não fetch refs do funnel inteiro)
    return tier1 + tier2 + tier3[:200]


def write_funnel(funnel_path: Path, candidates: list[dict]) -> None:
    """Preserva header comments, reescreve bloco candidates (mesmo pattern 46/47)."""
    header_lines: list[str] = []
    for line in funnel_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("candidates:"):
            break
        header_lines.append(line)
    yaml_body = yaml.safe_dump(
        {"candidates": candidates},
        allow_unicode=True,
        sort_keys=False,
        width=120,
        default_flow_style=False,
    )
    full = "\n".join(header_lines).rstrip() + "\n\n" + yaml_body
    funnel_path.write_text(full, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100,
                    help="cap N candidates pra enriquecer (default 100)")
    ap.add_argument("--refresh", action="store_true",
                    help="re-query mesmo se dataset_refs já populated")
    ap.add_argument("--dry-run", action="store_true",
                    help="mostra plan sem chamar API")
    ap.add_argument("--funnel", type=Path, default=FUNNEL_YML)
    args = ap.parse_args()

    if not args.funnel.exists():
        print(f"missing {args.funnel}", file=sys.stderr)
        return 1
    doc = yaml.safe_load(args.funnel.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    print(f"loaded {len(candidates)} candidates", file=sys.stderr)

    pool = priority_pool(candidates)
    print(f"priority pool: {len(pool)} candidates com referenced_works", file=sys.stderr)
    targets = pool[: args.limit]
    print(f"will process top {len(targets)}", file=sys.stderr)

    if args.dry_run:
        print("\n[dry-run] sample candidates:", file=sys.stderr)
        for rank, i in enumerate(targets[:5], 1):
            c = candidates[i]
            refs = c.get("referenced_works") or []
            title = (c.get("title") or "")[:55]
            print(f"  [{rank}] {len(refs):>3} refs — {title}", file=sys.stderr)
        return 0

    n_enriched = 0
    n_skipped = 0
    n_with_datasets = 0
    total_datasets = 0

    for rank, i in enumerate(targets, 1):
        c = candidates[i]
        if c.get("dataset_refs") is not None and not args.refresh:
            n_skipped += 1
            continue

        ref_ids = [r.split("/")[-1] for r in (c.get("referenced_works") or []) if r]
        if not ref_ids:
            continue

        # Batch fetch — usa cache. 50 ids/batch via fetch_works_batch.
        title_short = (c.get("title") or "")[:55]
        if rank <= 10 or rank % 20 == 0:
            print(f"  [{rank:>3}/{len(targets)}] {len(ref_ids):>3} refs — {title_short}",
                  file=sys.stderr)

        fetched = fetch_works_batch(ref_ids, verbose=False)

        # Filtrar refs por type=dataset
        dataset_refs = []
        for ref in fetched:
            rtype = ref.get("type")
            if rtype in DATASET_TYPES:
                dataset_refs.append({
                    "openalex_id": ref.get("openalex_id") or ref.get("id"),
                    "doi": ref.get("doi"),
                    "title": ref.get("title"),
                    "type": rtype,
                })

        c["dataset_refs"] = dataset_refs
        if dataset_refs:
            n_with_datasets += 1
            total_datasets += len(dataset_refs)
            if rank <= 20:
                print(f"    → {len(dataset_refs)} dataset ref(s): "
                      f"{[d['title'][:40] for d in dataset_refs[:3]]}",
                      file=sys.stderr)
        n_enriched += 1

        # Checkpoint a cada 25
        if rank % 25 == 0:
            write_funnel(args.funnel, candidates)

    write_funnel(args.funnel, candidates)

    print("\n=== summary ===", file=sys.stderr)
    print(f"  enriched: {n_enriched}", file=sys.stderr)
    print(f"  skipped (already had dataset_refs): {n_skipped}", file=sys.stderr)
    print(f"  with ≥1 dataset ref: {n_with_datasets}/{n_enriched}", file=sys.stderr)
    print(f"  total dataset refs found: {total_datasets}", file=sys.stderr)
    if n_enriched:
        rate = 100 * n_with_datasets / n_enriched
        print(f"  hit rate: {rate:.1f}%", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
