"""Tokenization + IDF-weighted scoring shared by the funnel pipeline (41, 46, 47).

Stdlib + PyYAML only — same as the rest of `analysis/*`.

Scoring (v0.11): tokens are unigrams + bigrams; each token is weighted by its
IDF over a corpus (taxonomy categories + manifest items, optionally the funnel
candidates). A match score is the sum of IDF weights of the tokens shared
between a query (paper text or category) and a target (category or manifest
item). Rare, discriminative tokens ("longitudinal cohort") dominate; common
domain tokens ("school", "data") are downweighted. Replaces the earlier
bag-of-words count/positional scoring (validated in 49_match_dryrun.py: kills
the Income-Inequality→geometry-schools false positive and roughly halves the
`external` noise).

Functions:
  - tokenize(text)                       -> set[str]   (unigrams; edu_signal)
  - tokenize_bigrams(text)               -> set[str]   (unigrams + bigrams)
  - edu_signal(text)                     -> int        (Stage-2 domain pre-filter)
  - category_text/manifest_item_text/candidate_text(x) -> str  (corpus builders)
  - compute_idf(list[set[str]])          -> dict[str, float]
  - weighted_score(query, target, idf)   -> float
  - code_book_bonus(item, cat)           -> float      (domain/granularity nudge)
  - build_idf_index(cats, items, *, extra_docs=()) -> (idf, cat_tokens, item_tokens)
  - load_taxonomy(path)                  -> (cat_by_id, alias_lookup)
"""

from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "no", "na", "nos", "nas",
    "por", "para", "em", "com", "sem", "ou", "e", "ao", "à",
    "se", "que", "qual", "como", "via", "ser", "ter",
    "the", "of", "in", "on", "by", "to", "and", "or", "for",
    "is", "are", "was", "were", "be", "been", "this", "that",
    "these", "those", "from", "with", "at",
}

# Vocabulário de educação para o pré-filtro do Stage 2.
# Paper deve mentar >= N destes tokens em title+abstract para ser scoreado
# contra a taxonomia (default 2; ajustável via --edu-min). Cuts papers
# tangenciais (médicos, infra-de-rede) que descobrimos via co-citação mas
# não são domínio do lab.
EDU_KEYWORDS = frozenset({
    # EN — core (specific to education domain; not journal-metadata noise).
    # Removed: academic, university, college, school (sg), students/student (sg),
    # graduate, pupil(s), learning, primary, secondary — these fire on author
    # affiliations ("London School of Economics", "University of Chicago Press")
    # in any OpenAlex abstract preamble + on cross-domain papers (machine
    # learning, primary care, secondary outcomes).
    "education", "educational", "schools", "schooling",
    "teacher", "teachers",
    # EN — outcomes
    "achievement", "literacy", "numeracy", "proficiency",
    "graduation", "dropout", "enrollment",
    # EN — levels (specific)
    "kindergarten", "preschool", "elementary", "tertiary",
    # EN — instruction
    "curriculum", "classroom", "instruction", "instructional",
    "pedagogy", "pedagogical", "vocational",
    # PT (accent-stripped via tokenize). Removed: superior (court/courts),
    # aprendizado (machine learning translation).
    "educacao", "educacional", "escola", "escolas", "escolar",
    "aluno", "alunos", "professor", "professores", "ensino",
    "aprendizagem", "matricula", "matriculas",
    "alfabetizacao", "creche", "creches", "ideb", "saeb",
    "fundamental", "medio",
})


# v0.15 — Expansão do funil pra public policy + economics.
# Tokens canônicos de avaliação de política pública + identificação causal +
# nomes de programas famosos. Combinados com EDU_KEYWORDS no gate do Stage 2
# (46_extract_requirements.py) — paper passa se `edu_signal + policy_signal
# >= --edu-min` (default 2).
#
# Filosofia: bigrams + termos discriminativos. Evita unigrams genéricos
# ("policy", "evaluation" → matcheriam monetary policy / drug evaluation).
# tokenize_bigrams produz "policy evaluation" como token único, então
# bigrams aparecem aqui na forma "a b" (space-separated).
POLICY_KEYWORDS = frozenset({
    # EN — métodos canônicos (bigrams)
    "policy evaluation", "program evaluation", "impact evaluation",
    "causal effect", "treatment effect", "treatment effects",
    "randomized controlled", "random assignment", "natural experiment",
    "regression discontinuity", "instrumental variable", "instrumental variables",
    "synthetic control", "propensity score", "score matching",
    "intent treat",  # "intent-to-treat" tokeniza assim
    "average treatment", "local average",  # ATE / LATE
    # EN — tipos de programa
    "cash transfer", "conditional cash", "transfer program",
    "welfare reform", "minimum wage", "social program",
    "public policy", "policy intervention",
    # EN — programas famosos
    "progresa", "oportunidades", "head start", "jpal",
    # EN — métodos/conceitos discriminativos (unigrams cuidadosos)
    "endogeneity", "exogenous", "endogenous", "heterogeneous treatment",
    "compliers", "noncompliance",
    # PT (accent-stripped)
    "politica publica", "politicas publicas",
    "avaliacao impacto", "avaliacao politica",
    "transferencia renda", "bolsa familia",
    "intervencao", "intervencoes",
    "programa social", "programa publico",
    "saude familia",  # PSF
    "efeito causal", "efeito tratamento",
})


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _parts(text: str) -> list[str]:
    """Lowercase, strip accents, split on non-word, drop stopwords + short tokens."""
    if not text:
        return []
    norm = strip_accents(text.lower())
    return [p for p in re.split(r"[^a-z0-9]+", norm) if len(p) >= 3 and p not in STOPWORDS]


def tokenize(text: str) -> set[str]:
    """Unigram token set (used by edu_signal's keyword pre-filter)."""
    return set(_parts(text))


def tokenize_bigrams(text: str) -> set[str]:
    """Unigrams + consecutive bigrams. Bigrams let rare phrases
    ("longitudinal cohort", "school census") discriminate where single
    common tokens ("school", "data") would not."""
    parts = _parts(text)
    tokens: set[str] = set(parts)
    for a, b in zip(parts, parts[1:], strict=False):
        tokens.add(f"{a} {b}")
    return tokens


def edu_signal(text: str) -> int:
    """Count of EDU_KEYWORDS hits in text (tokenized).

    Stage-2 pre-filter (46_extract_requirements): a paper must show >= N
    education-domain tokens before being scored against the taxonomy. Avoids
    classifying medical/COVID/infra papers that surfaced via the bibliometric
    snowball but aren't on-topic.
    """
    tokens = tokenize(text)
    return sum(1 for kw in EDU_KEYWORDS if kw in tokens)


def policy_signal(text: str) -> int:
    """Count of POLICY_KEYWORDS hits in text (tokenized + bigrams).

    Counterpart to `edu_signal` para o escopo expandido (v0.15) que inclui
    public policy evaluation + economics. Bigrams ("policy evaluation",
    "treatment effect", etc.) precisam ser computados via tokenize_bigrams —
    senão "policy" sozinho nunca match.

    O Stage 2 (46_extract_requirements) usa `edu_signal + policy_signal >=
    edu_min` (default 2) — paper passa se tiver sinal edu OU policy >= 2.
    """
    tokens = tokenize_bigrams(text)
    return sum(1 for kw in POLICY_KEYWORDS if kw in tokens)


def domain_signal(text: str) -> int:
    """Combined edu + policy signal — primary Stage-2 gate (v0.15+).

    Conveniência pra 46_extract_requirements: substitui o gate antigo
    `edu_signal >= 2` por `domain_signal >= 2`, sem alocar 2 chamadas
    redundantes a tokenize().
    """
    return edu_signal(text) + policy_signal(text)


def category_text(cat: dict) -> str:
    """Category 'document': label_pt + aliases (PT) + aliases_en, concatenated.

    Excludes `notes` on purpose — that field holds metadata ("Feature Service",
    "INEP per-school", "data.rio") that pollutes the token set and inflates
    spurious matches.
    """
    chunks = [cat.get("label_pt", "")]
    chunks.extend(cat.get("aliases") or [])
    chunks.extend(cat.get("aliases_en") or [])
    return " ".join(chunks).strip()


def manifest_item_text(item: dict) -> str:
    title = item.get("title", "")
    snippet = item.get("snippet", "")
    tags = " ".join(item.get("tags") or [])
    return f"{title} {tags} {snippet}".strip()


def candidate_text(c: dict) -> str:
    return f"{c.get('title', '')} {c.get('abstract', '')}".strip()


def compute_idf(docs_tokens: list[set[str]]) -> dict[str, float]:
    """Smoothed IDF over a corpus of token-sets: log((N+1)/(df+1)) + 1.

    Common tokens (high df) approach weight 1.0; rare tokens (df=1) get the
    heaviest weight. Unknown tokens default to 1.0 in `weighted_score`.
    """
    n = len(docs_tokens)
    df: dict[str, int] = {}
    for tokens in docs_tokens:
        for t in tokens:
            df[t] = df.get(t, 0) + 1
    return {t: math.log((n + 1) / (d + 1)) + 1.0 for t, d in df.items()}


def weighted_score(query_tokens: set[str], target_tokens: set[str], idf: dict[str, float]) -> float:
    """Sum of IDF weights for tokens shared by query and target."""
    return sum(idf.get(t, 1.0) for t in (query_tokens & target_tokens))


# --- Code-book alignment (v0.12) -------------------------------------------
# Optional structured descriptors of a manifest item (`code_book`) matched
# against what a taxonomy category expects (`expects`). PURELY ADDITIVE: an item
# or category lacking these fields contributes 0, so lexical matching is
# unchanged where they are absent. The positive nudges lift a thinly-worded but
# correct item above lexical confusers — e.g. the IDEB-by-RA item (whose generic
# aliases "indicador de desempenho" otherwise rank it below "Saúde", "Qualidade
# do Emprego" and bus-transport "desempenho"). The domain *conflict* penalty
# (held in reserve, not applied to any item in v0.12) demotes cross-domain
# homonyms when boosting the correct item alone is not enough.
#
# `expects` fields may be a scalar (equality) or a list (membership) — the list
# form lets a variable-granularity category accept several units, e.g.
# performance-aggregated `unit_of_observation: [bairro, ra]`.
DOMAIN_MATCH_BONUS = 6.0
DOMAIN_CONFLICT_PENALTY = -8.0
UNIT_MATCH_BONUS = 3.0
GRANULARITY_MATCH_BONUS = 2.0


def _expect_match(expected, actual) -> bool:
    """True if `actual` (item code_book value) satisfies `expected` (category):
    scalar equality, or membership when `expected` is a list. None on either
    side never matches."""
    if expected is None or actual is None:
        return False
    if isinstance(expected, (list, tuple)):
        return actual in expected
    return actual == expected


def code_book_bonus(item: dict, cat: dict) -> float:
    """Granularity/domain alignment adjustment between an item's `code_book`
    and a category's `expects`. Returns 0.0 when either side lacks the field."""
    cb = item.get("code_book")
    exp = cat.get("expects")
    if not cb or not exp:
        return 0.0
    bonus = 0.0
    exp_dom, cb_dom = exp.get("domain"), cb.get("domain")
    if exp_dom and cb_dom:
        bonus += DOMAIN_MATCH_BONUS if _expect_match(exp_dom, cb_dom) else DOMAIN_CONFLICT_PENALTY
    if _expect_match(exp.get("unit_of_observation"), cb.get("unit_of_observation")):
        bonus += UNIT_MATCH_BONUS
    if _expect_match(exp.get("spatial_granularity"), cb.get("spatial_granularity")):
        bonus += GRANULARITY_MATCH_BONUS
    return bonus


# --- Enriched match (v0.15) -----------------------------------------------
# Sub-scores normalizados [0, 1] em 5 dimensões + composite ∈ [0, 10].
# Composite weights documentados em MATCH_DETAIL_WEIGHTS; revisáveis quando
# gold-set for labelado e P/R por dimensão for medível.
#
# Diferença vs code_book_bonus:
#   - code_book_bonus retorna PONTOS (+6/+3/+2/-8) somados ao IDF (47:140);
#     continua sendo o sinal primário de scoring/ranking.
#   - match_detail retorna DICT de sub-scores normalizados pra inspeção humana
#     + composite pra ranking secundário. Persistido em coverage.match_detail
#     (paralelo ao status binário existente).
MATCH_DETAIL_WEIGHTS = {
    "domain": 2.0,
    "granularity": 3.0,
    "temporal": 2.0,
    "schema": 2.0,
    "api": 1.0,
}


_API_CAPABILITY_SCORE = {
    "feature_service": 1.0,    # GeoJSON queryable, ideal pra reprodução
    "static_file": 0.7,        # Excel/CSV download — funcional, mas snapshot
    "document_link": 0.3,      # PDF/HTML externo — leitura humana, não ETL
    "none": 0.0,
}


def _parse_year_range(s: str | None) -> tuple[int, int] | None:
    """Extrai (start_year, end_year) de strings como '2007-2023 (bienal)',
    '2010 (Censo IBGE)', '2014-2019'. Retorna None quando não acha pelo menos
    um ano de 4 dígitos no range 1900-2099. Tolerante a ruído."""
    if not s:
        return None
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", str(s))
    if not years:
        return None
    ys = [int(y) for y in years]
    return (min(ys), max(ys))


def temporal_overlap_score(cb: dict | None, exp: dict | None) -> float:
    """Fração [0,1] do range temporal requerido pela categoria que o item cobre.

    Item temporal vem de code_book.temporal_coverage_parsed.{start_year,end_year}
    ou — fallback — parsed do code_book.temporal_coverage string. Cat declara
    expects.temporal_min_year/temporal_max_year (preferred span; None = neutral).

    Retorna 0.5 (neutral) quando qualquer lado falta dado temporal — não
    penaliza items legacy sem o campo, mas premia os enriquecidos.
    """
    if not cb or not exp:
        return 0.5
    item_range = None
    parsed = cb.get("temporal_coverage_parsed")
    if isinstance(parsed, dict) and parsed.get("start_year") and parsed.get("end_year"):
        item_range = (int(parsed["start_year"]), int(parsed["end_year"]))
    else:
        item_range = _parse_year_range(cb.get("temporal_coverage"))
    cat_min = exp.get("temporal_min_year")
    cat_max = exp.get("temporal_max_year")
    if item_range is None or cat_min is None or cat_max is None:
        return 0.5
    needed = int(cat_max) - int(cat_min) + 1
    if needed <= 0:
        return 0.5
    overlap_start = max(item_range[0], int(cat_min))
    overlap_end = min(item_range[1], int(cat_max))
    overlap = max(0, overlap_end - overlap_start + 1)
    return min(1.0, overlap / needed)


def api_capability_score(cb: dict | None) -> float:
    """Score [0,1] derivado de code_book.api_capability. Cat-agnostic — premia
    items fetchable (Feature Service > static file > document link > none).

    Retorna 0.5 (neutral) quando item não declara api_capability — não penaliza
    legacy, mas Feature Services validados ganham +1.0 quando preenchidos.
    """
    if not cb:
        return 0.5
    cap = cb.get("api_capability")
    if cap is None:
        return 0.5
    return _API_CAPABILITY_SCORE.get(cap, 0.0)


def schema_match_score(cb: dict | None, exp: dict | None) -> float:
    """Precision-style score [0,1]: fração das variáveis que a categoria precisa
    (`expects.key_variables_needed`) que o item efetivamente tem
    (`code_book.key_variables`). Tokens case-insensitive + accent-stripped.

    Retorna 0.5 (neutral) quando qualquer lado falta; 0 quando cat declara
    necessidades mas item não bate nenhuma; 1 quando item cobre todas.
    """
    if not cb or not exp:
        return 0.5
    needed = exp.get("key_variables_needed")
    have = cb.get("key_variables")
    if not needed or not have:
        return 0.5
    needed_n = {strip_accents(str(v)).lower().strip() for v in needed}
    have_n = {strip_accents(str(v)).lower().strip() for v in have}
    if not needed_n:
        return 0.5
    return len(needed_n & have_n) / len(needed_n)


def granularity_match_score(cb: dict | None, exp: dict | None) -> float:
    """Score [0,1]: média de (unit_of_observation match, spatial_granularity match).
    Cada sub-match é 0 ou 1. Neutral 0.5 se code_book/expects faltam ambos."""
    if not cb or not exp:
        return 0.5
    u_match = float(_expect_match(exp.get("unit_of_observation"), cb.get("unit_of_observation")))
    g_match = float(_expect_match(exp.get("spatial_granularity"), cb.get("spatial_granularity")))
    return (u_match + g_match) / 2.0


def domain_match_score(cb: dict | None, exp: dict | None) -> float:
    """Score [0,1]: 1 se domain bate, 0 se conflita, 0.5 se qualquer lado falta.

    Convergência negativa (item domain ≠ cat domain) vira 0 e não -1; o sinal
    de penalização absoluta já vive em code_book_bonus → IDF (47:140). Aqui
    é só sinal de leitura humana / ranking secundário.
    """
    if not cb or not exp:
        return 0.5
    exp_dom, cb_dom = exp.get("domain"), cb.get("domain")
    if exp_dom is None or cb_dom is None:
        return 0.5
    return 1.0 if _expect_match(exp_dom, cb_dom) else 0.0


def match_detail(item: dict, cat: dict) -> dict:
    """Compute todas as 5 sub-dimensões normalizadas + composite.

    Returns:
        {
          domain_match: float [0,1],
          granularity_match: float [0,1],
          temporal_match: float [0,1],
          schema_match: float [0,1],
          api_match: float [0,1],
          composite: float [0, sum(weights)],  # ~10 com weights padrão
        }

    Composite = Σ sub_score × weight. Pesos em MATCH_DETAIL_WEIGHTS.
    Quando code_book/expects estão vazios, sub-scores defaultam pra 0.5 (neutral)
    pra não punir items legacy — pero a composite ainda discrimina items
    enriquecidos no topo.
    """
    cb = item.get("code_book") or {}
    exp = cat.get("expects") or {}
    sub = {
        "domain_match": round(domain_match_score(cb, exp), 3),
        "granularity_match": round(granularity_match_score(cb, exp), 3),
        "temporal_match": round(temporal_overlap_score(cb, exp), 3),
        "schema_match": round(schema_match_score(cb, exp), 3),
        "api_match": round(api_capability_score(cb), 3),
    }
    w = MATCH_DETAIL_WEIGHTS
    composite = (
        sub["domain_match"] * w["domain"]
        + sub["granularity_match"] * w["granularity"]
        + sub["temporal_match"] * w["temporal"]
        + sub["schema_match"] * w["schema"]
        + sub["api_match"] * w["api"]
    )
    sub["composite"] = round(composite, 3)
    return sub


def build_idf_index(
    cats: dict[str, dict],
    items: list[dict],
    *,
    extra_docs: list[set[str]] | tuple = (),
) -> tuple[dict[str, float], dict[str, set[str]], list[set[str]]]:
    """Tokenize categories + manifest items and compute IDF over the combined
    corpus. `extra_docs` (e.g., funnel-candidate token-sets) are folded into the
    IDF document-frequency counts but not returned.

    Returns (idf, cat_tokens_by_id, item_tokens_list).
    """
    cat_tokens = {cid: tokenize_bigrams(category_text(cat)) for cid, cat in cats.items()}
    item_tokens = [tokenize_bigrams(manifest_item_text(it)) for it in items]
    idf = compute_idf(list(cat_tokens.values()) + item_tokens + list(extra_docs))
    return idf, cat_tokens, item_tokens


def load_taxonomy(path: Path) -> tuple[dict[str, dict], dict[str, str]]:
    """Returns (category_by_id, alias_lookup) from a taxonomy YAML file.

    `alias_lookup` keys are lowercased + stripped for case-insensitive match.
    Returns ({}, {}) if file missing.
    """
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    if not path.exists():
        return {}, {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cats: dict[str, dict] = {}
    alias_to_cat: dict[str, str] = {}
    for c in data.get("categories") or []:
        cid = c.get("id", "")
        if not cid:
            continue
        cats[cid] = c
        for a in c.get("aliases") or []:
            alias_to_cat[a.strip().lower()] = cid
    return cats, alias_to_cat


__all__ = [
    "STOPWORDS",
    "EDU_KEYWORDS",
    "strip_accents",
    "tokenize",
    "tokenize_bigrams",
    "edu_signal",
    "category_text",
    "manifest_item_text",
    "candidate_text",
    "compute_idf",
    "weighted_score",
    "code_book_bonus",
    "build_idf_index",
    "load_taxonomy",
]
