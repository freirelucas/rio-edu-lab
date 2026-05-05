"""Cliente para a API ArcGIS Hub do portal data.rio.

Foco: Grupo Educação (ID 91117c15dceb41eaa08df881fa9f9310).

Endpoints relevantes (REST API do ArcGIS Online):
- Lista de itens do grupo:  /sharing/rest/content/groups/{group_id}
- Metadados do item:        /sharing/rest/content/items/{item_id}
- Download do item:         /sharing/rest/content/items/{item_id}/data
- Metadados do grupo:       /sharing/rest/community/groups/{group_id}
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GROUP_ID = "91117c15dceb41eaa08df881fa9f9310"  # Grupo Educacao
PORTAL_BASE = "https://pcrj.maps.arcgis.com/sharing/rest"
USER_AGENT = "acec-hub/0.1 (research; +https://github.com/freirelucas/acec-hub)"

# Mapeamento de tipo do item -> extensão default para download
TYPE_TO_EXTENSION = {
    "Microsoft Excel": "xlsx",
    "PDF": "pdf",
    "Image": "png",
    "CSV": "csv",
    "CSV Collection": "zip",
    "Code Attachment": "zip",
    "Microsoft Word": "docx",
    "Microsoft Powerpoint": "pptx",
}

# Tipos que NÃO são arquivos baixáveis (são apps, services, links)
NON_DOWNLOADABLE_TYPES = {
    "Feature Service",
    "Web Mapping Application",
    "Hub Site Application",
    "Document Link",
    "Web Map",
    "Dashboard",
}


@dataclass
class HubItem:
    """Metadado de um item do data.rio."""

    id: str
    title: str
    type: str
    snippet: str | None = None
    modified: int | None = None  # epoch ms
    created: int | None = None
    url: str | None = None
    size: int | None = None
    num_views: int | None = None
    tags: list[str] = field(default_factory=list)
    owner: str | None = None

    @classmethod
    def from_api(cls, raw: dict[str, Any]) -> "HubItem":
        return cls(
            id=raw["id"],
            title=raw.get("title", ""),
            type=raw.get("type", ""),
            snippet=raw.get("snippet"),
            modified=raw.get("modified"),
            created=raw.get("created"),
            url=raw.get("url"),
            size=raw.get("size"),
            num_views=raw.get("numViews"),
            tags=raw.get("tags", []) or [],
            owner=raw.get("owner"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "snippet": self.snippet,
            "modified": self.modified,
            "created": self.created,
            "url": self.url,
            "size": self.size,
            "numViews": self.num_views,
            "tags": self.tags,
            "owner": self.owner,
        }

    @property
    def is_downloadable(self) -> bool:
        return self.type not in NON_DOWNLOADABLE_TYPES

    @property
    def extension(self) -> str:
        return TYPE_TO_EXTENSION.get(self.type, "bin")


class ArcGISHubClient:
    """Cliente HTTP para a API REST do ArcGIS Hub usado pelo data.rio.

    Exemplo:
        >>> client = ArcGISHubClient()
        >>> items = client.list_group_items()
        >>> print(f"Total: {len(items)}")
        >>> client.download_item(items[0], dest_dir=Path("data/raw"))
    """

    def __init__(
        self,
        portal_base: str = PORTAL_BASE,
        timeout: float = 30.0,
        sleep_between_calls: float = 0.3,
    ) -> None:
        self.portal_base = portal_base.rstrip("/")
        self.sleep = sleep_between_calls
        self._client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    def __enter__(self) -> "ArcGISHubClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # ------------------------------------------------------------------ API

    def get_group_metadata(self, group_id: str = GROUP_ID) -> dict[str, Any]:
        """Metadados do grupo (título, owner, criado, modificado)."""
        url = f"{self.portal_base}/community/groups/{group_id}"
        r = self._client.get(url, params={"f": "json"})
        r.raise_for_status()
        return r.json()

    def list_group_items(
        self,
        group_id: str = GROUP_ID,
        page_size: int = 100,
    ) -> list[HubItem]:
        """Lista todos os itens do grupo com paginação automática."""
        items: list[HubItem] = []
        start = 1
        url = f"{self.portal_base}/content/groups/{group_id}"

        while True:
            r = self._client.get(
                url, params={"f": "json", "num": page_size, "start": start}
            )
            r.raise_for_status()
            payload = r.json()
            page_items = payload.get("items", [])
            items.extend(HubItem.from_api(it) for it in page_items)

            next_start = payload.get("nextStart", -1)
            if next_start == -1 or not page_items:
                break
            start = next_start
            time.sleep(self.sleep)

        logger.info("Fetched %d items from group %s", len(items), group_id)
        return items

    def download_item(
        self,
        item: HubItem,
        dest_dir: Path,
        overwrite: bool = False,
    ) -> Path | None:
        """Baixa o conteúdo de um item para `dest_dir/{type}/{id}.{ext}`.

        Retorna None se o item não for baixável (Feature Service, etc.).
        """
        if not item.is_downloadable:
            logger.debug("Skipping non-downloadable item %s (%s)", item.id, item.type)
            return None

        type_dir = dest_dir / _slug(item.type)
        type_dir.mkdir(parents=True, exist_ok=True)
        dest = type_dir / f"{item.id}.{item.extension}"

        if dest.exists() and not overwrite:
            logger.debug("Already downloaded: %s", dest)
            return dest

        url = f"{self.portal_base}/content/items/{item.id}/data"
        try:
            with self._client.stream("GET", url, params={"f": "json"}) as r:
                r.raise_for_status()
                with dest.open("wb") as fh:
                    for chunk in r.iter_bytes():
                        fh.write(chunk)
        except httpx.HTTPError as e:
            logger.warning("Failed to download item %s: %s", item.id, e)
            return None

        logger.info("Downloaded %s (%s) -> %s", item.title[:60], item.type, dest)
        time.sleep(self.sleep)
        return dest

    # ------------------------------------------------------------ MANIFEST

    def write_manifest(
        self,
        items: list[HubItem],
        path: Path,
        group_id: str = GROUP_ID,
    ) -> None:
        """Escreve manifest.json canônico."""
        manifest = {
            "source": "data.rio (ArcGIS Hub) — Grupo Educação",
            "group_id": group_id,
            "group_url": f"https://www.data.rio/search?groupIds={group_id}",
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_items": len(items),
            "items": [it.to_dict() for it in items],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=2)
        logger.info("Wrote manifest with %d items to %s", len(items), path)

    @staticmethod
    def load_manifest(path: Path) -> tuple[dict[str, Any], list[HubItem]]:
        """Carrega manifest e retorna (metadados_globais, lista_de_items)."""
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        items = [HubItem.from_api(it) for it in data.get("items", [])]
        return data, items


def _slug(s: str) -> str:
    """Slugify simples para nome de pasta."""
    return (
        s.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace("_", "-")
        .strip("-")
    )
