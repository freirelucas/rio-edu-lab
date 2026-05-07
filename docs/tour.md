---
title: Tour de 5 minutos — rio-edu-lab
description: Em 5 painéis, o que descobrimos aplicando 4 papers seminais ao IDEB municipal do Rio.
hide:
  - toc
---

# Tour de 5 minutos

Cinco painéis, cada um com um chart interativo. Tempo total de leitura: ~5 min. Ao final, link para o paper consolidado e para os 4 produtos.

<section class="tour-slide" markdown>

## <span class="tour-slide-num">1</span> O problema: granularidade de RA

Painéis municipais costumam reportar IDEB por **Região Administrativa** (RA, 33 unidades). A média da RA suaviza extremos. Em 2023, quase todas as RAs estão em IDEB ≥ 5.5 — parece que está tudo razoavelmente bem.

<div data-chart="../_assets/charts/tour_slide_1.json"></div>

[Próximo →](#2-a-descoberta-mesmo-dado-mais-fino){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">2</span> A descoberta: mesmo dado, mais fino

Mesmos números, mesma escala de cor — mas agora cada bairro herda o IDEB para sua célula H3. **Bolsões vermelhos pulam aos olhos**: bairros com IDEB &lt; 5.5 dentro de RAs cuja média parece "ok".

<div data-chart="../_assets/charts/tour_slide_2.json"></div>

A decomposição **Theil-T** (Theil, 1967) confirma que essa heterogeneidade é majoritária: 66% da desigualdade total do IDEB municipal está **dentro das RAs**, não entre.

[Próximo →](#3-robustez-em-3-direcoes){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">3</span> Robustez em 3 direções

O achado não é artefato da escolha de indicador, da etapa escolar, ou de pesos arbitrários. Em 6 séries diferentes, a parcela within-RA fica entre 60% e 80%.

<div data-chart="../_assets/charts/tour_slide_3.json"></div>

A linha pontilhada em 50% é a "paridade" — abaixo dela, a desigualdade between-RA dominaria. Nenhuma série a cruza.

[Próximo →](#4-mecanismos-estruturais){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">4</span> Mecanismos estruturais

Dois sinais ortogonais explicam parte da heterogeneidade:

- **Lei de escala** (Bettencourt et al., 2010 — adaptado): infra de escolas escala com matrícula como `escolas = 0.008 · matrículas^0.77`. Sublinear (β &lt; 1) significa que **bairros maiores têm desproporcionalmente menos escolas por aluno**.
- **Trajetórias** (Mare 1980 + Reardon & Owens 2014 — adaptado): em 768 pseudocoortes 5º→9º ano, a média do delta é **−0.65** (87% das coortes pioram).

<div data-chart="../_assets/charts/tour_slide_4.json"></div>

Os dois mecanismos apontam para a mesma direção: a infraestrutura municipal não acompanha a demanda nas zonas que mais precisam, e a qualidade educacional cai durante o ensino fundamental II nessas mesmas zonas.

[Próximo →](#5-quem-precisa-mais){ .tour-next }

</section>

<section class="tour-slide" markdown>

## <span class="tour-slide-num">5</span> Quem precisa mais

Cruzando os dois sinais (déficit de escola por SAMI + queda de IDEB por Δ FUN-Rio), os 15 bairros prioritários:

<div data-chart="../_assets/charts/tour_slide_5.json"></div>

!!! warning "Confound importante"
    Bairros de Zona Sul (Humaitá, Leblon) aparecem nos primeiros lugares **porque** a sua coorte 5º→9º cai mais — provavelmente porque os alunos com mais recursos migram para escola privada no 6º ano, deixando o cohorte municipal do 9º enviesado para baixo. Não é o mesmo problema de Zona Norte/Oeste, onde a migração privada é menor e o sinal reflete subinvestimento real. A lista completa em [Bairros prioritários](bairros-prioritarios.md) traz a separação por mecanismo.

## Continue

<div class="grid cards" markdown>

-   [:material-map: Mapa interativo](mapa.md)
-   [:material-format-list-bulleted: Lista de bairros prioritários](bairros-prioritarios.md)
-   [:material-flask-outline: Paper consolidado](paper/hex_edu_manuscript.md)
-   [:material-package-variant: 4 produtos detalhados](produtos/index.md)

</div>

</section>
