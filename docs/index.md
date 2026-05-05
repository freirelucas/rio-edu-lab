# rio-edu-lab

> Laboratório exploratório sobre o Grupo Educação do data.rio.

Sandbox de pesquisa que precede e alimenta o produto **ACEC-Hub** — Atlas Cibernético da Educação Carioca. Aqui ficam as análises do inventário, probes de ingestão e relatórios reprodutíveis. A arquitetura-alvo do produto está versionada em [`reference/acec-hub/`](https://github.com/freirelucas/rio-edu-lab/tree/main/reference/acec-hub).

## Em uma linha

O Grupo Educação do data.rio publica **186 itens** (1991–2024) — séries históricas, mapas, painéis. Este lab destrincha esse acervo, valida o caminho de ingestão e produz inputs para os produtos do ACEC-Hub.

## Onde começar

| Quero… | Vá para |
|---|---|
| Entender o acervo | [Relatório 01 — EDA do manifest](reports/01_manifest_eda.md) |
| Entender como acessar os dados | [API do data.rio](data-rio-api.md) |
| Ver se o pipeline de ingestão funciona | [Relatório 02 — Probe de ingestão](reports/02_ingestion_probe.md) |
| Ler o produto-alvo | [README do ACEC-Hub](https://github.com/freirelucas/rio-edu-lab/blob/main/reference/README-acec-hub.md) |

## Achados-chave (até agora)

- **186 itens, dominados por séries históricas em Excel** (127, ~68%).
- **89% das visualizações** se concentram em apenas **5 itens interativos** — confirma o gap que o ACEC-Hub propõe ocupar.
- **170 itens "sem URL" no manifest não estão quebrados**: o probe confirmou que a API do ArcGIS Hub serve o conteúdo via `/sharing/rest/content/items/{id}/data` mesmo quando o campo `url` está vazio.
- **~200 MiB para todos os binários** — viável cachear localmente sem DVC ou git-lfs.

## Reproduzir

```bash
git clone https://github.com/freirelucas/rio-edu-lab.git
cd rio-edu-lab

# Tudo aqui usa só a stdlib do Python 3.10+
python3 analysis/01_manifest_eda.py    # gera CSV enriquecido + relatório 01
python3 analysis/02_ingestion_probe.py # probe da API + relatório 02
```

Para rodar o site localmente:

```bash
pip install mkdocs-material
mkdocs serve
```

## Licença

Código MIT. Dados derivados CC BY 4.0. Dados brutos seguem licença original do data.rio / IPP.
