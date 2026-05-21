---
title: Dados (data.rio) — rio-edu-lab
description: 9.855 itens públicos no portal data.rio. Como funciona a API, como bater contra um paper.
---

# Dados do data.rio

**9.855 itens públicos.** O lab snapshota o portal inteiro e cruza cada paper do catálogo contra ele. Esta página explica como o portal funciona e como você bate dados contra papers por conta própria.

O portal [data.rio](https://www.data.rio/) é uma instância do **ArcGIS Hub** rodando em `pcrj.maps.arcgis.com`. Não há documentação própria do IPP — tudo segue o padrão público da [ArcGIS REST API](https://developers.arcgis.com/rest/). Endpoints validados no [Relatório 02](reports/02_ingestion_probe.md).

## Endpoints principais

| O que você quer | Endpoint | Notas |
|---|---|---|
| Metadados de um grupo | `GET /sharing/rest/community/groups/{group_id}?f=json` | Owner, criação, contagem |
| Listar itens de um grupo | `GET /sharing/rest/content/groups/{group_id}?f=json&num=100&start=1` | Paginado via `nextStart` |
| Metadados completos de um item | `GET /sharing/rest/content/items/{id}?f=json` | Inclui `typeKeywords`, `description`, etc. |
| Baixar arquivo de um item | `GET /sharing/rest/content/items/{id}/data` | Para Excel, PDF, CSV Collection, Image |
| Search global | `GET /sharing/rest/search?q=group:{group_id}&f=json&num=100` | Filtros via `q` |
| Feature Service GeoJSON | URL externa do `pgeo3.rio.rj.gov.br/...` + `?f=geojson` | Vem no campo `url` do item |

Base usada: `https://pcrj.maps.arcgis.com/sharing/rest`. Sem autenticação.

## Padrões por tipo de item

| Tipo | `url` no manifest | Como acessar |
|---|---|---|
| **Microsoft Excel** | vazio | `/items/{id}/data` retorna `application/vnd...spreadsheetml.sheet` |
| **PDF** | vazio | `/items/{id}/data` retorna `application/pdf` |
| **CSV Collection** | vazio | `/items/{id}/data` retorna `application/zip` (CSVs dentro) |
| **Image** | vazio | `/items/{id}/data` retorna `image/png` (geralmente) |
| **Feature Service** | URL do ArcGIS Server externo | Consumir como GeoJSON/MapServer direto |
| **Web Mapping Application** | URL do app | Página web — não baixe |
| **Hub Site Application** | URL do hub | Página web — não baixe |
| **Document Link** | URL externa | Apenas um link curador |

**Importante**: o nome real do arquivo aparece no header `Content-Disposition` da resposta de `/data` (ex.: `filename="3726.xlsx"`). O ID amigável do título fica só no metadata `title`.

## Manifest org-wide

A partir da v0.8, o manifest do laboratório cobre **todo o portal data.rio**, não só o Grupo Educação. Isso permite matchar requisitos de papers contra qualquer fonte de dado público do Rio (transporte para acessibilidade espacial, demografia para SES agregado, etc.), não apenas os datasets pre-tagueados com "educação".

```
org_id    = OlP4dGNtIcnD3RYf (PrefeituraRio)
portal    = https://www.data.rio/
total     = 9855 itens (snapshot 2026-05-18)
fetched   = via /sharing/rest/search?q=orgid:OlP4dGNtIcnD3RYf
script    = analysis/00_fetch_manifest.py
```

Distribuição por tipo (top-10):

| Tipo | Quantidade |
|---|---|
| PDF | 4,073 |
| Image | 1,115 |
| Microsoft Excel | 987 |
| Feature Service | 876 |
| Web Map | 506 |
| Hub Page | 391 |
| Scene Service | 331 |
| Dashboard | 294 |
| Web Mapping Application | 269 |
| Form | 197 |

Para regenerar: `python3 analysis/00_fetch_manifest.py` (~1m30s wall clock, 1 req/0.3s).

### Histórico

Snapshot anterior (até v0.7.x): apenas Grupo Educação (group_id `91117c15dceb41eaa08df881fa9f9310`, 186 itens). Era um filtro útil para o MVP centrado em educação, mas limitava o matching paper↔dado a fontes pré-tagueadas.

## Exemplo: baixar todos os Excels

```python
import json, urllib.request
from pathlib import Path

PORTAL = "https://pcrj.maps.arcgis.com/sharing/rest"
manifest = json.loads(Path("data/manifest.json").read_text(encoding="utf-8"))

dest = Path("data/raw/excel")
dest.mkdir(parents=True, exist_ok=True)

for item in manifest["items"]:
    if item["type"] != "Microsoft Excel":
        continue
    url = f"{PORTAL}/content/items/{item['id']}/data"
    out = dest / f"{item['id']}.xlsx"
    if out.exists():
        continue
    urllib.request.urlretrieve(url, out)
```

Custo total estimado: ~100 MiB (127 arquivos, média ~800 KiB cada).

## Caveats

- **`size` está em bytes**, apesar de aparentar KB em alguma documentação informal.
- **Rate-limiting**: nenhum sinal explícito; mantenha um `sleep` de ~0.3s entre chamadas para não estressar o portal.
- **Versionamento**: o portal não expõe histórico de revisões. Cada `modified` é o último update. Para reprodutibilidade científica, faça snapshot local + DOI Zenodo.
- **Nomes de arquivo**: opacos no portal (`3726.xlsx`). Para nomes humanos, sempre cruze com o `title` do manifest.

## Search global (descobrindo itens fora do Grupo Educação)

Para buscar items em qualquer grupo do portal (ex.: geometria de bairros, que não está no Grupo Educação):

```
GET /sharing/rest/search?q=limite+bairros&num=15&f=json
```

Foi assim que `dc94b29fc3594a5bb4d297bee0c9a3f2` ("Limite de Bairros", IPP) foi achado — Feature Service hospedado em `pgeo3.rio.rj.gov.br/arcgis/rest/services/Cartografia/Limites_administrativos/MapServer/4`. 166 features cobrindo os bairros oficiais do município, incluindo `nome`, `codbairro`, `codra`, `rp`, `cod_rp`. Download via `?f=geojson&where=1=1&outFields=*&outSR=4326`.

## Itens cobertos pelo probe

Validados em produção (HTTP 200, conteúdo esperado):

- `918dd39478594792a9cfa7080b84c0b5` — Excel — Base IPS por RA
- `eafc70844f41438da45a79563fd1d310` — PDF — Estudos Cariocas (PNAD)
- `0a220ea7972449e39a28210dd317f636` — Feature Service — Escolas Municipais
- `7001b082c7174c539bfbf4e8b34c682c` — Document Link — Painel.RIO
- `8644dbd04a0c472faa2b727718a8bcad` — CSV Collection — Taxa de Analfabetismo

Respostas brutas em [`data/raw/probe/`](https://github.com/freirelucas/rio-edu-lab/tree/main/data/raw/probe).

## Link reverso: papers por item

Para cada item do data.rio referenciado pelo catálogo, a página [Papers por item do data.rio](papers-by-data-rio.md) lista quais papers o utilizam e que requisito ele atende. Auto-gerada por `analysis/41_match_requirements.py`.
