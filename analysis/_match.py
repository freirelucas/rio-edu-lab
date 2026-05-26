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
    # EN — core
    "education", "educational", "school", "schools", "schooling",
    "teacher", "teachers", "student", "students", "pupil", "pupils",
    # EN — outcomes
    "achievement", "learning", "literacy", "numeracy", "proficiency",
    "graduate", "graduation", "dropout", "enrollment",
    # EN — levels
    "kindergarten", "preschool", "primary", "secondary", "elementary",
    "college", "university", "academic", "tertiary",
    # EN — instruction
    "curriculum", "classroom", "instruction", "instructional",
    "pedagogy", "pedagogical", "vocational",
    # PT (accent-stripped via tokenize)
    "educacao", "educacional", "escola", "escolas", "escolar",
    "aluno", "alunos", "professor", "professores", "ensino",
    "aprendizado", "aprendizagem", "matricula", "matriculas",
    "alfabetizacao", "creche", "creches", "ideb", "saeb",
    "fundamental", "medio", "superior",
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


# --- Code-book alignment (protótipo v0.12) ---------------------------------
# Descritores estruturados opcionais de um item (`code_book`) casados contra o
# que uma categoria espera (`expects`). PURO ADITIVO: item ou categoria sem
# esses campos contribuem 0, então o matching lexical existente fica idêntico.
# Conflito de domínio é penalizado (demove homônimos cross-domínio tipo
# "Escolas de Samba"/"Escolas de música" numa query de escola de ensino);
# alinhamento de unidade/granularidade dá empurrões positivos menores.
DOMAIN_MATCH_BONUS = 6.0
DOMAIN_CONFLICT_PENALTY = -8.0
UNIT_MATCH_BONUS = 3.0
GRANULARITY_MATCH_BONUS = 2.0


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
        bonus += DOMAIN_MATCH_BONUS if cb_dom == exp_dom else DOMAIN_CONFLICT_PENALTY
    if exp.get("unit_of_observation") and cb.get("unit_of_observation") == exp.get("unit_of_observation"):
        bonus += UNIT_MATCH_BONUS
    if exp.get("spatial_granularity") and cb.get("spatial_granularity") == exp.get("spatial_granularity"):
        bonus += GRANULARITY_MATCH_BONUS
    return bonus


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
