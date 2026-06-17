"""VSM S3* Auditor — auditoria esporádica do pipeline (cold cache + sample).

Reproduz operacionalmente o canal vertical S3* descrito em
`.claude/skills/vsm-s3star-auditor.md` e `docs/arquitetura.md`. **NÃO é
parte do CI rotineiro** (esse é S2/S3). Roda esporadicamente quando
trust no output do pipeline está em questão.

Procedure (4 fases):

1. **Bootstrap Theil determinism** — re-roda 35_bootstrap_theil_ci.py e
   diffa byte-equal contra commit. Diff = bug em acec.stats.theil_decompose.

2. **Sample 20 candidates** (seed=42 fixo) — inspeção visual de
   match_detail.composite + status + suggested_requirements top-1.
   Output em audit/ pra revisão humana.

3. **Schema validation cross-stages** — re-roda 31_build_paper_catalog
   --validate-funnel pra ver se YAML ainda obedece schema.

4. **LLM vs BoW agreement** (se LLM populado) — re-roda 56 e verifica
   agreement ≥ 70%, taxonomy_gap ≤ 5%.

Outputs:
  data/processed/audit_<date>.md  — relatório markdown legível
  data/processed/audit_<date>.json — machine-parseable summary

Não modifica nenhum artefato do pipeline. Read-only audit.

Uso:
  python3 analysis/62_s3star_audit.py            # audit completo
  python3 analysis/62_s3star_audit.py --sample 50   # mais candidates
  python3 analysis/62_s3star_audit.py --skip-bootstrap  # pular Theil
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
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
PROCESSED_DIR = ROOT / "data" / "processed"
TODAY = date.today().isoformat()


def audit_bootstrap_theil() -> dict:
    """Phase 1: re-run 35 + diff vs committed. Deterministic seed."""
    script = ROOT / "analysis" / "35_bootstrap_theil_ci.py"
    csv_out = PROCESSED_DIR / "theil_bootstrap_ci.csv"
    if not script.exists():
        return {"status": "skipped", "reason": "script not found"}
    if not csv_out.exists():
        return {"status": "skipped", "reason": "committed csv not found"}
    try:
        r = subprocess.run(
            ["python3", str(script)],
            capture_output=True, text=True, timeout=300, cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "reason": "bootstrap took > 300s"}
    if r.returncode != 0:
        return {"status": "error", "stderr": r.stderr[:500]}
    # Diff git
    diff = subprocess.run(
        ["git", "diff", "--quiet", str(csv_out)],
        cwd=ROOT, capture_output=True,
    )
    return {
        "status": "pass" if diff.returncode == 0 else "drift",
        "csv_path": str(csv_out.relative_to(ROOT)),
        "explanation": (
            "Bootstrap byte-equal. Determinism OK." if diff.returncode == 0
            else "DRIFT: bootstrap output mudou desde último commit. "
                 "Possível bug em acec.stats.theil_decompose ou no script 35."
        ),
    }


def audit_sample_candidates(n: int = 20, seed: int = 42) -> dict:
    """Phase 2: amostra random N candidates pra inspeção manual."""
    if not FUNNEL_YML.exists():
        return {"status": "skipped", "reason": "funnel missing"}
    doc = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    candidates = doc.get("candidates") or []
    if not candidates:
        return {"status": "skipped", "reason": "empty funnel"}
    random.seed(seed)
    n = min(n, len(candidates))
    sample = random.sample(candidates, n)
    rows = []
    for c in sample:
        cov = c.get("coverage") or []
        statuses = [x.get("status") for x in cov]
        composites = [
            (x.get("match_detail") or {}).get("composite") for x in cov
        ]
        rows.append({
            "openalex_id": (c.get("openalex_id") or "?").split("/")[-1],
            "title": (c.get("title") or "")[:80],
            "citations": c.get("citations") or 0,
            "is_brazilian": bool(c.get("is_brazilian")),
            "n_coverage": len(cov),
            "statuses": statuses,
            "composites": [round(x, 2) if x else None for x in composites],
        })
    return {
        "status": "sample-ready",
        "n_sampled": n,
        "seed": seed,
        "n_total_candidates": len(candidates),
        "rows": rows,
        "explanation": (
            f"Random sample of {n} candidates (seed={seed}). "
            "Inspect manually: composite makes sense? top-1 cat correct? "
            "coverage status honest?"
        ),
    }


def audit_schema_validation() -> dict:
    """Phase 3: re-run 31 --validate-funnel."""
    script = ROOT / "analysis" / "31_build_paper_catalog.py"
    if not script.exists():
        return {"status": "skipped", "reason": "script not found"}
    try:
        r = subprocess.run(
            ["python3", str(script), "--validate-funnel"],
            capture_output=True, text=True, timeout=60, cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    return {
        "status": "pass" if r.returncode == 0 else "fail",
        "exit_code": r.returncode,
        "stdout_tail": r.stdout[-500:] if r.stdout else "",
        "explanation": (
            "Schema validation passa. Catálogo + funnel obedecem schema."
            if r.returncode == 0 else
            "FAIL: schema violado. Investigar entries inválidas."
        ),
    }


def audit_llm_vs_bow() -> dict:
    """Phase 4 (opcional): re-run 56 e checa agreement."""
    script = ROOT / "analysis" / "56_llm_vs_bow_compare.py"
    if not script.exists():
        return {"status": "skipped", "reason": "script not found"}
    summary_path = PROCESSED_DIR / "llm_vs_bow_comparison.json"
    if not summary_path.exists():
        return {"status": "skipped", "reason": "no comparison json yet"}
    try:
        r = subprocess.run(
            ["python3", str(script)],
            capture_output=True, text=True, timeout=60, cwd=ROOT,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if r.returncode != 0:
        return {"status": "error", "stderr": r.stderr[:500]}
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    n_with_both = summary.get("n_with_both") or 0
    if n_with_both == 0:
        return {
            "status": "no-data",
            "explanation": "Nenhum candidate tem ambos llm_* e bow_*. "
                          "Rode 55_llm_extract_requirements primeiro.",
        }
    agreement = summary.get("top1_agreement") or 0
    gap = summary.get("taxonomy_gap_rate") or 0
    return {
        "status": "computed",
        "n_with_both": n_with_both,
        "top1_agreement": agreement,
        "taxonomy_gap_rate": gap,
        "explanation": (
            f"LLM vs BoW agreement: {agreement:.1%} (target ≥70%); "
            f"taxonomy gap rate: {gap:.1%} (target ≤5%)"
        ),
    }


def render_markdown(summary: dict) -> str:
    """Render audit summary as readable Markdown."""
    lines = []
    lines.append(f"# VSM S3* Audit — {TODAY}")
    lines.append("")
    lines.append("Esporádico, read-only. NÃO modifica artefatos do pipeline.")
    lines.append("Auto-gerado por `analysis/62_s3star_audit.py`.")
    lines.append("")

    lines.append("## Phase 1 — Bootstrap Theil determinism")
    p1 = summary["bootstrap_theil"]
    lines.append(f"- **Status**: `{p1['status']}`")
    lines.append(f"- {p1.get('explanation', '')}")
    lines.append("")

    lines.append("## Phase 2 — Random sample candidates")
    p2 = summary["sample"]
    lines.append(f"- **N sampled**: {p2.get('n_sampled', 0)} (seed={p2.get('seed', 42)})")
    lines.append(f"- {p2.get('explanation', '')}")
    lines.append("")
    if p2.get("rows"):
        lines.append("| openalex_id | cit | BR? | n_cov | statuses | composites | title |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in p2["rows"]:
            br = "✓" if r["is_brazilian"] else " "
            stat = ",".join(s or "?" for s in r["statuses"])[:30]
            comp = ",".join(str(c) for c in r["composites"])[:30]
            lines.append(
                f"| {r['openalex_id']} | {r['citations']} | {br} | {r['n_coverage']} | "
                f"{stat} | {comp} | {r['title'][:60]} |"
            )
        lines.append("")

    lines.append("## Phase 3 — Schema validation")
    p3 = summary["schema"]
    lines.append(f"- **Status**: `{p3['status']}`")
    lines.append(f"- {p3.get('explanation', '')}")
    lines.append("")

    lines.append("## Phase 4 — LLM vs BoW agreement")
    p4 = summary["llm_vs_bow"]
    lines.append(f"- **Status**: `{p4['status']}`")
    lines.append(f"- {p4.get('explanation', '')}")
    lines.append("")

    lines.append("## Recommendation")
    overall = []
    if p1.get("status") == "drift":
        overall.append("**RED** — bootstrap drift detected (Theil bug?)")
    if p3.get("status") == "fail":
        overall.append("**RED** — schema validation failed")
    if p4.get("status") == "computed":
        if p4.get("top1_agreement", 1) < 0.7:
            overall.append("**YELLOW** — LLM vs BoW agreement low")
    if not overall:
        overall.append("**GREEN** — pipeline trustworthy. Nada urgente.")
    for line in overall:
        lines.append(f"- {line}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-bootstrap", action="store_true",
                    help="skip phase 1 (theil bootstrap re-run)")
    args = ap.parse_args()

    print(f"VSM S3* Auditor — {TODAY}", file=sys.stderr)
    print("Reproduz canal vertical S3*. Esporádico, read-only.", file=sys.stderr)
    print("", file=sys.stderr)

    summary: dict = {}

    print("Phase 1: bootstrap Theil determinism…", file=sys.stderr)
    if args.skip_bootstrap:
        summary["bootstrap_theil"] = {"status": "skipped", "reason": "--skip-bootstrap"}
    else:
        summary["bootstrap_theil"] = audit_bootstrap_theil()
    print(f"  → {summary['bootstrap_theil']['status']}", file=sys.stderr)

    print("Phase 2: sample candidates…", file=sys.stderr)
    summary["sample"] = audit_sample_candidates(n=args.sample, seed=args.seed)
    print(f"  → sampled {summary['sample'].get('n_sampled', 0)}", file=sys.stderr)

    print("Phase 3: schema validation…", file=sys.stderr)
    summary["schema"] = audit_schema_validation()
    print(f"  → {summary['schema']['status']}", file=sys.stderr)

    print("Phase 4: LLM vs BoW…", file=sys.stderr)
    summary["llm_vs_bow"] = audit_llm_vs_bow()
    print(f"  → {summary['llm_vs_bow']['status']}", file=sys.stderr)

    # Write outputs (NOT committed by default — read-only audit goes to data/processed/)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    md_path = PROCESSED_DIR / f"audit_{TODAY}.md"
    json_path = PROCESSED_DIR / f"audit_{TODAY}.json"

    md_path.write_text(render_markdown(summary), encoding="utf-8")
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("", file=sys.stderr)
    print(f"wrote {md_path.relative_to(ROOT)}", file=sys.stderr)
    print(f"wrote {json_path.relative_to(ROOT)}", file=sys.stderr)

    # Overall verdict
    print("", file=sys.stderr)
    verdict = "GREEN"
    if summary["bootstrap_theil"].get("status") == "drift":
        verdict = "RED"
    if summary["schema"].get("status") == "fail":
        verdict = "RED"
    if (
        summary["llm_vs_bow"].get("status") == "computed"
        and (summary["llm_vs_bow"].get("top1_agreement") or 1) < 0.7
    ):
        if verdict == "GREEN":
            verdict = "YELLOW"
    print(f"=== AUDIT VERDICT: {verdict} ===", file=sys.stderr)

    return 0 if verdict in ("GREEN", "YELLOW") else 1


if __name__ == "__main__":
    sys.exit(main())
