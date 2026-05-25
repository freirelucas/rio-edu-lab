"""Dry-run experimental: compara scoring TF-IDF (novo) vs bag-of-words (atual).

Não modifica `data/papers_funnel.yml` nem `data/papers_catalog.yml`. Apenas
gera relatório comparativo em `data/processed/match_dryrun_*` pro curador
avaliar antes de decidir se o novo scoring vai pra PR.

Algoritmo novo (Stage 2 e 3):
- Tokenização com bigrams (1-2 palavras consecutivas).
- Cada token recebe peso IDF = log(N / df) sobre corpus combinado
  (aliases das categorias + papers do funil + manifest items).
- Score = soma dos pesos IDF dos tokens em interseção
  (token da alias-set da categoria E presente no paper/item).
- Mantém set-intersection do original (fast lookup) mas discrimina
  tokens raros ("longitudinal panel") vs comuns ("school").
- Thresholds calibrados empiricamente após observar distribuição.

Output:
- data/processed/match_dryrun_report.md   relatório markdown comparativo
- data/processed/match_dryrun_delta.csv   linha por (candidate, categoria) old vs new

Uso:
  pip install scikit-learn
  python3 analysis/49_match_dryrun.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required", file=sys.stderr)
    sys.exit(1)

import math
import re
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))
from _match import (  # type: ignore
    EDU_KEYWORDS,
    edu_signal,
)

FUNNEL_YML = ROOT / "data" / "papers_funnel.yml"
CATALOG_YML = ROOT / "data" / "papers_catalog.yml"
TAXONOMY_YML = ROOT / "data" / "requirements_taxonomy.yml"
MANIFEST_JSON = ROOT / "data" / "manifest.json"
OUT_REPORT = ROOT / "data" / "processed" / "match_dryrun_report.md"
OUT_DELTA_CSV = ROOT / "data" / "processed" / "match_dryrun_delta.csv"

EXTERNAL_LEVELS = {"individual"}
EXTERNAL_IDS = {"travel-network"}

# Novos thresholds (calibrar empiricamente após primeiro run)
STAGE2_TOP_K = 3
STAGE2_MIN_SCORE = 3.0  # IDF-weighted score mínimo
STAGE3_AVAILABLE = 5.0  # mantém threshold antigo (5.0) mas agora ponderado IDF
STAGE3_PARTIAL_MIN = 2.0


STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "no", "na", "nos", "nas",
    "por", "para", "em", "com", "sem", "ou", "e", "ao", "à",
    "se", "que", "qual", "como", "via", "ser", "ter",
    "the", "of", "in", "on", "by", "to", "and", "or", "for",
    "is", "are", "was", "were", "be", "been", "this", "that",
    "these", "those", "from", "with", "at", "as",
}


def strip_accents(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def tokenize_with_bigrams(text: str) -> set[str]:
    """Lowercase, strip accents, drop stopwords, generate unigrams + bigrams."""
    if not text:
        return set()
    norm = strip_accents(text.lower())
    parts = [p for p in re.split(r"[^a-z0-9]+", norm) if len(p) >= 3 and p not in STOPWORDS]
    tokens: set[str] = set(parts)
    # Bigrams (consecutive non-stopword tokens)
    for a, b in zip(parts, parts[1:]):
        tokens.add(f"{a} {b}")
    return tokens


def compute_idf(docs_tokens: list[set[str]]) -> dict[str, float]:
    """IDF = log(N / df) over a corpus of token-sets.

    Tokens that appear in >50% of docs get downweighted (probably common
    domain terms like 'school'); rare tokens (df=1) get heaviest weight.
    """
    n = len(docs_tokens)
    df: dict[str, int] = {}
    for tokens in docs_tokens:
        for t in tokens:
            df[t] = df.get(t, 0) + 1
    # IDF smoothed: log((N+1)/(df+1)) + 1
    return {t: math.log((n + 1) / (d + 1)) + 1.0 for t, d in df.items()}


def weighted_score(query_tokens: set[str], cat_tokens: set[str], idf: dict[str, float]) -> float:
    """Sum of IDF weights for tokens in intersection."""
    common = query_tokens & cat_tokens
    return sum(idf.get(t, 1.0) for t in common)


def is_external_category(cat: dict) -> bool:
    if cat.get("level") in EXTERNAL_LEVELS:
        return True
    if cat.get("id") in EXTERNAL_IDS:
        return True
    notes = (cat.get("notes") or "").lower()
    return "não disponível no data.rio" in notes or "nao disponivel no data.rio" in notes


def category_text(cat: dict) -> str:
    """Concatena aliases PT + EN + label como 'documento' da categoria."""
    chunks = [cat.get("label_pt", "")]
    chunks.extend(cat.get("aliases") or [])
    chunks.extend(cat.get("aliases_en") or [])
    return " ".join(chunks).strip()


def candidate_text(c: dict) -> str:
    return f"{c.get('title','')} {c.get('abstract','')}".strip()


def manifest_item_text(item: dict) -> str:
    title = item.get("title", "")
    snippet = item.get("snippet", "")
    tags = " ".join(item.get("tags") or [])
    return f"{title} {tags} {snippet}".strip()


def status_from_sim(score: float) -> str:
    if score >= STAGE3_AVAILABLE:
        return "available"
    if score >= STAGE3_PARTIAL_MIN:
        return "partial"
    return "missing"


def main() -> int:
    print("loading inputs…")
    fun = yaml.safe_load(FUNNEL_YML.read_text(encoding="utf-8")) or {}
    cat_doc = yaml.safe_load(CATALOG_YML.read_text(encoding="utf-8")) or {}
    tax = yaml.safe_load(TAXONOMY_YML.read_text(encoding="utf-8")) or {}
    manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))

    candidates = fun.get("candidates", [])
    catalog_papers = cat_doc.get("papers", [])
    cats = {c["id"]: c for c in tax.get("categories", [])}
    items = manifest.get("items", [])
    print(f"  {len(candidates)} candidates, {len(catalog_papers)} catalog papers, "
          f"{len(cats)} categories, {len(items)} manifest items")

    # ─── NEW: tokenize + IDF over combined corpus ───
    cat_ids = list(cats.keys())
    cat_tokens = {cid: tokenize_with_bigrams(category_text(cats[cid])) for cid in cat_ids}
    cand_tokens = [tokenize_with_bigrams(candidate_text(c)) for c in candidates]
    item_tokens = [tokenize_with_bigrams(manifest_item_text(it)) for it in items]

    all_docs = list(cat_tokens.values()) + cand_tokens + item_tokens
    print(f"computing IDF over {len(all_docs)} docs…")
    idf = compute_idf(all_docs)
    print(f"  vocab size: {len(idf)} tokens (unigrams + bigrams)")

    # ─── Stage 2 new: paper → top categorias ───
    print("computing new Stage 2 suggestions…")
    new_suggestions: list[list[tuple[str, float]]] = []
    for i, c in enumerate(candidates):
        if edu_signal(candidate_text(c)) < 2:
            new_suggestions.append([])
            continue
        scored = []
        for cid in cat_ids:
            s = weighted_score(cand_tokens[i], cat_tokens[cid], idf)
            if s >= STAGE2_MIN_SCORE:
                scored.append((cid, s))
        scored.sort(key=lambda x: -x[1])
        new_suggestions.append(scored[:STAGE2_TOP_K])

    # ─── Stage 3 new: categoria → best manifest item ───
    print("computing new Stage 3 coverage…")
    cat_best_item: dict[str, tuple[int, float]] = {}
    for cid in cat_ids:
        if is_external_category(cats[cid]):
            continue
        best_idx, best_score = -1, 0.0
        for k, toks in enumerate(item_tokens):
            s = weighted_score(toks, cat_tokens[cid], idf)
            if s > best_score:
                best_score, best_idx = s, k
        if best_idx >= 0:
            cat_best_item[cid] = (best_idx, best_score)

    new_coverage: list[list[dict]] = []
    for i, c in enumerate(candidates):
        sugg = new_suggestions[i]
        if not sugg:
            new_coverage.append([])
            continue
        rows = []
        for cid, _sugg_score in sugg:
            cat = cats[cid]
            if is_external_category(cat):
                rows.append({
                    "category_id": cid,
                    "manifest_item_id": None,
                    "manifest_title": "(fora do data.rio — externo)",
                    "score": 0.0,
                    "status": "external",
                })
                continue
            best = cat_best_item.get(cid)
            if not best:
                rows.append({
                    "category_id": cid,
                    "manifest_item_id": None,
                    "manifest_title": "(nenhum item bate)",
                    "score": 0.0,
                    "status": "missing",
                })
                continue
            idx, sc = best
            rows.append({
                "category_id": cid,
                "manifest_item_id": items[idx].get("id"),
                "manifest_title": items[idx].get("title", ""),
                "score": round(sc, 2),
                "status": status_from_sim(sc),
            })
        new_coverage.append(rows)

    # ─── Comparação OLD vs NEW ───
    print("computing delta vs old funnel…")
    rows_csv: list[dict] = []
    old_status_dist: Counter = Counter()
    new_status_dist: Counter = Counter()

    for i, c in enumerate(candidates):
        old_sugg = {s["category_id"]: float(s["score"]) for s in (c.get("suggested_requirements") or [])}
        new_sugg = {cid: s for cid, s in new_suggestions[i]}
        old_cov = {x["category_id"]: x for x in (c.get("coverage") or [])}
        new_cov = {x["category_id"]: x for x in new_coverage[i]}

        for cov in (c.get("coverage") or []):
            old_status_dist[cov["status"]] += 1
        for cov in new_coverage[i]:
            new_status_dist[cov["status"]] += 1

        all_cats = set(old_sugg.keys()) | set(new_sugg.keys()) | set(old_cov.keys()) | set(new_cov.keys())
        for cid in all_cats:
            rows_csv.append({
                "openalex_id": c.get("openalex_id", ""),
                "title": (c.get("title") or "")[:100],
                "category_id": cid,
                "old_stage2_score": old_sugg.get(cid, 0.0),
                "new_stage2_sim": round(new_sugg.get(cid, 0.0), 3),
                "old_status": old_cov.get(cid, {}).get("status", ""),
                "new_status": new_cov.get(cid, {}).get("status", ""),
                "old_score": old_cov.get(cid, {}).get("score", 0.0),
                "new_score": new_cov.get(cid, {}).get("score", 0.0),
                "old_item": old_cov.get(cid, {}).get("manifest_item_id", ""),
                "new_item": new_cov.get(cid, {}).get("manifest_item_id", ""),
            })

    # ─── CSV ───
    OUT_DELTA_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_DELTA_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_csv[0].keys()))
        w.writeheader()
        w.writerows(rows_csv)
    print(f"wrote {OUT_DELTA_CSV.relative_to(ROOT)} ({len(rows_csv)} rows)")

    # ─── Headline papers seed (12 do catálogo) ───
    seed_titles = {p["title"][:80].lower(): p for p in catalog_papers}
    seed_findings = []
    for i, c in enumerate(candidates):
        ct = (c.get("title") or "")[:80].lower()
        if ct in seed_titles:
            seed_findings.append((seed_titles[ct], new_suggestions[i], new_coverage[i]))

    # ─── Falso positivo check: Income Inequality 1913-1998 ───
    fp_check = None
    for i, c in enumerate(candidates):
        if "income inequality" in (c.get("title") or "").lower() and "1913" in (c.get("title") or ""):
            fp_check = {
                "title": c["title"],
                "old": c.get("coverage") or [],
                "new": new_coverage[i],
            }
            break

    # ─── Quem ganha/perde `available` ───
    gainers = []
    losers = []
    for i, c in enumerate(candidates):
        old_avail = {cov["category_id"] for cov in (c.get("coverage") or []) if cov["status"] == "available"}
        new_avail = {cov["category_id"] for cov in new_coverage[i] if cov["status"] == "available"}
        gained = new_avail - old_avail
        lost = old_avail - new_avail
        if gained:
            gainers.append((c.get("title", "")[:80], list(gained)))
        if lost:
            losers.append((c.get("title", "")[:80], list(lost)))

    # ─── Report markdown ───
    score_dist_old = []
    score_dist_new = []
    for c in candidates:
        for s in c.get("suggested_requirements") or []:
            score_dist_old.append(float(s["score"]))
    for sugg_list in new_suggestions:
        for cid, s in sugg_list:
            score_dist_new.append(s)

    def pct(c: Counter) -> str:
        total = sum(c.values()) or 1
        return ", ".join(f"{k}={v} ({v/total*100:.0f}%)" for k, v in c.most_common())

    lines = [
        "# Match Dry-Run Report",
        "",
        "_Gerado por `analysis/49_match_dryrun.py`. Não modifica YAMLs canônicos._",
        "",
        "## Comparação de scoring",
        "",
        "| Algoritmo | Stage 2 (paper → categoria) | Stage 3 (categoria → item) |",
        "|---|---|---|",
        "| **OLD** | bag-of-words, count de tokens (set intersection) | bag-of-words, weighted title=3 / tags=2 / snippet=1 |",
        "| **NEW** | TF-IDF bigrams (1-2), cosine similarity | TF-IDF bigrams, cosine similarity contra aliases |",
        "",
        "## Distribuição de scores Stage 2",
        "",
        f"- **OLD** (top-1 por candidate, {len(score_dist_old)} obs): min={min(score_dist_old):.1f}, max={max(score_dist_old):.1f}, "
        f"mediana={sorted(score_dist_old)[len(score_dist_old)//2]:.1f}",
        f"- **NEW** ({len(score_dist_new)} obs, IDF-weighted): min={min(score_dist_new):.2f}, max={max(score_dist_new):.2f}, "
        f"mediana={sorted(score_dist_new)[len(score_dist_new)//2]:.2f}" if score_dist_new else "- NEW: empty",
        "",
        "## Distribuição de status Stage 3",
        "",
        f"- **OLD**: {pct(old_status_dist)}",
        f"- **NEW**: {pct(new_status_dist)}",
        "",
        "## Falso positivo crítico: Income Inequality 1913-1998",
        "",
    ]
    if fp_check:
        lines.append(f"**Paper:** {fp_check['title']}")
        lines.append("")
        lines.append("**Antes:**")
        for cov in fp_check["old"]:
            lines.append(f"- `{cov['category_id']}` → status=`{cov['status']}`, score={cov['score']}")
        lines.append("")
        lines.append("**Depois:**")
        if fp_check["new"]:
            for cov in fp_check["new"]:
                lines.append(f"- `{cov['category_id']}` → status=`{cov['status']}`, score={cov['score']}")
        else:
            lines.append("- (sem sugestões → FP eliminado)")
        lines.append("")
    else:
        lines.append("_(paper não encontrado no funnel; pode ter sido filtrado por edu_signal)_")
        lines.append("")

    lines += [
        "## Seed papers (12 do catálogo curado) — categorias top-1 novas",
        "",
    ]
    for paper, sugg, cov in seed_findings:
        lines.append(f"### {', '.join(paper['authors'])} ({paper['year']}) — _{paper['title'][:80]}_")
        lines.append(f"  - **Curado (catálogo):** {', '.join(paper.get('data_requirements') or [])}")
        if sugg:
            top = sugg[0]
            lines.append(f"  - **NEW top-1:** `{top[0]}` (score={top[1]:.2f})")
        else:
            lines.append("  - **NEW:** sem sugestões (edu_signal < 2 ou todos abaixo de threshold)")
        if cov:
            cov_str = ", ".join(f"`{x['category_id']}`={x['status']}" for x in cov)
            lines.append(f"  - **NEW coverage:** {cov_str}")
        lines.append("")

    lines += [
        f"## Ganhadores de `available` ({len(gainers)})",
        "",
    ]
    for title, cats_g in gainers[:10]:
        lines.append(f"- _{title}_ → ganhou: {', '.join(cats_g)}")
    if len(gainers) > 10:
        lines.append(f"... e mais {len(gainers)-10}")
    lines.append("")

    lines += [
        f"## Perdedores de `available` ({len(losers)})",
        "",
    ]
    for title, cats_l in losers[:10]:
        lines.append(f"- _{title}_ → perdeu: {', '.join(cats_l)}")
    if len(losers) > 10:
        lines.append(f"... e mais {len(losers)-10}")
    lines.append("")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
