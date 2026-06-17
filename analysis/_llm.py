"""Provider-agnostic LLM dispatcher para v3 LLM extraction.

Sprint v0.15 Path D — preparação pra migração `_anthropic.py` → `_rio.py`.
Mantém os call sites (55, 49, etc.) provider-agnostic; dispatch baseado em
`LLM_PROVIDER` env var.

Providers suportados:
  anthropic (default)  → Claude Haiku 4.5 via Anthropic SDK
                         (production-ready, $0.001/paper, requer ANTHROPIC_API_KEY)
  rio                  → Rio-3.5-Open-397B via OpenAI-compatible endpoint
                         (PT-BR nativo, MIT, soberano; requer RIO_API_BASE +
                          deployment via Ollama/vLLM/HF endpoint)

Migration plan (Path D):
  Hoje:           LLM_PROVIDER unset → defaults to anthropic
                  Existing callers unchanged
  Quando Rio
  endpoint sair:  LLM_PROVIDER=rio + RIO_API_BASE=<endpoint> → flip total
                  Mesmo output shape, callers não mudam

Uso pelos callers:
    from _llm import extract_requirements
    result = extract_requirements(title, abstract, dry_run=False)
    # result["_provider"] identifica qual backend respondeu
"""

from __future__ import annotations

import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports adiados pra dentro das funções pra não quebrar quando SDK ausente
# (e.g., anthropic SDK não instalado quando user só vai usar rio backend)

DEFAULT_PROVIDER = "anthropic"
SUPPORTED_PROVIDERS = frozenset({"anthropic", "rio"})


def get_provider() -> str:
    """Returns active LLM provider name. Reads LLM_PROVIDER env var; default
    'anthropic' pra backward compat."""
    provider = os.environ.get("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"LLM_PROVIDER={provider!r} not supported. "
            f"Choose from: {sorted(SUPPORTED_PROVIDERS)}"
        )
    return provider


def extract_requirements(
    title: str,
    abstract: str,
    model: str | None = None,
    max_retries: int = 5,
    dry_run: bool = False,
    verbose: bool = True,
    provider: str | None = None,
) -> dict[str, Any] | None:
    """Provider-agnostic paper-categorization call.

    Dispatch baseado em LLM_PROVIDER (default anthropic). Output shape
    idêntico entre providers — sempre `{datasets, taxonomy_gap,
    gap_description, _provider, _model, _usage, _stop_reason, _called_at}`.

    Args:
        title, abstract: paper text input
        model: provider-specific model name (None → provider default)
        max_retries: max retry attempts (passthrough)
        dry_run: render prompt sem chamar API (zero-cost preview)
        verbose: print warns em stderr
        provider: override LLM_PROVIDER explicitly (testing/manual)

    Returns:
        dict ou None em erro silencioso.
    """
    provider = provider or get_provider()

    if provider == "anthropic":
        from _anthropic import DEFAULT_MODEL as ANTHROPIC_DEFAULT
        from _anthropic import extract_requirements as _ext_anthropic
        result = _ext_anthropic(
            title=title,
            abstract=abstract,
            model=model or ANTHROPIC_DEFAULT,
            max_retries=max_retries,
            dry_run=dry_run,
            verbose=verbose,
        )
        if result is not None and "_provider" not in result:
            result["_provider"] = "anthropic"
        return result

    if provider == "rio":
        from _rio import DEFAULT_MODEL as RIO_DEFAULT
        from _rio import extract_requirements as _ext_rio
        return _ext_rio(
            title=title,
            abstract=abstract,
            model=model or RIO_DEFAULT,
            max_retries=max_retries,
            dry_run=dry_run,
            verbose=verbose,
        )

    # Defensive — shouldn't reach (get_provider valida)
    raise ValueError(f"unknown provider: {provider}")


__all__ = [
    "DEFAULT_PROVIDER",
    "SUPPORTED_PROVIDERS",
    "get_provider",
    "extract_requirements",
]
