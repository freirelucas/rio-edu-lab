---
title: Para gestores — política educacional municipal baseada em evidência
description: Síntese dirigida a gestores da SME-Rio, IPP e prefeitura. Achados, implicações de política e lista de bairros prioritários cruzando os 2 produtos do lab.
---

# Para gestores públicos

> Se você é responsável por política educacional municipal — SME-Rio, IPP, gabinete da prefeitura — leia esta página primeiro. Os dois produtos ativos do lab (HEX-EDU + VULN-EDU) convergem em **três decisões operacionais**: granularidade de bairro, lista de 15 bairros prioritários, e a distinção resilientes / sub-performance / vulneráveis.

<div class="how-to-read" markdown>
### Como ler esta página

Três blocos, em ordem de uso. **(1)** O achado-base que justifica a granularidade de bairro. **(2)** Os 15 bairros prioritários cruzando déficit de escola e queda de IDEB. **(3)** Os insights consolidados de HEX-EDU (acesso ponderado) e VULN-EDU (quadrantes IDS × IDEB). Cada bloco linka para o relatório técnico que documenta o método e os dados.
</div>

<div class="big-num-grid">
  <div class="big-num"><span class="num">66%</span><span class="label">da desigualdade do IDEB está <em>dentro</em> das RAs, não entre — escala administrativa errada</span></div>
  <div class="big-num"><span class="num">15</span><span class="label">bairros prioritários cruzando déficit de escolas + queda de IDEB</span></div>
  <div class="big-num"><span class="num">39%</span><span class="label">dos bairros estão em quadrantes não-concordantes — investir em SES não basta</span></div>
</div>

## 1. O achado-base: granularidade de bairro é a escala correta

O painel municipal típico reporta IDEB por **Região Administrativa** (33 RAs). Em 2023, quase todas as RAs estão em IDEB ≥ 5,5 — parece tudo razoavelmente bem. **A decomposição Theil-T sobre IDEB por bairro mostra que 66% da variância está dentro das RAs**, não entre. Coropléticos por RA suavizam a heterogeneidade real.

Implicação operacional: política educacional municipal precisa olhar **por bairro** (163 unidades), não por RA. A escala administrativa atual mascara a maior parte do problema.

[Ver Relatório 06 →](reports/06_theil_ideb.md){ .md-button }
[Ver mapa interativo →](mapa.md){ .md-button }

## 2. Quinze bairros prioritários

Cruzamento de dois sinais ortogonais do MVP-1:

- **SAMI** ([Relatório 13](reports/13_pm_12.md)) — desvio da lei de escala. SAMI &lt; 0 = bairro tem **menos escolas** que o esperado pelo seu volume de matrícula (sub-servido em infraestrutura).
- **Δ médio** ([Relatório 12](reports/12_fun_rio.md)) — média da queda de IDEB do 5º para o 9º ano em pseudocoortes. Δ &lt; 0 = a turma piora ao longo do fundamental.

Bairros com **SAMI negativo E Δ negativo** são duplamente prioritários: infraestrutura defasada e qualidade caindo no ciclo.

<div data-chart="_assets/charts/tour_slide_5.json"></div>

!!! warning "Distinção importante (confound de migração privada)"
    Alguns bairros que aparecem no topo (Humaitá, Leblon, Jardim Botânico) provavelmente refletem **migração para escola privada** entre 5º e 9º ano: alunos com mais recursos saem da rede municipal no 6º ano, e o cohorte municipal do 9º fica enviesado para baixo. Esse é um problema **real** mas de natureza diferente do subinvestimento estrutural (Pavuna, Pilares, Curicica). Use a coluna "AP" como heurística:

    - **AP 2** (Zona Sul) → mais provável confound de privatização.
    - **AP 3 e 5** (Zona Norte / Oeste) → mais provável subinvestimento estrutural.

A lista completa de 115 bairros está em [`data/processed/bairros_prioritarios.csv`](https://github.com/freirelucas/rio-edu-lab/blob/main/data/processed/bairros_prioritarios.csv).

[Ver lista completa →](bairros-prioritarios.md){ .md-button }

## 3. Insights consolidados dos dois produtos

### HEX-EDU — acesso ponderado por IDEB

<div class="policy-callout" markdown>
  <header>
    <span class="icon" aria-hidden="true">📐</span>
    <h3>HEX-EDU: acessibilidade Pereira-style</h3>
  </header>
  <div class="body" markdown>
  <div class="cell" markdown>
**Achado**

AP 3 (Zona Norte) entrega o **maior acesso ponderado** por IDEB do município (média 113). Zona Sul fica em 59 por baixa densidade de escolas. AP 4 (Barra/Jacarepaguá) em 29.
  </div>
  <div class="cell" markdown>
**Implicação**

Planejamento educacional precisa combinar **qualidade** e **densidade**. Olhar só média de IDEB por região esconde vazios de oferta em áreas onde a qualidade existe mas a opção é distante.
  </div>
  <div class="cell" markdown>
**Ações**

1. Expandir rede em **AP 4** — poucas escolas elegíveis acima da mediana de IDEB.
2. Auditar **Centro (AP 1)** — 2º maior acesso ponderado (96).
3. Combinar com VULN-EDU para identificar baixo acesso × alta vulnerabilidade.
  </div>
  </div>
  <footer><a href="../reports/14_acessibilidade/">Como auditar: relatório 14 + <code>analysis/26_hex_accessibility.py</code> →</a></footer>
</div>

### VULN-EDU — gradiente IDS × IDEB por bairro

<div class="policy-callout" markdown>
  <header>
    <span class="icon" aria-hidden="true">🧭</span>
    <h3>VULN-EDU: quadrantes socioeconômico × educacional</h3>
  </header>
  <div class="body" markdown>
  <div class="cell" markdown>
**Achado**

Gradiente SES × IDEB existe (Pearson +0,40) mas é **modesto** — IDS explica só 16% da variância. **39% dos bairros estão em quadrantes não-concordantes**: 22% resilientes + 17% sub-performando.
  </div>
  <div class="cell" markdown>
**Implicação**

Investir onde o SES é baixo **não basta** para subir o IDEB. E bairros de SES alto não necessariamente entregam IDEB alto na rede municipal — provável migração à rede privada.
  </div>
  <div class="cell" markdown>
**Ações**

1. Estudar os **32 bairros resilientes** (Q2): Vargem Grande, periferia de Jacarepaguá.
2. Priorizar os **5 mais vulneráveis**: Santo Cristo, Sampaio, Gardênia Azul, Parque Columbia, Acari.
3. Auditar os **25 em sub-performance** (Q3): Maria da Graça, partes da Tijuca.
  </div>
  </div>
  <footer><a href="../reports/15_vuln_edu/">Como auditar: relatório 15 + <code>analysis/29_vuln_edu.py</code> →</a></footer>
</div>

## Próximos passos para gestores

- **Operacionalizar a lista de 15 bairros prioritários** como pauta de uma reunião SME-Rio + IPP. Os bairros estão no CSV, com SAMI e Δ FUN-Rio separados — permite combinar como preferir.
- **Aprender com os 32 bairros resilientes** (VULN-EDU Q2): visitas técnicas, mapeamento de boas práticas, replicação em bairros vulneráveis.
- **Cruzar com IPS por RA (painel temporal)** quando o IDS 2022 sair — a v0.2 do VULN-EDU re-roda automaticamente.
- **Citar o lab** em diagnósticos técnicos via [DOI Zenodo](https://doi.org/10.5281/zenodo.20060620). Dados derivados são CC BY 4.0.

## Continue

<div class="grid cards" markdown>

-   [:material-map: Mapa interativo](mapa.md)
-   [:material-package-variant: Produtos detalhados](produtos/index.md)
-   [:material-format-list-bulleted: Lista completa de bairros](bairros-prioritarios.md)
-   [:material-book-open-variant: Investigação técnica](investigacao.md)

</div>
