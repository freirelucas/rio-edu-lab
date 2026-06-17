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
