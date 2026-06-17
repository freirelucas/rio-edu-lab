"""LLM-assisted backfill de `code_book` em items do data.rio manifest.

Sprint v0.15 Stream 1.4 — escala o vertical slice (5 items hand-curated) pra
~60 items prioritários via Claude haiku-4-5. Cada item recebe code_book v2:

  {
    "domain": "educacao-basica" | ... | null,
    "unit_of_observation": "bairro|ra|ap|escola|aluno|setor|...",
    "spatial_granularity": "bairro|ra|ap|ponto|setor|municipio|...",
    "temporal_coverage_parsed": {start_year, end_year, frequency} | null,
    "api_capability": "feature_service|static_file|document_link|none",
    "key_variables": ["ideb", "ano", "bairro", ...] | null,
    "confidence": float [0, 1],
    "_llm_model": "claude-haiku-4-5",
    "_llm_called_at": ISO timestamp,
  }

Input por item: title + snippet + type + tags. Não baixamos o file — o título +
snippet do data.rio já carrega 90% da info necessária (esses itens são
metadados verbose; o IPP escreve descrições explícitas).

Priority pool (ordem):
  1. Items edu-tagged WITHOUT code_book, ordenados por numViews desc
  2. Cap padrão --limit 60 (~$0.06 com haiku, ~5min wall clock)
  3. Idempotente — pula items com code_book (--refresh força bypass)

Custo: ~$0.001/item com prompt caching (SYSTEM + TOOL cacheados em ephemeral
nas chamadas subsequentes). 60 items ≈ $0.06.

Uso:
  python3 analysis/49_codebook_backfill.py --dry-run --limit 5   # preview sem API
  ANTHROPIC_API_KEY=sk-... python3 analysis/49_codebook_backfill.py --limit 60
  ANTHROPIC_API_KEY=sk-... python3 analysis/49_codebook_backfill.py --refresh --limit 10

Cache: data/cache/anthropic/codebook_{item_id}.json — gitignored.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml  # noqa: F401  (manifest é JSON, mas mantemos no requirements pra coerência)
except ImportError:
    pass

try:
    import anthropic  # type: ignore[import-not-found]
    HAS_ANTHROPIC = True
except ImportError:
    anthropic = None  # type: ignore[assignment]
    HAS_ANTHROPIC = False

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from _anthropic import DEFAULT_MODEL, _get_api_key  # noqa: E402

MANIFEST_JSON = ROOT / "data" / "manifest.json"
CACHE_DIR = ROOT / "data" / "cache" / "anthropic"

# Tags do IPP que sinalizam item educacional (priority pool).
EDU_TAGS = frozenset({
    "Educação", "Educação Básica", "Educação Superior",
    "Escolaridade da população", "Ensino",
})

SYSTEM_PROMPT_CODEBOOK = """You are an expert data curator for the rio-edu-lab project. Given metadata for a data.rio item (Instituto Pereira Passos, city of Rio de Janeiro open data portal), classify it on 5 structured dimensions: domain, unit_of_observation, spatial_granularity, temporal_coverage_parsed, api_capability, plus key_variables.

CRITICAL CONSTRAINTS:
1. Output ONLY via the `extract_data_item_codebook` tool.
2. Be CONSERVATIVE: return null when the metadata genuinely doesn't tell you. Empty/null is HONEST; guessing is harmful.
3. For Brazilian education data, "IDEB" / "SAEB" / "matrícula" are the canonical variables — extract them when mentioned.
4. `api_capability` should be inferred from `type`:
   - "Feature Service" / "Web Map" → "feature_service"
   - "Microsoft Excel" / "CSV Collection" / "PDF" → "static_file" (Excel/CSV) OR "document_link" (PDF/external HTML)
   - "Document Link" → "document_link"
5. `temporal_coverage_parsed`: extract concrete years (1900-2099) from title/snippet. If only one year mentioned (e.g. "Censo 2010"), start_year == end_year. If a range like "2007/2009/.../2023", start_year=2007, end_year=2023.
6. Frequency: "anual"|"bienal"|"trienal"|"pontual"|"atualizado" (atualizado = continuously updated). Null when uncertain.
7. `key_variables`: lowercase, accent-stripped. Top 3-7 variables/columns the item exposes. Examples: ["ideb", "ano", "bairro"], ["matricula", "escola"], ["taxa_analfabetismo", "faixa_etaria"].
8. confidence ∈ [0, 1]: your honest probability the extraction is correct. < 0.5 = "wild guess from sparse metadata"."""

EXTRACT_CODEBOOK_TOOL = {
    "name": "extract_data_item_codebook",
    "description": "Extract structured code_book fields for a data.rio manifest item.",
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "domain", "unit_of_observation", "spatial_granularity",
            "temporal_coverage_parsed", "api_capability", "key_variables",
            "confidence",
        ],
        "properties": {
            "domain": {
                "type": ["string", "null"],
                "enum": [
                    "educacao-basica", "educacao-superior", "saude",
                    "transporte", "ambiente", "social", "economia",
                    "infraestrutura", "seguranca", "cultura", "habitacao",
                    "geografia", "demografia", None,
                ],
                "description": "Top-level theme. Null if cross-cutting or unclear.",
            },
            "unit_of_observation": {
                "type": ["string", "null"],
                "enum": [
                    "bairro", "ra", "ap", "rp", "cre", "escola", "aluno",
                    "professor", "setor_censitario", "individuo", "domicilio",
                    "municipio", "favela", "ponto", None,
                ],
                "description": "What entity each row represents.",
            },
            "spatial_granularity": {
                "type": ["string", "null"],
                "enum": [
                    "bairro", "ra", "ap", "rp", "cre", "ponto", "linha",
                    "poligono", "setor_censitario", "municipio", "favela", None,
                ],
                "description": "Spatial unit / geometry resolution.",
            },
            "temporal_coverage_parsed": {
                "type": ["object", "null"],
                "additionalProperties": False,
                "required": ["start_year", "end_year", "frequency"],
                "properties": {
                    "start_year": {"type": ["integer", "null"], "minimum": 1900, "maximum": 2099},
                    "end_year": {"type": ["integer", "null"], "minimum": 1900, "maximum": 2099},
                    "frequency": {
                        "type": ["string", "null"],
                        "enum": ["anual", "bienal", "trienal", "pontual", "atualizado", None],
                    },
                },
            },
            "api_capability": {
                "type": "string",
                "enum": ["feature_service", "static_file", "document_link", "none"],
            },
            "key_variables": {
                "type": ["array", "null"],
                "items": {"type": "string"},
                "minItems": 0,
                "maxItems": 12,
                "description": "Top 3-7 variable names, lowercase + accent-stripped.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
    },
}


def _cache_path(item_id: str) -> Path:
    return CACHE_DIR / f"codebook_{item_id}.json"


def _cache_get(item_id: str) -> dict | None:
    p = _cache_path(item_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _cache_set(item_id: str, payload: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(item_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _build_user_message(item: dict) -> str:
    parts = [
        f"**Title:** {item.get('title', '(no title)')}",
        f"**Type:** {item.get('type', '(no type)')}",
        f"**Tags:** {', '.join(item.get('tags') or []) or '(none)'}",
    ]
    snippet = (item.get("snippet") or "").strip()
    if snippet:
        if len(snippet) > 1500:
            snippet = snippet[:1500] + "…"
        parts.append(f"**Snippet:** {snippet}")
    if item.get("url"):
        parts.append(f"**URL:** {item['url']}")
    return "\n\n".join(parts)


def extract_codebook(
    item: dict,
    *,
    model: str = DEFAULT_MODEL,
    max_retries: int = 4,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict | None:
    """Single-item LLM extraction. Returns code_book dict ou None em erro."""
    user_msg = _build_user_message(item)

    if dry_run:
        return {
            "_dry_run": True,
            "model": model,
            "user_message": user_msg,
            "item_id": item.get("id"),
        }

    if not HAS_ANTHROPIC:
        raise RuntimeError("anthropic package required: pip install anthropic")
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY env var required")

    # v0.17 resource bargain (VSM S3) — check MAX_TOKENS_PER_PAPER + MAX_LLM_BUDGET_USD
    # antes da call. Raise LLMBudgetExceeded se cap excedido.
    try:
        from _llm import get_budget_tracker  # local import — avoid cycle
    except ImportError:
        get_budget_tracker = None
    if get_budget_tracker is not None:
        # Estimar tokens via heurística 4 chars/tok + 800 system overhead
        est_input = (len(user_msg or "")) // 4 + 800
        get_budget_tracker().check_pre_call(est_input)

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.with_options(max_retries=max_retries).messages.create(
            model=model,
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": SYSTEM_PROMPT_CODEBOOK,
                "cache_control": {"type": "ephemeral"},
            }],
            tools=[{**EXTRACT_CODEBOOK_TOOL, "cache_control": {"type": "ephemeral"}}],
            tool_choice={"type": "tool", "name": "extract_data_item_codebook"},
            messages=[{"role": "user", "content": user_msg}],
        )
    except anthropic.AuthenticationError as e:
        raise RuntimeError(f"ANTHROPIC_API_KEY inválida: {e}") from e
    except Exception as e:  # noqa: BLE001
        if verbose:
            print(f"  [llm-warn] {type(e).__name__}: {e}", file=sys.stderr)
        return None

    # v0.17 — record cost post-call (sem surpresas em batch grande)
    if get_budget_tracker is not None:
        usage = response.usage
        get_budget_tracker().record_post_call(
            {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
            },
            "anthropic",
        )

    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_data_item_codebook":
            result = dict(block.input)
            result["_llm_model"] = response.model
            result["_llm_called_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return result
    return None


def priority_pool(items: list[dict]) -> list[int]:
    """Edu-tagged items WITHOUT code_book, ordenados por numViews desc."""
    idx = []
    for i, it in enumerate(items):
        if it.get("code_book"):
            continue
        tags = set(it.get("tags") or [])
        if tags & EDU_TAGS:
            idx.append(i)
    idx.sort(key=lambda i: -(items[i].get("numViews") or 0))
    return idx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--refresh", action="store_true",
                    help="re-query LLM even if item already has code_book (overwrites)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-cache", action="store_true",
                    help="ignora cache local (mas ainda persiste novas calls)")
    args = ap.parse_args()

    if not MANIFEST_JSON.exists():
        print(f"missing {MANIFEST_JSON}", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
    items = manifest["items"]
    print(f"loaded {len(items)} manifest items")

    has_key = bool(_get_api_key())
    if not has_key and not args.dry_run:
        print("[warn] ANTHROPIC_API_KEY not set — use --dry-run to preview, or set key.")
        return 2

    pool = priority_pool(items)
    print(f"priority pool: {len(pool)} edu-tagged items sem code_book (top {args.limit} by numViews)")

    targets = pool[: args.limit]
    n_done = 0
    n_skipped = 0
    n_errors = 0
    n_low_conf = 0

    for rank, i in enumerate(targets, 1):
        it = items[i]
        if it.get("code_book") and not args.refresh:
            n_skipped += 1
            continue

        item_id = it["id"]
        title = (it.get("title") or "")[:55]

        # Cache hit?
        cached = None if args.no_cache else _cache_get(item_id)
        if cached is not None and not args.refresh:
            cb = cached.get("code_book")
            if cb:
                it["code_book"] = cb
                n_done += 1
                if (cb.get("confidence") or 0) < 0.5:
                    n_low_conf += 1
                if rank <= 10:
                    print(f"  [{rank:>3}/{len(targets)}] CACHE  conf={cb.get('confidence', 0):.2f} {title}")
                continue

        if args.dry_run:
            user_msg = _build_user_message(it)
            print(f"  [{rank:>3}/{len(targets)}] [dry] {item_id[:16]}... {title}")
            print(f"        len(user_msg) = {len(user_msg)} chars")
            continue

        if rank <= 10 or rank % 10 == 0:
            print(f"  [{rank:>3}/{len(targets)}] calling LLM — {title}")

        # v0.17 — captura LLMBudgetExceeded (resource bargain)
        try:
            result = extract_codebook(it)
        except Exception as e:  # noqa: BLE001
            if type(e).__name__ == "LLMBudgetExceeded":
                print(f"\n[BUDGET] {e}", file=sys.stderr)
                print(f"[BUDGET] paramos em {rank-1}/{len(targets)} pra evitar surpresa", file=sys.stderr)
                try:
                    from _llm import get_budget_tracker
                    print(f"[BUDGET] cumulative cost USD: {get_budget_tracker().cumulative_cost_usd:.4f}", file=sys.stderr)
                except ImportError:
                    pass
                break  # save manifest progress + relata
            raise

        if result is None:
            n_errors += 1
            print(f"  [{rank:>3}/{len(targets)}] ERROR — {title}", file=sys.stderr)
            continue

        # Persist nesting: separate fields go directly into code_book; _llm_* metadata too.
        code_book = {
            "domain": result.get("domain"),
            "unit_of_observation": result.get("unit_of_observation"),
            "spatial_granularity": result.get("spatial_granularity"),
            "temporal_coverage_parsed": result.get("temporal_coverage_parsed"),
            "api_capability": result.get("api_capability"),
            "key_variables": result.get("key_variables"),
            "confidence": result.get("confidence"),
            "_llm_model": result.get("_llm_model"),
            "_llm_called_at": result.get("_llm_called_at"),
        }
        it["code_book"] = code_book
        _cache_set(item_id, {"code_book": code_book, "item_title": it.get("title")})

        conf = code_book.get("confidence") or 0
        if conf < 0.5:
            n_low_conf += 1
        n_done += 1

        # Throttle defensive (haiku is fast but politeness keeps quotas safe)
        time.sleep(0.3)

    if args.dry_run:
        print(f"\n[dry-run] would query {len([i for i in targets if not items[i].get('code_book')])} items")
        return 0

    print("\n=== summary ===")
    print(f"  enriched: {n_done}")
    print(f"  skipped (already had code_book): {n_skipped}")
    print(f"  errors: {n_errors}")
    print(f"  low confidence (<0.5): {n_low_conf}")

    if n_done > 0:
        MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {MANIFEST_JSON.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
