"""Append a 'Continue lendo' footer to each docs/reports/*.md.

Idempotent: if the marker `<!-- continue-lendo -->` is already present,
the existing footer is replaced (so the script can be re-run after
restructuring nav).

Each footer is tailored: links forward to the natural next report (or
to the relevant product page for technical reports) plus 1-2 jumps to
the public-facing surfaces (papers / mapa / sobre).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "docs" / "reports"
MARKER = "<!-- continue-lendo -->"

# Per-report footer content. Keys must match filenames in docs/reports/.
FOOTERS: dict[str, str] = {
    "01_manifest_eda.md": """
- [02 — Probe da API](02_ingestion_probe.md)
- [Papers](../papers/index.md)
- [Reproduzir](../reproduzir.md)
""",
    "02_ingestion_probe.md": """
- [03 — Catálogo dos Excels](03_excel_catalog.md)
- [API do data.rio](../data-rio-api.md)
- [Papers](../papers/index.md)
""",
    "03_excel_catalog.md": """
- [04 — Auditoria do shortlist](04_shortlist_audit.md)
- [Sobre — glossário](../sobre.md#glossario)
""",
    "04_shortlist_audit.md": """
- [06 — Theil base](06_theil_ideb.md)
- [HEX-EDU (página de produto)](../produtos/hex_edu.md)
""",
    "05_pdf_corpus.md": """
- [Papers](../papers/index.md)
- [Reproduzir](../reproduzir.md)
""",
    "06_theil_ideb.md": """
- [HEX-EDU (página de produto)](../produtos/hex_edu.md)
- [06b — Theil ponderado](06b_theil_weighted.md)
- [07 — Mapa estático](07_hex_edu_static.md)
- [10 — Replicação metodológica](10_method_replication.md)
""",
    "06b_theil_weighted.md": """
- [HEX-EDU (página de produto)](../produtos/hex_edu.md)
- [09 — IDEB séries finais (9º)](09_anos_finais.md)
""",
    "07_hex_edu_static.md": """
- [08 — Mapa interativo (técnico)](08_hex_edu_interactive.md)
- [Mapa interativo (página pública)](../mapa.md)
- [HEX-EDU (página de produto)](../produtos/hex_edu.md)
""",
    "08_hex_edu_interactive.md": """
- [Mapa (página pública)](../mapa.md)
- [HEX-EDU (página de produto)](../produtos/hex_edu.md)
- [Papers](../papers/index.md)
""",
    "09_anos_finais.md": """
- [12 — FUN-Rio (trajetórias)](12_fun_rio.md)
- [HEX-EDU (página de produto)](../produtos/hex_edu.md)
""",
    "10_method_replication.md": """
- [HEX-EDU (página de produto)](../produtos/hex_edu.md)
- [Sobre — glossário](../sobre.md#glossario)
""",
    "11_thesha_rio.md": """
- [HEX-EDU (produto canônico — Theil 3-níveis vive aqui como robustez)](../produtos/hex_edu.md)
- [HEX-EDU (2-níveis)](../produtos/hex_edu.md)
- [Bairros prioritários](../bairros-prioritarios.md)
""",
    "12_fun_rio.md": """
- [Bairros prioritários (cruzamento com PM-12)](../bairros-prioritarios.md)
- [09 — IDEB séries finais (9º)](09_anos_finais.md)
- [HEX-EDU (produto canônico)](../produtos/hex_edu.md)
""",
    "13_pm_12.md": """
- [Bairros prioritários (cruzamento SAMI + Δ FUN)](../bairros-prioritarios.md)
- [Trajetórias 5º→9º (Relatório 12)](12_fun_rio.md)
- [HEX-EDU (produto canônico)](../produtos/hex_edu.md)
""",
}

FOOTER_TEMPLATE = """{marker}

## Continue lendo

!!! tip ""
{links}
"""


def render_footer(filename: str) -> str | None:
    body = FOOTERS.get(filename)
    if not body:
        return None
    indented = "\n".join(("    " + line if line.strip() else line) for line in body.strip("\n").splitlines())
    return FOOTER_TEMPLATE.format(marker=MARKER, links=indented)


MARKER_RE = re.compile(re.escape(MARKER) + r".*\Z", re.DOTALL)


def main() -> int:
    n_modified = 0
    for path in sorted(REPORTS_DIR.glob("*.md")):
        footer = render_footer(path.name)
        if not footer:
            print(f"  skip {path.name}: no footer defined")
            continue
        text = path.read_text(encoding="utf-8")
        if MARKER in text:
            new_text = MARKER_RE.sub(footer.strip(), text).rstrip() + "\n"
        else:
            new_text = text.rstrip() + "\n\n" + footer
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            n_modified += 1
            print(f"  wrote footer for {path.name}")
    print(f"\nupdated {n_modified} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
