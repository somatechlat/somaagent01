import pytest
from starlette.requests import Request

from services.gateway import main as gateway_main


def _make_cookie_request(cookie_name: str, token: str) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/v1/resource",
        "raw_path": b"/v1/resource",
        "query_string": b"",
        "headers": [(b"cookie", f"{cookie_name}={token}".encode("latin-1"))],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "scheme": "http",
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _reset_auth_globals(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(gateway_main, "REQUIRE_AUTH", True, raising=False)
    monkeypatch.setenv("GATEWAY_JWT_COOKIE_NAME", "jwt")
    monkeypatch.setattr(gateway_main, "JWT_SECRET", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_PUBLIC_KEY", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_JWKS_URL", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_AUDIENCE", None, raising=False)
    monkeypatch.setattr(gateway_main, "JWT_ISSUER", None, raising=False)


def _stub_jwt(monkeypatch: pytest.MonkeyPatch):
    async def fake_resolve_signing_key(_: dict[str, str]):
        return "secret"

    def fake_get_unverified_header(_: str):
        return {"alg": "HS256"}

    def fake_decode(_: str, *, key=None, **__):
        assert key == "secret"
        return {"sub": "user-1", "tenant": "t-cookie", "scope": "admin"}

    monkeypatch.setattr(gateway_main, "_resolve_signing_key", fake_resolve_signing_key)
    monkeypatch.setattr(gateway_main.jwt, "get_unverified_header", fake_get_unverified_header)
    monkeypatch.setattr(gateway_main.jwt, "decode", fake_decode)


@pytest.mark.asyncio
async def test_authorize_request_accepts_jwt_cookie(monkeypatch: pytest.MonkeyPatch):
    _stub_jwt(monkeypatch)

    # Unit tests should not make real OPA calls; stub evaluation to a no-op
    async def noop_opa(*_, **__):
        return None

    monkeypatch.setattr(gateway_main, "_evaluate_opa", noop_opa)
    request = _make_cookie_request("jwt", "good-token")
    meta = await gateway_main.authorize_request(request, {})
    assert meta["tenant"] == "t-cookie"
    assert meta["subject"] == "user-1"
