"""Aplica `data/code_signals.yml` em candidates do funnel.

Sprint v0.15 alt · Stream 2 ajustada — `code_signal` populado SEM GITHUB_TOKEN.
As buscas são feitas in-session via mcp__github__search_code (sem API key),
curador (claude_session) persiste em YAML, este script aplica em
`data/papers_funnel.yml` idempotentemente.

Schema da entrada (data/code_signals.yml):
  version: 1
  searched_at: "2026-06-08"
  signals:
    <openalex_id>:
      doi: <bare DOI>
      queries:
        - {q: '"<doi>" extension:py', total_hits: 0, code_hits_kept: 0}
        - {q: '"<doi>" extension:R', total_hits: 1, code_hits_kept: 1}
      n_code_hits: 1
      top_repos: ["owner/repo1", "owner/repo2"]
      _source: claude_session
      _classified_at: "2026-06-08"

Merge strategy: substitui completamente o campo `code_signal` no candidate
(replace, não merge parcial). Preserva o resto do candidate intacto.

Idempotente — segunda call é noop. Strict mode falha em openalex_id ausente.
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
SIGNALS_YML = ROOT / "data" / "code_signals.yml"
FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"


def load_signals(path: Path) -> dict[str, dict]:
    """Returns {openalex_id: code_signal_dict}. Valida version + presença.

    Raises ValueError se schema malformado.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: root deve ser dict")
    if doc.get("version") != 1:
        raise ValueError(f"{path}: version != 1 (got {doc.get('version')!r})")
    signals = doc.get("signals") or {}
    if not isinstance(signals, dict):
        raise ValueError(f"{path}: 'signals' deve ser dict")
    return signals


def write_funnel(funnel_path: Path, candidates: list[dict]) -> None:
    """Preserva header comments + reescreve candidates block.

    Mesma estratégia de 46/47 (analysis/46_extract_requirements.py:62-77).
    """
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


def apply_signals(
    candidates: list[dict],
    signals: dict[str, dict],
    *,
    strict: bool = False,
) -> tuple[int, int, list[str]]:
    """Mutates candidates in-place. Returns (n_applied, n_unchanged, missing_ids).

    Normaliza openalex_id em ambos os lados — funnel armazena URL completa
    (`https://openalex.org/W123`), YAML pode usar bare ID (`W123`). Match
    invariante ao prefixo.
    """
    def _strip(oid: str | None) -> str | None:
        if not oid:
            return None
        s = str(oid).strip()
        return s.rsplit("/", 1)[-1] if "/" in s else s

    by_id = {}
    for c in candidates:
        norm = _strip(c.get("openalex_id"))
        if norm:
            by_id[norm] = c

    n_applied = 0
    n_unchanged = 0
    missing: list[str] = []
    for oid_raw, sig in signals.items():
        oid = _strip(oid_raw)
        c = by_id.get(oid)
        if c is None:
            missing.append(oid_raw)
            if strict:
                raise KeyError(f"openalex_id {oid_raw!r} not in funnel")
            continue
        existing = c.get("code_signal")
        if existing == sig:
            n_unchanged += 1
            continue
        c["code_signal"] = dict(sig)
        n_applied += 1
    return n_applied, n_unchanged, missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--signals", type=Path, default=SIGNALS_YML)
    ap.add_argument("--funnel", type=Path, default=FUNNEL_YML)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="falha se openalex_id em signals não está no funnel")
    args = ap.parse_args()

    try:
        signals = load_signals(args.signals)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"loaded {len(signals)} code_signal entries from {args.signals.relative_to(ROOT)}")

    if not args.funnel.exists():
        print(f"missing {args.funnel}", file=sys.stderr)
        return 1
    doc = yaml.safe_load(args.funnel.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    print(f"loaded {len(candidates)} candidates from funnel")

    try:
        n_applied, n_unchanged, missing = apply_signals(
            candidates, signals, strict=args.strict,
        )
    except KeyError as e:
        print(f"strict mode failure: {e}", file=sys.stderr)
        return 2

    print("\n=== summary ===")
    print(f"  applied: {n_applied}")
    print(f"  unchanged (already equal): {n_unchanged}")
    print(f"  missing openalex_ids (skipped): {len(missing)}")
    for mid in missing[:5]:
        print(f"    - {mid}")
    if len(missing) > 5:
        print(f"    ... and {len(missing) - 5} more")

    if args.dry_run:
        print("\n[dry-run] not writing funnel")
        return 0

    if n_applied == 0:
        print("nothing to write (all signals already applied)")
        return 0

    write_funnel(args.funnel, candidates)
    print(f"wrote {args.funnel.relative_to(ROOT)}")

    # Headline: signals com hits vs sem
    n_with_hits = sum(1 for s in signals.values() if (s.get("n_code_hits") or 0) > 0)
    print(f"\n  signals with n_code_hits > 0: {n_with_hits}/{len(signals)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
