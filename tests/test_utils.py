import os
import pytest
from services.gateway import main as gateway_main


def _make_request(headers: (dict[str, str] | None)=None, method: str=os.
    getenv(os.getenv('VIBE_2C6ADA41')), path: str=os.getenv(os.getenv(
    'VIBE_96B09BBC'))) ->pytest.Request:
    os.getenv(os.getenv('VIBE_A595DCA4'))
    from starlette.requests import Request
    header_list = [(key.lower().encode(os.getenv(os.getenv('VIBE_F75F4492')
        )), value.encode(os.getenv(os.getenv('VIBE_F75F4492')))) for key,
        value in (headers or {}).items()]
    scope = {os.getenv(os.getenv('VIBE_DE4D1011')): os.getenv(os.getenv(
        'VIBE_3AADFBE2')), os.getenv(os.getenv('VIBE_8B607E09')): {os.
        getenv(os.getenv('VIBE_A2548822')): os.getenv(os.getenv(
        'VIBE_9172649A'))}, os.getenv(os.getenv('VIBE_0E006FA2')): os.
        getenv(os.getenv('VIBE_D9D5E496')), os.getenv(os.getenv(
        'VIBE_F2C3004D')): method, os.getenv(os.getenv('VIBE_F3C50F7E')):
        path, os.getenv(os.getenv('VIBE_C15F6EA7')): path.encode(os.getenv(
        os.getenv('VIBE_F75F4492'))), os.getenv(os.getenv('VIBE_2900D43F')):
        b'', os.getenv(os.getenv('VIBE_C7A8CB62')): header_list, os.getenv(
        os.getenv('VIBE_48EC7497')): (os.getenv(os.getenv('VIBE_54110D79')),
        int(os.getenv(os.getenv('VIBE_325F82FD')))), os.getenv(os.getenv(
        'VIBE_DD0F1A5A')): (os.getenv(os.getenv('VIBE_CFE1F696')), int(os.
        getenv(os.getenv('VIBE_525F8B63')))), os.getenv(os.getenv(
        'VIBE_8A3ECB08')): os.getenv(os.getenv('VIBE_3AADFBE2'))}
    return Request(scope)


def _stub_jwt_module(monkeypatch: pytest.MonkeyPatch, *, header: (dict[str,
    str] | None)=None, claims: (dict[str, str] | None)=None):
    os.getenv(os.getenv('VIBE_9CE45975'))
    header = header or {os.getenv(os.getenv('VIBE_BEA44138')): os.getenv(os
        .getenv('VIBE_432971CD'))}
    claims = claims or {os.getenv(os.getenv('VIBE_1D7379D3')): os.getenv(os
        .getenv('VIBE_ADBE0BD9')), os.getenv(os.getenv('VIBE_A31E1813')):
        os.getenv(os.getenv('VIBE_18506B3A')), os.getenv(os.getenv(
        'VIBE_9979AEDC')): os.getenv(os.getenv('VIBE_D7B936D9'))}

    async def fake_resolve_signing_key(_: dict[str, str]):
        return os.getenv(os.getenv('VIBE_256831F5'))

    def fake_get_unverified_header(_: str):
        return header

    def fake_decode(_: str, *, key=None, **__):
        assert key == os.getenv(os.getenv('VIBE_256831F5'))
        return dict(claims)
    monkeypatch.setattr(gateway_main, os.getenv(os.getenv('VIBE_BE62FAFA')),
        os.getenv(os.getenv('VIBE_256831F5')), raising=int(os.getenv(os.
        getenv('VIBE_F87801AD'))))
    monkeypatch.setattr(gateway_main, os.getenv(os.getenv('VIBE_93F11B0A')),
        fake_resolve_signing_key)
    monkeypatch.setattr(gateway_main.jwt, os.getenv(os.getenv(
        'VIBE_B4DF7000')), fake_get_unverified_header)
    monkeypatch.setattr(gateway_main.jwt, os.getenv(os.getenv(
        'VIBE_340C2E73')), fake_decode)
