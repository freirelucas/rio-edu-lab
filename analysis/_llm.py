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


# ─── Resource bargain (VSM S3) ────────────────────────────────────────────
# Caps explícitos pra LLM extraction. Env vars:
#   MAX_TOKENS_PER_PAPER  — limit input+output tokens por chamada (0 = unlimited;
#                           recomendado 4000-6000)
#   MAX_LLM_BUDGET_USD    — limit cumulative cost USD por processo (0 = unlimited;
#                           recomendado 5.00)
#
# Pricing assumido (2026):
#   anthropic (Claude Haiku 4.5): $1.00/M input + $5.00/M output
#   rio (self-hosted Ollama/vLLM/HF): $0.00 marginal (cost é hardware/cloud)
#
# Quando cap excedido: LLMBudgetExceeded raise. Caller decide retry/abort.

ANTHROPIC_PRICING = {"input_per_1m": 1.0, "output_per_1m": 5.0}
RIO_PRICING = {"input_per_1m": 0.0, "output_per_1m": 0.0}


class LLMBudgetExceeded(RuntimeError):
    """Raised when MAX_TOKENS_PER_PAPER or MAX_LLM_BUDGET_USD exceeded."""


class _BudgetTracker:
    """Singleton per-process — soma custos cumulativos + enforce caps."""

    def __init__(self) -> None:
        self.cumulative_cost_usd: float = 0.0
        self.n_calls: int = 0
        self._max_tokens_cached: int | None = None
        self._max_budget_cached: float | None = None

    @property
    def max_tokens_per_paper(self) -> int | None:
        """Re-read env each call (allows monkeypatch in tests)."""
        raw = os.environ.get("MAX_TOKENS_PER_PAPER", "0")
        try:
            val = int(raw)
        except ValueError:
            return None
        return val if val > 0 else None

    @property
    def max_budget_usd(self) -> float | None:
        raw = os.environ.get("MAX_LLM_BUDGET_USD", "0")
        try:
            val = float(raw)
        except ValueError:
            return None
        return val if val > 0 else None

    def check_pre_call(self, estimated_input_tokens: int = 0) -> None:
        """Raise LLMBudgetExceeded if would exceed budget."""
        max_tok = self.max_tokens_per_paper
        if max_tok and estimated_input_tokens > max_tok:
            raise LLMBudgetExceeded(
                f"MAX_TOKENS_PER_PAPER={max_tok} excedido "
                f"(estimated input: {estimated_input_tokens})"
            )
        max_budget = self.max_budget_usd
        if max_budget and self.cumulative_cost_usd >= max_budget:
            raise LLMBudgetExceeded(
                f"MAX_LLM_BUDGET_USD={max_budget:.2f} excedido "
                f"(cumulative: ${self.cumulative_cost_usd:.4f}, n_calls={self.n_calls})"
            )

    def record_post_call(self, usage: dict, provider: str) -> float:
        """Compute cost from usage + provider rates; accumulate. Returns this call's cost."""
        pricing = ANTHROPIC_PRICING if provider == "anthropic" else RIO_PRICING
        input_toks = (usage or {}).get("input_tokens", 0) or 0
        output_toks = (usage or {}).get("output_tokens", 0) or 0
        cost = (input_toks / 1_000_000) * pricing["input_per_1m"] + (
            output_toks / 1_000_000
        ) * pricing["output_per_1m"]
        self.cumulative_cost_usd += cost
        self.n_calls += 1
        return cost

    def reset(self) -> None:
        """Reset cumulative state. Útil pra tests."""
        self.cumulative_cost_usd = 0.0
        self.n_calls = 0


# Singleton instance — accumula across calls dentro do mesmo processo
_BUDGET = _BudgetTracker()


def get_budget_tracker() -> _BudgetTracker:
    """Returns the per-process budget tracker."""
    return _BUDGET


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

    # Resource bargain pre-check (skip em dry_run — sem custo real)
    if not dry_run:
        # Estimar tokens via 4 chars/tok (Anthropic heuristic) — não precisa
        # tokenizer real pro pre-check; o post-call usage tem o número exato.
        est_input = (len(title or "") + len(abstract or "")) // 4 + 800  # +800 prompt overhead
        _BUDGET.check_pre_call(est_input)

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
        if result is not None and not dry_run and "_usage" in result:
            cost = _BUDGET.record_post_call(result["_usage"], "anthropic")
            result["_cost_usd"] = round(cost, 6)
            result["_cumulative_cost_usd"] = round(_BUDGET.cumulative_cost_usd, 6)
        return result

    if provider == "rio":
        from _rio import DEFAULT_MODEL as RIO_DEFAULT
        from _rio import extract_requirements as _ext_rio
        result = _ext_rio(
            title=title,
            abstract=abstract,
            model=model or RIO_DEFAULT,
            max_retries=max_retries,
            dry_run=dry_run,
            verbose=verbose,
        )
        if result is not None and not dry_run and "_usage" in result:
            cost = _BUDGET.record_post_call(result["_usage"], "rio")
            result["_cost_usd"] = round(cost, 6)
            result["_cumulative_cost_usd"] = round(_BUDGET.cumulative_cost_usd, 6)
        return result

    # Defensive — shouldn't reach (get_provider valida)
    raise ValueError(f"unknown provider: {provider}")


__all__ = [
    "DEFAULT_PROVIDER",
    "SUPPORTED_PROVIDERS",
    "LLMBudgetExceeded",
    "ANTHROPIC_PRICING",
    "RIO_PRICING",
    "get_provider",
    "get_budget_tracker",
    "extract_requirements",
]
