"""Unit tests for the IDF-weighted matching primitives in `analysis/_match.py`.

Guards the funnel Stage 2/3 scoring core (v0.11): bigram tokenization, IDF
weighting (rare tokens > common tokens), and the shared-token score. The last
test is a regression for the bag-of-words false positive that IDF was promoted
to eliminate — a single corpus-common token must not dominate a match.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))

from _match import (  # noqa: E402
    DOMAIN_CONFLICT_PENALTY,
    DOMAIN_MATCH_BONUS,
    GRANULARITY_MATCH_BONUS,
    UNIT_MATCH_BONUS,
    build_idf_index,
    code_book_bonus,
    compute_idf,
    edu_signal,
    tokenize,
    tokenize_bigrams,
    weighted_score,
)


def test_tokenize_drops_stopwords_and_short_tokens():
    toks = tokenize("The school of education")
    assert "school" in toks
    assert "education" in toks
    assert "the" not in toks
    assert "of" not in toks


def test_tokenize_strips_accents():
    assert "educacao" in tokenize("Educação")


def test_bigrams_present_and_skip_stopwords():
    toks = tokenize_bigrams("longitudinal cohort panel")
    assert {"longitudinal", "cohort", "panel"} <= toks
    assert "longitudinal cohort" in toks
    assert "cohort panel" in toks


def test_idf_rare_beats_common():
    docs = [{"common", "rare"}, {"common"}, {"common"}, {"common"}]
    idf = compute_idf(docs)
    assert idf["rare"] > idf["common"]


def test_weighted_score_sums_shared_idf():
    idf = {"a": 3.0, "b": 1.0}
    assert weighted_score({"a", "b"}, {"a", "b"}, idf) == 4.0
    assert weighted_score({"a"}, {"b"}, idf) == 0.0


def test_edu_signal_counts_domain_terms():
    assert edu_signal("school teacher student achievement") >= 4
    assert edu_signal("blood pressure cardiac arrest") == 0


def test_common_token_does_not_dominate():
    """A target sharing only a corpus-wide common token ('school') with a query
    must score below one sharing rarer, discriminative tokens."""
    cats = {
        "geo": {"label_pt": "", "aliases": ["school location map"], "aliases_en": []},
        "perf": {"label_pt": "", "aliases": ["school achievement scores ideb"], "aliases_en": []},
    }
    items = [{"title": f"school dataset {i}", "snippet": "", "tags": []} for i in range(20)]
    items.append({"title": "ideb achievement scores by neighborhood", "snippet": "", "tags": []})
    idf, cat_tokens, item_tokens = build_idf_index(cats, items)
    ideb_item = item_tokens[-1]
    s_perf = weighted_score(ideb_item, cat_tokens["perf"], idf)
    s_geo = weighted_score(ideb_item, cat_tokens["geo"], idf)
    assert s_perf > s_geo


# --- code_book_bonus -------------------------------------------------------

def test_code_book_bonus_zero_when_field_absent():
    """Purely additive: no `code_book` or no `expects` → 0 (lexical unchanged)."""
    cat = {"expects": {"domain": "educacao-basica"}}
    item = {"code_book": {"domain": "educacao-basica"}}
    assert code_book_bonus({}, cat) == 0.0
    assert code_book_bonus(item, {}) == 0.0
    assert code_book_bonus({"code_book": {}}, cat) == 0.0


def test_code_book_bonus_domain_match_and_conflict():
    cat = {"expects": {"domain": "educacao-basica"}}
    assert code_book_bonus({"code_book": {"domain": "educacao-basica"}}, cat) == DOMAIN_MATCH_BONUS
    assert code_book_bonus({"code_book": {"domain": "economia"}}, cat) == DOMAIN_CONFLICT_PENALTY


def test_code_book_bonus_sums_aligned_fields():
    cat = {"expects": {"domain": "educacao-basica", "unit_of_observation": "escola",
                       "spatial_granularity": "ponto"}}
    item = {"code_book": {"domain": "educacao-basica", "unit_of_observation": "escola",
                          "spatial_granularity": "ponto"}}
    assert code_book_bonus(item, cat) == (
        DOMAIN_MATCH_BONUS + UNIT_MATCH_BONUS + GRANULARITY_MATCH_BONUS
    )


def test_code_book_bonus_unit_list_membership():
    """A variable-granularity category lists several acceptable units."""
    cat = {"expects": {"unit_of_observation": ["bairro", "ra"]}}
    assert code_book_bonus({"code_book": {"unit_of_observation": "ra"}}, cat) == UNIT_MATCH_BONUS
    assert code_book_bonus({"code_book": {"unit_of_observation": "escola"}}, cat) == 0.0


def test_code_book_bonus_lifts_correct_item_over_lexical_confuser():
    """The motivating case: an IDEB item (thin lexical score) must end up above a
    cross-domain 'desempenho' confuser once the code-book nudge is added."""
    cat = {"expects": {"domain": "educacao-basica", "unit_of_observation": ["bairro", "ra"],
                       "spatial_granularity": ["bairro", "ra", "ap"]}}
    ideb = {"code_book": {"domain": "educacao-basica", "unit_of_observation": "bairro",
                          "spatial_granularity": "bairro"}}
    confuser = {"title": "employment quality index"}  # no code_book
    ideb_lexical, confuser_lexical = 10.0, 16.0
    assert ideb_lexical + code_book_bonus(ideb, cat) > confuser_lexical + code_book_bonus(confuser, cat)
