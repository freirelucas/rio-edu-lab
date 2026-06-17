"""Rio-3.5-Open-397B adapter via OpenAI-compatible chat/completions endpoint.

Path D do plano de migração v0.15+: substituir gradualmente as chamadas
Anthropic Claude do v3 LLM extraction (`_anthropic.py`) pelo modelo da
Prefeitura do Rio. Razões: PT-BR nativo, MIT, mesmo time do data.rio (IPP),
multimodal disponível (futuro), soberania.

Estado do modelo (hf.co/prefeitura-rio/Rio-3.5-Open-397B):
- 397B params MoE (~17B active, Qwen3.5-397B-A17B base + Nex-N2-Pro merge)
- BF16/F32 weights; quantizações disponíveis pra llama.cpp/Ollama/LM Studio/Jan
- SEM HF Inference Provider deployment hoje (19 requests pending)
- 189k downloads/mês — adoção alta

Backends suportados (todos via OpenAI-compatible /v1/chat/completions):
  1. **Ollama local** (default — `OLLAMA_HOST=http://localhost:11434`)
     - `ollama pull rio-3.5-open-397b` (quando quant publicado)
     - Tool use suportado em Ollama 0.4+
  2. **vLLM self-hosted** (vLLM serve --model prefeitura-rio/Rio-3.5-Open-397B)
  3. **llama.cpp server** com `--port 8080 --chat-format chatml` (suporte tool
     calling em build recente)
  4. **HF Inference Endpoints** dedicado (quando Prefeitura publicar)
  5. **API providers** (Together/Replicate/Fireworks, quando hospedarem)

Config via env vars:
  RIO_API_BASE    URL do endpoint (default http://localhost:11434/v1 → Ollama)
  RIO_API_KEY     token (default "ollama" → fake pra Ollama; obrigatório pra HF)
  RIO_MODEL       model tag (default "rio-3.5-open-397b")

Interface mirrors `_anthropic.py:extract_requirements` — mesmo input/output
shape, mesmo dry_run path. Drop-in compatible via `_llm.py` dispatcher.

Opt-in: NENHUM SDK extra requerido — só urllib (stdlib). Custo zero pra
desenvolvedor sem Ollama local; falha graceful quando endpoint inacessível.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Reusa schemas + categorias do _anthropic.py (mesma taxonomy)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _anthropic import EXTRACT_TOOL, SYSTEM_PROMPT  # noqa: E402

DEFAULT_MODEL = "rio-3.5-open-397b"
DEFAULT_API_BASE = "http://localhost:11434/v1"  # Ollama
DEFAULT_API_KEY = "ollama"  # Ollama ignora auth; placeholder pra OpenAI client

TIMEOUT_S = 120  # MoE de 397B pode demorar mesmo com 17B active
_RETRY_DELAYS = (2.0, 4.0, 8.0, 16.0)


def _get_api_base() -> str:
    return os.environ.get("RIO_API_BASE", DEFAULT_API_BASE).rstrip("/")


def _get_api_key() -> str:
    return os.environ.get("RIO_API_KEY", DEFAULT_API_KEY).strip()


def _get_model() -> str:
    return os.environ.get("RIO_MODEL", DEFAULT_MODEL).strip()


def _convert_tool_to_openai(tool: dict) -> dict:
    """Anthropic tool format → OpenAI tool format.

    Anthropic: {name, description, input_schema}
    OpenAI:    {type: "function", function: {name, description, parameters}}
    """
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "parameters": tool["input_schema"],
        },
    }


def _build_user_message(title: str, abstract: str) -> str:
    """Mesma renderização que _anthropic.py:_build_user_message."""
    abstract = (abstract or "").strip()
    if len(abstract) > 2000:
        abstract = abstract[:2000] + "…"
    return f"**Paper title:** {title or '(missing)'}\n\n**Abstract:** {abstract or '(no abstract available)'}"


def _http_post_json(url: str, payload: dict, api_key: str) -> dict | None:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "rio-edu-lab/0.15 (rio-adapter)",
        },
    )
    last_err: Exception | None = None
    for delay in (0.0, *_RETRY_DELAYS):
        if delay:
            time.sleep(delay)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            status = e.code
            if status in (401, 403):
                # Auth-related: não retry, hard fail upstream
                raise RuntimeError(
                    f"Rio endpoint auth failure ({status}). Check RIO_API_KEY."
                ) from e
            if status in (429, 500, 502, 503, 504):
                print(f"    [rio-retry] HTTP {status}", file=sys.stderr)
                last_err = e
                continue
            return None
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue
    if last_err:
        print(f"    [rio-warn] giveup: {last_err}", file=sys.stderr)
    return None


def extract_requirements(
    title: str,
    abstract: str,
    model: str | None = None,
    max_retries: int = 4,  # noqa: ARG001  (matches _anthropic signature)
    dry_run: bool = False,
    verbose: bool = True,
) -> dict | None:
    """Drop-in replacement de `_anthropic.extract_requirements`.

    Mesma assinatura, mesmo output shape:
      {datasets, taxonomy_gap, gap_description, _model, _usage, _stop_reason,
       _called_at}

    Diferença interna: chama OpenAI-compatible /v1/chat/completions em vez
    da Anthropic SDK. Sem prompt caching (Ollama/vLLM não suportam Anthropic
    `cache_control`), mas Rio MoE com 17B active é fast o suficiente pra runs
    em batch < $10 equivalente.

    Returns None em erro silencioso (verbose=True imprime warn).
    """
    model = model or _get_model()
    user_msg = _build_user_message(title, abstract)

    if dry_run:
        return {
            "_dry_run": True,
            "_provider": "rio",
            "model": model,
            "system_prompt": SYSTEM_PROMPT,
            "user_message": user_msg,
            "tool": EXTRACT_TOOL,
            "api_base": _get_api_base(),
        }

    api_base = _get_api_base()
    api_key = _get_api_key()
    url = f"{api_base}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "tools": [_convert_tool_to_openai(EXTRACT_TOOL)],
        "tool_choice": {
            "type": "function",
            "function": {"name": "extract_paper_requirements"},
        },
        "max_tokens": 1024,
        "temperature": 0.0,
    }

    try:
        response = _http_post_json(url, payload, api_key)
    except RuntimeError:
        raise  # auth failure propaga
    except Exception as e:  # noqa: BLE001
        if verbose:
            print(f"  [llm-warn] rio request failed: {e}", file=sys.stderr)
        return None

    if response is None:
        return None

    choices = response.get("choices") or []
    if not choices:
        if verbose:
            print(f"  [llm-warn] rio response sem choices: {response}", file=sys.stderr)
        return None

    message = choices[0].get("message") or {}
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        if verbose:
            print(
                f"  [llm-warn] rio response sem tool_calls "
                f"(finish_reason={choices[0].get('finish_reason')})",
                file=sys.stderr,
            )
        return None

    # Parse first tool call (strict mode → schema garantido se chegou aqui)
    call = tool_calls[0]
    func = call.get("function") or {}
    args_raw = func.get("arguments") or "{}"
    try:
        result = json.loads(args_raw) if isinstance(args_raw, str) else dict(args_raw)
    except json.JSONDecodeError as e:
        if verbose:
            print(f"  [llm-warn] rio tool args não-JSON: {e}", file=sys.stderr)
        return None

    result["_provider"] = "rio"
    result["_model"] = response.get("model", model)
    result["_stop_reason"] = choices[0].get("finish_reason")
    result["_called_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    usage = response.get("usage") or {}
    result["_usage"] = {
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
        # Rio/Ollama/vLLM não expõem cache breakdown (provider-specific)
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }
    return result


__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_API_BASE",
    "extract_requirements",
]
