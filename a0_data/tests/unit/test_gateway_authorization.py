import pytest
from fastapi import HTTPException
from starlette.requests import Request

from services.gateway import main as gateway_main


def _make_request(
    headers: dict[str, str] | None = None, method: str = "GET", path: str = "/v1/resource"
) -> Request:
    header_list = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("latin-1"),
        "query_string": b"",
        "headers": header_list,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _reset_auth_globals(monkeypatch: pytest.MonkeyPatch):
    """Ensure security globals are reset between tests."""

    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", True, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_SECRET", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_PUBLIC_KEY", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_JWKS_URL", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_AUDIENCE", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_ISSUER", None, raising=False)
    monkeypatch.setattr(gateway_main, "_OPENFGA_CLIENT", None, raising=False)
    gateway_main.JWKS_CACHE.clear()


def _stub_jwt_module(
    monkeypatch: pytest.MonkeyPatch,
    *,
    header: dict[str, str] | None = None,
    claims: dict[str, str] | None = None,
):
    """Patch jwt helpers to provide deterministic behaviour for tests."""

    header = header or {"alg": "HS256"}
    claims = claims or {"sub": "user-123", "tenant": "tenant-42", "scope": "read"}

    async def fake_resolve_signing_key(_: dict[str, str]):
        return "secret"

    def fake_get_unverified_header(_: str):
        return header

    def fake_decode(_: str, *, key=None, **__):
        assert key == "secret"
        return dict(claims)

    monkeypatch.setattr(gateway_main, "JWT_SECRET", "secret", raising=False)
    monkeypatch.setattr(gateway_main, "_resolve_signing_key", fake_resolve_signing_key)
    monkeypatch.setattr(gateway_main.jwt, "get_unverified_header", fake_get_unverified_header)
    monkeypatch.setattr(gateway_main.jwt, "decode", fake_decode)


@pytest.mark.asyncio
async def test_authorize_request_requires_header_when_auth_enforced(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", True, raising=False)
    request = _make_request()

    with pytest.raises(HTTPException) as excinfo:
        await gateway_main.authorize_request(request, {})

    assert excinfo.value.status_code == 401


@pytest.mark.asyncio
async def test_authorize_request_invalid_token_header(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", True, raising=False)

    request = _make_request({"authorization": "Bearer token"})

    def fake_get_unverified_header(_: str):
        raise gateway_main.jwt.PyJWTError("invalid header")

    monkeypatch.setattr(gateway_main.jwt, "get_unverified_header", fake_get_unverified_header)

    with pytest.raises(HTTPException) as excinfo:
        await gateway_main.authorize_request(request, {})

    assert excinfo.value.status_code == 401


@pytest.mark.asyncio
async def test_authorize_request_returns_metadata_on_success(monkeypatch: pytest.MonkeyPatch):
    _stub_jwt_module(monkeypatch)

    async def noop_opa(*_, **__):
        return None

    monkeypatch.setattr(gateway_main, "_evaluate_opa", noop_opa)

    request = _make_request({"authorization": "Bearer good-token"})
    payload = {"message": "hello"}

    metadata = await gateway_main.authorize_request(request, payload)

    assert metadata["tenant"] == "tenant-42"
    assert metadata["subject"] == "user-123"
    assert metadata["scope"] == "read"


@pytest.mark.asyncio
async def test_authorize_request_denied_by_opa(monkeypatch: pytest.MonkeyPatch):
    _stub_jwt_module(monkeypatch)

    async def deny_opa(*_, **__):
        raise HTTPException(status_code=403, detail="blocked")

    monkeypatch.setattr(gateway_main, "_evaluate_opa", deny_opa)

    request = _make_request({"authorization": "Bearer good-token"})

    with pytest.raises(HTTPException) as excinfo:
        await gateway_main.authorize_request(request, {})

    assert excinfo.value.status_code == 403


@pytest.mark.asyncio
async def test_authorize_request_denied_by_openfga(monkeypatch: pytest.MonkeyPatch):
    claims = {"sub": "user-456", "tenant": "tenant-99"}
    _stub_jwt_module(monkeypatch, claims=claims)

    async def noop_opa(*_, **__):
        return None

    class StubOpenFGAClient:
        async def check_tenant_access(self, tenant: str, subject: str):
            assert tenant == "tenant-99"
            assert subject == "user-456"
            return False

    monkeypatch.setattr(gateway_main, "_evaluate_opa", noop_opa)
    monkeypatch.setattr(gateway_main, "_get_openfga_client", lambda: StubOpenFGAClient())

    request = _make_request({"authorization": "Bearer good-token"})

    with pytest.raises(HTTPException) as excinfo:
        await gateway_main.authorize_request(request, {})

    assert excinfo.value.status_code == 403
