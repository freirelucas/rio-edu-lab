"""Fetch das Escolas Municipais do Rio (IPP / data.rio).

Insumo da análise de acessibilidade educacional do HEX-EDU v0.6.
Item canônico do data.rio:

  id    = 0a220ea7972449e39a28210dd317f636
  title = Escolas Municipais
  url   = https://pgeo3.rio.rj.gov.br/arcgis/rest/services/Educacao/SME/MapServer/1

Cobre escolas municipais, EDIs, creches e outros equipamentos da SME-Rio.

Outputs:
  - data/raw/geo/escolas_municipais.geojson
  - data/raw/geo/escolas_municipais_provenance.json

Uso:
  python3 analysis/25_fetch_escolas_municipais.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_GEO = ROOT / "data" / "raw" / "geo" / "escolas_municipais.geojson"
OUT_PROV = ROOT / "data" / "raw" / "geo" / "escolas_municipais_provenance.json"

ITEM_ID = "0a220ea7972449e39a28210dd317f636"
ITEM_URL = (
    "https://pcrj.maps.arcgis.com/sharing/rest/content/items/"
    f"{ITEM_ID}?f=json"
)
SERVICE_URL = (
    "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/"
    "Educacao/SME/MapServer/1"
)
USER_AGENT = "rio-edu-lab/0.6 (research; +https://github.com/freirelucas/rio-edu-lab)"
TIMEOUT = 60
MAX_RECORDS_PER_PAGE = 2000


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def fetch_paginated() -> dict:
    """ArcGIS Feature Layer query — paginated to handle services with > 2000 features."""
    all_features = []
    offset = 0
    while True:
        query = (
            f"{SERVICE_URL}/query"
            "?where=1%3D1&outFields=*&outSR=4326&returnGeometry=true&f=geojson"
            f"&resultOffset={offset}&resultRecordCount={MAX_RECORDS_PER_PAGE}"
        )
        print(f"  GET offset={offset} count={MAX_RECORDS_PER_PAGE}")
        payload = json.loads(http_get(query))
        features = payload.get("features", [])
        all_features.extend(features)
        if len(features) < MAX_RECORDS_PER_PAGE:
            break
        offset += MAX_RECORDS_PER_PAGE
        if offset > 50000:  # safety
            raise RuntimeError("pagination runaway > 50000")
    payload["features"] = all_features
    return payload


def normalize_string_props(feat: dict) -> dict:
    """Trim padding from string fields (ArcGIS often returns space-padded strings)."""
    props = feat.get("properties", {})
    for k, v in list(props.items()):
        if isinstance(v, str):
            props[k] = v.strip()
    # Drop noisy server-computed columns if present
    for noisy in ("st_area(shape)", "st_perimeter(shape)"):
        props.pop(noisy, None)
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
    OUT_GEO.parent.mkdir(parents=True, exist_ok=True)

    print(f"GET item metadata {ITEM_URL}")
    item_meta = fetch_item_metadata()

    print(f"GET service features {SERVICE_URL}")
    geojson = fetch_paginated()

    n_total = len(geojson["features"])
    print(f"  {n_total} features fetched")

    geojson["features"] = [normalize_string_props(f) for f in geojson["features"]]

    OUT_GEO.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT_GEO.relative_to(ROOT)} ({OUT_GEO.stat().st_size / 1024:.1f} KiB)")

    # Sample first feature's properties — useful to know fields available
    sample_props = geojson["features"][0]["properties"] if geojson["features"] else {}

    provenance = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fetched_by": "analysis/25_fetch_escolas_municipais.py",
        "manifest_item": item_meta,
        "service_url": SERVICE_URL,
        "n_features": n_total,
        "sample_properties_keys": sorted(sample_props.keys()),
    }
    OUT_PROV.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"wrote {OUT_PROV.relative_to(ROOT)}")

    # Quick breakdown by tipo if field exists
    types = {}
    for f in geojson["features"]:
        t = f["properties"].get("tipo") or f["properties"].get("tipo_unidade") or "?"
        types[t] = types.get(t, 0) + 1
    if types:
        print(f"\nbreakdown by tipo: {dict(sorted(types.items(), key=lambda x: -x[1])[:10])}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
