"""Anthropic API wrapper para v3 LLM extraction de paper → categoria.

v3 do funil: classifica paper title+abstract contra a taxonomia fechada de 10
categorias via Claude API. Substitui (na v3) o bag-of-words do 46. Output
estruturado via Tool Use (strict mode); response é cached + retryable.

Design notes:
- Modelo: `claude-haiku-4-5` (~$0.001/paper; 374 candidates ≈ $0.40 total)
- System prompt + tool com `cache_control: ephemeral` — forward-compat
  (minimum cacheable prefix em haiku 4.5 = 4096 tok; meu system ~900 tok,
  então cache silenciosamente NÃO aderir hoje, mas o marker é noop seguro
  se o system crescer no futuro)
- Strict tool use (`strict: True` + `additionalProperties: False`) garante
  schema válido sem parsing manual
- Retry: SDK auto-retry 429/5xx com backoff; subimos pra max_retries=5
- Auth: `ANTHROPIC_API_KEY` env var (auto-resolved pelo SDK)

Opt-in: requer `pip install anthropic` (NÃO está em requirements.txt do lab —
mantém a v3 LLM opcional). Falha graceful se SDK ausente.

Custos esperados pra primeira run nos 374 candidates funil:
- Input: ~1300 tok × 374 = ~486K tok @ $1/M = ~$0.49
- Output: ~200 tok × 374 = ~75K tok @ $5/M = ~$0.37
- Total: ~$0.86 (sem cache); ~$0.20-0.40 se cache adelir no futuro
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    anthropic = None  # type: ignore

DEFAULT_MODEL = "claude-haiku-4-5"

# 10 categorias fechadas (mesma taxonomy de data/requirements_taxonomy.yml).
TAXONOMY_CATEGORIES = [
    "geometry-schools",
    "geometry-neighborhoods",
    "performance-aggregated",
    "ses-aggregated",
    "enrollment-counts",
    "spatial-partition",
    "microdata-student",
    "microdata-household",
    "longitudinal-cohort",
    "travel-network",
]


SYSTEM_PROMPT = """You are an expert classifier of educational research papers. Given a paper's title and abstract, identify which DATA categories from the rio-edu-lab taxonomy would be needed to replicate the paper's methodology on Rio de Janeiro's open data (data.rio).

The 10 closed categories:

1. **geometry-schools** — School locations (point geometry). E.g., georeferenced school census.
2. **geometry-neighborhoods** — Neighborhood/zone polygons (bairros, RAs, AP).
3. **performance-aggregated** — Educational performance metrics aggregated by spatial unit (IDEB, SAEB, test scores by school/district/region).
4. **ses-aggregated** — Socioeconomic status aggregated by spatial unit (IDS, income index, INSE).
5. **enrollment-counts** — Enrollment / matrícula counts by unit (students by school/grade/year).
6. **spatial-partition** — Spatial hierarchical partitioning (RA, AP, CRE administrative regions).
7. **microdata-student** — Individual student microdata (per-pupil records, panel data on students).
8. **microdata-household** — Individual household microdata (Census, PNAD).
9. **longitudinal-cohort** — Multi-year tracked cohort data (panel on individuals across years).
10. **travel-network** — Transit network / GTFS / accessibility (Pereira-style mobility, isochrones).

For the given paper:
1. Identify which category_ids are ACTUALLY needed — be STRICT. The paper's METHODOLOGY must require this data type, not just be topically related. Don't classify a paper "about education" as needing all education categories.
2. Provide confidence 0.0-1.0 per category (high = methodology clearly states it; low = inferred).
3. Quote 1 line from the abstract as evidence (10-30 words; the actual text fragment that supports this category).
4. Mark `taxonomy_gap: true` if the paper needs data OUTSIDE these 10 categories (e.g., voting records, healthcare access, labor market, environmental data, qualitative interviews). Then describe what's missing in `gap_description`.

Use the `extract_paper_requirements` tool to respond. Over-classification dilutes the signal — when in doubt, prefer fewer categories at higher confidence."""


EXTRACT_TOOL = {
    "name": "extract_paper_requirements",
    "description": "Extract structured data requirements from a paper based on its title and abstract.",
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "datasets": {
                "type": "array",
                "description": "List of taxonomy categories required by the paper's methodology.",
                "items": {
                    "type": "object",
                    "properties": {
                        "category_id": {
                            "type": "string",
                            "enum": TAXONOMY_CATEGORIES,
                            "description": "Category from the closed taxonomy.",
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Confidence 0-1.",
                        },
                        "evidence_excerpt": {
                            "type": "string",
                            "description": "Brief quote (10-30 words) from the abstract supporting this category.",
                        },
                    },
                    "required": ["category_id", "confidence", "evidence_excerpt"],
                    "additionalProperties": False,
                },
            },
            "taxonomy_gap": {
                "type": "boolean",
                "description": "True if paper needs data outside the 10 closed categories.",
            },
            "gap_description": {
                "type": ["string", "null"],
                "description": "If taxonomy_gap is true, describe what kind of data is missing. Null otherwise.",
            },
        },
        "required": ["datasets", "taxonomy_gap", "gap_description"],
        "additionalProperties": False,
    },
}


def _get_api_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    return key or None


def _build_user_message(title: str, abstract: str) -> str:
    """Para input estruturado. Abstract truncado a 2000 chars pra controle de
    custo (haiku 4.5 input $1/M; mesmo um abstract de 4000 chars é só ~1K tok,
    mas papers ocasionais com PDF de methods extraído são bem maiores)."""
    abstract = (abstract or "").strip()
    if len(abstract) > 2000:
        abstract = abstract[:2000] + "…"
    return f"**Paper title:** {title or '(missing)'}\n\n**Abstract:** {abstract or '(no abstract available)'}"


def extract_requirements(
    title: str,
    abstract: str,
    model: str = DEFAULT_MODEL,
    max_retries: int = 5,
    dry_run: bool = False,
    verbose: bool = True,
) -> dict | None:
    """Chama Claude pra extrair {datasets, taxonomy_gap, gap_description} estruturado.

    Returns dict com keys: datasets, taxonomy_gap, gap_description, _model,
    _usage (input/output/cache_read/cache_creation tokens), _stop_reason,
    _called_at (ISO UTC timestamp).

    Em `dry_run=True`: retorna `{"_dry_run": True, ...}` sem chamar API
    (cost-guard pra inspeção de prompt antes de gastar).

    None em erro silencioso (com warn em stderr).
    """
    user_msg = _build_user_message(title, abstract)

    if dry_run:
        # dry_run NÃO requer SDK — só renderiza prompt pra inspeção.
        return {
            "_dry_run": True,
            "model": model,
            "system_prompt": SYSTEM_PROMPT,
            "user_message": user_msg,
            "tool": EXTRACT_TOOL,
        }

    if not HAS_ANTHROPIC:
        raise RuntimeError(
            "anthropic package required: `pip install anthropic`. "
            "v3 LLM extraction é opt-in; não está em requirements.txt do lab."
        )

    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY env var required. Set it in shell (dev) "
            "or as a GitHub repo secret (CI)."
        )

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.with_options(max_retries=max_retries).messages.create(
            model=model,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[{**EXTRACT_TOOL, "cache_control": {"type": "ephemeral"}}],
            tool_choice={"type": "tool", "name": "extract_paper_requirements"},
            messages=[{"role": "user", "content": user_msg}],
        )
    except anthropic.BadRequestError as e:
        if verbose:
            print(f"  [llm-warn] BadRequest: {e}", file=sys.stderr)
        return None
    except anthropic.AuthenticationError as e:
        # Hard fail — sem retry; usuário precisa fixar a key.
        raise RuntimeError(f"ANTHROPIC_API_KEY inválida: {e}") from e
    except anthropic.APIStatusError as e:
        # 429/5xx já retried pelo SDK; se chegou aqui, esgotou tentativas.
        if verbose:
            print(f"  [llm-warn] APIStatus {e.status_code}: {e.message[:80]}", file=sys.stderr)
        return None
    except Exception as e:  # noqa: BLE001
        if verbose:
            print(f"  [llm-warn] {type(e).__name__}: {e}", file=sys.stderr)
        return None

    # Tool Use parse — strict mode garante schema válido se chegou aqui.
    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_paper_requirements":
            result = dict(block.input)
            result["_model"] = response.model
            result["_stop_reason"] = response.stop_reason
            result["_called_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            usage = response.usage
            result["_usage"] = {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
                "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
            }
            return result

    # Sem tool_use no response (raro com tool_choice forçado, mas possível em refusal).
    if verbose:
        print(
            f"  [llm-warn] sem tool_use no response (stop_reason={response.stop_reason})",
            file=sys.stderr,
        )
    return None


__all__ = [
    "DEFAULT_MODEL",
    "TAXONOMY_CATEGORIES",
    "SYSTEM_PROMPT",
    "EXTRACT_TOOL",
    "HAS_ANTHROPIC",
    "extract_requirements",
]
