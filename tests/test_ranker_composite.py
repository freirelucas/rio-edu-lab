"""Testes do ranker primário blended (v0.22) em `analysis/47_check_coverage.py`.

Task #2 do backlog v1.0: migrar `match_detail.composite` de sinal paralelo pra
RANKER PRIMÁRIO — items enriquecidos (com `code_book`) passam a competir pelo
`cat_top` via fit estrutural, não só relevância lexical.

Contrato garantido aqui (todos determinísticos, inputs sintéticos — `idf` +
token-sets construídos à mão dão controle exato sobre o lexical; `code_book` +
`expects` sobre o composite):

  1. NEUTRAL_COMPOSITE = 0.5·Σ(pesos) = 5.0 (item sem code_book).
  2. Items legacy (sem code_book) → rank == lexical (delta 0): ranking idêntico
     ao legacy, zero regressão nos ~9820 items sem code_book.
  3. `--composite-weight 0` reproduz EXATO o argmax puro-lexical (escape hatch).
  4. Booster estrutural pode FLIPAR a seleção: mesmo conjunto de items, um
     enriquecido perde no lexical mas vence no rank blended (weight=1).
  5. Gate `lex > 0`: item off-topic (lexical 0), por mais enriquecido, NUNCA é
     elegível — preserva a semântica `missing` (impossível roubar o slot).
  6. Categorias `external` são puladas.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
sys.path.insert(0, str(ANALYSIS))


def _import_cov():
    spec = importlib.util.spec_from_file_location(
        "cov47", str(ANALYSIS / "47_check_coverage.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# code_book totalmente alinhado + expects casando em TODAS as dimensões →
# composite máximo (domain 1·2 + gran 1·3 + temporal 1·2 + schema 1·2 + api 1·1
# = 10.0) e code_book_bonus = +6 (domain) +3 (unit) +2 (spatial) = +11.
_FULL_CODEBOOK = {
    "domain": "educacao-basica",
    "unit_of_observation": "bairro",
    "spatial_granularity": "bairro",
    "temporal_coverage_parsed": {"start_year": 2007, "end_year": 2023},
    "api_capability": "feature_service",
    "key_variables": ["a", "b"],
}
_FULL_EXPECTS = {
    "domain": "educacao-basica",
    "unit_of_observation": "bairro",
    "spatial_granularity": "bairro",
    "temporal_min_year": 2010,
    "temporal_max_year": 2020,
    "key_variables_needed": ["a", "b"],
}


# ─── constantes ────────────────────────────────────────────────────────────


def test_neutral_composite_is_five_derived_from_weights():
    m = _import_cov()
    assert m.NEUTRAL_COMPOSITE == 5.0
    # derivado dos pesos (não hard-coded) — continua correto se mudarem
    assert m.NEUTRAL_COMPOSITE == 0.5 * sum(m.MATCH_DETAIL_WEIGHTS.values())


def test_default_composite_weight_is_one():
    m = _import_cov()
    assert m.DEFAULT_COMPOSITE_WEIGHT == 1.0


# ─── legacy items: rank == lexical (delta 0) ───────────────────────────────


def test_legacy_items_rank_equals_lexical():
    """Sem code_book, o booster é 0 → rank_score == score, em qualquer weight."""
    m = _import_cov()
    idf = {"tHi": 20.0, "tLo": 5.0}
    cats = {"catA": {"id": "catA"}}
    cat_tokens = {"catA": {"tHi", "tLo"}}
    items = [{"id": "HI", "title": "forte"}, {"id": "LO", "title": "fraco"}]
    item_tokens = [{"tHi"}, {"tLo"}]  # HI compartilha tHi (20), LO tLo (5)

    for w in (0.0, 1.0, 5.0):
        cat_top, flips = m.select_cat_top(cats, items, idf, cat_tokens, item_tokens, w)
        top = cat_top["catA"]
        assert top["item"]["id"] == "HI"          # maior lexical vence
        assert top["score"] == 20.0
        assert top["rank_score"] == 20.0          # delta 0 — sem code_book
        assert flips == 0


# ─── weight=0 reproduz o argmax puro-lexical (escape hatch) ─────────────────


def test_weight_zero_reproduces_pure_lexical_argmax():
    """Com weight=0, um enriquecido de composite=10 NÃO ganha boost — o argmax
    é puramente lexical (score = weighted + code_book_bonus, sem composite)."""
    m = _import_cov()
    # Item enriquecido com lexical baixo; legacy com lexical alto o suficiente
    # pra vencer sem o booster do composite.
    idf = {"tLegacy": 30.0, "tEnr": 5.0}
    cats = {"catA": {"id": "catA", "expects": _FULL_EXPECTS}}
    cat_tokens = {"catA": {"tLegacy", "tEnr"}}
    items = [
        {"id": "L", "title": "legacy"},                       # lex = 30
        {"id": "E", "title": "enr", "code_book": _FULL_CODEBOOK},  # lex = 5 + 11 = 16
    ]
    item_tokens = [{"tLegacy"}, {"tEnr"}]

    cat_top, flips = m.select_cat_top(cats, items, idf, cat_tokens, item_tokens, 0.0)
    top = cat_top["catA"]
    assert top["item"]["id"] == "L"        # 30 > 16 — composite ignorado
    assert top["rank_score"] == top["score"] == 30.0
    assert flips == 0


# ─── composite FLIPA a seleção (o coração da task #2) ───────────────────────


def test_composite_flips_selection_at_weight_one():
    """Mesmo conjunto de items: legacy vence no lexical (20 > 16), mas o
    enriquecido (composite=10 → +5) vence no rank blended a weight=1 (21 > 20).
    Prova que o composite é RANKER PRIMÁRIO, não decoração."""
    m = _import_cov()
    idf = {"tLegacy": 20.0, "tEnr": 5.0}
    cats = {"catA": {"id": "catA", "expects": _FULL_EXPECTS}}
    cat_tokens = {"catA": {"tLegacy", "tEnr"}}
    items = [
        {"id": "L", "title": "legacy"},                        # lex = 20
        {"id": "E", "title": "enr", "code_book": _FULL_CODEBOOK},   # lex = 5 + 11 = 16
    ]
    item_tokens = [{"tLegacy"}, {"tEnr"}]

    # weight 0 → legacy vence (puro lexical)
    top0, flips0 = m.select_cat_top(cats, items, idf, cat_tokens, item_tokens, 0.0)
    assert top0["catA"]["item"]["id"] == "L"
    assert flips0 == 0

    # weight 1 → composite (10 → delta +5) eleva E: rank_E = 16+5 = 21 > 20
    top1, flips1 = m.select_cat_top(cats, items, idf, cat_tokens, item_tokens, 1.0)
    win = top1["catA"]
    assert win["item"]["id"] == "E"          # enriquecido FLIPOU a seleção
    assert win["score"] == 16.0              # score = lexical do vencedor (dirige status)
    assert win["rank_score"] == 21.0         # rank = lexical + booster estrutural
    assert win["rank_score"] > win["score"]  # booster elevou o item
    assert flips1 == 1                        # 1 categoria flipada pelo composite


# ─── gate lex>0: off-topic enriquecido NUNCA é elegível ─────────────────────


def test_offtopic_enriched_item_never_selected_gate_lex_positive():
    """Item com ZERO overlap lexical (lex=0), por mais enriquecido, é pulado —
    preserva a semântica `missing`. Impossível um item off-topic mas com
    code_book bonito roubar o slot da categoria."""
    m = _import_cov()
    # expects SÓ com temporal/schema (sem domain/unit/spatial) → code_book_bonus=0
    # pra qualquer item; assim o lexical do ghost é puramente weighted_score = 0.
    expects_no_geo = {
        "temporal_min_year": 2010, "temporal_max_year": 2020,
        "key_variables_needed": ["a", "b"],
    }
    idf = {"tCat": 10.0}
    cats = {"catA": {"id": "catA", "expects": expects_no_geo}}
    cat_tokens = {"catA": {"tCat"}}
    # ghost: nenhum token em comum com a categoria → weighted_score = 0 → lex = 0
    ghost_cb = {
        "temporal_coverage_parsed": {"start_year": 2007, "end_year": 2023},
        "api_capability": "feature_service",
        "key_variables": ["a", "b"],
    }
    items = [{"id": "GHOST", "title": "off-topic", "code_book": ghost_cb}]
    item_tokens = [{"zzz_unrelated"}]

    cat_top, flips = m.select_cat_top(cats, items, idf, cat_tokens, item_tokens, 1.0)
    assert "catA" not in cat_top   # nenhum item elegível → downstream vira 'missing'
    assert flips == 0


def test_eligible_legacy_beats_ineligible_offtopic_enriched():
    """Com um ghost enriquecido (lex=0) E um legacy on-topic (lex>0), o legacy
    vence — o ghost nunca entra na disputa."""
    m = _import_cov()
    expects_no_geo = {"temporal_min_year": 2010, "temporal_max_year": 2020,
                      "key_variables_needed": ["a", "b"]}
    idf = {"tCat": 8.0}
    cats = {"catA": {"id": "catA", "expects": expects_no_geo}}
    cat_tokens = {"catA": {"tCat"}}
    ghost_cb = {"temporal_coverage_parsed": {"start_year": 2007, "end_year": 2023},
                "api_capability": "feature_service", "key_variables": ["a", "b"]}
    items = [
        {"id": "GHOST", "code_book": ghost_cb},   # lex = 0 → inelegível
        {"id": "REAL", "title": "on-topic"},      # lex = 8 → vence
    ]
    item_tokens = [{"zzz"}, {"tCat"}]

    cat_top, flips = m.select_cat_top(cats, items, idf, cat_tokens, item_tokens, 1.0)
    assert cat_top["catA"]["item"]["id"] == "REAL"
    assert cat_top["catA"]["score"] == 8.0
    assert flips == 0


# ─── categorias external puladas ───────────────────────────────────────────


def test_external_categories_are_skipped():
    m = _import_cov()
    idf = {"t": 10.0}
    cats = {
        "ext": {"id": "ext", "level": "individual"},         # external por level
        "normal": {"id": "normal"},
    }
    cat_tokens = {"ext": {"t"}, "normal": {"t"}}
    items = [{"id": "X", "title": "x"}]
    item_tokens = [{"t"}]

    cat_top, _ = m.select_cat_top(cats, items, idf, cat_tokens, item_tokens, 1.0)
    assert "ext" not in cat_top       # categoria external não é rankeada
    assert cat_top["normal"]["item"]["id"] == "X"
