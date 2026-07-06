"""Sanitização de texto não-confiável pra células de tabela Markdown.

Contexto de segurança: as páginas públicas do site (sala, inbox, paper↔dataset)
renderizam TÍTULOS de papers vindos de fonte NÃO-CONFIÁVEL (OpenAlex, comunidade
via issues). python-markdown repassa HTML cru por padrão → um título com
`<script>` viraria XSS; um título com `|` quebraria a estrutura da tabela.

Descoberto por teste adversarial (tests/test_corporation_safety.py +
test_safe_md.py). Defense-in-depth: sanitiza antes de interpolar.

Uso:
    from _safe_md import sanitize_cell
    row = f"| {sanitize_cell(untrusted_title)} |"
"""

from __future__ import annotations


def sanitize_cell(text: str | None, max_len: int | None = None) -> str:
    """Torna `text` seguro pra uma célula de tabela Markdown.

    - `|` → `\\|` (pipe escapado, renderiza literal, não quebra coluna)
    - `<` / `>` → `&lt;` / `&gt;` (neutraliza HTML cru / <script> / XSS)
    - newline / CR / tab → espaço (não quebra a linha da tabela)
    - controle (< 0x20, exceto já tratados) → removido
    - opcional truncamento em max_len (com reticências)

    Retorna string vazia pra None.
    """
    if not text:
        return ""
    s = str(text)
    # Ordem importa: escapar < > ANTES de qualquer coisa que insira < >.
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = s.replace("|", "\\|")
    # Quebras de linha e tabs viram espaço (senão quebram a row).
    for ch in ("\n", "\r", "\t"):
        s = s.replace(ch, " ")
    # Remove outros caracteres de controle (0x00-0x1F remanescentes).
    s = "".join(c for c in s if ord(c) >= 0x20)
    # Colapsa espaços múltiplos.
    s = " ".join(s.split())
    if max_len is not None and len(s) > max_len:
        s = s[:max_len].rstrip() + "…"
    return s


__all__ = ["sanitize_cell"]
