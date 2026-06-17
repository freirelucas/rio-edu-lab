"""Tests pro dispatcher `analysis/_llm.py` (provider-agnostic LLM routing).

Valida:
- LLM_PROVIDER env routing (anthropic default, rio opt-in)
- Provider invalid raises clear error
- Dispatch chama adapter correto
- Output shape consistency (_provider sempre presente)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_llm():
    spec = importlib.util.spec_from_file_location("llm_dispatcher", str(ANALYSIS / "_llm.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── get_provider ─────────────────────────────────────────────────────────


def test_provider_defaults_to_anthropic(monkeypatch):
    llm = _import_llm()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert llm.get_provider() == "anthropic"


def test_provider_reads_env(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("LLM_PROVIDER", "rio")
    assert llm.get_provider() == "rio"


def test_provider_case_insensitive(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("LLM_PROVIDER", "RIO")
    assert llm.get_provider() == "rio"


def test_provider_strips_whitespace(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("LLM_PROVIDER", "  anthropic\n")
    assert llm.get_provider() == "anthropic"


def test_provider_invalid_raises(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("LLM_PROVIDER", "openai")  # not supported
    try:
        llm.get_provider()
        raise AssertionError("should have raised")
    except ValueError as e:
        assert "openai" in str(e)
        assert "anthropic" in str(e)  # mensagem lista as valid options


def test_supported_providers_set():
    llm = _import_llm()
    assert "anthropic" in llm.SUPPORTED_PROVIDERS
    assert "rio" in llm.SUPPORTED_PROVIDERS
    assert len(llm.SUPPORTED_PROVIDERS) == 2  # bound — manter pequeno até v0.16


# ─── extract_requirements dispatch ────────────────────────────────────────


def test_dispatch_to_anthropic_when_default(monkeypatch):
    llm = _import_llm()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with patch("_anthropic.extract_requirements") as mock_ant:
        mock_ant.return_value = {"datasets": [], "_provider": "anthropic"}
        result = llm.extract_requirements("X", "Y")
    mock_ant.assert_called_once()
    assert result["_provider"] == "anthropic"


def test_dispatch_to_rio_when_env_set(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("LLM_PROVIDER", "rio")
    with patch("_rio.extract_requirements") as mock_rio:
        mock_rio.return_value = {"datasets": [], "_provider": "rio"}
        result = llm.extract_requirements("X", "Y")
    mock_rio.assert_called_once()
    assert result["_provider"] == "rio"


def test_dispatch_explicit_provider_override(monkeypatch):
    """Argument `provider=...` overrides env (útil pra tests/sample)."""
    llm = _import_llm()
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    with patch("_rio.extract_requirements") as mock_rio:
        mock_rio.return_value = {"datasets": [], "_provider": "rio"}
        result = llm.extract_requirements("X", "Y", provider="rio")
    mock_rio.assert_called_once()
    assert result["_provider"] == "rio"


def test_dispatch_passes_through_dry_run(monkeypatch):
    llm = _import_llm()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with patch("_anthropic.extract_requirements") as mock_ant:
        mock_ant.return_value = {"_dry_run": True}
        llm.extract_requirements("X", "Y", dry_run=True)
    _, kwargs = mock_ant.call_args
    assert kwargs["dry_run"] is True


def test_dispatch_passes_through_model_override(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("LLM_PROVIDER", "rio")
    with patch("_rio.extract_requirements") as mock_rio:
        mock_rio.return_value = {"datasets": []}
        llm.extract_requirements("X", "Y", model="rio-3.5-int4")
    _, kwargs = mock_rio.call_args
    assert kwargs["model"] == "rio-3.5-int4"


def test_dispatch_injects_provider_tag_in_anthropic_response(monkeypatch):
    """Anthropic backend não preenche _provider — dispatcher injeta."""
    llm = _import_llm()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with patch("_anthropic.extract_requirements") as mock_ant:
        mock_ant.return_value = {"datasets": []}  # sem _provider
        result = llm.extract_requirements("X", "Y")
    assert result["_provider"] == "anthropic"


def test_dispatch_handles_none_response(monkeypatch):
    """Adapter retorna None em erro → dispatcher repassa sem crash."""
    llm = _import_llm()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    with patch("_anthropic.extract_requirements", return_value=None):
        result = llm.extract_requirements("X", "Y")
    assert result is None


# ─── Resource bargain (VSM S3 — MAX_TOKENS_PER_PAPER + MAX_LLM_BUDGET_USD) ─


def test_budget_tracker_pricing_constants():
    llm = _import_llm()
    assert llm.ANTHROPIC_PRICING["input_per_1m"] == 1.0
    assert llm.ANTHROPIC_PRICING["output_per_1m"] == 5.0
    assert llm.RIO_PRICING["input_per_1m"] == 0.0


def test_budget_tracker_singleton():
    llm = _import_llm()
    b1 = llm.get_budget_tracker()
    b2 = llm.get_budget_tracker()
    assert b1 is b2


def test_budget_no_cap_by_default(monkeypatch):
    llm = _import_llm()
    monkeypatch.delenv("MAX_TOKENS_PER_PAPER", raising=False)
    monkeypatch.delenv("MAX_LLM_BUDGET_USD", raising=False)
    b = llm.get_budget_tracker()
    assert b.max_tokens_per_paper is None
    assert b.max_budget_usd is None
    # check_pre_call não levanta sem caps
    b.check_pre_call(estimated_input_tokens=1_000_000)


def test_budget_max_tokens_enforced(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("MAX_TOKENS_PER_PAPER", "1000")
    b = llm.get_budget_tracker()
    try:
        b.check_pre_call(estimated_input_tokens=2000)
        raise AssertionError("should have raised")
    except llm.LLMBudgetExceeded as e:
        assert "MAX_TOKENS_PER_PAPER" in str(e)


def test_budget_max_tokens_zero_means_unlimited(monkeypatch):
    """0 ou strings inválidas → unlimited (default behavior)."""
    llm = _import_llm()
    monkeypatch.setenv("MAX_TOKENS_PER_PAPER", "0")
    b = llm.get_budget_tracker()
    assert b.max_tokens_per_paper is None


def test_budget_record_anthropic_cost(monkeypatch):
    llm = _import_llm()
    b = llm.get_budget_tracker()
    b.reset()
    # 1M input + 1M output do Haiku 4.5 = $1 + $5 = $6
    cost = b.record_post_call({"input_tokens": 1_000_000, "output_tokens": 1_000_000}, "anthropic")
    assert cost == 6.0
    assert b.cumulative_cost_usd == 6.0
    assert b.n_calls == 1


def test_budget_record_rio_zero_cost(monkeypatch):
    llm = _import_llm()
    b = llm.get_budget_tracker()
    b.reset()
    cost = b.record_post_call({"input_tokens": 1_000_000, "output_tokens": 1_000_000}, "rio")
    assert cost == 0.0
    assert b.cumulative_cost_usd == 0.0


def test_budget_cumulative_cost_caps(monkeypatch):
    llm = _import_llm()
    monkeypatch.setenv("MAX_LLM_BUDGET_USD", "0.10")
    b = llm.get_budget_tracker()
    b.reset()
    # Push cost past cap
    b.record_post_call({"input_tokens": 100_000, "output_tokens": 0}, "anthropic")  # $0.10
    # Próximo check_pre_call deve falhar
    try:
        b.check_pre_call(estimated_input_tokens=100)
        raise AssertionError("should have raised")
    except llm.LLMBudgetExceeded as e:
        assert "MAX_LLM_BUDGET_USD" in str(e)


def test_budget_reset():
    llm = _import_llm()
    b = llm.get_budget_tracker()
    b.record_post_call({"input_tokens": 100_000, "output_tokens": 0}, "anthropic")
    assert b.cumulative_cost_usd > 0
    b.reset()
    assert b.cumulative_cost_usd == 0.0
    assert b.n_calls == 0


def test_dispatch_integrates_cost_tracking_for_anthropic(monkeypatch):
    """Dispatcher record_post_call após Anthropic; injeta _cost_usd no result."""
    llm = _import_llm()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("MAX_TOKENS_PER_PAPER", raising=False)
    monkeypatch.delenv("MAX_LLM_BUDGET_USD", raising=False)
    llm.get_budget_tracker().reset()
    with patch("_anthropic.extract_requirements") as mock_ant:
        mock_ant.return_value = {
            "datasets": [],
            "_usage": {"input_tokens": 1_000_000, "output_tokens": 200_000},
        }
        result = llm.extract_requirements("X", "Y")
    assert "_cost_usd" in result
    # 1M × $1 + 200K × $5 = $1.00 + $1.00 = $2.00
    assert result["_cost_usd"] == 2.0
    assert llm.get_budget_tracker().n_calls == 1


def test_dispatch_skips_budget_in_dry_run(monkeypatch):
    """dry_run não toca budget (zero custo real)."""
    llm = _import_llm()
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    llm.get_budget_tracker().reset()
    with patch("_anthropic.extract_requirements") as mock_ant:
        mock_ant.return_value = {"_dry_run": True, "_provider": "anthropic"}
        result = llm.extract_requirements("X", "Y", dry_run=True)
    assert "_cost_usd" not in result
    assert llm.get_budget_tracker().n_calls == 0
