import types

import pytest

pytestmark = pytest.mark.asyncio


async def test_build_context_flag_off(monkeypatch):
    from services.common import learning as l

    monkeypatch.setattr(l.cfg, "flag", lambda k: False)

    res = await l.build_context("s-1", [{"role": "user", "content": "hi"}])
    assert res == []


async def test_publish_reward_flag_off(monkeypatch):
    from services.common import learning as l

    monkeypatch.setattr(l.cfg, "flag", lambda k: False)

    ok = await l.publish_reward("s-1", "signal", 0.5)
    assert ok is False


async def test_build_context_success_normalizes(monkeypatch):
    from services.common import learning as l

    # Enable flag
    monkeypatch.setattr(l.cfg, "flag", lambda k: True)

    class _Resp:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            return None

        def json(self):
            return self._data

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            return _Resp(
                [
                    {"role": "system", "content": "A"},
                    {"role": "assistant", "content": "B", "extra": 1},
                    {"role": "user", "content": "C"},
                    {"nope": 1},
                ]
            )

    monkeypatch.setattr(l, "httpx", types.SimpleNamespace(AsyncClient=lambda timeout: _Client()))

    out = await l.build_context("s-1", [{"role": "user", "content": "q"}])
    assert out == [
        {"role": "system", "content": "A"},
        {"role": "assistant", "content": "B"},
        {"role": "user", "content": "C"},
    ]


async def test_publish_reward_success(monkeypatch):
    from services.common import learning as l

    monkeypatch.setattr(l.cfg, "flag", lambda k: True)

    class _Resp:
        def raise_for_status(self):
            return None

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json):
            return _Resp()

    monkeypatch.setattr(l, "httpx", types.SimpleNamespace(AsyncClient=lambda timeout: _Client()))

    ok = await l.publish_reward("s-1", "response.delivered", 0.9, {"k": "v"})
    assert ok is True
