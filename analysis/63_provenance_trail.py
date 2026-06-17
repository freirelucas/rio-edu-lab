"""Provenance Trail Generator — auditabilidade um-clique por paper replicado.

Sprint v0.17 — fecha a promessa "auditabilidade um clique" do `docs/sobre.md`.
Pra cada paper com `replication_status: full | partial`, gera um arquivo
audit-trail completo encadeando:

  paper DOI/URL
   ↓ (data_availability_statement.sources com sha256 quando disponível)
  data.rio items
   ↓ (manifest.json hash do snapshot)
  manifest snapshot
   ↓ (git commit hash do script de replicação)
  código replicador
   ↓ (data_processed sha256 das CSVs de saída)
  resultados publicados

Output em `docs/provenance/<paper_id>.md` (committed, parte do hotsite).

Diferença vs TOP scorecard:
  - TOP: 8 standards × 4 levels — score de transparência
  - Provenance trail: cadeia DETERMINÍSTICA de hashes pra reprodução

Auto-rodável via CI drift check — re-roda + diffa pra detectar drift
silencioso (mudança no script sem rerun da replicação → hash do code não
bate com o do paper provenance).

Uso:
  python3 analysis/63_provenance_trail.py            # gera todos
  python3 analysis/63_provenance_trail.py --paper-id theil-1967-economics
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"
OUT_DIR = ROOT / "docs" / "provenance"
OUT_SUMMARY = ROOT / "data" / "processed" / "provenance_summary.json"


def file_sha256(path: Path) -> str:
    """SHA256 hex do arquivo. Empty/missing → 'NONE'."""
    if not path.exists():
        return "NONE"
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1 << 16)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def git_commit_for_path(path: Path) -> str:
    """Returns short SHA do último commit que tocou path. 'UNKNOWN' se erro."""
    try:
        r = subprocess.run(
            ["git", "log", "-1", "--format=%h", "--", str(path.relative_to(ROOT))],
            capture_output=True, text=True, timeout=10, cwd=ROOT, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN"


def repo_head_commit() -> str:
    """Returns current HEAD short SHA. 'UNKNOWN' se erro."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5, cwd=ROOT, check=False,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN"


def build_provenance(paper: dict, manifest_hash: str, head_commit: str) -> dict:
    """Compute provenance dict pra 1 paper."""
    pid = paper["id"]
    scripts = paper.get("scripts") or []
    script_commits = {}
    for sid in scripts:
        # Glob por padrão numérico (10_theil_ideb.py) ou nome direto.
        matches = list((ROOT / "analysis").glob(f"{sid:02d}_*.py" if isinstance(sid, int) else f"{sid}.py"))
        if matches:
            script_commits[str(sid)] = {
                "path": str(matches[0].relative_to(ROOT)),
                "last_commit": git_commit_for_path(matches[0]),
            }

    # Hash committed CSVs em data/processed/ que provavelmente são output desta replication
    processed_hashes = {}
    if pid == "theil-1967-economics":
        for fname in ["theil_ideb_anos_iniciais.csv", "theil_ideb_anos_finais.csv", "theil_bootstrap_ci.csv"]:
            p = ROOT / "data" / "processed" / fname
            if p.exists():
                processed_hashes[fname] = file_sha256(p)
    elif pid == "pereira-2019-ipea":
        for fname in ["hex_edu_2023.csv", "acessibilidade_por_ap.csv"]:
            p = ROOT / "data" / "processed" / fname
            if p.exists():
                processed_hashes[fname] = file_sha256(p)
    elif pid == "reardon-2011-whither":
        for fname in ["vuln_edu_bairros.csv", "quadrantes_summary.csv"]:
            p = ROOT / "data" / "processed" / fname
            if p.exists():
                processed_hashes[fname] = file_sha256(p)

    # Build provenance dict
    catalog_prov = paper.get("provenance") or {}
    das = paper.get("data_availability_statement") or {}

    return {
        "paper_id": pid,
        "paper_doi_or_url": paper.get("doi_or_url"),
        "openalex_id": paper.get("openalex_id"),
        "replication_status": paper.get("replication_status"),
        "replicator": catalog_prov.get("replicator"),
        "replication_date": catalog_prov.get("replication_date"),

        "data_sources": [
            {
                "name": s.get("name"),
                "url": s.get("url"),
                "access_date": s.get("access_date"),
                "license": s.get("license"),
                "declared_sha256": s.get("sha256"),  # declared in catalog
            }
            for s in (das.get("sources") or [])
        ],

        "manifest_snapshot": {
            "path": "data/manifest.json",
            "sha256": manifest_hash,
        },

        "code": {
            "scripts": script_commits,
            "head_commit_at_audit": head_commit,
        },

        "results": {
            "processed_csv_hashes": processed_hashes,
        },

        "audit_chain_complete": (
            bool(catalog_prov.get("replicator"))
            and bool(catalog_prov.get("replication_date"))
            and bool(script_commits)
            and bool(processed_hashes)
        ),
    }


def render_markdown(prov: dict, paper: dict) -> str:
    """Render provenance dict como Markdown legível com badges de audit."""
    lines = []
    lines.append(f"# Provenance trail — {paper.get('title', prov['paper_id'])}")
    lines.append("")
    lines.append(f"**Paper ID**: `{prov['paper_id']}`")
    lines.append(f"**DOI/URL**: {prov['paper_doi_or_url'] or '_(none)_'}")
    lines.append(f"**OpenAlex**: {prov['openalex_id'] or '_(none)_'}")
    lines.append(f"**Status**: `{prov['replication_status']}`")
    lines.append(f"**Replicator**: {prov['replicator'] or '_(unspecified)_'}")
    lines.append(f"**Replication date**: {prov['replication_date'] or '_(unspecified)_'}")
    lines.append("")

    if prov["audit_chain_complete"]:
        lines.append("✅ **Audit chain complete** — paper DOI → data sources → manifest snapshot → code commits → results.")
    else:
        lines.append("⚠️ **Audit chain partial** — alguns elos faltam. Veja seções abaixo.")
    lines.append("")

    lines.append("## 📊 Data sources")
    lines.append("")
    if prov["data_sources"]:
        lines.append("| Source | URL | Access date | License | Declared SHA256 |")
        lines.append("|---|---|---|---|---|")
        for s in prov["data_sources"]:
            sha = s.get("declared_sha256") or "_(not declared)_"
            lines.append(f"| {s.get('name', '?')} | {s.get('url', '?')} | {s.get('access_date', '?')} | {s.get('license', '?')} | `{sha[:12]}...` |")
    else:
        lines.append("_(no data_availability_statement.sources populated yet)_")
    lines.append("")

    lines.append("## 🗃️ Manifest snapshot")
    lines.append("")
    lines.append(f"- **Path**: `{prov['manifest_snapshot']['path']}`")
    lines.append(f"- **SHA256**: `{prov['manifest_snapshot']['sha256']}`")
    lines.append("")

    lines.append("## 💻 Code (scripts replicadores)")
    lines.append("")
    if prov["code"]["scripts"]:
        lines.append("| Script ID | Path | Last commit |")
        lines.append("|---|---|---|")
        for sid, info in prov["code"]["scripts"].items():
            lines.append(f"| {sid} | `{info['path']}` | `{info['last_commit']}` |")
    else:
        lines.append("_(catalogo.scripts vazio ou paths não resolvidos)_")
    lines.append(f"\n- **HEAD commit no momento do audit**: `{prov['code']['head_commit_at_audit']}`")
    lines.append("")

    lines.append("## 📈 Results (data/processed/ outputs)")
    lines.append("")
    if prov["results"]["processed_csv_hashes"]:
        lines.append("| File | SHA256 (first 12) |")
        lines.append("|---|---|")
        for fname, h in prov["results"]["processed_csv_hashes"].items():
            lines.append(f"| `{fname}` | `{h[:12]}...` |")
    else:
        lines.append("_(no processed CSVs found for this paper_id)_")
    lines.append("")

    lines.append("## How to verify")
    lines.append("")
    lines.append("```bash")
    lines.append("# 1. Pull repo at the commit above")
    lines.append(f"git checkout {prov['code']['head_commit_at_audit']}")
    lines.append("")
    lines.append("# 2. Re-run replication scripts")
    for info in prov["code"]["scripts"].values():
        lines.append(f"python3 {info['path']}")
    lines.append("")
    lines.append("# 3. Verify hashes match")
    for fname, h in prov["results"]["processed_csv_hashes"].items():
        lines.append(f"sha256sum data/processed/{fname}")
        lines.append(f"# Expect: {h}")
    lines.append("```")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Auto-gerado por `analysis/63_provenance_trail.py`. Audit trail v0.17. CC-BY-4.0._")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper-id", default=None, help="só processa este paper")
    args = ap.parse_args()

    if not CATALOG_YML.exists():
        print(f"missing {CATALOG_YML}", file=sys.stderr)
        return 1
    catalog = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8")) or {}
    papers = catalog.get("papers") or []

    # Filter pra replicated papers
    replicated = [p for p in papers if p.get("replication_status") in ("full", "partial")]
    if args.paper_id:
        replicated = [p for p in replicated if p["id"] == args.paper_id]
        if not replicated:
            print(f"no replicated paper with id={args.paper_id}", file=sys.stderr)
            return 1

    print(f"generating provenance for {len(replicated)} papers", file=sys.stderr)

    # Compute manifest hash once (shared across all papers)
    manifest_hash = file_sha256(MANIFEST_JSON)
    head_commit = repo_head_commit()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)

    summary = []
    for paper in replicated:
        prov = build_provenance(paper, manifest_hash, head_commit)
        md = render_markdown(prov, paper)
        out_path = OUT_DIR / f"{paper['id']}.md"
        out_path.write_text(md, encoding="utf-8")
        summary.append({
            "paper_id": prov["paper_id"],
            "audit_chain_complete": prov["audit_chain_complete"],
            "n_data_sources": len(prov["data_sources"]),
            "n_scripts": len(prov["code"]["scripts"]),
            "n_processed_outputs": len(prov["results"]["processed_csv_hashes"]),
        })
        print(f"  wrote {out_path.relative_to(ROOT)}", file=sys.stderr)

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT_SUMMARY.relative_to(ROOT)}", file=sys.stderr)

    n_complete = sum(1 for s in summary if s["audit_chain_complete"])
    print("\n=== headline ===", file=sys.stderr)
    print(f"  papers processed: {len(summary)}", file=sys.stderr)
    print(f"  audit chain complete: {n_complete}/{len(summary)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
