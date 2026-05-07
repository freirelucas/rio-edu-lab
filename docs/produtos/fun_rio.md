---
title: FUN-Rio — trajetórias 5º→9º ano por pseudocoorte
description: Mare (1980) + Reardon & Owens (2014) aplicado ao IDEB municipal carioca por bairro.
---

# ⏳ FUN-Rio

> Trajetórias educacionais de pseudocoortes 5º→9º ano por bairro. **87% das 768 transições observadas pioram.** O slope −0.53 contra IDEB inicial **refuta o efeito Mateus**: bairros melhores caem mais.

[![paper](https://img.shields.io/badge/paper--base-Mare_1980-008572)](https://doi.org/10.2307/2287436)
[![paper](https://img.shields.io/badge/Reardon%20%26%20Owens%202014-008572)](https://doi.org/10.1146/annurev-soc-071913-043152)
[![relatório](https://img.shields.io/badge/leitura_t%C3%A9cnica-relat%C3%B3rio_12-grey)](../reports/12_fun_rio.md)

<div class="compare-grid" markdown>

<div class="compare-paper" markdown>
### Mare (1980) + Reardon & Owens (2014)

**Mare (1980)**: introduz o **modelo de transições escolares** — desigualdade educacional não é uma variável só, mas a probabilidade *condicional* de avançar para a próxima etapa, dado que se chegou na atual. Cada transição (entrar na escola, completar fundamental, entrar no médio, etc.) tem seu próprio gradiente social.

**Reardon & Owens (2014)**: revisão de 60 anos pós-Brown sobre **segregação escolar e gradientes de desempenho**. Achado central: a segregação racial baixou após Brown, mas a segregação por origem socioeconômica subiu. A trajetória educacional reflete a stratificação residencial.

**Achado conjunto**: a desigualdade não é estática — ela se acumula (ou se reorganiza) ao longo do percurso escolar. **Olhar só o estado final perde a maior parte da história**.
</div>

<div class="compare-rio" markdown>
### O que achamos no Rio

**O que é**: aplicamos o conceito de "trajetória" usando **pseudocoorte** — a turma que faz IDEB 5º ano em ano T é tratada como aproximação da mesma turma medida no 9º ano em T+4. Com IDEB bienal, há 7 pseudocoortes possíveis (2007→2011 a 2019→2023).

**Métrica**: `Δ[bairro, T] = IDEB_9º[bairro, T+4] − IDEB_5º[bairro, T]`.

**Achados (768 pseudocoortes em 124 bairros)**:

- **Δ médio = −0.65** (mediana −0.67)
- **87%** das pseudocoortes têm Δ &lt; 0
- **Slope −0.53** vs IDEB-5 base (correlação −0.53)

O sinal do slope é **oposto ao efeito Mateus**: bairros que começam mais altos no 5º caem mais ao chegar no 9º. Documentamos transparentemente esse achado contra-intuitivo.
</div>

</div>

## Comparação

Mare e Reardon & Owens descrevem **acúmulo desigual** ao longo do percurso. Nosso achado é parcialmente compatível e parcialmente surpreendente:

- **Compatível**: confirma que olhar só o final perde estrutura. Δ médio 5º→9º é sólido (−0.65, em quase 9 de cada 10 pseudocoortes).
- **Surpreendente**: o gradiente é **regressivo**. Bairros com IDEB-5 mais alto (Zona Sul, parte da Zona Norte) caem mais que os de IDEB-5 baixo. O efeito acumulativo acontece, mas ao contrário do esperado.

A explicação mais provável (que **não conseguimos separar** com os dados públicos disponíveis):

- **Migração para escola privada no 6º ano**: famílias com mais recursos retiram filhos da rede municipal entre 5º e 6º. O cohorte municipal do 9º ano fica enviesado para baixo, especialmente em zonas onde a migração é factível.
- **Regressão à média estatística**: bairros com IDEB-5 muito alto são extremos amostrais, com tendência matemática a regredir para a média.
- **Perda diferencial de qualidade**: escolas públicas pré-bem-avaliadas se deterioram quando perdem corpo discente.

Os 3 mecanismos podem co-existir. **Separar requer microdado individual** (transferências, evasão, matrícula privada por bairro) — não-disponível no data.rio.

## Distribuição completa

![FUN-Rio dist](../reports/_assets/12_fun_rio_dist.png)

Esquerda: histograma das 768 pseudocoortes. Pico claramente abaixo de zero. Direita: scatter Δ vs IDEB-5; slope −0.53 visível como nuvem inclinada.

## Mapa do Δ médio

![FUN-Rio map](../reports/_assets/12_fun_rio_map.png)

Cinza/vermelho domina — perda generalizada espacialmente. Bairros azuis (que **melhoram** entre 5º e 9º) são minoria.

## Caveats

- **Pseudocoorte ≠ coorte real**. O 5º ano de 2007 não é estritamente o mesmo grupo do 9º de 2011. Confound documentado acima.
- **Janela bienal do IDEB** mistura 2 ciclos. Versão futura com microdado anual reduziria isso.
- **Apenas rede municipal**. Migração para privada é o sinal econômico real; nós só vemos o resultado em dado municipal.
- **Slope é correlacional**, não causal. Não estamos identificando "perda de qualidade"; estamos identificando "mudança no IDEB médio do cohorte municipal" entre 5º e 9º.

## Reproduzir

```bash
python3 analysis/10_theil_ideb.py     # IDEB 5º
python3 analysis/15_anos_finais.py    # IDEB 9º
python3 analysis/19_fun_rio.py        # pseudocoortes
```

## Referências

- Mare, R. D. (1980). "Social Background and School Continuation Decisions". *Journal of the American Statistical Association* 75(370). [DOI](https://doi.org/10.2307/2287436)
- Reardon, S. F.; Owens, A. (2014). "60 Years After Brown: Trends and Consequences of School Segregation". *Annual Review of Sociology* 40. [DOI](https://doi.org/10.1146/annurev-soc-071913-043152)

## Continue

<div class="grid cards" markdown>

-   [:material-map: Mapa interativo](../mapa.md)
-   [:material-format-list-bulleted: Bairros prioritários (combina FUN-Rio + PM-12)](../bairros-prioritarios.md)
-   [:material-chart-line: PM-12 (alocação de escolas)](pm_12.md)
-   [:material-text-box-outline: Relatório técnico](../reports/12_fun_rio.md)

</div>
