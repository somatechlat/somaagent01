import json
import argparse
import pytest

from scripts import persona_admin as cli


class FakeClient:
    def __init__(self):
        import asyncio
        self._loop = asyncio.new_event_loop()

    def _get_loop(self):
        return self._loop

    async def get_persona(self, persona_id):
        return {"id": persona_id, "name": "Test Persona", "_etag": "abc"}

    async def put_persona(self, persona_id, payload, *, etag=None):
        assert isinstance(payload, dict)
        if etag and etag != "good-etag":
            raise RuntimeError("412 Precondition Failed: ETag mismatch")
        return {"id": persona_id, "updated": True}

    async def delete_persona(self, persona_id):
        return {"id": persona_id, "deleted": True}

    async def _request(self, method, path, *, json=None, params=None, headers=None, allow_404=False):  # noqa: WPS211
        # Simulate ETag precondition for DELETE
        if method == "DELETE" and headers and headers.get("If-Match") == "bad-etag":
            raise RuntimeError("412 Precondition Failed: ETag mismatch")
        return {"ok": True}


@pytest.fixture(autouse=True)
def patch_client(monkeypatch):
    from python.integrations import somabrain_client

    fake = FakeClient()
    monkeypatch.setattr(somabrain_client.SomaBrainClient, "get", staticmethod(lambda: fake))
    yield


def test_persona_get_prints_json(capsys):
    ns = argparse.Namespace(persona_id="p1")
    code = cli.cmd_get(ns)
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["id"] == "p1"


def test_persona_put_with_etag_good(tmp_path, capsys):
    p = tmp_path / "p.json"
    p.write_text("{}")
    ns = argparse.Namespace(persona_id="p1", path=str(p), etag="good-etag")
    code = cli.cmd_put(ns)
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["updated"] is True


def test_persona_put_with_etag_conflict(tmp_path, capsys):
    p = tmp_path / "p.json"
    p.write_text("{}")
    ns = argparse.Namespace(persona_id="p1", path=str(p), etag="bad-etag")
    code = cli.cmd_put(ns)
    assert code != 0
    err = capsys.readouterr().err
    assert "412" in err or "Precondition Failed" in err


def test_persona_delete_with_etag_conflict(capsys):
    ns = argparse.Namespace(persona_id="p1", etag="bad-etag")
    code = cli.cmd_delete(ns)
    assert code != 0
    err = capsys.readouterr().err
    assert "412" in err or "Precondition Failed" in err
