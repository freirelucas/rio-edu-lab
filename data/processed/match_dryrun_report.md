# Match Dry-Run Report

_Gerado por `analysis/49_match_dryrun.py`. Não modifica YAMLs canônicos._

## Comparação de scoring

| Algoritmo | Stage 2 (paper → categoria) | Stage 3 (categoria → item) |
|---|---|---|
| **OLD** | bag-of-words, count de tokens (set intersection) | bag-of-words, weighted title=3 / tags=2 / snippet=1 |
| **NEW** | TF-IDF bigrams (1-2), cosine similarity | TF-IDF bigrams, cosine similarity contra aliases |

## Distribuição de scores Stage 2

- **OLD** (top-1 por candidate, 64 obs): min=2.0, max=4.0, mediana=2.0
- **NEW** (141 obs, IDF-weighted): min=5.85, max=40.01, mediana=7.58

## Distribuição de status Stage 3

- **OLD**: available=98 (52%), external=89 (48%)
- **NEW**: available=97 (69%), external=44 (31%)

## Falso positivo crítico: Income Inequality 1913-1998

**Paper:** Income Inequality in the United States, 1913-1998

**Antes:**
- `microdata-student` → status=`external`, score=0.0
- `microdata-household` → status=`external`, score=0.0
- `geometry-schools` → status=`available`, score=13.0

**Depois:**
- (sem sugestões → FP eliminado)

## Seed papers (12 do catálogo curado) — categorias top-1 novas

### Coleman, Campbell, Hobson, McPartland, Mood, Weinfeld, York (1966) — _Equality of Educational Opportunity_
  - **Curado (catálogo):** desempenho por unidade, agrupamento espacial
  - **NEW top-1:** `geometry-schools` (score=6.46)
  - **NEW coverage:** `geometry-schools`=available, `performance-aggregated`=available, `ses-aggregated`=available

## Ganhadores de `available` (36)

- _EQUALITY OF EDUCATIONAL OPPORTUNITY_ → ganhou: performance-aggregated
- _The Bell Curve: Intelligence and Class Structure in American Life._ → ganhou: spatial-partition
- _Schooling in Capitalist America: Educational Reform and the Contradictions of Ec_ → ganhou: geometry-schools, performance-aggregated
- _Home Advantage: Social Class and Parental Intervention in Elementary Education_ → ganhou: geometry-schools, performance-aggregated
- _High school achievement : public, Catholic, and private schools compared_ → ganhou: ses-aggregated
- _Estimation of Educational Borrowing Constraints Using Returns to Schooling_ → ganhou: geometry-schools, performance-aggregated
- _A Decomposition Analysis of the Trend in UK Income Inequality_ → ganhou: geometry-schools
- _Schooling and Economic Well-Being: The Role of Nonmarket Effects_ → ganhou: performance-aggregated
- _The quality of schooling : quantity alone is misleading_ → ganhou: geometry-schools
- _Teacher Characteristics and Gains in Student Achievement: Estimation Using Micro_ → ganhou: performance-aggregated
... e mais 26

## Perdedores de `available` (36)

- _Income Inequality in the United States, 1913-1998_ → perdeu: geometry-schools
- _Handbook of Labor Economics_ → perdeu: geometry-schools, geometry-neighborhoods
- _The Constant Flux: A Study of Class Mobility in Industrial Societies._ → perdeu: geometry-schools, geometry-neighborhoods
- _The Black-White Test Score Gap_ → perdeu: performance-aggregated
- _Home Advantage: Social Class and Parental Intervention in Elementary Education_ → perdeu: ses-aggregated
- _Socioeconomic Status Modifies Heritability of IQ in Young Children_ → perdeu: ses-aggregated
- _Trends in educational assortative marriage from 1940 to 2003_ → perdeu: geometry-schools
- _Why Do Some Occupations Pay More than Others? Social Closure and Earnings Inequa_ → perdeu: geometry-schools, geometry-neighborhoods
- _Estimation of Educational Borrowing Constraints Using Returns to Schooling_ → perdeu: ses-aggregated
- _Investing in Children: Changes in Parental Spending on Children, 1972–2007_ → perdeu: geometry-schools, geometry-neighborhoods
... e mais 26
