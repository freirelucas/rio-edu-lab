"""Re-fetch data/manifest.json com escopo org-wide do data.rio (não só Grupo Educação).

O manifest original foi scrapeado do grupo `91117c15dceb41eaa08df881fa9f9310`
("Grupo Educação") via `acec manifest refresh`. Resultado: 186 itens. O org
inteiro da Prefeitura do Rio (orgid OlP4dGNtIcnD3RYf no portal pcrj.maps.arcgis.com)
tem ~9855 itens distribuídos entre dezenas de grupos (Transporte, Saúde,
Demografia, Urbanismo, etc.). Para o lab funcionar como seletor+replicador
genérico de papers contra dados públicos do Rio (não só educação), precisamos
do universo completo.

Endpoint: /sharing/rest/search?q=orgid:OlP4dGNtIcnD3RYf — paginação automática.

Stdlib + urllib (segue o padrão de `analysis/_openalex.py`). Throttle 0.3s
entre páginas (~100 itens/página → ~30s wall clock).

Schema dos items preservado (id, title, type, snippet, modified, created, url,
size, numViews, tags, owner) para compatibilidade com 41, 47, e o cliente
acec-hub. Campo top-level `source` atualizado para refletir o novo escopo.

Uso:
  python3 analysis/00_fetch_manifest.py             # full org-wide
  python3 analysis/00_fetch_manifest.py --dry-run   # só conta total
  python3 analysis/00_fetch_manifest.py --max 500   # cap para teste rápido
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.json"

PORTAL_BASE = "https://pcrj.maps.arcgis.com/sharing/rest"
ORG_ID = "OlP4dGNtIcnD3RYf"  # PrefeituraRio
USER_AGENT = "rio-edu-lab/0.8 (https://github.com/freirelucas/rio-edu-lab)"
PAGE_SIZE = 100
THROTTLE_S = 0.3
TIMEOUT_S = 30


def fetch_page(start: int, page_size: int = PAGE_SIZE) -> dict:
    q = f"orgid:{ORG_ID}"
    params = {
        "q": q,
        "num": str(page_size),
        "start": str(start),
        "f": "json",
    }
    url = f"{PORTAL_BASE}/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_item(raw: dict) -> dict:
    """Match schema de `data/manifest.json` (HubItem.to_dict do acec-hub)."""
    return {
        "id": raw["id"],
        "title": raw.get("title", "") or "",
        "type": raw.get("type", "") or "",
        "snippet": raw.get("snippet"),
        "modified": raw.get("modified"),
        "created": raw.get("created"),
        "url": raw.get("url"),
        "size": raw.get("size"),
        "numViews": raw.get("numViews"),
        "tags": raw.get("tags") or [],
        "owner": raw.get("owner"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Só conta total, não regrava o manifest")
    ap.add_argument("--max", type=int, default=None,
                    help="Cap de itens (default: todos)")
    args = ap.parse_args()

    print(f"fetching org-wide manifest (orgid={ORG_ID})", file=sys.stderr)

    items: list[dict] = []
    seen: set[str] = set()
    start = 1
    total_reported: int | None = None
    while True:
        try:
            data = fetch_page(start, PAGE_SIZE)
        except Exception as e:
            print(f"  [error] page start={start}: {e}", file=sys.stderr)
            return 1

        if total_reported is None:
            total_reported = data.get("total", 0)
            print(f"  total reported by API: {total_reported}", file=sys.stderr)

        results = data.get("results") or []
        for r in results:
            oid = r.get("id")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            items.append(normalize_item(r))

        next_start = data.get("nextStart", -1)
        print(
            f"  page start={start}: +{len(results)} items "
            f"(total so far: {len(items)})",
            file=sys.stderr,
        )

        if next_start == -1 or not results:
            break
        if args.max and len(items) >= args.max:
            print(f"  [cap] reached --max={args.max}", file=sys.stderr)
            items = items[: args.max]
            break
        start = next_start
        time.sleep(THROTTLE_S)

    print(f"\n=== summary ===")
    print(f"  total fetched: {len(items)}")
    print(f"  total reported by API: {total_reported}")
    print(f"  unique ids: {len(seen)}")
    types = {}
    for it in items:
        t = it.get("type") or "(empty)"
        types[t] = types.get(t, 0) + 1
    print(f"  top types:")
    for t, n in sorted(types.items(), key=lambda x: -x[1])[:10]:
        print(f"    {t}: {n}")

    if args.dry_run:
        print("\n[dry-run] not writing manifest")
        return 0

    manifest = {
        "source": "data.rio (ArcGIS Hub) — Organização PCRJ (org-wide)",
        "org_id": ORG_ID,
        "portal_url": "https://www.data.rio/",
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_items": len(items),
        "items": items,
    }
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nwrote {MANIFEST.relative_to(ROOT)} ({len(items)} items)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
