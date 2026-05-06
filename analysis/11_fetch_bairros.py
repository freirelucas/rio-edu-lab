"""Fetch da geometria oficial dos bairros do Rio (IPP / data.rio).

Substrato espacial para o produto HEX-EDU. O manifest do Grupo Educação
não contém este item — a geometria está em outro grupo do data.rio
(`pcrj.maps.arcgis.com`), publicada pelo IPP via servidor próprio
`pgeo3.rio.rj.gov.br`. Achado por search em
/sharing/rest/search?q=limite+bairros.

Faz:
  - GET /query?where=1=1&outFields=*&f=geojson contra o Feature Layer
  - Normaliza strings (alguns campos vêm com padding de espaços fixos)
  - Valida cobertura: cruza nomes com data/processed/ideb_bairros.csv
  - Persiste provenance (URL, item id, modified, fetched_at)

Outputs:
  - data/raw/geo/bairros.geojson
  - data/raw/geo/_provenance.json

Uso:
  python3 analysis/11_fetch_bairros.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_GEO = ROOT / "data" / "raw" / "geo" / "bairros.geojson"
OUT_PROV = ROOT / "data" / "raw" / "geo" / "_provenance.json"
IDEB_CSV = ROOT / "data" / "processed" / "ideb_bairros.csv"

# Item & service. Search cmd that found this:
#   curl '.../sharing/rest/search?q=limite+bairros&num=15&f=json'
ITEM_ID = "dc94b29fc3594a5bb4d297bee0c9a3f2"
ITEM_URL = (
    "https://pcrj.maps.arcgis.com/sharing/rest/content/items/"
    f"{ITEM_ID}?f=json"
)
SERVICE_URL = (
    "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/"
    "Cartografia/Limites_administrativos/MapServer/4"
)
USER_AGENT = "rio-edu-lab/0.1 (research; +https://github.com/freirelucas/rio-edu-lab)"
TIMEOUT = 60

# String fields that come padded with spaces from the ArcGIS server.
PADDED_STRING_FIELDS = ("nome", "regiao_adm", "rp", "link")


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def normalize_feature(feat: dict) -> dict:
    props = feat.get("properties", {})
    for k in PADDED_STRING_FIELDS:
        if k in props and isinstance(props[k], str):
            props[k] = props[k].strip()
    # Drop noisy server-side computed columns
    for noisy in ("st_area(shape)", "st_perimeter(shape)"):
        props.pop(noisy, None)
    return feat


def fetch_bairros() -> dict:
    query = (
        f"{SERVICE_URL}/query"
        "?where=1%3D1&outFields=*&outSR=4326&returnGeometry=true&f=geojson"
    )
    print(f"GET {query}")
    payload = json.loads(http_get(query))
    if payload.get("exceededTransferLimit"):
        raise RuntimeError(
            "exceededTransferLimit — service truncated; need pagination"
        )
    n_feat = len(payload.get("features", []))
    print(f"  features: {n_feat}")

    # Normalize all features
    payload["features"] = [normalize_feature(f) for f in payload["features"]]
    return payload


def fetch_item_metadata() -> dict:
    print(f"GET {ITEM_URL}")
    raw = json.loads(http_get(ITEM_URL))
    return {
        "id": raw.get("id"),
        "title": raw.get("title"),
        "type": raw.get("type"),
        "owner": raw.get("owner"),
        "modified_epoch_ms": raw.get("modified"),
        "modified": datetime.fromtimestamp(
            raw["modified"] / 1000, tz=timezone.utc
        ).isoformat() if raw.get("modified") else None,
        "snippet": raw.get("snippet"),
    }


def cross_check_with_ideb(geojson: dict) -> dict:
    if not IDEB_CSV.exists():
        return {"checked": False, "reason": f"{IDEB_CSV.relative_to(ROOT)} not found"}

    geom_names = {
        f["properties"].get("nome", "").strip().lower()
        for f in geojson["features"]
    }
    geom_names.discard("")

    ideb_names = set()
    with IDEB_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n = (row.get("bairro") or "").strip().lower()
            if n:
                ideb_names.add(n)

    matched = ideb_names & geom_names
    missing_in_geom = sorted(ideb_names - geom_names)
    extra_in_geom = sorted(geom_names - ideb_names)

    return {
        "checked": True,
        "n_geom": len(geom_names),
        "n_ideb": len(ideb_names),
        "matched": len(matched),
        "missing_in_geom": missing_in_geom,
        "extra_in_geom_sample": extra_in_geom[:10],
        "extra_in_geom_total": len(extra_in_geom),
    }


def main() -> int:
    OUT_GEO.parent.mkdir(parents=True, exist_ok=True)

    item_meta = fetch_item_metadata()
    geojson = fetch_bairros()

    OUT_GEO.write_text(json.dumps(geojson, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT_GEO.relative_to(ROOT)} ({len(geojson['features'])} features, "
          f"{OUT_GEO.stat().st_size / 1024:.1f} KiB)")

    cross = cross_check_with_ideb(geojson)
    print(f"\ncross-check vs ideb_bairros.csv: {json.dumps(cross, ensure_ascii=False, indent=2)[:600]}")

    provenance = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fetched_by": "analysis/11_fetch_bairros.py",
        "manifest_item": item_meta,
        "service_url": SERVICE_URL,
        "n_features": len(geojson["features"]),
        "fields": [
            f["properties"].keys()
            for f in geojson["features"][:1]
        ][0] and sorted(geojson["features"][0]["properties"].keys()),
        "cross_check": cross,
    }
    OUT_PROV.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"wrote {OUT_PROV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
