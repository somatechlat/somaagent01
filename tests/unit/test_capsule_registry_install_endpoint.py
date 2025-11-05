import pytest

pytest.skip("Capsule registry removed from project", allow_module_level=True)
import importlib
import os
import tempfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

TEST_STORAGE_ROOT = Path(tempfile.gettempdir()) / "capsule-registry-test-storage"
TEST_INSTALL_ROOT = Path(tempfile.gettempdir()) / "capsule-registry-test-install"
os.environ.setdefault("CAPSULE_STORAGE_PATH", str(TEST_STORAGE_ROOT))
os.environ.setdefault("CAPSULE_INSTALL_PATH", str(TEST_INSTALL_ROOT))

capsule_main = importlib.import_module("services.capsule_registry.main")


class _FakeConn:
    def __init__(self, record):
        self._record = record

    async def fetchrow(
        self, query: str, capsule_id: str
    ):  # pragma: no cover - FastAPI enforces signature
        if capsule_id == "capsule-123":
            return self._record
        return None


class _FakeAcquire:
    def __init__(self, record):
        self._record = record

    async def __aenter__(self):
        return _FakeConn(self._record)

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, record):
        self._record = record

    def acquire(self):
        return _FakeAcquire(self._record)


class _FakeStore:
    def __init__(self, record):
        self.pool = _FakePool(record)


@pytest.mark.asyncio
async def test_install_endpoint_returns_install_location(monkeypatch, tmp_path):
    record = {"signature": "sig-value"}
    capsule_main.app.dependency_overrides[capsule_main.get_store] = lambda: _FakeStore(record)

    def fake_install_capsule(capsule_id: str, path: str):
        target = Path(path) / "extracted"
        target.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(capsule_main, "install_capsule", fake_install_capsule)
    monkeypatch.setattr(capsule_main, "CAPSULE_INSTALL_BASE", tmp_path)

    try:
        transport = ASGITransport(app=capsule_main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/capsules/capsule-123/install")

        assert response.status_code == 200
        payload = response.json()
        assert payload["capsule_id"] == "capsule-123"
        assert payload["install_path"].endswith("capsule-123/extracted")
        assert payload["signature"] == "sig-value"
    finally:
        capsule_main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_install_endpoint_returns_404_for_missing_capsule(tmp_path):
    capsule_main.app.dependency_overrides[capsule_main.get_store] = lambda: _FakeStore(None)
    try:
        transport = ASGITransport(app=capsule_main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/capsules/missing/install")

        assert response.status_code == 404
        assert response.json()["detail"] == "Capsule not found"
    finally:
        capsule_main.app.dependency_overrides.clear()
