import pytest
from services.gateway import main as gateway_main


def _make_request(
    headers: dict[str, str] | None = None, method: str = "GET", path: str = "/v1/resource"
) -> pytest.Request:
    """Create a mock request for testing."""
    from starlette.requests import Request
    
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


def _stub_jwt_module(
    monkeypatch: pytest.MonkeyPatch,
    *,
    header: dict[str, str] | None = None,
    claims: dict[str, str] | None = None,
):
    """Patch jwt helpers to provide deterministic behavior for tests."""
    import jwt
    
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