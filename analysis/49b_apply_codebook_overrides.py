"""Aplica `data/codebook_overrides.yml` em `data/manifest.json`.

Sprint v0.15 alt — alternative ao `49_codebook_backfill.py` (que chama
Anthropic API). Aqui o curator (claude_session, claude_api, ou human) já
deixou as classifications em YAML committável; este script só faz o merge
idempotente no manifest.json.

Schema da entrada (data/codebook_overrides.yml):
  version: 1
  overrides:
    <item_id>:
      domain: ...
      unit_of_observation: ...
      spatial_granularity: ...
      temporal_coverage_parsed: {start_year, end_year, frequency}
      api_capability: ...
      key_variables: [...]
      confidence: float [0, 1]
      _source: claude_session | claude_api | human
      _classified_at: ISO date

Merge strategy: override REPLACES `item.code_book` completamente (não merge
parcial — evita estados híbridos confusos). Existing fields que não estão no
override (ex. temporal_coverage string original, key_variables herdado do
vertical slice) NÃO são preservados. Pra preservar legacy fields, inclua-os
no override explicitamente.

Idempotente: re-run aplica os MESMOS overrides; manifest.json fica byte-equal
(JSON deterministically sorted by item ordering, fields ordered como vêm do
YAML insertion).

Uso:
  python3 analysis/49b_apply_codebook_overrides.py --dry-run    # preview
  python3 analysis/49b_apply_codebook_overrides.py              # apply
  python3 analysis/49b_apply_codebook_overrides.py --strict     # falha se item id não existe
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OVERRIDES_YML = ROOT / "data" / "codebook_overrides.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"


def load_overrides(path: Path) -> dict[str, dict]:
    """Returns {item_id: code_book_dict}. Valida version + presença de
    `overrides`. Levanta ValueError se schema malformado."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: root deve ser dict")
    if doc.get("version") != 1:
        raise ValueError(f"{path}: version != 1 (got {doc.get('version')!r})")
    overrides = doc.get("overrides") or {}
    if not isinstance(overrides, dict):
        raise ValueError(f"{path}: 'overrides' deve ser dict")
    return overrides


def apply_overrides(
    manifest: dict,
    overrides: dict[str, dict],
    *,
    strict: bool = False,
) -> tuple[int, int, list[str]]:
    """Mutates manifest in-place. Returns (n_applied, n_unchanged, missing_ids)."""
    items_by_id = {it["id"]: it for it in manifest["items"]}
    n_applied = 0
    n_unchanged = 0
    missing: list[str] = []
    for item_id, override_cb in overrides.items():
        it = items_by_id.get(item_id)
        if it is None:
            missing.append(item_id)
            if strict:
                raise KeyError(f"item id {item_id!r} not in manifest")
            continue
        existing = it.get("code_book")
        if existing == override_cb:
            n_unchanged += 1
            continue
        it["code_book"] = dict(override_cb)
        n_applied += 1
    return n_applied, n_unchanged, missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--overrides", type=Path, default=OVERRIDES_YML)
    ap.add_argument("--manifest", type=Path, default=MANIFEST_JSON)
    ap.add_argument("--dry-run", action="store_true",
                    help="mostra o que seria aplicado, sem escrever")
    ap.add_argument("--strict", action="store_true",
                    help="falha se item_id no overrides não existe no manifest")
    args = ap.parse_args()

    try:
        overrides = load_overrides(args.overrides)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"loaded {len(overrides)} overrides from {args.overrides.relative_to(ROOT)}")

    if not args.manifest.exists():
        print(f"missing {args.manifest}", file=sys.stderr)
        return 1
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    try:
        n_applied, n_unchanged, missing = apply_overrides(
            manifest, overrides, strict=args.strict,
        )
    except KeyError as e:
        print(f"strict mode failure: {e}", file=sys.stderr)
        return 2

    print("\n=== summary ===")
    print(f"  applied: {n_applied}")
    print(f"  unchanged (already equal to override): {n_unchanged}")
    print(f"  missing item ids (skipped): {len(missing)}")
    for mid in missing[:5]:
        print(f"    - {mid}")
    if len(missing) > 5:
        print(f"    ... and {len(missing) - 5} more")

    if args.dry_run:
        print("\n[dry-run] not writing manifest")
        return 0

    if n_applied == 0:
        print("nothing to write (all overrides already applied)")
        return 0

    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    print(f"wrote {args.manifest.relative_to(ROOT)}")

    # Headline: distribuição de confidence
    confs = [
        (cb.get("confidence") or 0)
        for cb in overrides.values()
        if isinstance(cb, dict)
    ]
    if confs:
        n_high = sum(1 for c in confs if c >= 0.7)
        n_med = sum(1 for c in confs if 0.5 <= c < 0.7)
        n_low = sum(1 for c in confs if c < 0.5)
        print(f"\n  confidence dist: high (≥0.7) = {n_high}, mid [0.5-0.7) = {n_med}, low (<0.5) = {n_low}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
