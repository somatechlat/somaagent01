import pytest

pytest.skip("Capsule functionality removed from project", allow_module_level=True)
import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from services.gateway import main as gateway_main


def _make_response(
    method: str,
    url: str,
    *,
    status_code: int = 200,
    json_data=None,
    content: bytes | None = None,
    headers: dict[str, str] | None = None,
    text: str | None = None,
) -> httpx.Response:
    request = httpx.Request(method, url)
    if json_data is not None:
        return httpx.Response(status_code, json=json_data, headers=headers, request=request)
    return httpx.Response(
        status_code, content=content or b"", text=text, headers=headers, request=request
    )


def _patch_async_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    method: str,
    url: str,
    response: httpx.Response | None = None,
    exception: Exception | None = None,
) -> None:
    class DummyAsyncClient:
        def __init__(self, *_, **__):
    # Removed per Vibe rule
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, call_url: str, *args, **kwargs):
            assert method.upper() == "GET"
            assert call_url == url
            if exception:
                raise exception
            assert response is not None
            return response

        async def post(self, call_url: str, *args, **kwargs):
            assert method.upper() == "POST"
            assert call_url == url
            if exception:
                raise exception
            assert response is not None
            return response

    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)


@pytest.mark.asyncio
async def test_proxy_list_capsules(monkeypatch):
    base_url = "http://registry.test"
    expected_url = f"{base_url}/capsules"
    monkeypatch.setattr(gateway_main, "CAPSULE_REGISTRY_URL", base_url)
    payload = [{"id": "capsule-1", "name": "Demo", "signature": "sig"}]
    response = _make_response("GET", expected_url, json_data=payload)
    _patch_async_client(monkeypatch, method="GET", url=expected_url, response=response)

    transport = ASGITransport(app=gateway_main.app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        resp = await client.get("/v1/capsules")

    assert resp.status_code == 200
    assert resp.json() == payload


@pytest.mark.asyncio
async def test_proxy_install_capsule(monkeypatch):
    base_url = "http://registry.test"
    capsule_id = "capsule-123"
    expected_url = f"{base_url}/capsules/{capsule_id}/install"
    monkeypatch.setattr(gateway_main, "CAPSULE_REGISTRY_URL", base_url)
    payload = {
        "capsule_id": capsule_id,
        "install_path": "/capsules/installed/capsule-123",
        "signature": "sig",
    }
    response = _make_response("POST", expected_url, json_data=payload)
    _patch_async_client(monkeypatch, method="POST", url=expected_url, response=response)

    transport = ASGITransport(app=gateway_main.app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        resp = await client.post(f"/v1/capsules/{capsule_id}/install")

    assert resp.status_code == 200
    assert resp.json() == payload


@pytest.mark.asyncio
async def test_proxy_download_capsule(monkeypatch):
    base_url = "http://registry.test"
    capsule_id = "capsule-123"
    expected_url = f"{base_url}/capsules/{capsule_id}"
    monkeypatch.setattr(gateway_main, "CAPSULE_REGISTRY_URL", base_url)
    headers = {
        "content-type": "application/zip",
        "content-disposition": "attachment; filename=capsule.zip",
    }
    response = _make_response("GET", expected_url, content=b"ZIPDATA", headers=headers)
    _patch_async_client(monkeypatch, method="GET", url=expected_url, response=response)

    transport = ASGITransport(app=gateway_main.app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        resp = await client.get(f"/v1/capsules/{capsule_id}")

    assert resp.status_code == 200
    assert resp.content == b"ZIPDATA"
    assert resp.headers["content-disposition"] == "attachment; filename=capsule.zip"
    assert resp.headers["content-type"] == "application/zip"


@pytest.mark.asyncio
async def test_proxy_install_capsule_http_error(monkeypatch):
    base_url = "http://registry.test"
    capsule_id = "missing"
    expected_url = f"{base_url}/capsules/{capsule_id}/install"
    monkeypatch.setattr(gateway_main, "CAPSULE_REGISTRY_URL", base_url)
    response = _make_response("POST", expected_url, status_code=404, content=b"capsule missing")
    _patch_async_client(monkeypatch, method="POST", url=expected_url, response=response)

    transport = ASGITransport(app=gateway_main.app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        resp = await client.post(f"/v1/capsules/{capsule_id}/install")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "capsule missing"


@pytest.mark.asyncio
async def test_proxy_install_capsule_request_error(monkeypatch):
    base_url = "http://registry.test"
    capsule_id = "capsule-123"
    expected_url = f"{base_url}/capsules/{capsule_id}/install"
    monkeypatch.setattr(gateway_main, "CAPSULE_REGISTRY_URL", base_url)
    exception = httpx.RequestError("boom", request=httpx.Request("POST", expected_url))
    _patch_async_client(monkeypatch, method="POST", url=expected_url, exception=exception)

    transport = ASGITransport(app=gateway_main.app)
    async with AsyncClient(transport=transport, base_url="http://gateway") as client:
        resp = await client.post(f"/v1/capsules/{capsule_id}/install")

    assert resp.status_code == 502
    assert resp.json()["detail"] == "Capsule registry unavailable"
