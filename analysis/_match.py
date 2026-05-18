"""Tokenization + scoring primitives shared by 41 + funnel scripts (46, 47).

Promoted out of `41_match_requirements.py` to avoid duplication across the
funnel pipeline. Stdlib + PyYAML only — same as the rest of `analysis/*`.

Functions:
  - tokenize(text)                       -> set[str]
  - category_keywords(cat_dict)          -> set[str]
  - score_item(item_dict, keywords)      -> float          (manifest item lookup)
  - score_against_categories(text, cats) -> list[(cid, hits)]  (text-side classifier)
  - load_taxonomy(path)                  -> (cat_by_id, alias_lookup)

Constants:
  - STOPWORDS, WEIGHT_TITLE, WEIGHT_TAGS, WEIGHT_SNIPPET
"""

from __future__ import annotations

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
}

WEIGHT_TITLE = 3.0
WEIGHT_TAGS = 2.0
WEIGHT_SNIPPET = 1.0


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def tokenize(text: str) -> set[str]:
    """Lowercase, strip accents, split on non-word, drop stopwords + short tokens."""
    if not text:
        return set()
    norm = strip_accents(text.lower())
    parts = re.split(r"[^a-z0-9]+", norm)
    return {p for p in parts if len(p) >= 3 and p not in STOPWORDS}


def category_keywords(cat: dict) -> set[str]:
    """Build keyword set from a taxonomy category (label_pt + aliases + notes)."""
    chunks = [cat.get("label_pt", "")]
    chunks.extend(cat.get("aliases") or [])
    if cat.get("notes"):
        chunks.append(cat["notes"])
    tokens: set[str] = set()
    for c in chunks:
        tokens |= tokenize(c)
    return tokens


def score_item(item: dict, keywords: set[str]) -> float:
    """Score a manifest item against a keyword set: title=3, tags=2, snippet=1."""
    title_tokens = tokenize(item.get("title", ""))
    snippet_tokens = tokenize(item.get("snippet", ""))
    tag_tokens: set[str] = set()
    for t in item.get("tags") or []:
        tag_tokens |= tokenize(t)
    score = 0.0
    for kw in keywords:
        if kw in title_tokens:
            score += WEIGHT_TITLE
        if kw in tag_tokens:
            score += WEIGHT_TAGS
        if kw in snippet_tokens:
            score += WEIGHT_SNIPPET
    return score


def score_against_categories(
    text: str,
    cats: dict[str, dict],
) -> list[tuple[str, float]]:
    """Score arbitrary text (e.g., paper title+abstract) against taxonomy categories.

    For each category, count how many of its keyword tokens appear in the text.
    Returns [(category_id, score)] sorted desc. Empty list if text empty or no hits.
    Unlike score_item, this is a symmetric token-overlap (no title/tags/snippet
    weighting on the text side, since arbitrary text has no such structure).
    """
    tokens = tokenize(text)
    if not tokens:
        return []
    scored: list[tuple[str, float]] = []
    for cid, cat in cats.items():
        kws = category_keywords(cat)
        hits = sum(1 for kw in kws if kw in tokens)
        if hits > 0:
            scored.append((cid, float(hits)))
    scored.sort(key=lambda x: -x[1])
    return scored


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
    "WEIGHT_TITLE",
    "WEIGHT_TAGS",
    "WEIGHT_SNIPPET",
    "strip_accents",
    "tokenize",
    "category_keywords",
    "score_item",
    "score_against_categories",
    "load_taxonomy",
]
