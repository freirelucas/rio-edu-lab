"""Testes do módulo de ingestão ArcGIS."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from acec.ingest import GROUP_ID, ArcGISHubClient
from acec.ingest.arcgis import HubItem, _slug

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "manifest.json"


class TestHubItem:
    def test_from_api_minimal(self) -> None:
        raw = {"id": "abc123", "title": "Teste", "type": "PDF"}
        item = HubItem.from_api(raw)
        assert item.id == "abc123"
        assert item.title == "Teste"
        assert item.type == "PDF"
        assert item.tags == []

    def test_from_api_full(self) -> None:
        raw = {
            "id": "abc123",
            "title": "Teste",
            "type": "Microsoft Excel",
            "snippet": "snippet teste",
            "modified": 1700000000000,
            "tags": ["educação", "rio"],
        }
        item = HubItem.from_api(raw)
        assert item.snippet == "snippet teste"
        assert item.tags == ["educação", "rio"]

    def test_is_downloadable(self) -> None:
        excel = HubItem(id="x", title="t", type="Microsoft Excel")
        feature = HubItem(id="x", title="t", type="Feature Service")
        assert excel.is_downloadable
        assert not feature.is_downloadable

    def test_extension(self) -> None:
        assert HubItem(id="x", title="t", type="PDF").extension == "pdf"
        assert HubItem(id="x", title="t", type="Microsoft Excel").extension == "xlsx"
        assert HubItem(id="x", title="t", type="Unknown").extension == "bin"

    def test_roundtrip(self) -> None:
        raw = {
            "id": "abc",
            "title": "T",
            "type": "PDF",
            "snippet": "s",
            "modified": 1,
            "created": 0,
            "url": None,
            "size": 100,
            "numViews": 5,
            "tags": ["a"],
            "owner": "x",
        }
        item = HubItem.from_api(raw)
        assert item.to_dict() == raw


class TestSlug:
    def test_basic(self) -> None:
        assert _slug("Microsoft Excel") == "microsoft-excel"
        assert _slug("PDF") == "pdf"
        assert _slug("Feature Service") == "feature-service"


class TestManifest:
    def test_manifest_exists_and_valid(self) -> None:
        """O manifest commitado deve existir e ter exatamente os 186 itens."""
        assert MANIFEST_PATH.exists(), f"manifest.json ausente em {MANIFEST_PATH}"
        with MANIFEST_PATH.open() as fh:
            data = json.load(fh)
        assert data["group_id"] == GROUP_ID
        assert data["total_items"] == len(data["items"])
        assert data["total_items"] >= 180  # tolerância pra ±5 itens

    def test_load_manifest(self) -> None:
        if not MANIFEST_PATH.exists():
            pytest.skip("manifest.json não encontrado")
        meta, items = ArcGISHubClient.load_manifest(MANIFEST_PATH)
        assert isinstance(items, list)
        assert all(isinstance(it, HubItem) for it in items)
        assert all(it.id for it in items)


@pytest.mark.skip(reason="Requer rede; rodar manualmente com -k network")
class TestNetworkLive:
    def test_get_group_metadata(self) -> None:
        with ArcGISHubClient() as client:
            meta = client.get_group_metadata()
        assert meta["id"] == GROUP_ID
        assert "Educacao" in meta.get("title", "")

    def test_list_group_items(self) -> None:
        with ArcGISHubClient() as client:
            items = client.list_group_items()
        assert len(items) >= 180
