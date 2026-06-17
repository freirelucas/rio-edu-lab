"""Tests pro `analysis/49_codebook_backfill.py` (LLM-assisted code_book backfill).

Cobre helpers puros (priority_pool, _build_user_message, cache),
extract_codebook em dry_run (sem SDK), e mock da call quando SDK presente.

NÃO chama API real. Tests rodam em CI sem ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_49():
    spec = importlib.util.spec_from_file_location("cb_backfill", str(ANALYSIS / "49_codebook_backfill.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── priority_pool ────────────────────────────────────────────────────────


def test_priority_pool_filters_to_edu_tags_without_codebook():
    cb = _import_49()
    items = [
        {"id": "a", "tags": ["Educação"], "numViews": 100},                    # in pool
        {"id": "b", "tags": ["Saúde"], "numViews": 999},                       # not edu
        {"id": "c", "tags": ["Educação"], "code_book": {"x": 1}, "numViews": 200},  # has cb
        {"id": "d", "tags": ["Ensino"], "numViews": 50},                       # in pool
        {"id": "e", "tags": ["Escolaridade da população"], "numViews": 1000},  # in pool
    ]
    pool = cb.priority_pool(items)
    # Ordered by numViews desc: e(1000), a(100), d(50)
    assert pool == [4, 0, 3]


def test_priority_pool_empty_when_all_have_codebook():
    cb = _import_49()
    items = [
        {"id": "a", "tags": ["Educação"], "code_book": {"domain": "x"}, "numViews": 100},
        {"id": "b", "tags": ["Educação"], "code_book": {"x": 1}, "numViews": 50},
    ]
    assert cb.priority_pool(items) == []


def test_priority_pool_treats_empty_codebook_as_unenriched():
    """code_book: {} é tratado como 'precisa backfill' (truthy check em it.get(\"code_book\"))."""
    cb = _import_49()
    items = [
        {"id": "a", "tags": ["Educação"], "code_book": {}, "numViews": 100},  # empty → in pool
        {"id": "b", "tags": ["Educação"], "code_book": {"domain": "x"}, "numViews": 50},  # populated → skip
    ]
    assert cb.priority_pool(items) == [0]


def test_priority_pool_handles_missing_tags():
    cb = _import_49()
    items = [
        {"id": "a", "numViews": 100},                  # no tags key
        {"id": "b", "tags": None, "numViews": 50},     # tags=None
        {"id": "c", "tags": [], "numViews": 25},       # empty tags
        {"id": "d", "tags": ["Educação"], "numViews": 10},  # only one in pool
    ]
    assert cb.priority_pool(items) == [3]


# ─── _build_user_message ──────────────────────────────────────────────────


def test_build_user_message_includes_core_fields():
    cb = _import_49()
    item = {
        "title": "IDEB por bairro",
        "type": "Microsoft Excel",
        "tags": ["Educação", "IPP"],
        "snippet": "Indicador IDEB calculado por bairro 2007-2023",
    }
    msg = cb._build_user_message(item)
    assert "IDEB por bairro" in msg
    assert "Microsoft Excel" in msg
    assert "Educação" in msg
    assert "Indicador IDEB" in msg


def test_build_user_message_handles_missing_fields():
    cb = _import_49()
    msg = cb._build_user_message({"id": "x"})
    assert "(no title)" in msg
    assert "(no type)" in msg
    assert "(none)" in msg  # tags fallback


def test_build_user_message_truncates_long_snippet():
    cb = _import_49()
    item = {"title": "X", "snippet": "a" * 3000}
    msg = cb._build_user_message(item)
    # cap = 1500 + ellipsis
    assert "…" in msg
    assert len(msg) < 2500  # bounded


def test_build_user_message_includes_url_when_present():
    cb = _import_49()
    item = {"title": "X", "url": "https://example.com/api"}
    msg = cb._build_user_message(item)
    assert "https://example.com/api" in msg


# ─── cache get/set ────────────────────────────────────────────────────────


def test_cache_roundtrip(tmp_path, monkeypatch):
    cb = _import_49()
    monkeypatch.setattr(cb, "CACHE_DIR", tmp_path / "anthropic")
    payload = {"code_book": {"domain": "educacao-basica"}, "item_title": "T"}
    cb._cache_set("item_id_1", payload)
    got = cb._cache_get("item_id_1")
    assert got == payload


def test_cache_miss_returns_none(tmp_path, monkeypatch):
    cb = _import_49()
    monkeypatch.setattr(cb, "CACHE_DIR", tmp_path / "anthropic")
    assert cb._cache_get("never_set") is None


def test_cache_corrupt_returns_none(tmp_path, monkeypatch):
    cb = _import_49()
    monkeypatch.setattr(cb, "CACHE_DIR", tmp_path / "anthropic")
    p = cb._cache_path("x")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("not json{")
    assert cb._cache_get("x") is None


# ─── extract_codebook ─────────────────────────────────────────────────────


def test_extract_codebook_dry_run_no_sdk():
    """Dry-run não requer SDK ou API key — só renderiza prompt."""
    cb = _import_49()
    result = cb.extract_codebook(
        {"id": "foo", "title": "IDEB por bairro", "type": "Excel"},
        dry_run=True,
    )
    assert result["_dry_run"] is True
    assert "IDEB por bairro" in result["user_message"]
    assert result["item_id"] == "foo"


def test_extract_codebook_without_sdk_raises(monkeypatch):
    cb = _import_49()
    monkeypatch.setattr(cb, "HAS_ANTHROPIC", False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    try:
        cb.extract_codebook({"id": "x", "title": "X"}, dry_run=False)
        raise AssertionError("should have raised")
    except RuntimeError as e:
        assert "anthropic package required" in str(e)


def test_extract_codebook_without_key_raises(monkeypatch):
    cb = _import_49()
    monkeypatch.setattr(cb, "HAS_ANTHROPIC", True)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        cb.extract_codebook({"id": "x", "title": "X"}, dry_run=False)
        raise AssertionError("should have raised")
    except RuntimeError as e:
        assert "ANTHROPIC_API_KEY" in str(e)


def test_extract_codebook_parses_tool_use_response(monkeypatch):
    """Mock do client SDK retornando um tool_use block bem-formado."""
    cb = _import_49()
    monkeypatch.setattr(cb, "HAS_ANTHROPIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "extract_data_item_codebook"
    mock_block.input = {
        "domain": "educacao-basica",
        "unit_of_observation": "bairro",
        "spatial_granularity": "bairro",
        "temporal_coverage_parsed": {"start_year": 2007, "end_year": 2023, "frequency": "bienal"},
        "api_capability": "static_file",
        "key_variables": ["ideb", "ano", "bairro"],
        "confidence": 0.92,
    }
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.model = "claude-haiku-4-5"
    mock_response.stop_reason = "tool_use"

    mock_client = MagicMock()
    mock_client.with_options.return_value.messages.create.return_value = mock_response

    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_anthropic.AuthenticationError = type("AE", (Exception,), {})
    monkeypatch.setattr(cb, "anthropic", mock_anthropic)

    result = cb.extract_codebook({"id": "test_id", "title": "IDEB", "type": "Excel"})

    assert result["domain"] == "educacao-basica"
    assert result["confidence"] == 0.92
    assert result["temporal_coverage_parsed"]["start_year"] == 2007
    assert result["_llm_model"] == "claude-haiku-4-5"
    assert "_llm_called_at" in result


def test_extract_codebook_returns_none_on_no_tool_block(monkeypatch):
    cb = _import_49()
    monkeypatch.setattr(cb, "HAS_ANTHROPIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    # Response sem tool_use block
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_response = MagicMock()
    mock_response.content = [mock_text_block]

    mock_client = MagicMock()
    mock_client.with_options.return_value.messages.create.return_value = mock_response

    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_anthropic.AuthenticationError = type("AE", (Exception,), {})
    monkeypatch.setattr(cb, "anthropic", mock_anthropic)

    result = cb.extract_codebook({"id": "x", "title": "X"})
    assert result is None


def test_extract_codebook_returns_none_on_exception(monkeypatch):
    """SDK API status errors viram None (não propaga; permite skip)."""
    cb = _import_49()
    monkeypatch.setattr(cb, "HAS_ANTHROPIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-fake")

    mock_client = MagicMock()
    mock_client.with_options.return_value.messages.create.side_effect = ValueError("boom")

    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_anthropic.AuthenticationError = type("AE", (Exception,), {})
    monkeypatch.setattr(cb, "anthropic", mock_anthropic)

    result = cb.extract_codebook({"id": "x", "title": "X"}, verbose=False)
    assert result is None


# ─── schema invariants ───────────────────────────────────────────────────


def test_tool_schema_has_required_fields():
    cb = _import_49()
    schema = cb.EXTRACT_CODEBOOK_TOOL["input_schema"]
    expected = {
        "domain", "unit_of_observation", "spatial_granularity",
        "temporal_coverage_parsed", "api_capability", "key_variables",
        "confidence",
    }
    assert set(schema["required"]) == expected
    assert schema["additionalProperties"] is False  # strict


def test_tool_schema_temporal_nested_strict():
    cb = _import_49()
    schema = cb.EXTRACT_CODEBOOK_TOOL["input_schema"]
    temporal = schema["properties"]["temporal_coverage_parsed"]
    # nested obj é strict + tem os 3 fields
    obj_schema = temporal  # since it's union [object, null]
    assert obj_schema["additionalProperties"] is False
    assert set(obj_schema["required"]) == {"start_year", "end_year", "frequency"}


def test_edu_tags_includes_canonical_strings():
    cb = _import_49()
    assert "Educação" in cb.EDU_TAGS
    assert "Educação Básica" in cb.EDU_TAGS
    assert "Escolaridade da população" in cb.EDU_TAGS


# ─── v0.17 resource bargain integration ───────────────────────────────────


def test_extract_codebook_respects_budget_cap(monkeypatch):
    """49 chama Anthropic SDK direto, mas plumbed pra check budget pre-call.
    MAX_TOKENS_PER_PAPER=10 deve disparar LLMBudgetExceeded."""
    cb = _import_49()
    # Force budget cap super-baixo
    monkeypatch.setenv("MAX_TOKENS_PER_PAPER", "10")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.setattr(cb, "HAS_ANTHROPIC", True)

    # Reset budget pra estado limpo
    from _llm import LLMBudgetExceeded, get_budget_tracker
    get_budget_tracker().reset()

    item = {"id": "x", "title": "Y" * 200, "type": "Excel", "snippet": "long snippet" * 30}
    try:
        cb.extract_codebook(item)
        raise AssertionError("should have raised LLMBudgetExceeded")
    except LLMBudgetExceeded as e:
        assert "MAX_TOKENS_PER_PAPER" in str(e)


def test_extract_codebook_records_cost_on_success(monkeypatch):
    """Após chamada bem-sucedida, cumulative cost cresce."""
    cb = _import_49()
    monkeypatch.setattr(cb, "HAS_ANTHROPIC", True)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.delenv("MAX_TOKENS_PER_PAPER", raising=False)
    monkeypatch.delenv("MAX_LLM_BUDGET_USD", raising=False)

    from _llm import get_budget_tracker
    get_budget_tracker().reset()
    initial_cost = get_budget_tracker().cumulative_cost_usd
    initial_calls = get_budget_tracker().n_calls

    # Mock Anthropic response
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "extract_data_item_codebook"
    mock_block.input = {
        "domain": "educacao-basica", "unit_of_observation": "escola",
        "spatial_granularity": "ponto", "temporal_coverage_parsed": None,
        "api_capability": "static_file", "key_variables": ["ideb"],
        "confidence": 0.8,
    }
    mock_usage = MagicMock()
    mock_usage.input_tokens = 100_000
    mock_usage.output_tokens = 10_000
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.model = "claude-haiku-4-5"
    mock_response.usage = mock_usage

    mock_client = MagicMock()
    mock_client.with_options.return_value.messages.create.return_value = mock_response
    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_anthropic.AuthenticationError = type("AE", (Exception,), {})
    monkeypatch.setattr(cb, "anthropic", mock_anthropic)

    item = {"id": "x", "title": "Y", "type": "Excel"}
    result = cb.extract_codebook(item, verbose=False)
    assert result is not None

    # Custo registrado: 100K × $1/M + 10K × $5/M = $0.10 + $0.05 = $0.15
    assert get_budget_tracker().n_calls == initial_calls + 1
    expected_cost = 100_000 * 1.0e-6 + 10_000 * 5.0e-6
    assert abs(get_budget_tracker().cumulative_cost_usd - (initial_cost + expected_cost)) < 1e-9
