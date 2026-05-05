"""Download lote dos Excels do Grupo Educação.

Para cada item de tipo 'Microsoft Excel' no manifest:
  - GET /sharing/rest/content/items/{id}/data
  - salva em data/raw/excel/{id}.xlsx
  - registra status, bytes baixados, content-type, filename do
    Content-Disposition em data/raw/excel/_index.json

Resumível: pula arquivos já baixados (tamanho > 0).
Polite: sleep entre chamadas; segue redirects; user-agent identificável.

Uso:
  python analysis/03_download_excels.py
  python analysis/03_download_excels.py --limit 5         # smoke test
  python analysis/03_download_excels.py --force           # re-baixa tudo
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.json"
DEST = ROOT / "data" / "raw" / "excel"
INDEX = DEST / "_index.json"

PORTAL = "https://pcrj.maps.arcgis.com/sharing/rest"
USER_AGENT = "rio-edu-lab/0.1 (research; contact via github.com/freirelucas/rio-edu-lab)"
TIMEOUT = 60
SLEEP_BETWEEN = 0.4
CHUNK = 64 * 1024


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None, help="baixa só N itens (smoke test)")
    p.add_argument("--force", action="store_true", help="re-baixa mesmo arquivos existentes")
    p.add_argument("--type", default="Microsoft Excel", help="filtro por type do manifest")
    return p.parse_args()


def filename_from_disposition(value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(r'filename\s*=\s*"([^"]+)"', value) or re.search(
        r"filename\s*=\s*([^;]+)", value
    )
    return m.group(1).strip() if m else None


def download_one(item_id: str, dest: Path) -> dict:
    url = f"{PORTAL}/content/items/{item_id}/data"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            headers = resp.headers
            ct = headers.get("Content-Type", "")
            cd = headers.get("Content-Disposition", "")
            cl = headers.get("Content-Length")
            tmp = dest.with_suffix(dest.suffix + ".part")
            written = 0
            with tmp.open("wb") as fh:
                while True:
                    buf = resp.read(CHUNK)
                    if not buf:
                        break
                    fh.write(buf)
                    written += len(buf)
            tmp.rename(dest)
        return {
            "id": item_id,
            "status": "ok",
            "http_status": 200,
            "bytes": written,
            "content_type": ct,
            "content_length": int(cl) if cl and cl.isdigit() else None,
            "remote_filename": filename_from_disposition(cd),
            "elapsed_s": round(time.monotonic() - started, 2),
        }
    except urllib.error.HTTPError as e:
        return {"id": item_id, "status": "http_error", "http_status": e.code, "error": str(e)}
    except Exception as e:
        return {"id": item_id, "status": "error", "error": repr(e)}


def main() -> int:
    args = parse_args()
    DEST.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    items = [it for it in manifest["items"] if it.get("type") == args.type]
    if args.limit:
        items = items[: args.limit]

    print(f"target: {args.type}, total: {len(items)}, dest: {DEST.relative_to(ROOT)}")

    index: dict[str, dict] = {}
    if INDEX.exists():
        index = json.loads(INDEX.read_text(encoding="utf-8"))

    skipped = downloaded = errors = 0
    started = time.monotonic()
    for i, item in enumerate(items, 1):
        item_id = item["id"]
        dest = DEST / f"{item_id}.xlsx"

        if dest.exists() and dest.stat().st_size > 0 and not args.force:
            skipped += 1
            if i % 25 == 0 or i == len(items):
                print(f"[{i}/{len(items)}] cached  {item_id}  ({skipped} skipped)")
            continue

        result = download_one(item_id, dest)
        result["title"] = item.get("title", "")
        index[item_id] = result

        if result["status"] == "ok":
            downloaded += 1
            print(
                f"[{i}/{len(items)}] ok      {item_id}  "
                f"{result['bytes']:>9,} B  {result['elapsed_s']:>5.2f}s  "
                f"{(item.get('title') or '')[:60]}"
            )
        else:
            errors += 1
            print(f"[{i}/{len(items)}] FAIL    {item_id}  {result.get('error')}")

        # Persist index incrementally so a kill -9 doesn't lose state
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(SLEEP_BETWEEN)

    elapsed = time.monotonic() - started
    total_bytes = sum(
        r.get("bytes", 0) for r in index.values() if r.get("status") == "ok"
    )
    print(
        f"\ndone in {elapsed:.1f}s. "
        f"downloaded={downloaded}, skipped={skipped}, errors={errors}, "
        f"total cached bytes={total_bytes:,} ({total_bytes / 1024**2:.1f} MiB)"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
