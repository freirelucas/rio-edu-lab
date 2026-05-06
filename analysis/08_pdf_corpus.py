"""Catálogo empírico dos PDFs do Grupo Educação.

Para cada PDF em data/raw/pdf/:
  - n_pages, has_text_layer (boolean), first_page_text (~500 chars)
  - colecao (heurística: classifica entre Estudos Cariocas / Rio Estudos /
    Notas Técnicas IPP / Cadernos do Rio / outros, com base em title + p1)
  - issue_year (se detectável no título ou na 1ª página)

Outputs:
  - data/processed/pdf_catalog.csv
  - data/raw/pdf/_first_pages/{id}.txt   (texto da 1ª página, para grep manual)
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "pdf"
INDEX = RAW / "_index.json"
MANIFEST = ROOT / "data" / "manifest.json"
OUT_CSV = ROOT / "data" / "processed" / "pdf_catalog.csv"
FIRST_PAGES = RAW / "_first_pages"

COLLECTIONS = [
    ("Estudos Cariocas", re.compile(r"\bestudos cariocas\b", re.I)),
    ("Rio Estudos", re.compile(r"\brio[\s\-]*estudos\b", re.I)),
    ("Notas Técnicas IPP", re.compile(r"\bnotas?\s+técnicas?\s+ipp\b|\bnota técnica\b", re.I)),
    ("Cadernos do Rio", re.compile(r"\bcadernos do rio\b", re.I)),
    ("Painel.RIO / Atlas", re.compile(r"\bpainel\.rio\b|\batlas\b", re.I)),
]

YEAR_RE = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")


def classify_collection(title: str, first_page: str) -> str:
    haystack = f"{title}\n{first_page[:2000]}"
    for label, regex in COLLECTIONS:
        if regex.search(haystack):
            return label
    return "(outros)"


def detect_year(title: str, first_page: str) -> int | None:
    # title first, then first page
    candidates: list[int] = []
    for src in (title, first_page[:2000]):
        for m in YEAR_RE.finditer(src):
            candidates.append(int(m.group(0)))
    if not candidates:
        return None
    # Pick the most common, or the latest if tied
    cnt = Counter(candidates)
    most = cnt.most_common(1)[0][1]
    tied = [y for y, c in cnt.items() if c == most]
    return max(tied)


def parse_pdf(path: Path) -> dict:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(str(path), strict=False)
        n_pages = len(reader.pages)
        first_page_text = ""
        if n_pages:
            try:
                first_page_text = (reader.pages[0].extract_text() or "")[:2000]
            except Exception as e:
                first_page_text = f"(erro extraindo p1: {e!r})"
        has_text = bool(first_page_text and not first_page_text.startswith("(erro"))
        is_encrypted = bool(getattr(reader, "is_encrypted", False))
        return {
            "n_pages": n_pages,
            "has_text_layer": has_text,
            "is_encrypted": is_encrypted,
            "first_page_text": first_page_text,
        }
    except PdfReadError as e:
        return {"error": f"PdfReadError: {e}"}
    except Exception as e:
        return {"error": repr(e)}


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pdf_items = {it["id"]: it for it in manifest["items"] if it.get("type") == "PDF"}

    files = sorted(RAW.glob("*.pdf"))
    if not files:
        print("no PDFs in data/raw/pdf/. Run 07_download_pdfs.py first.")
        return 1
    print(f"manifest pdf items: {len(pdf_items)}, files on disk: {len(files)}")

    FIRST_PAGES.mkdir(parents=True, exist_ok=True)

    rows = []
    started = time.monotonic()
    for i, path in enumerate(files, 1):
        item_id = path.stem
        item = pdf_items.get(item_id, {})
        title = item.get("title", "")
        size = path.stat().st_size

        info = parse_pdf(path)
        first_page = info.get("first_page_text", "") or ""
        if first_page:
            (FIRST_PAGES / f"{item_id}.txt").write_text(first_page, encoding="utf-8")

        row = {
            "id": item_id,
            "title": title,
            "file_bytes": size,
            "n_pages": info.get("n_pages"),
            "has_text_layer": info.get("has_text_layer"),
            "is_encrypted": info.get("is_encrypted"),
            "colecao": classify_collection(title, first_page),
            "issue_year": detect_year(title, first_page),
            "num_views": item.get("numViews", 0) or 0,
            "tags": "|".join(item.get("tags", []) or []),
            "first_paragraph": (first_page.replace("\n", " ").strip()[:280]),
            "parse_error": info.get("error", ""),
        }
        rows.append(row)
        if i % 10 == 0 or i == len(files):
            print(f"[{i}/{len(files)}] {item_id}  pages={info.get('n_pages')}  text={info.get('has_text_layer')}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    elapsed = time.monotonic() - started
    print(
        f"\ndone in {elapsed:.1f}s. "
        f"cataloged={len(rows)}, with_text={sum(1 for r in rows if r['has_text_layer'])}, "
        f"errors={sum(1 for r in rows if r['parse_error'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
