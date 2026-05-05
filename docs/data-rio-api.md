# API do data.rio

O portal [data.rio](https://www.data.rio/) é uma instância do **ArcGIS Hub** rodando em `pcrj.maps.arcgis.com`. **Não há documentação própria do IPP** — tudo segue o padrão público da [ArcGIS REST API](https://developers.arcgis.com/rest/). Esta página resume os endpoints úteis para o caso de uso do ACEC-Hub, validados experimentalmente no [Relatório 02](reports/02_ingestion_probe.md).

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

## Grupo Educação

```
group_id  = 91117c15dceb41eaa08df881fa9f9310
group_url = https://www.data.rio/search?groupIds=91117c15dceb41eaa08df881fa9f9310
total     = 186 itens (snapshot 2026-05-05)
```

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

## Itens cobertos pelo probe

Validados em produção (HTTP 200, conteúdo esperado):

- `918dd39478594792a9cfa7080b84c0b5` — Excel — Base IPS por RA
- `eafc70844f41438da45a79563fd1d310` — PDF — Estudos Cariocas (PNAD)
- `0a220ea7972449e39a28210dd317f636` — Feature Service — Escolas Municipais
- `7001b082c7174c539bfbf4e8b34c682c` — Document Link — Painel.RIO
- `8644dbd04a0c472faa2b727718a8bcad` — CSV Collection — Taxa de Analfabetismo

Respostas brutas em [`data/raw/probe/`](https://github.com/freirelucas/rio-edu-lab/tree/main/data/raw/probe).
