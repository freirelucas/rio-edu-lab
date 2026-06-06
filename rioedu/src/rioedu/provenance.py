"""Provenance stamp: repo commit + manifest snapshot hash + UTC timestamp.

Embebed em cada notebook gerado pra que o leitor consiga reproduzir byte-a-byte
o output (modulo timestamp): `rioedu generate` no mesmo commit + mesmo manifest
= mesmo notebook.
"""
from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _git_rev(root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(root), text=True, stderr=subprocess.DEVNULL
        )
        return out.strip()[:12]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _sha256_file(path: Path, n_chars: int = 12) -> str:
    if not path.exists():
        return "missing"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:n_chars]


def compute(repo_root: Path) -> dict:
    return {
        "repo_commit": _git_rev(repo_root),
        "manifest_hash": _sha256_file(repo_root / "data" / "manifest.json"),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
