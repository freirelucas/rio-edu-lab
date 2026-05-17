"""Fetch do IDS (Índice de Desenvolvimento Social) por setor censitário.

Insumo do produto VULN-EDU: cruza vulnerabilidade socioeconômica com IDEB
por bairro. Esta sessão baixa o Feature Service do IPP/PCRJ.

  id    = 0afd8c122fb4400b847693e715106304
  title = Índice de Desenvolvimento Social (IDS) - Região Metropolitana do RJ (2010)
  url   = https://services1.arcgis.com/OlP4dGNtIcnD3RYf/ArcGIS/rest/services/IDS_RM_2010/FeatureServer/0

Filtramos para NM_MUNICIP = 'Rio de Janeiro' (~10.504 setores).
Camada inclui IDS composto + 7 sub-indicadores normalizados (água, esgoto,
lixo, banheiros/pessoa, analfabetismo 10-14, renda do responsável em 3
faixas) — base do Censo 2010.

Salvamos como CSV (sem geometria) — VULN-EDU agrega por bairro e usa o
bairros.geojson canônico para o coroplético; geometria por setor seria
~27 MiB sem ganho analítico. Quem quiser geometria pode re-rodar e
adicionar `--with-geometry` (saída `ids_setores.geojson`, gitignored).

Outputs (default):
  - data/raw/geo/ids_setores.csv          (atributos por setor; ~2 MiB)
  - data/raw/geo/ids_setores_provenance.json

Uso:
  python3 analysis/28_fetch_ids.py
  python3 analysis/28_fetch_ids.py --with-geometry   # também salva geojson
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_CSV = ROOT / "data" / "raw" / "geo" / "ids_setores.csv"
OUT_GEO = ROOT / "data" / "raw" / "geo" / "ids_setores.geojson"
OUT_PROV = ROOT / "data" / "raw" / "geo" / "ids_setores_provenance.json"

ITEM_ID = "0afd8c122fb4400b847693e715106304"
ITEM_URL = (
    "https://pcrj.maps.arcgis.com/sharing/rest/content/items/"
    f"{ITEM_ID}?f=json"
)
SERVICE_URL = (
    "https://services1.arcgis.com/OlP4dGNtIcnD3RYf/ArcGIS/rest/services/"
    "IDS_RM_2010/FeatureServer/0"
)
USER_AGENT = "rio-edu-lab/0.7 (research; +https://github.com/freirelucas/rio-edu-lab)"
TIMEOUT = 90
MAX_RECORDS_PER_PAGE = 2000
RIO_FILTER = "NM_MUNICIP='RIO DE JANEIRO'"

# Columns kept in the slim CSV — covers everything VULN-EDU needs.
CSV_COLS = [
    "OBJECTID", "CD_GEOCODI", "NM_BAIRRO", "NM_SUBDIST", "NM_DISTRIT",
    "INDIC_AGUA_ADEQUADA", "INDIC_ESGOTO_ADEQUADO", "INDIC_LIXO_ADEQUADO",
    "INDIC_MEDBANH_PES", "INDIC_ANALFAB_10A14",
    "INDIC_RENDARESP_POS_SM", "INDIC_RENDARESP_POS_ATE2SM",
    "INDIC_RENDARESP_P_MAISDE10SM",
    "I_AGUA_ADEQUADA", "I_ESGOTO_ADEQUADO", "I_LIXO_ADEQUADO",
    "I_MEDBANH_PES", "I_ANALFAB_10A14",
    "I_RENDARESP_POS_SM", "I_RENDARESP_POS_ATE2SM",
    "I_RENDARESP_P_MAISDE10SM",
    "IDS",
]


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def fetch_paginated() -> dict:
    """ArcGIS Feature Layer query — paginated, restricted to Rio Municipal."""
    all_features = []
    offset = 0
    base_params = {
        "where": RIO_FILTER,
        "outFields": "*",
        "outSR": "4326",
        "returnGeometry": "true",
        "f": "geojson",
        "orderByFields": "OBJECTID",
    }
    while True:
        params = {
            **base_params,
            "resultOffset": str(offset),
            "resultRecordCount": str(MAX_RECORDS_PER_PAGE),
        }
        query = f"{SERVICE_URL}/query?" + urllib.parse.urlencode(params)
        print(f"  GET offset={offset} count={MAX_RECORDS_PER_PAGE}")
        payload = json.loads(http_get(query))
        features = payload.get("features", [])
        all_features.extend(features)
        if len(features) < MAX_RECORDS_PER_PAGE:
            break
        offset += MAX_RECORDS_PER_PAGE
        if offset > 50000:
            raise RuntimeError("pagination runaway > 50000")
    payload["features"] = all_features
    return payload


def normalize_string_props(feat: dict) -> dict:
    props = feat.get("properties", {})
    for k, v in list(props.items()):
        if isinstance(v, str):
            props[k] = v.strip()
    return feat


def fetch_item_metadata() -> dict:
    raw = json.loads(http_get(ITEM_URL))
    return {
        "id": raw.get("id"),
        "title": raw.get("title"),
        "type": raw.get("type"),
        "owner": raw.get("owner"),
        "modified_epoch_ms": raw.get("modified"),
        "modified": (
            datetime.fromtimestamp(raw["modified"] / 1000, tz=timezone.utc).isoformat()
            if raw.get("modified") else None
        ),
        "snippet": raw.get("snippet"),
    }


def main() -> int:
    with_geometry = "--with-geometry" in sys.argv
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    print(f"GET item metadata {ITEM_URL}")
    item_meta = fetch_item_metadata()

    print(f"GET service features {SERVICE_URL}  (filter: {RIO_FILTER})")
    geojson = fetch_paginated()

    n_total = len(geojson["features"])
    print(f"  {n_total} setores fetched")

    geojson["features"] = [normalize_string_props(f) for f in geojson["features"]]

    # Always write slim CSV (attributes only) — base of VULN-EDU pipeline.
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLS, extrasaction="ignore")
        writer.writeheader()
        for feat in geojson["features"]:
            writer.writerow({k: feat["properties"].get(k) for k in CSV_COLS})
    print(f"wrote {OUT_CSV.relative_to(ROOT)} ({OUT_CSV.stat().st_size / 1024:.1f} KiB)")

    if with_geometry:
        OUT_GEO.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {OUT_GEO.relative_to(ROOT)} "
              f"({OUT_GEO.stat().st_size / 1024 / 1024:.1f} MiB) [gitignored]")

    sample_props = geojson["features"][0]["properties"] if geojson["features"] else {}

    provenance = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fetched_by": "analysis/28_fetch_ids.py",
        "manifest_item": item_meta,
        "service_url": SERVICE_URL,
        "filter": RIO_FILTER,
        "n_features": n_total,
        "csv_columns": CSV_COLS,
        "with_geometry": with_geometry,
        "sample_properties_keys": sorted(sample_props.keys()),
    }
    OUT_PROV.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"wrote {OUT_PROV.relative_to(ROOT)}")

    # Quick summary
    bairros = {}
    ids_vals = []
    for f in geojson["features"]:
        p = f["properties"]
        b = p.get("NM_BAIRRO") or "?"
        bairros[b] = bairros.get(b, 0) + 1
        ids = p.get("IDS")
        if ids is not None:
            ids_vals.append(ids)
    print(f"\nbairros distintos: {len(bairros)}")
    print(f"IDS range: [{min(ids_vals):.3f}, {max(ids_vals):.3f}], n={len(ids_vals)}")
    top = sorted(bairros.items(), key=lambda x: -x[1])[:5]
    print(f"top bairros por # setores: {top}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
