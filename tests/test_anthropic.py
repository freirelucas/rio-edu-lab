"""Tests pro `analysis/_anthropic.py` (v3 LLM extraction wrapper).

Cobre: TAXONOMY consistente, EXTRACT_TOOL schema (strict mode + closed enum),
_get_api_key env var, _build_user_message (truncation), dry_run path
(sem chamar API), graceful failure quando SDK ausente, parse de tool_use no
response (mockado).

NÃO requer `pip install anthropic` — testa graceful path + mocka client quando
necessário pra cobrir o caminho de sucesso.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))

import _anthropic as la  # noqa: E402

# ─── Constants + schema consistency ────────────────────────────────────────

def test_default_model_is_haiku_4_5():
    """Model id deve ser a alias correta (sem date suffix)."""
    assert la.DEFAULT_MODEL == "claude-haiku-4-5"


def test_taxonomy_has_10_categories():
    """Mantém em sync com data/requirements_taxonomy.yml."""
    assert len(la.TAXONOMY_CATEGORIES) == 10
    assert "performance-aggregated" in la.TAXONOMY_CATEGORIES
    assert "microdata-student" in la.TAXONOMY_CATEGORIES


def test_extract_tool_strict_mode():
    """strict=True + additionalProperties=False garante schema validation."""
    assert la.EXTRACT_TOOL["strict"] is True
    schema = la.EXTRACT_TOOL["input_schema"]
    assert schema["additionalProperties"] is False
    # Nested: dataset items também strict
    assert schema["properties"]["datasets"]["items"]["additionalProperties"] is False


def test_extract_tool_category_enum_matches_taxonomy():
    """O enum no tool schema é a única fonte de truth pro LLM."""
    enum = la.EXTRACT_TOOL["input_schema"]["properties"]["datasets"]["items"][
        "properties"
    ]["category_id"]["enum"]
    assert enum == la.TAXONOMY_CATEGORIES


def test_extract_tool_confidence_bounded():
    """confidence ∈ [0, 1]."""
    conf = la.EXTRACT_TOOL["input_schema"]["properties"]["datasets"]["items"][
        "properties"
    ]["confidence"]
    assert conf["minimum"] == 0
    assert conf["maximum"] == 1


def test_extract_tool_all_required_fields():
    """Top-level required: datasets, taxonomy_gap, gap_description."""
    required = la.EXTRACT_TOOL["input_schema"]["required"]
    assert set(required) == {"datasets", "taxonomy_gap", "gap_description"}


def test_system_prompt_mentions_all_categories():
    """Sanity: cada categoria deve aparecer no system prompt (com numbering)."""
    for cat in la.TAXONOMY_CATEGORIES:
        assert cat in la.SYSTEM_PROMPT


# ─── env vars ──────────────────────────────────────────────────────────────

def test_get_api_key_returns_none_when_unset():
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        assert la._get_api_key() is None


def test_get_api_key_returns_value_when_set():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
        assert la._get_api_key() == "sk-ant-test"


def test_get_api_key_strips_whitespace():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "  sk-ant-test  "}):
        assert la._get_api_key() == "sk-ant-test"


# ─── _build_user_message ───────────────────────────────────────────────────

def test_build_user_message_basic():
    msg = la._build_user_message("Theil decomposition", "We use IDEB data by bairro.")
    assert "Theil decomposition" in msg
    assert "IDEB data by bairro" in msg
    assert "**Paper title:**" in msg
    assert "**Abstract:**" in msg


def test_build_user_message_truncates_long_abstract():
    """Abstracts > 2000 chars são truncados com ellipsis (cost guard)."""
    long_abs = "X" * 3000
    msg = la._build_user_message("Title", long_abs)
    assert len(msg) < 3500  # truncated
    assert "…" in msg


def test_build_user_message_handles_missing_fields():
    """Title/abstract vazios — não crasha, marca como missing."""
    msg = la._build_user_message("", "")
    assert "missing" in msg
    assert "no abstract" in msg


# ─── dry_run path ─────────────────────────────────────────────────────────

def test_dry_run_returns_prompt_without_calling_api():
    """dry_run=True NÃO chama API — retorna prompt + tool schema."""
    # Mesmo sem SDK instalado, dry_run deve funcionar
    result = la.extract_requirements(
        title="Test paper",
        abstract="Test abstract about IDEB.",
        dry_run=True,
    )
    assert result["_dry_run"] is True
    assert "Test paper" in result["user_message"]
    assert "Test abstract about IDEB" in result["user_message"]
    assert result["tool"]["name"] == "extract_paper_requirements"
    assert "10 closed categories" in result["system_prompt"]


# ─── SDK ausente — falha graceful ──────────────────────────────────────────

def test_extract_raises_when_anthropic_not_installed():
    """Se anthropic não instalado, RuntimeError com mensagem clara."""
    with patch.object(la, "HAS_ANTHROPIC", False):
        with pytest.raises(RuntimeError, match="anthropic package required"):
            la.extract_requirements("t", "a", dry_run=False)


def test_extract_dry_run_works_without_sdk():
    """dry_run NÃO precisa do SDK — só renderiza prompt."""
    with patch.object(la, "HAS_ANTHROPIC", False):
        result = la.extract_requirements("t", "a", dry_run=True)
        assert result["_dry_run"] is True


def test_extract_raises_when_api_key_missing():
    """Sem ANTHROPIC_API_KEY, RuntimeError pré-call (não vaza pro SDK)."""
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    with patch.dict(os.environ, env, clear=True):
        with patch.object(la, "HAS_ANTHROPIC", True):
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                la.extract_requirements("t", "a", dry_run=False)


# ─── tool_use response parsing (mocked client) ─────────────────────────────

def _make_mock_response(
    tool_input: dict,
    model: str = "claude-haiku-4-5",
    stop_reason: str = "tool_use",
    input_tokens: int = 1200,
    output_tokens: int = 180,
    cache_read: int = 0,
    cache_creation: int = 0,
):
    """Simula response.content com block.type='tool_use' + block.input."""
    tool_block = SimpleNamespace(
        type="tool_use",
        name="extract_paper_requirements",
        input=tool_input,
    )
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read,
        cache_creation_input_tokens=cache_creation,
    )
    return SimpleNamespace(
        content=[tool_block],
        model=model,
        stop_reason=stop_reason,
        usage=usage,
    )


def test_extract_parses_tool_use_response():
    """Happy path: mock client retorna tool_use → wrapper extrai estruturado."""
    expected_input = {
        "datasets": [
            {
                "category_id": "performance-aggregated",
                "confidence": 0.9,
                "evidence_excerpt": "IDEB scores by bairro",
            }
        ],
        "taxonomy_gap": False,
        "gap_description": None,
    }
    mock_client = MagicMock()
    mock_client.with_options.return_value.messages.create.return_value = (
        _make_mock_response(expected_input)
    )
    with patch.object(la, "HAS_ANTHROPIC", True), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch.object(la, "anthropic", MagicMock(Anthropic=lambda **k: mock_client)):
        result = la.extract_requirements("t", "abstract", verbose=False)

    assert result is not None
    assert result["datasets"][0]["category_id"] == "performance-aggregated"
    assert result["taxonomy_gap"] is False
    assert result["_model"] == "claude-haiku-4-5"
    assert result["_stop_reason"] == "tool_use"
    assert result["_called_at"].endswith("Z")
    assert result["_usage"]["input_tokens"] == 1200
    assert result["_usage"]["output_tokens"] == 180
    assert result["_usage"]["cache_read_input_tokens"] == 0


def test_extract_returns_none_when_no_tool_use_block():
    """Se response não tem tool_use (ex.: refusal), retorna None com warn."""
    text_block = SimpleNamespace(type="text", text="I cannot classify this.")
    fake_response = SimpleNamespace(
        content=[text_block],
        model="claude-haiku-4-5",
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=100, output_tokens=20,
                              cache_read_input_tokens=0, cache_creation_input_tokens=0),
    )
    mock_client = MagicMock()
    mock_client.with_options.return_value.messages.create.return_value = fake_response
    with patch.object(la, "HAS_ANTHROPIC", True), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch.object(la, "anthropic", MagicMock(Anthropic=lambda **k: mock_client)):
        result = la.extract_requirements("t", "a", verbose=False)
    assert result is None


def test_extract_captures_cache_hits_in_usage():
    """Se cache adere (input ≥ 4096 tok no futuro), reportamos no _usage."""
    mock_client = MagicMock()
    mock_client.with_options.return_value.messages.create.return_value = (
        _make_mock_response(
            {"datasets": [], "taxonomy_gap": True, "gap_description": "voting data"},
            cache_read=950,
            cache_creation=0,
        )
    )
    with patch.object(la, "HAS_ANTHROPIC", True), \
         patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}), \
         patch.object(la, "anthropic", MagicMock(Anthropic=lambda **k: mock_client)):
        result = la.extract_requirements("t", "a", verbose=False)
    assert result["_usage"]["cache_read_input_tokens"] == 950
    assert result["taxonomy_gap"] is True
    assert result["gap_description"] == "voting data"
