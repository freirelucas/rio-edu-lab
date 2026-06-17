"""Stage 1 do funil — descoberta bibliométrica em lote no OpenAlex.

Lê `data/openalex_seeds.yml` (núcleo curado de papers canônicos) e expande
em 2 tracks:

  - **Mainstream** (backward snowball): para cada seed `track: mainstream`,
    busca `referenced_works` no OpenAlex. Papers que o seed cita herdam a
    curadoria do seed. Rank por co-citação: candidato citado por N seeds
    tem `cocitation_count: N`.

  - **Outsider** (forward snowball + filtro lateral): para cada seed,
    busca papers que citam o seed via `?filter=cites:Wxxx&cited_by_count`
    range [20, 500]. Sobrevive se também tem `data_signal.score > 0`
    (sinal de replicabilidade — github/osf/dataverse/replication package
    no abstract).

  - **Data signal**: scan regex de `abstract + pdf_url_oa` por padrões
    de replicabilidade. Score = +3 por hit, +1 se doi, +1 se pdf_url_oa.
    Mainstream papers sem signal entram mesmo assim; outsiders sem
    signal são descartados.

Upsert em `data/papers_funnel.yml`: candidatos novos são inseridos com
`decision/suggested_requirements/coverage` vazios. Candidatos já presentes
têm `discovered_via` unido, `track`/`cocitation_count`/`data_signal` e
metadata refrescados; MAS `decision`, `decision_reason`,
`suggested_requirements`, `coverage` são preservados intactos.

Uso:
  python3 analysis/45_bulk_discover.py                      # todos os seeds
  python3 analysis/45_bulk_discover.py --seeds W123,W456    # subset
  python3 analysis/45_bulk_discover.py --dry-run            # sem escrever
  python3 analysis/45_bulk_discover.py --no-forward         # só backward
  python3 analysis/45_bulk_discover.py --no-backward        # só forward
  python3 analysis/45_bulk_discover.py --top-forward 25     # cap forward

Rede: OpenAlex public API, 1 req/s. ~5 min wall clock com 20 seeds full.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _openalex import (  # noqa: E402
    fetch_work_by_id,
    fetch_works_batch,
    iterate_cites,
    parse_work,
)
from _semanticscholar import fetch_papers_batch as ss_fetch_papers_batch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEEDS_YML = ROOT / "data" / "openalex_seeds.yml"
LEGACY_CONCEPTS_YML = ROOT / "data" / "openalex_concepts.yml"
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
VISITED_FILE = ROOT / "data" / "snowball_visited.json"

DEFAULT_TOP_FORWARD = 50
DEFAULT_BACKWARD_CAP = 50
OUTSIDER_MIN_CITATIONS = 20
OUTSIDER_MAX_CITATIONS = 500
# v2 depth-2 snowball
DEFAULT_DEPTH = 1
DEFAULT_MAX_NEW = 2000
DEFAULT_PASS2_SIZE = 100
PASS2_MIN_CITATIONS = 10  # mais permissivo que OUTSIDER_MIN; pass2 cresce de cima pra baixo

DATA_SIGNAL_PATTERNS = [
    r"github\.com",
    r"osf\.io",
    r"dataverse",
    r"harvard\.edu/dvn",
    r"replication (?:package|files|materials|code)",
    r"data (?:are )?available",
    r"supplement(?:ary)? data",
]
_DATA_SIGNAL_RE = re.compile("|".join(DATA_SIGNAL_PATTERNS), re.IGNORECASE)


# ─── Visited tracker (snowball v2) ─────────────────────────────────────────
# Persiste IDs já usados como seed (Pass 1 ou Pass 2) entre runs, pra que
# depth-2 não re-expanda os mesmos hubs em runs subsequentes. Reset com
# --reset-visited.

def load_visited() -> set[str]:
    if not VISITED_FILE.exists():
        return set()
    try:
        data = json.loads(VISITED_FILE.read_text(encoding="utf-8"))
        return set(data.get("visited") or [])
    except (json.JSONDecodeError, OSError):
        return set()


def save_visited(visited: set[str]) -> None:
    VISITED_FILE.parent.mkdir(parents=True, exist_ok=True)
    VISITED_FILE.write_text(
        json.dumps({"visited": sorted(visited), "n": len(visited)}, indent=2),
        encoding="utf-8",
    )


def _norm_id(openalex_id: str) -> str:
    """Strip URL prefix de OpenAlex ID."""
    s = (openalex_id or "").strip()
    if s.startswith("https://openalex.org/"):
        s = s[len("https://openalex.org/"):]
    return s


def pick_pass2_seeds(
    agg: dict[str, dict], n: int, visited: set[str],
    min_citations: int = PASS2_MIN_CITATIONS,
) -> list[str]:
    """Top-N candidates do Pass 1 (por citation) pra virarem seeds do Pass 2.

    Filtros: tem abstract, ≥ min_citations citations, ainda não visitado.
    """
    candidates = [
        (oid, row) for oid, row in agg.items()
        if (row.get("abstract") or "").strip()
        and int(row.get("cited_by_count") or 0) >= min_citations
        and _norm_id(oid) not in visited
        and not row.get("is_retracted")
    ]
    candidates.sort(key=lambda kv: -int(kv[1].get("cited_by_count") or 0))
    return [oid for oid, _ in candidates[:n]]


def load_seeds(args_seeds: str | None = None) -> list[dict]:
    if LEGACY_CONCEPTS_YML.exists():
        print(
            f"error: {LEGACY_CONCEPTS_YML.relative_to(ROOT)} is deprecated. "
            f"Migrate to {SEEDS_YML.relative_to(ROOT)} (see schema in header).",
            file=sys.stderr,
        )
        sys.exit(2)
    if not SEEDS_YML.exists():
        print(f"missing {SEEDS_YML.relative_to(ROOT)}", file=sys.stderr)
        sys.exit(1)
    data = yaml.safe_load(SEEDS_YML.read_text(encoding="utf-8")) or {}
    seeds = [s for s in (data.get("seeds") or []) if s.get("enabled", True)]
    for s in seeds:
        if not s.get("openalex_id", "").startswith("W"):
            print(f"  [warn] invalid openalex_id in seed: {s.get('label')!r}", file=sys.stderr)
        if s.get("track") not in ("mainstream", "outsider"):
            print(f"  [warn] seed {s.get('openalex_id')} has invalid track", file=sys.stderr)
    if args_seeds:
        wanted = {x.strip() for x in args_seeds.split(",") if x.strip()}
        seeds = [s for s in seeds if s.get("openalex_id") in wanted]
    return seeds


def load_funnel() -> tuple[dict, dict[str, dict]]:
    if not FUNNEL_YML.exists():
        return {"version": 1, "candidates": []}, {}
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    cands = doc.get("candidates") or []
    by_id = {c["openalex_id"]: c for c in cands if c.get("openalex_id")}
    return doc, by_id


def write_funnel(doc: dict, candidates: list[dict]) -> None:
    doc["candidates"] = candidates
    header_lines: list[str] = []
    if FUNNEL_YML.exists():
        for line in FUNNEL_YML.read_text(encoding="utf-8").splitlines():
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
    FUNNEL_YML.write_text(full, encoding="utf-8")


def compute_data_signal(row: dict) -> dict:
    text = ((row.get("abstract") or "") + " " + (row.get("pdf_url_oa") or "")).lower()
    hits = list({m.group(0) for m in _DATA_SIGNAL_RE.finditer(text)})
    score = 3 * len(hits)
    if row.get("doi"):
        score += 1
    if row.get("pdf_url_oa"):
        score += 1
    return {"score": score, "hits": sorted(hits)}


def backward_snowball(seed_id: str, cap: int = DEFAULT_BACKWARD_CAP) -> list[dict]:
    """Fetch refs of seed, batch-resolve them, return parsed rows."""
    work = fetch_work_by_id(seed_id)
    if not work:
        print(f"  [warn] {seed_id} fetch failed (no backward)", file=sys.stderr)
        return []
    refs = work.get("referenced_works") or []
    if not refs:
        print(f"  [warn] {seed_id} has 0 referenced_works", file=sys.stderr)
        return []
    refs_capped = refs[:cap]
    print(f"  backward: {len(refs)} refs (cap to {len(refs_capped)})")
    works = fetch_works_batch(refs_capped)
    rows = [parse_work(w) for w in works if w.get("id")]
    for r in rows:
        r["_source"] = f"backward-from-{seed_id}"
    return rows


def forward_snowball(seed_id: str, top: int) -> list[dict]:
    rows = iterate_cites(
        seed_id,
        top=top,
        min_citations=OUTSIDER_MIN_CITATIONS,
        max_citations=OUTSIDER_MAX_CITATIONS,
    )
    for r in rows:
        r["_source"] = f"forward-from-{seed_id}"
    print(f"  forward: {len(rows)} hits in [{OUTSIDER_MIN_CITATIONS},{OUTSIDER_MAX_CITATIONS}] citations")
    return rows


def aggregate_candidates(
    all_rows: list[dict],
    seeds_by_id: dict[str, dict],
) -> dict[str, dict]:
    agg: dict[str, dict] = {}
    for row in all_rows:
        oid = row.get("openalex_id", "")
        if not oid:
            continue
        src = row.pop("_source", "")
        if oid not in agg:
            agg[oid] = {**row, "discovered_via": [src] if src else []}
        else:
            existing = agg[oid]
            via = set(existing["discovered_via"])
            if src:
                via.add(src)
            existing["discovered_via"] = sorted(via)
            if int(row.get("cited_by_count") or 0) > int(existing.get("cited_by_count") or 0):
                existing["cited_by_count"] = row["cited_by_count"]
            for k in (
                # legacy fields
                "title", "authors", "year", "venue", "doi", "abstract", "pdf_url_oa", "concepts_top3",
                # v2 rich fields (preencher se outra discovery trouxe valor)
                "concepts", "topics", "primary_topic", "keywords", "institutions",
                "is_brazilian", "related_works", "best_oa_pdf_url", "fwci",
                "counts_by_year", "is_retracted", "mesh", "sdg",
            ):
                if not existing.get(k) and row.get(k):
                    existing[k] = row[k]
    # If a seed openalex_id ended up as an aggregated row (auto-citation case),
    # tag its source so downstream sees it as a seed.
    for oid, seed in seeds_by_id.items():
        oid_full = f"https://openalex.org/{oid}"
        if oid_full in agg:
            via = set(agg[oid_full]["discovered_via"])
            via.add(f"seed-{seed['track']}")
            agg[oid_full]["discovered_via"] = sorted(via)

    for row in agg.values():
        backward_seeds = [s for s in row["discovered_via"] if s.startswith("backward-from-")]
        row["cocitation_count"] = len(backward_seeds)
        if row["cocitation_count"] >= 1 or any(s.startswith("seed-mainstream") for s in row["discovered_via"]):
            row["track"] = "mainstream"
        else:
            row["track"] = "outsider"
        row["data_signal"] = compute_data_signal(row)
    return agg


def enrich_with_semscholar(agg: dict[str, dict], verbose: bool = True) -> None:
    """Fallback abstract via Semantic Scholar para candidates com abstract vazio + DOI.

    Não duplica calls — OpenAlex sempre vai primeiro; SS é a rede de segurança.
    Marca `abstract_source` em cada candidate ("openalex" | "semscholar" | "none").
    Mutates agg in place.
    """
    needs_ss: list[tuple[str, dict]] = []
    for oid, row in agg.items():
        has_abs = bool((row.get("abstract") or "").strip())
        if has_abs:
            row["abstract_source"] = "openalex"
        elif (row.get("doi") or "").strip():
            needs_ss.append((oid, row))
        else:
            row["abstract_source"] = "none"

    if not needs_ss:
        if verbose:
            print("  ss fallback: 0 candidates need it", file=sys.stderr)
        return

    if verbose:
        print(
            f"  ss fallback: {len(needs_ss)} candidates com abstract vazio + DOI",
            file=sys.stderr,
        )

    dois = [row["doi"] for _, row in needs_ss]
    results = ss_fetch_papers_batch(dois, verbose=verbose)

    n_filled = 0
    for _, row in needs_ss:
        doi_lc = row["doi"].lower()
        paper = results.get(doi_lc)
        abs_text = (paper.get("abstract") if paper else None) or ""
        if abs_text:
            row["abstract"] = abs_text
            row["abstract_source"] = "semscholar"
            # Recompute data_signal — abstract mudou, pode ter github/osf/etc.
            row["data_signal"] = compute_data_signal(row)
            n_filled += 1
        else:
            row["abstract_source"] = "none"

    if verbose:
        print(
            f"  ss fallback: filled {n_filled}/{len(needs_ss)} empty abstracts",
            file=sys.stderr,
        )


def filter_outsiders(agg: dict[str, dict]) -> dict[str, dict]:
    """Outsiders must have at least 1 regex data-signal hit (not just DOI/OA).

    DOI and pdf_url_oa give baseline +1 each in the score, but those are
    only weak replicability signals (most published papers have them).
    The regex hits (github, osf, dataverse, replication package) are the
    real evidence. Require ≥1 to keep an outsider in the funnel.
    """
    kept: dict[str, dict] = {}
    dropped_cit = 0
    dropped_signal = 0
    for oid, row in agg.items():
        if row["track"] == "mainstream":
            kept[oid] = row
            continue
        cit = int(row.get("cited_by_count") or 0)
        if not (OUTSIDER_MIN_CITATIONS <= cit <= OUTSIDER_MAX_CITATIONS):
            dropped_cit += 1
            continue
        if not row["data_signal"].get("hits"):
            dropped_signal += 1
            continue
        kept[oid] = row
    if dropped_cit or dropped_signal:
        print(
            f"  filter_outsiders: dropped {dropped_cit} out-of-range citations, "
            f"{dropped_signal} no regex data-signal hit"
        )
    return kept


def merge_candidate(existing: dict, new: dict) -> dict:
    discovered = set(existing.get("discovered_via") or []) | set(new.get("discovered_via") or [])
    return {
        "openalex_id": existing["openalex_id"],
        "doi": new.get("doi") or existing.get("doi") or "",
        "title": new.get("title") or existing.get("title") or "",
        "authors": new.get("authors") or existing.get("authors") or "",
        "year": new.get("year") or existing.get("year") or "",
        "venue": new.get("venue") or existing.get("venue") or "",
        "citations": int(new.get("cited_by_count") or existing.get("citations") or 0),
        "abstract": new.get("abstract") or existing.get("abstract") or "",
        "abstract_source": new.get("abstract_source") or existing.get("abstract_source") or "",
        "pdf_url_oa": new.get("pdf_url_oa") or existing.get("pdf_url_oa") or "",
        "concepts_top3": new.get("concepts_top3") or existing.get("concepts_top3") or "",
        # v2 rich fields
        "concepts": new.get("concepts") or existing.get("concepts") or [],
        "topics": new.get("topics") or existing.get("topics") or [],
        "primary_topic": new.get("primary_topic") or existing.get("primary_topic"),
        "keywords": new.get("keywords") or existing.get("keywords") or [],
        "institutions": new.get("institutions") or existing.get("institutions") or [],
        "is_brazilian": bool(new.get("is_brazilian") or existing.get("is_brazilian")),
        "related_works": new.get("related_works") or existing.get("related_works") or [],
        "referenced_works": new.get("referenced_works") or existing.get("referenced_works") or [],
        "best_oa_pdf_url": new.get("best_oa_pdf_url") or existing.get("best_oa_pdf_url") or "",
        "fwci": new.get("fwci") if new.get("fwci") is not None else existing.get("fwci"),
        "counts_by_year": new.get("counts_by_year") or existing.get("counts_by_year") or [],
        "is_retracted": bool(new.get("is_retracted") or existing.get("is_retracted")),
        "mesh": new.get("mesh") or existing.get("mesh") or [],
        "sdg": new.get("sdg") or existing.get("sdg") or [],
        # Discovery metadata
        "discovered_via": sorted(discovered),
        "track": new.get("track") or existing.get("track") or "legacy",
        "cocitation_count": int(new.get("cocitation_count") or existing.get("cocitation_count") or 0),
        "data_signal": new.get("data_signal") or existing.get("data_signal") or {"score": 0, "hits": []},
        # Preserved exactly:
        "suggested_requirements": existing.get("suggested_requirements") or [],
        "coverage": existing.get("coverage") or [],
        "decision": existing.get("decision") or "",
        "decision_reason": existing.get("decision_reason") or "",
    }


def new_candidate(row: dict) -> dict:
    return {
        "openalex_id": row["openalex_id"],
        "doi": row.get("doi") or "",
        "title": row.get("title") or "",
        "authors": row.get("authors") or "",
        "year": row.get("year") or "",
        "venue": row.get("venue") or "",
        "citations": int(row.get("cited_by_count") or 0),
        "abstract": row.get("abstract") or "",
        "abstract_source": row.get("abstract_source") or "",
        "pdf_url_oa": row.get("pdf_url_oa") or "",
        "concepts_top3": row.get("concepts_top3") or "",
        # v2 rich fields
        "concepts": row.get("concepts") or [],
        "topics": row.get("topics") or [],
        "primary_topic": row.get("primary_topic"),
        "keywords": row.get("keywords") or [],
        "institutions": row.get("institutions") or [],
        "is_brazilian": bool(row.get("is_brazilian")),
        "related_works": row.get("related_works") or [],
        "referenced_works": row.get("referenced_works") or [],
        "best_oa_pdf_url": row.get("best_oa_pdf_url") or "",
        "fwci": row.get("fwci"),
        "counts_by_year": row.get("counts_by_year") or [],
        "is_retracted": bool(row.get("is_retracted")),
        "mesh": row.get("mesh") or [],
        "sdg": row.get("sdg") or [],
        # Discovery metadata
        "discovered_via": row.get("discovered_via") or [],
        "track": row.get("track") or "outsider",
        "cocitation_count": int(row.get("cocitation_count") or 0),
        "data_signal": row.get("data_signal") or {"score": 0, "hits": []},
        "suggested_requirements": [],
        "coverage": [],
        "decision": "",
        "decision_reason": "",
    }


def print_summary(candidates: list[dict], n_new: int, n_updated: int) -> None:
    print("\n=== summary ===")
    print(f"  new candidates: {n_new}")
    print(f"  refreshed: {n_updated}")
    print(f"  total in funnel: {len(candidates)}")
    track_dist = {"mainstream": 0, "outsider": 0, "legacy": 0}
    for c in candidates:
        track_dist[c.get("track", "legacy")] = track_dist.get(c.get("track", "legacy"), 0) + 1
    print(f"  by track: {track_dist}")
    coc_dist: dict[int, int] = {}
    for c in candidates:
        n = int(c.get("cocitation_count") or 0)
        coc_dist[n] = coc_dist.get(n, 0) + 1
    print(f"  cocitation_count distribution: {dict(sorted(coc_dist.items()))}")
    with_signal = sum(1 for c in candidates if (c.get("data_signal") or {}).get("score", 0) > 0)
    print(f"  with data_signal > 0: {with_signal}")
    if candidates:
        top1 = max(candidates, key=lambda c: int(c.get("citations") or 0))
        print(
            f"  top by citations: {top1.get('title', '')[:70]} "
            f"({top1.get('year', '?')}) — {top1.get('citations', 0):,} cit"
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", help="Comma-separated openalex_ids (default: all enabled in yml)")
    ap.add_argument(
        "--top-forward",
        type=int,
        default=DEFAULT_TOP_FORWARD,
        help=f"Cap forward hits per seed (default {DEFAULT_TOP_FORWARD})",
    )
    ap.add_argument(
        "--backward-cap",
        type=int,
        default=DEFAULT_BACKWARD_CAP,
        help=f"Cap referenced_works per seed (default {DEFAULT_BACKWARD_CAP})",
    )
    ap.add_argument("--no-forward", action="store_true", help="Skip forward snowball")
    ap.add_argument("--no-backward", action="store_true", help="Skip backward snowball")
    ap.add_argument(
        "--no-semscholar",
        action="store_true",
        help="Skip Semantic Scholar fallback para abstracts vazios",
    )
    ap.add_argument(
        "--depth",
        type=int,
        default=DEFAULT_DEPTH,
        help=f"Hops do snowball (1 = só seeds, 2 = expande top Pass 1; default {DEFAULT_DEPTH})",
    )
    ap.add_argument(
        "--max-new",
        type=int,
        default=DEFAULT_MAX_NEW,
        help=f"Cap de candidates NOVOS adicionados ao funil por run (default {DEFAULT_MAX_NEW})",
    )
    ap.add_argument(
        "--pass2-size",
        type=int,
        default=DEFAULT_PASS2_SIZE,
        help=f"Quantos candidates do Pass 1 viram seeds do Pass 2 (default {DEFAULT_PASS2_SIZE})",
    )
    ap.add_argument(
        "--reset-visited",
        action="store_true",
        help="Reseta data/snowball_visited.json antes do run",
    )
    ap.add_argument("--dry-run", action="store_true", help="Don't write papers_funnel.yml")
    args = ap.parse_args()

    seeds = load_seeds(args.seeds)
    if not seeds:
        print("no enabled seeds to run", file=sys.stderr)
        return 1
    print(f"running snowball over {len(seeds)} seeds")

    seeds_by_id = {s["openalex_id"]: s for s in seeds}
    doc, by_id = load_funnel()
    print(f"funnel has {len(by_id)} existing candidates")

    visited = set() if args.reset_visited else load_visited()
    if args.reset_visited:
        print("--reset-visited: visited set cleared")
    elif visited:
        print(f"visited set: {len(visited)} previously-snowballed IDs")
    for seed in seeds:
        visited.add(_norm_id(seed["openalex_id"]))

    # === Pass 1: snowball a partir dos seeds curados ===
    print(f"\n=== Pass 1: snowball from {len(seeds)} seeds ===")
    all_rows: list[dict] = []
    for seed in seeds:
        sid = seed["openalex_id"]
        label = seed.get("label", sid)[:60]
        print(f"\n[{sid}] track={seed['track']} — {label}")
        if seed["track"] == "mainstream" and not args.no_backward:
            all_rows += backward_snowball(sid, cap=args.backward_cap)
        if not args.no_forward:
            top_fwd = seed.get("top_forward") or args.top_forward
            all_rows += forward_snowball(sid, top=top_fwd)

    print(f"\nPass 1 raw rows: {len(all_rows)}")
    agg = aggregate_candidates(all_rows, seeds_by_id)
    print(f"Pass 1 unique: {len(agg)}")

    # === Pass 2 (depth-2): expande top Pass 1 candidates ===
    if args.depth >= 2:
        pass2_seeds = pick_pass2_seeds(agg, args.pass2_size, visited)
        print(f"\n=== Pass 2: snowball from top-{len(pass2_seeds)} Pass 1 candidates ===")
        pass2_rows: list[dict] = []
        for sid in pass2_seeds:
            visited.add(_norm_id(sid))
            label = (agg[sid].get("title") or "")[:60]
            print(f"\n[{sid}] pass2 — {label}")
            if not args.no_backward:
                pass2_rows += backward_snowball(sid, cap=args.backward_cap)
            if not args.no_forward:
                pass2_rows += forward_snowball(sid, top=args.top_forward)

        print(f"\nPass 2 raw rows: {len(pass2_rows)}")
        if pass2_rows:
            pass2_agg = aggregate_candidates(pass2_rows, {})
            new_in_pass2 = sum(1 for oid in pass2_agg if oid not in agg)
            print(f"Pass 2 unique: {len(pass2_agg)} (new vs Pass 1: {new_in_pass2})")
            # Merge: prefer Pass 1 values quando já existe (mais autoritativo via seed)
            for oid, row in pass2_agg.items():
                if oid not in agg:
                    agg[oid] = row

    save_visited(visited)
    print(f"visited set after run: {len(visited)} IDs")

    if not args.no_semscholar:
        enrich_with_semscholar(agg)
    agg = filter_outsiders(agg)
    print(f"after outsider filter: {len(agg)}")

    # === --max-new cap: limita quantos NOVOS candidates entram no funil ===
    new_oids = [oid for oid in agg if oid not in by_id]
    if len(new_oids) > args.max_new:
        # Ordena por citation desc e fica com top max_new
        new_oids_sorted = sorted(
            new_oids,
            key=lambda oid: -int(agg[oid].get("cited_by_count") or 0),
        )
        kept_new = set(new_oids_sorted[:args.max_new])
        dropped = len(new_oids) - args.max_new
        print(f"--max-new cap: keep top {args.max_new} novos, drop {dropped} de baixa citação")
        agg = {oid: row for oid, row in agg.items() if oid in by_id or oid in kept_new}

    n_new = 0
    n_updated = 0
    for oid, row in agg.items():
        if oid in by_id:
            by_id[oid] = merge_candidate(by_id[oid], row)
            n_updated += 1
        else:
            by_id[oid] = new_candidate(row)
            n_new += 1

    candidates = sorted(
        by_id.values(),
        key=lambda c: (-int(c.get("citations") or 0), c.get("year") or 0),
    )
    print_summary(candidates, n_new, n_updated)

    if args.dry_run:
        print("\n[dry-run] not writing papers_funnel.yml")
        return 0

    write_funnel(doc, candidates)
    print(f"\nwrote {FUNNEL_YML.relative_to(ROOT)} ({len(candidates)} candidates)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
