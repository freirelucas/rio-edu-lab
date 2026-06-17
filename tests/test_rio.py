"""Tests pro adapter `analysis/_rio.py` (Rio-3.5-Open-397B via OpenAI-compatible).

Mocks urlopen pra evitar HTTP real. Valida conversão tool format Anthropic→OpenAI,
parse de tool_calls do response, dry_run path (sem network), e env var routing.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_rio():
    spec = importlib.util.spec_from_file_location("rio_adapter", str(ANALYSIS / "_rio.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── env-driven config ────────────────────────────────────────────────────


def test_default_api_base_is_ollama(monkeypatch):
    rio = _import_rio()
    monkeypatch.delenv("RIO_API_BASE", raising=False)
    assert rio._get_api_base() == "http://localhost:11434/v1"


def test_custom_api_base_from_env(monkeypatch):
    rio = _import_rio()
    monkeypatch.setenv("RIO_API_BASE", "https://endpoint.huggingface.cloud/v1/")
    assert rio._get_api_base() == "https://endpoint.huggingface.cloud/v1"  # trailing / stripped


def test_default_api_key_is_ollama_placeholder(monkeypatch):
    rio = _import_rio()
    monkeypatch.delenv("RIO_API_KEY", raising=False)
    assert rio._get_api_key() == "ollama"


def test_custom_api_key_from_env(monkeypatch):
    rio = _import_rio()
    monkeypatch.setenv("RIO_API_KEY", "  hf_abc123\n")
    assert rio._get_api_key() == "hf_abc123"  # stripped


def test_default_model(monkeypatch):
    rio = _import_rio()
    monkeypatch.delenv("RIO_MODEL", raising=False)
    assert rio._get_model() == "rio-3.5-open-397b"


def test_custom_model_from_env(monkeypatch):
    rio = _import_rio()
    monkeypatch.setenv("RIO_MODEL", "rio-3.5-int4")
    assert rio._get_model() == "rio-3.5-int4"


# ─── tool format conversion ───────────────────────────────────────────────


def test_convert_anthropic_tool_to_openai_format():
    rio = _import_rio()
    anthropic_tool = {
        "name": "extract_paper_requirements",
        "description": "Classify paper data needs",
        "input_schema": {"type": "object", "properties": {"x": {"type": "string"}}},
    }
    openai_tool = rio._convert_tool_to_openai(anthropic_tool)
    assert openai_tool["type"] == "function"
    assert openai_tool["function"]["name"] == "extract_paper_requirements"
    assert openai_tool["function"]["description"] == "Classify paper data needs"
    assert openai_tool["function"]["parameters"] == anthropic_tool["input_schema"]


def test_convert_tool_handles_missing_description():
    rio = _import_rio()
    tool = {"name": "x", "input_schema": {"type": "object"}}
    converted = rio._convert_tool_to_openai(tool)
    assert converted["function"]["description"] == ""


# ─── _build_user_message ──────────────────────────────────────────────────


def test_build_user_message_includes_title_and_abstract():
    rio = _import_rio()
    msg = rio._build_user_message("Title X", "Abstract Y")
    assert "Title X" in msg
    assert "Abstract Y" in msg
    assert "Paper title" in msg


def test_build_user_message_truncates_long_abstract():
    rio = _import_rio()
    msg = rio._build_user_message("T", "a" * 3000)
    assert "…" in msg
    assert len(msg) < 2500


def test_build_user_message_handles_empty():
    rio = _import_rio()
    msg = rio._build_user_message("", "")
    assert "(missing)" in msg
    assert "(no abstract available)" in msg


# ─── extract_requirements: dry-run path (no network) ──────────────────────


def test_extract_dry_run_no_network():
    """dry_run não chama HTTP — só renderiza prompt pra inspeção."""
    rio = _import_rio()
    result = rio.extract_requirements(
        title="X", abstract="Y", dry_run=True,
    )
    assert result["_dry_run"] is True
    assert result["_provider"] == "rio"
    assert "X" in result["user_message"]
    assert "Y" in result["user_message"]
    assert result["tool"]["name"] == "extract_paper_requirements"


def test_extract_dry_run_respects_env_api_base(monkeypatch):
    rio = _import_rio()
    monkeypatch.setenv("RIO_API_BASE", "http://my-endpoint/v1")
    result = rio.extract_requirements("X", "Y", dry_run=True)
    assert result["api_base"] == "http://my-endpoint/v1"


# ─── extract_requirements: HTTP mocked ────────────────────────────────────


def _mock_openai_response(arguments: dict, finish_reason: str = "tool_calls", usage: dict | None = None):
    """Build OpenAI-compatible response with tool_call."""
    return {
        "model": "rio-3.5-open-397b",
        "choices": [{
            "finish_reason": finish_reason,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "extract_paper_requirements",
                        "arguments": json.dumps(arguments),
                    },
                }],
            },
        }],
        "usage": usage or {"prompt_tokens": 100, "completion_tokens": 50},
    }


def _mock_http_resp(body: dict):
    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps(body).encode("utf-8")
    return Resp()


def test_extract_parses_tool_use_response(monkeypatch):
    rio = _import_rio()
    monkeypatch.setattr(rio, "_RETRY_DELAYS", ())
    arguments = {
        "datasets": [{"category_id": "performance-aggregated", "confidence": 0.9, "evidence_excerpt": "..."}],
        "taxonomy_gap": False,
        "gap_description": None,
    }
    body = _mock_openai_response(arguments)
    with patch("urllib.request.urlopen", return_value=_mock_http_resp(body)):
        result = rio.extract_requirements("X", "Y")
    assert result["_provider"] == "rio"
    assert result["taxonomy_gap"] is False
    assert result["datasets"][0]["category_id"] == "performance-aggregated"
    assert result["_model"] == "rio-3.5-open-397b"
    assert result["_usage"]["input_tokens"] == 100
    assert "_called_at" in result


def test_extract_returns_none_on_no_tool_calls(monkeypatch):
    """Modelo responde com text em vez de tool_call → None graceful."""
    rio = _import_rio()
    monkeypatch.setattr(rio, "_RETRY_DELAYS", ())
    body = {
        "model": "rio-3.5-open-397b",
        "choices": [{
            "finish_reason": "stop",
            "message": {"role": "assistant", "content": "text instead", "tool_calls": []},
        }],
    }
    with patch("urllib.request.urlopen", return_value=_mock_http_resp(body)):
        result = rio.extract_requirements("X", "Y", verbose=False)
    assert result is None


def test_extract_returns_none_on_no_choices(monkeypatch):
    rio = _import_rio()
    monkeypatch.setattr(rio, "_RETRY_DELAYS", ())
    body = {"model": "rio", "choices": []}
    with patch("urllib.request.urlopen", return_value=_mock_http_resp(body)):
        result = rio.extract_requirements("X", "Y", verbose=False)
    assert result is None


def test_extract_handles_invalid_json_in_arguments(monkeypatch):
    rio = _import_rio()
    monkeypatch.setattr(rio, "_RETRY_DELAYS", ())
    body = {
        "model": "rio",
        "choices": [{
            "finish_reason": "tool_calls",
            "message": {"tool_calls": [{
                "function": {"name": "x", "arguments": "{not valid json"},
            }]},
        }],
    }
    with patch("urllib.request.urlopen", return_value=_mock_http_resp(body)):
        result = rio.extract_requirements("X", "Y", verbose=False)
    assert result is None


def test_extract_401_raises_auth_error(monkeypatch):
    """401/403 → RuntimeError (não retry; user precisa fixar key)."""
    rio = _import_rio()
    monkeypatch.setattr(rio, "_RETRY_DELAYS", ())
    err = urllib.error.HTTPError(url="x", code=401, msg="Unauthorized", hdrs=None, fp=io.BytesIO(b""))
    with patch("urllib.request.urlopen", side_effect=err):
        try:
            rio.extract_requirements("X", "Y", verbose=False)
            raise AssertionError("should have raised")
        except RuntimeError as e:
            assert "auth" in str(e).lower()


def test_extract_500_retries_and_gives_up(monkeypatch):
    rio = _import_rio()
    monkeypatch.setattr(rio, "_RETRY_DELAYS", (0,))  # 1 retry fast
    err = urllib.error.HTTPError(url="x", code=500, msg="boom", hdrs=None, fp=io.BytesIO(b""))
    with patch("urllib.request.urlopen", side_effect=err):
        result = rio.extract_requirements("X", "Y", verbose=False)
    assert result is None


# ─── schema invariants ────────────────────────────────────────────────────


def test_module_exports_match_anthropic_interface():
    """Rio adapter precisa exportar mesma interface pra ser drop-in."""
    rio = _import_rio()
    assert hasattr(rio, "DEFAULT_MODEL")
    assert hasattr(rio, "extract_requirements")
    # SDK-free (só urllib stdlib)
    assert rio.DEFAULT_MODEL == "rio-3.5-open-397b"
