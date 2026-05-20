---
title: Achados — rio-edu-lab
description: 3 achados sobre educação no Rio. Cada um é replicação literal de paper acadêmico publicado, aplicado aos dados públicos do município.
---

# Achados

**3 papers replicados. 3 achados sobre educação no Rio.** Cada um é a aplicação literal de um método publicado contra dados públicos do município. Sem opinião, sem extrapolação — o que o número diz, dizemos. O que falta, declaramos.

## Desigualdade — 66% da variância do IDEB está dentro dos bairros { #desigualdade }

**Paper:** Theil, H. (1967). *Economics and Information Theory*. North-Holland Pub. Co. · [DOI](https://lccn.loc.gov/67025784)

A intuição comum é que a desigualdade educacional carioca é "Zona Sul × Zona Oeste" — uma diferença grande **entre** regiões. A decomposição Theil-T, aplicada literalmente ao IDEB municipal por bairro, mostra o oposto:

> **66% da variância do IDEB está dentro das Regiões Administrativas, não entre.**
> Coropléticos por RA escondem a maior parte do problema.

Robusto em **6 séries × 9 anos** (5º e 9º anos, ponderado por matrícula, Aprovação/SAEB/IDEB separadamente): a parcela within-RA fica entre 59% e 73%. Nenhuma série cruza a paridade 50%.

**Onde isso fica claro:** [Mapa interativo](mapa.md) mostra a variação bairro-a-bairro dentro de cada RA — bolsões de baixo desempenho cercados de bairros médios, em regiões que aparentam ser monolíticas no choropleth tradicional.

**Como auditar:**
- [Mini-page do paper](papers/theil-1967-economics.md) — bibliografia + requisitos × cobertura
- [Relatório 06 — Decomposição Theil do IDEB por bairro](reports/06_theil_ideb.md)
- [Relatório 11 — Theil 3-níveis (AP/RA/bairro)](reports/11_thesha_rio.md)
- [HEX-EDU — produto técnico](produtos/hex_edu.md)
- Código: `analysis/10_theil_ideb.py`, `analysis/18_thesha_rio.py`

---

## Acessibilidade — AP 3 lidera, não a Zona Sul { #acessibilidade }

**Paper:** Pereira, R. H. M., Braga, C. K. V., Serra, B., & Nadalin, V. (2019). *Desigualdades socioespaciais de acesso a oportunidades nas cidades brasileiras, 2019*. IPEA Texto para Discussão 2535. · [DOI/handle](https://hdl.handle.net/10419/240730)

O paper propõe uma métrica de acessibilidade ponderada pela qualidade do destino — não basta ter uma escola perto, ela precisa ser boa. Aplicado ao Rio (versão parcial: haversine + IDEB, sem isócronas reais):

> **AP 3 (Zona Norte) lidera o ranking de acesso ponderado por IDEB com 113.
> AP 4 (Jacarepaguá/Barra) fica em último com 29.**

Coropléticos por AP escondem variação intra-zona: AP 3 tem alta densidade de escolas medianas; Zona Sul tem escolas excelentes, mas espalhadas e poucas — por isso seu acesso ponderado fica abaixo.

**Como auditar:**
- [Mini-page do paper](papers/pereira-2019-ipea.md)
- [Relatório 14 — Acessibilidade Pereira-style](reports/14_acessibilidade.md)
- [HEX-EDU — produto técnico](produtos/hex_edu.md)
- Código: `analysis/13_hex_edu_static.py`, `analysis/14_hex_edu_folium.py`

**Limites da replicação atual:** versão parcial. Pereira et al. usam isócronas reais via OpenTripPlanner (rede viária + GTFS); aqui usamos distância haversine como proxy. A versão completa exige adicionar `travel-network` (OSM + GTFS RioCard) — categoria hoje **external** no funil.

---

## Vulnerabilidade — riqueza prediz educação só parcialmente { #vulnerabilidade }

**Paper:** Reardon, S. F. (2011). *The widening academic-achievement gap between the rich and the poor*. In G. J. Duncan & R. J. Murnane (Eds.), *Whither Opportunity?* (pp. 91–116). Russell Sage Foundation. · [URL](https://cepa.stanford.edu/content/widening-academic-achievement-gap-between-rich-and-poor-new-evidence-and-possible)

A hipótese clássica de Reardon (validada nos EUA): há um gradiente claro entre status socioeconômico (SES) e desempenho escolar. Aplicado ao Rio (IDS Censo 2010 × IDEB 2023 por bairro, 144 bairros):

> **O gradiente existe (Pearson +0,40) mas é modesto: R²=0,16.
> 39% dos bairros estão em quadrantes não-concordantes:
> 22% resilientes (baixo SES, bom IDEB), 17% sub-performando (bom SES, baixo IDEB).**

Quase metade dos bairros do Rio **não** obedece o gradiente esperado. A relação existe — mas explica menos da metade da variância.

**Como auditar:**
- [Mini-page do paper](papers/reardon-2011-whither.md)
- [Relatório 15 — IDS × IDEB gradiente](reports/15_vuln_edu.md)
- [VULN-EDU — produto técnico](produtos/vuln_edu.md)
- [Bairros prioritários](bairros-prioritarios.md) — cruzamento com outros sinais
- Código: `analysis/22_vuln_edu.py`

**Limites da replicação atual:** IDS é granularidade de Região de Planejamento (RP) — interpolado pra bairro via vizinhança. Versão futura usa INSE 2023 direto por escola, quando incorporado ao manifest data.rio.

---

## Próximos achados em construção

6 papers no catálogo com dados cobertos e replicação leve planejada:

<div class="paper-grid">

<a class="paper-card status-pending" href="papers/coleman-1966-eeo/">
  <h4>Coleman et al. (1966)</h4>
  <p class="meta">2.776 citações · sociologia educacional</p>
  <p class="insight">A variância entre alunos vs dentro de escolas — clássico estudo que reorientou a política educacional dos EUA.</p>
  <span class="cta">Catalogado →</span>
</a>

<a class="paper-card status-pending" href="papers/hanushek-1986-jel/">
  <h4>Hanushek (1986)</h4>
  <p class="meta">2.715 citações · função-produção</p>
  <p class="insight">Survey clássico: input educacional (gasto, recursos) prediz pouco do output. Replicar contra IDEB × despesa/aluno municipal.</p>
  <span class="cta">Catalogado →</span>
</a>

<a class="paper-card status-pending" href="papers/hoxby-2000-aer/">
  <h4>Hoxby (2000)</h4>
  <p class="meta">1.105 citações · school choice</p>
  <p class="insight">Variação geográfica como IV pra efeitos de competição entre escolas.</p>
  <span class="cta">Catalogado →</span>
</a>

<a class="paper-card status-pending" href="papers/soares-andrade-2006/">
  <h4>Soares & Andrade (2006)</h4>
  <p class="meta">3 citações · sociologia · 🇧🇷</p>
  <p class="insight">Decomposição de variância em escolas de BH — replicável no Rio com microdados SAEB.</p>
  <span class="cta">Catalogado →</span>
</a>

<a class="paper-card status-pending" href="papers/alves-soares-2013/">
  <h4>Alves & Soares (2013)</h4>
  <p class="meta">101 citações · política educacional · 🇧🇷</p>
  <p class="insight">IDEB confunde efeito-escola com efeito-NSE. Propõe ajuste por contexto socioeconômico.</p>
  <span class="cta">Catalogado →</span>
</a>

<a class="paper-card status-pending" href="papers/reardon-owens-2014/">
  <h4>Reardon & Owens (2014)</h4>
  <p class="meta">503 citações · segregação escolar</p>
  <p class="insight">Medidas de segregação escolar (raça, SES) nos EUA — adaptar pra rede municipal do Rio.</p>
  <span class="cta">Catalogado →</span>
</a>

</div>

[Ver catálogo completo →](papers/index.md){ .md-button } [Como o funil funciona →](index.md#como-o-funil-funciona){ .md-button }
