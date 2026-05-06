"""Parser for hierarchical AP→RP→RA→bairro Excel sheets from data.rio.

The IPP publishes municipal indicators (IDEB, matrícula, etc.) in a single
sheet whose first column encodes the AP/RP/RA/bairro hierarchy as text
labels distinguishable by fixed regex patterns. This module exposes a
generic parser that walks those rows and yields one record per leaf
(bairro), tagged with its parent AP and RA.

Usage:
    from acec.transform.ideb_parser import parse_hierarchical_sheet
    rows = parse_hierarchical_sheet(
        path="data/raw/excel/9fd1a8cc...xlsx",
        sheet_name="ANOS_INICIAIS",
        score_cols={2007: 28, 2009: 29, ..., 2023: 36},
    )

Promoted from `rio-edu-lab/analysis/10_theil_ideb.py:43-65` (and copies
in scripts 15, 16, 17). Single canonical version lives here now.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

RE_TOTAL = re.compile(r"^total$", re.IGNORECASE)
RE_AP = re.compile(r"^área de planejamento\s+\d+", re.IGNORECASE)
RE_RP = re.compile(r"^região de planejamento\s+\d+\.\d+", re.IGNORECASE)
RE_RA = re.compile(r"^([IVX]+)\s+", re.IGNORECASE)


def _cell_num(v: Any) -> float | None:
    """Convert Excel cell to float; treat '...', '-', '..' as missing."""
    if v in (None, "", "...", "-", "..", "…"):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ("", "...", "-", "..", "…"):
        return None
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def parse_hierarchical_sheet(
    path: str | Path,
    sheet_name: str,
    score_cols: dict[Any, int],
) -> list[dict]:
    """Walk a hierarchical sheet and yield one dict per bairro leaf.

    Args:
      path: xls/xlsx file path.
      sheet_name: which sheet to read.
      score_cols: mapping of label → column index (e.g. {2007: 28, 2009: 29}).
                  Each label becomes a key in the output dict's `scores`.

    Returns:
      List of dicts shaped {ap, ra, bairro, scores: {label: value | None}}.
      Skips Total/AP/RP/footer rows; leaves under no current RA are dropped.
    """
    import xlrd

    book = xlrd.open_workbook(str(path))
    sh = book.sheet_by_name(sheet_name)

    out: list[dict] = []
    current_ap: str | None = None
    current_ra: str | None = None

    for r in range(sh.nrows):
        label = str(sh.cell_value(r, 0)).strip()
        if not label or label.lower().startswith(("fonte:", "nota:", "..", "a partir")):
            continue
        scores = {k: _cell_num(sh.cell_value(r, c)) for k, c in score_cols.items()}

        if RE_TOTAL.match(label):
            continue
        if RE_AP.match(label):
            current_ap = label
            continue
        if RE_RP.match(label):
            continue
        if RE_RA.match(label):
            current_ra = label
            continue
        if current_ra is None:
            continue
        out.append({
            "ap": current_ap,
            "ra": current_ra,
            "bairro": label,
            "scores": scores,
        })

    return out


__all__ = ["parse_hierarchical_sheet", "_cell_num"]
