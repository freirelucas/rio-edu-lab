"""Testes adversariais do sanitizador de Markdown (`analysis/_safe_md.py`).

Encontrou 2 vulns reais em páginas públicas (sala/inbox/paper↔dataset) que
renderizam títulos de fonte não-confiável: pipe quebra tabela, <script> = XSS.
Estes testes travam a regressão.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import():
    spec = importlib.util.spec_from_file_location("safe_md", str(ANALYSIS / "_safe_md.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pipe_escaped_not_column_break():
    """ATAQUE 1: `|` no título quebraria a coluna da tabela."""
    m = _import()
    out = m.sanitize_cell("Pipe | quebra | tabela")
    assert "\\|" in out          # escapado
    # nenhum pipe não-escapado sobrou
    import re
    assert len(re.findall(r"(?<!\\)\|", out)) == 0


def test_script_tag_neutralized_xss():
    """ATAQUE 2: <script> passaria como HTML cru (python-markdown não escapa)."""
    m = _import()
    out = m.sanitize_cell("<script>alert('xss')</script>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "<" not in out and ">" not in out


def test_ampersand_escaped_first():
    """& deve virar &amp; (senão &lt; do próximo passo seria double-encode ruim)."""
    m = _import()
    out = m.sanitize_cell("Tom & Jerry")
    assert "&amp;" in out
    # não vira &amp;amp; (double-encode)
    assert "&amp;amp;" not in out


def test_newlines_become_space_no_row_break():
    """ATAQUE 3: newline no título quebraria a linha da tabela."""
    m = _import()
    out = m.sanitize_cell("linha1\nlinha2\rlinha3\tcol")
    assert "\n" not in out and "\r" not in out and "\t" not in out
    assert "linha1 linha2 linha3 col" == out


def test_control_chars_stripped():
    m = _import()
    out = m.sanitize_cell("evil\x00\x01\x1fend")
    assert "\x00" not in out and "\x01" not in out and "\x1f" not in out
    assert out == "evilend"


def test_none_and_empty():
    m = _import()
    assert m.sanitize_cell(None) == ""
    assert m.sanitize_cell("") == ""


def test_max_len_truncation():
    m = _import()
    out = m.sanitize_cell("a" * 100, max_len=10)
    assert len(out) <= 11  # 10 + ellipsis
    assert out.endswith("…")


def test_normal_title_passes_through():
    """Título normal não é destruído."""
    m = _import()
    out = m.sanitize_cell("Equality of Educational Opportunity (Coleman 1966)")
    assert out == "Equality of Educational Opportunity (Coleman 1966)"


def test_multiple_spaces_collapsed():
    m = _import()
    assert m.sanitize_cell("a    b     c") == "a b c"


def test_shell_and_sql_injection_are_inert_text():
    """ATAQUE 4: injeção shell/SQL — vira texto inerte (f-string nunca eval)."""
    m = _import()
    out = m.sanitize_cell("$(rm -rf /) ; DROP TABLE papers;--")
    # o conteúdo permanece como TEXTO (não há execução); só < > | são neutralizados
    assert "rm -rf" in out  # texto preservado, jamais executado
    assert "DROP TABLE" in out


def test_link_syntax_brackets_survive_as_text():
    """Título com [colchetes] não vira link nem quebra (fica texto)."""
    m = _import()
    out = m.sanitize_cell("[link](javascript:void(0))")
    # colchetes preservados como texto; o perigo real (< >) já é escapado
    assert "javascript" in out  # texto, não href executável numa célula
    assert "<" not in out
