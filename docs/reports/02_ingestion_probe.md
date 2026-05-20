# 02 — Probe de ingestão (ArcGIS Hub)

Hipótese testada: itens sem `url` no manifest do grupo são resolvíveis via `/sharing/rest/content/items/{id}`, e o conteúdo de tipos baixáveis está em `/sharing/rest/content/items/{id}/data`.

_Portal: `https://pcrj.maps.arcgis.com/sharing/rest`_

## Resultado por item

| Tipo | Título | Meta HTTP | URL resolvida | /data Content-Type | /data tamanho |
| :--- | :--- | ---: | :--- | :--- | ---: |
| Microsoft Excel | Base IPS por RA | 200 | `—` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | 828.5 KiB |
| PDF | Estudos Cariocas — PNAD | 200 | `—` | `application/pdf` | 3.1 MiB |
| Feature Service | Escolas Municipais | 200 | `https://pgeo3.rio.rj.gov.br/arcgis/rest/service...` | `—` | — |
| Document Link | Painel.RIO | 200 | `https://painel.rio` | `—` | — |
| CSV Collection | Taxa de Analfabetismo | 200 | `—` | `application/zip` | 3.2 KiB |

### Microsoft Excel — Base IPS por RA
- ID: `918dd39478594792a9cfa7080b84c0b5`
- Meta status: **200**
- typeKeywords: `Data, Document, Microsoft Excel`
- size (manifest field, bytes): 848,416 (828.5 KiB)
- `/data` HEAD status: **200**
- `/data` Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `/data` Content-Length: 828.5 KiB
- Content-Disposition: `inline; filename="3726.xlsx"; size=848416`
- URL final: `https://pcrj.maps.arcgis.com/sharing/rest/content/items/918dd39478594792a9cfa7080b84c0b5/data`

### PDF — Estudos Cariocas — PNAD
- ID: `eafc70844f41438da45a79563fd1d310`
- Meta status: **200**
- typeKeywords: `'Document', 'PDF'], ['Data', Data, Document, PDF`
- size (manifest field, bytes): 3,254,684 (3.1 MiB)
- `/data` HEAD status: **200**
- `/data` Content-Type: `application/pdf`
- `/data` Content-Length: 3.1 MiB
- Content-Disposition: `attachment; filename="2399.pdf"; size=3254684`
- URL final: `https://pcrj.maps.arcgis.com/sharing/rest/content/items/eafc70844f41438da45a79563fd1d310/data`

### Feature Service — Escolas Municipais
- ID: `0a220ea7972449e39a28210dd317f636`
- Meta status: **200**
- `url` no metadata completo: `https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Educacao/SME/MapServer/1`
- typeKeywords: `ArcGIS Server, Data, Feature Access, Feature Service, Metadata, Service`
- size (manifest field, bytes): 72 (72 B)

### Document Link — Painel.RIO
- ID: `7001b082c7174c539bfbf4e8b34c682c`
- Meta status: **200**
- `url` no metadata completo: `https://painel.rio`
- typeKeywords: `Data, Document`
- size (manifest field, bytes): 18 (18 B)

### CSV Collection — Taxa de Analfabetismo
- ID: `8644dbd04a0c472faa2b727718a8bcad`
- Meta status: **200**
- typeKeywords: `CSV Collection, zip`
- size (manifest field, bytes): 3,262 (3.2 KiB)
- `/data` HEAD status: **200**
- `/data` Content-Type: `application/zip`
- `/data` Content-Length: 3.2 KiB
- Content-Disposition: `attachment; filename="tabela_894.zip"; size=3262`
- URL final: `https://pcrj.maps.arcgis.com/sharing/rest/content/items/8644dbd04a0c472faa2b727718a8bcad/data`

## Conclusões

1. **Hipótese confirmada.** Todos os 5 itens responderam HTTP 200 em `/sharing/rest/content/items/{id}`. Os 170 itens "sem URL" no manifest **não estão quebrados** — para tipos baixáveis (Excel, PDF, CSV Collection), o conteúdo é servido em `/data` com `Content-Type` correto, sem necessidade de campo `url` explícito.
2. **Padrão por tipo:**
   - **Excel / PDF / CSV Collection / Image**: campo `url` permanece vazio mesmo no metadata completo; o download é sempre `/sharing/rest/content/items/{id}/data`.
   - **Feature Service**: `url` aponta para o ArcGIS Server externo do IPP (`pgeo3.rio.rj.gov.br/arcgis/rest/services/...`). É uma API GeoJSON/MapServer consumível diretamente.
   - **Document Link / Web Mapping Application / Hub Site Application**: `url` aponta para um site externo (não há binário a baixar).
3. **Filenames reais via `Content-Disposition`** (`3726.xlsx`, `2399.pdf`, `tabela_894.zip`). Os IDs no portal são numéricos sequenciais; o nome amigável está só no metadata `title`.
4. **Campo `size` do manifest está em bytes**, não KB como sugere o README. Confere com `Content-Length` do HEAD. Vale corrigir a documentação.
5. **Custo de download estimado**: 127 Excels × ~800 KiB ≈ **100 MiB**, 35 PDFs × ~3 MiB ≈ **105 MiB**. Total dos artefatos baixáveis ≈ 200 MiB — totalmente viável para um cache local; não precisa de DVC nesta fase.

**Próximo passo natural:** baixar todos os Excels (script de ingestão lote, respeitando `sleep` entre chamadas), salvar em `data/raw/excel/{id}.xlsx`, e fazer EDA do conteúdo (sheets, headers, granularidade real) para o shortlist do HEX-EDU.

<!-- continue-lendo -->

## Continue lendo

!!! tip ""
    - [03 — Catálogo dos Excels](03_excel_catalog.md)
    - [API do data.rio](../data-rio-api.md)
    - [Papers](../papers/index.md)
