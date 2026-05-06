# 05 — Corpus dos PDFs (Estudos Cariocas et al.)

Os 35 PDFs do Grupo Educação são publicações do IPP (Instituto Pereira Passos) em quatro coleções editoriais distintas. Este relatório lê o conteúdo real de cada arquivo (texto da 1ª página + total de páginas) e classifica por coleção.

## Visão geral

| Métrica | Valor |
| :--- | :--- |
| Arquivos | 35 |
| Tamanho total em disco | 63.0 MiB |
| Páginas totais | 717 |
| Páginas por arquivo (p50 / p90) | 14 / 33 |
| Com camada de texto extraível | 25/35 (71%) |
| Criptografados | 0 |
| Erros de parse | 0 |

## Distribuição por coleção

| Coleção | Arquivos | Views totais | Páginas totais |
| :--- | ---: | ---: | ---: |
| Rio Estudos | 14 | 7,246 | 175 |
| Estudos Cariocas | 8 | 4,999 | 186 |
| Notas Técnicas IPP | 6 | 3,626 | 120 |
| Cadernos do Rio | 4 | 2,777 | 69 |
| (outros) | 3 | 947 | 167 |

## Janela temporal das publicações

Anos detectados (no título ou na 1ª página): **2001–2026** (35 de 35 PDFs com ano detectável)

## Top 10 por visualizações

| Views | Páginas | Coleção | Ano | Título |
| ---: | ---: | :--- | ---: | :--- |
| 885 | 105 | Estudos Cariocas | 2008 | COLEÇÃO ESTUDOS CARIOCAS - A Cidade do Rio de Janeiro n |
| 872 | 15 | Cadernos do Rio | 2024 | Cadernos do Rio - Prévias do Censo: Dinâmica Demográfic |
| 855 | 15 | Cadernos do Rio | 2013 | CADERNOS DO RIO - Educação (Junho/2013) |
| 755 | 16 | Rio Estudos | 2001 | RIO ESTUDOS Nº 26 - A cultura da paz em resposta à viol |
| 727 | 8 | Estudos Cariocas | 2002 | COLEÇÃO ESTUDOS CARIOCAS - O analfabetismo na Cidade do |
| 724 | 32 | Notas Técnicas IPP | 2014 | NOTA TÉCNICA 31 - Pesquisa Nacional de Saúde Escolar (P |
| 682 | 15 | Notas Técnicas IPP | 2013 | NOTA TÉCNICA 25 - Avaliação das crianças de creches mun |
| 668 | 33 | Rio Estudos | 2001 | RIO ESTUDOS Nº 03 - Rio: educação, causas e efeitos (Ma |
| 653 | 14 | Estudos Cariocas | 2005 | COLEÇÃO ESTUDOS CARIOCAS - Os dirigentes das escolas mu |
| 653 | 8 | Rio Estudos | 2002 | RIO ESTUDOS Nº 72 - O futuro da sociedade e o presente  |

## Arquivos com problema (sem texto extraível ou erro)

| Páginas | Erro / motivo | Título |
| ---: | :--- | :--- |
| 13 | (sem camada de texto — provável scanned image) | RIO ESTUDOS Nº 170 - Ações Culturais para crianças e adolesc |
| 19 | (sem camada de texto — provável scanned image) | Cadernos do Rio - Prévias do Censo: Cor ou Raça (Dezembro/20 |
| 5 | (sem camada de texto — provável scanned image) | RIO ESTUDOS Nº 56 - Como se tornar um Diretor-líder  (Junho/ |
| 4 | (sem camada de texto — provável scanned image) | RIO ESTUDOS Nº 227 - Os precursores da educação nova (Novemb |
| 20 | (sem camada de texto — provável scanned image) | Cadernos do Rio - Prévias do Censo: Sexo e Idade (Dezembro/2 |
| 15 | (sem camada de texto — provável scanned image) | Cadernos do Rio - Prévias do Censo: Dinâmica Demográfica dos |
| 13 | (sem camada de texto — provável scanned image) | RIO ESTUDOS Nº 88 - Município prioriza ações para jovens (Ja |
| 8 | (sem camada de texto — provável scanned image) | RIO ESTUDOS Nº 72 - O futuro da sociedade e o presente da ed |
| 5 | (sem camada de texto — provável scanned image) | RIO ESTUDOS Nº 38 - Pesquisa da CNTE: violência dentro da es |
| 14 | (sem camada de texto — provável scanned image) | RIO ESTUDOS Nº 36 - A Educação Infantil no Brasil entre 1994 |

## Reprodutibilidade

```bash
pip install pypdf
python3 analysis/07_download_pdfs.py    # baixa data/raw/pdf/*.pdf (~100 MiB)
python3 analysis/08_pdf_corpus.py       # gera CSV + textos da 1ª página
python3 analysis/09_report_pdf_corpus.py
```

Textos completos da 1ª página de cada PDF ficam em `data/raw/pdf/_first_pages/{id}.txt` (gitignored, mas reproduzíveis), úteis para grep manual quando precisar achar uma metodologia citada.
