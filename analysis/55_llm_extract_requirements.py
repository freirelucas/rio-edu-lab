"""Stage 2 v3 — LLM extraction de paper → dados (Claude API, opt-in).

Substitui (na v3) o bag-of-words IDF do 46_extract_requirements.py pra
classificação semântica de paper → categoria da taxonomy. Roda lado a lado
com o 46 — não substitui no funil; persiste em campos paralelos pra
comparação direta (`56_llm_vs_bow_compare.py`, próxima sprint).

Persiste em cada candidate de papers_funnel.yml:
- `llm_suggested_requirements`: [{category_id, confidence, evidence_excerpt}]
- `llm_taxonomy_gap`: bool — paper precisa de dado fora das 10 cats?
- `llm_gap_description`: str | null — descrição do gap
- `llm_model`: str — model id usado
- `llm_call_at`: ISO timestamp UTC
- `llm_stop_reason`: str — pra debug

Idempotente: pula candidates com `llm_call_at` setado, a menos que --refresh.
Cost-guard:
  - --dry-run: mostra primeiro prompt + plan, NÃO chama API
  - --limit N: cap em N candidates por run (default 10 pra teste; --all pra 374)
  - --since-rank N: começa do N-ésimo candidate (por citation desc) — útil
    pra re-rodar só os top, ou retomar depois de interrupção

Estimativa de custo (haiku 4.5 @ $1/$5 per M tok):
- ~1300 tok input × ~200 tok output por paper
- 10 papers ≈ $0.02 · 100 papers ≈ $0.20 · 374 papers ≈ $0.75

Uso:
  pip install anthropic  # opt-in; não está em requirements.txt
  export ANTHROPIC_API_KEY=sk-ant-...
  python3 analysis/55_llm_extract_requirements.py --limit 3 --dry-run
  python3 analysis/55_llm_extract_requirements.py --limit 5
  python3 analysis/55_llm_extract_requirements.py --all
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _anthropic import HAS_ANTHROPIC, extract_requirements  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"


def load_funnel() -> tuple[dict, list[dict]]:
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    return doc, doc.get("candidates") or []


def write_funnel(doc: dict, candidates: list[dict]) -> None:
    """Preserva header comments, reescreve bloco candidates."""
    header_lines: list[str] = []
    for line in FUNNEL_YML.read_text(encoding="utf-8").splitlines():
        if line.startswith("candidates:"):
            break
        header_lines.append(line)
    doc["candidates"] = candidates
    yaml_body = yaml.safe_dump(
        {"candidates": candidates},
        allow_unicode=True,
        sort_keys=False,
        width=120,
        default_flow_style=False,
    )
    full = "\n".join(header_lines).rstrip() + "\n\n" + yaml_body
    FUNNEL_YML.write_text(full, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--limit", type=int, default=10,
                    help="Cap de candidates por run (default 10). Use --all pra todos.")
    ap.add_argument("--all", action="store_true",
                    help="Roda todos os candidates elegíveis (ignora --limit).")
    ap.add_argument("--since-rank", type=int, default=0,
                    help="Começa do N-ésimo candidate (por citation desc). Default 0.")
    ap.add_argument("--refresh", action="store_true",
                    help="Re-chama API mesmo pra candidates com llm_call_at setado.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Mostra primeiro prompt + plan; NÃO chama API.")
    ap.add_argument("--model", default=None,
                    help="Override do modelo (default: claude-haiku-4-5).")
    ap.add_argument("--require-abstract", action="store_true",
                    help="Skip candidates sem abstract (signal-only mode).")
    args = ap.parse_args()

    if not HAS_ANTHROPIC and not args.dry_run:
        print(
            "error: anthropic package not installed. v3 LLM extraction é opt-in.\n"
            "  pip install anthropic\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "(Use --dry-run pra inspecionar o prompt sem instalar.)",
            file=sys.stderr,
        )
        return 1

    if not FUNNEL_YML.exists():
        print(f"missing {FUNNEL_YML.relative_to(ROOT)}", file=sys.stderr)
        return 1

    doc, candidates = load_funnel()
    print(f"loaded {len(candidates)} candidates from {FUNNEL_YML.relative_to(ROOT)}")

    # Ordena por citation desc pra processar high-impact primeiro.
    candidates_sorted = sorted(
        candidates,
        key=lambda c: -int(c.get("citations") or c.get("cited_by_count") or 0),
    )

    # Filtra elegíveis (skip already-processed unless --refresh; skip sem abstract se exigido).
    eligible: list[dict] = []
    skipped_done = 0
    skipped_no_abstract = 0
    for c in candidates_sorted:
        if not args.refresh and c.get("llm_call_at"):
            skipped_done += 1
            continue
        if args.require_abstract and not (c.get("abstract") or "").strip():
            skipped_no_abstract += 1
            continue
        eligible.append(c)

    # Aplica --since-rank e --limit
    eligible = eligible[args.since_rank:]
    if not args.all:
        eligible = eligible[: args.limit]

    print(f"eligible: {len(eligible)} (skipped {skipped_done} already done, "
          f"{skipped_no_abstract} no-abstract)")

    if not eligible:
        print("nothing to do (use --refresh pra re-chamar; --since-rank N pra retomar)")
        return 0

    # Dry-run: mostra primeiro prompt + plan, sem chamar.
    if args.dry_run:
        sample = eligible[0]
        result = extract_requirements(
            title=sample.get("title", ""),
            abstract=sample.get("abstract", ""),
            dry_run=True,
        )
        print("\n=== DRY RUN ===")
        print(f"Would process {len(eligible)} candidates.")
        print(f"Sample (rank 0): {sample.get('title', '')[:70]}")
        print(f"  citations: {sample.get('citations', 0)}")
        print(f"  abstract length: {len(sample.get('abstract') or '')}")
        print(f"  doi: {sample.get('doi') or '(none)'}")
        print(f"\n--- system prompt ({len(result['system_prompt'])} chars) ---")
        print(result["system_prompt"][:500] + ("…" if len(result["system_prompt"]) > 500 else ""))
        print(f"\n--- user message ({len(result['user_message'])} chars) ---")
        print(result["user_message"][:500] + ("…" if len(result["user_message"]) > 500 else ""))
        print("\n--- tool ---")
        print(f"  name: {result['tool']['name']}")
        print(f"  strict: {result['tool']['strict']}")
        est_input_tok = (len(result["system_prompt"]) + len(result["user_message"])) // 4  # rough
        est_cost = est_input_tok * 1.0e-6 * len(eligible) + 200 * 5e-6 * len(eligible)
        print(f"\nEstimated cost: ~${est_cost:.2f} for {len(eligible)} calls "
              f"(haiku 4.5 @ $1/$5 per 1M tok; rough ~{est_input_tok} input + ~200 output per paper)")
        return 0

    # Real run.
    n_success = 0
    n_failed = 0
    total_usage = {"input_tokens": 0, "output_tokens": 0,
                   "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}

    for i, c in enumerate(eligible, 1):
        oid_short = (c.get("openalex_id") or "?").split("/")[-1][:12]
        title_short = (c.get("title") or "?")[:60].replace("\n", " ")
        print(f"\n[{i}/{len(eligible)}] {oid_short} — {title_short}", file=sys.stderr)

        result = extract_requirements(
            title=c.get("title", ""),
            abstract=c.get("abstract", ""),
            model=args.model or "claude-haiku-4-5",
            verbose=True,
        )

        if result is None:
            n_failed += 1
            print("  → FAIL", file=sys.stderr)
            continue

        # Persiste no candidate.
        c["llm_suggested_requirements"] = result.get("datasets") or []
        c["llm_taxonomy_gap"] = bool(result.get("taxonomy_gap"))
        c["llm_gap_description"] = result.get("gap_description")
        c["llm_model"] = result["_model"]
        c["llm_call_at"] = result["_called_at"]
        c["llm_stop_reason"] = result["_stop_reason"]

        usage = result["_usage"]
        for k in total_usage:
            total_usage[k] += usage.get(k, 0)

        n_datasets = len(c["llm_suggested_requirements"])
        gap = "gap" if c["llm_taxonomy_gap"] else "covered"
        cache_note = f", cache_read={usage['cache_read_input_tokens']}" if usage["cache_read_input_tokens"] else ""
        print(
            f"  → {n_datasets} cats, {gap}, "
            f"{usage['input_tokens']}in/{usage['output_tokens']}out tok{cache_note}",
            file=sys.stderr,
        )
        n_success += 1

        # Salva a cada 5 calls pra não perder progresso em interrupção.
        if i % 5 == 0:
            write_funnel(doc, candidates)
            print(f"  (saved checkpoint at {i}/{len(eligible)})", file=sys.stderr)

    # Save final.
    write_funnel(doc, candidates)

    # Resumo + cost estimate
    print("\n=== summary ===")
    print(f"  success: {n_success}")
    print(f"  failed:  {n_failed}")
    print(f"  total tokens: {total_usage['input_tokens']} in / {total_usage['output_tokens']} out")
    if total_usage["cache_read_input_tokens"]:
        print(f"  cache hits: {total_usage['cache_read_input_tokens']} tok")
    if total_usage["cache_creation_input_tokens"]:
        print(f"  cache writes: {total_usage['cache_creation_input_tokens']} tok")
    # haiku 4.5: $1/M input, $5/M output, $1.25/M cache write, $0.1/M cache read
    cost = (
        total_usage["input_tokens"] * 1.0e-6
        + total_usage["output_tokens"] * 5.0e-6
        + total_usage["cache_creation_input_tokens"] * 1.25e-6
        + total_usage["cache_read_input_tokens"] * 0.1e-6
    )
    print(f"  estimated cost: ${cost:.4f}")
    print(f"  wrote {FUNNEL_YML.relative_to(ROOT)}")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
