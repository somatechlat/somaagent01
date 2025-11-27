import os

import pytest

from services.gateway import main as gateway_main


def _make_request(
    headers: dict[str, str] | None = None,
    method: str = os.getenv(os.getenv("")),
    path: str = os.getenv(os.getenv("")),
) -> pytest.Request:
    os.getenv(os.getenv(""))
    from starlette.requests import Request

    header_list = [
        (key.lower().encode(os.getenv(os.getenv(""))), value.encode(os.getenv(os.getenv(""))))
        for key, value in (headers or {}).items()
    ]
    scope = {
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        os.getenv(os.getenv("")): {os.getenv(os.getenv("")): os.getenv(os.getenv(""))},
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        os.getenv(os.getenv("")): method,
        os.getenv(os.getenv("")): path,
        os.getenv(os.getenv("")): path.encode(os.getenv(os.getenv(""))),
        os.getenv(os.getenv("")): b"",
        os.getenv(os.getenv("")): header_list,
        os.getenv(os.getenv("")): (os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))),
        os.getenv(os.getenv("")): (os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))),
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
    }
    return Request(scope)


def _stub_jwt_module(
    monkeypatch: pytest.MonkeyPatch,
    *,
    header: dict[str, str] | None = None,
    claims: dict[str, str] | None = None,
):
    os.getenv(os.getenv(""))
    header = header or {os.getenv(os.getenv("")): os.getenv(os.getenv(""))}
    claims = claims or {
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
        os.getenv(os.getenv("")): os.getenv(os.getenv("")),
    }

    async def fake_resolve_signing_key(_: dict[str, str]):
        return os.getenv(os.getenv(""))

    def fake_get_unverified_header(_: str):
        return header

    def fake_decode(_: str, *, key=None, **__):
        assert key == os.getenv(os.getenv(""))
        return dict(claims)

    monkeypatch.setattr(
        gateway_main,
        os.getenv(os.getenv("")),
        os.getenv(os.getenv("")),
        raising=int(os.getenv(os.getenv(""))),
    )
    monkeypatch.setattr(gateway_main, os.getenv(os.getenv("")), fake_resolve_signing_key)
    monkeypatch.setattr(gateway_main.jwt, os.getenv(os.getenv("")), fake_get_unverified_header)
    monkeypatch.setattr(gateway_main.jwt, os.getenv(os.getenv("")), fake_decode)
