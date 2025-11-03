import json
import types
import argparse
import builtins
import io
import os
import sys
import pytest

from scripts import constitution_admin as cli


class FakeClient:
    def __init__(self):
        import asyncio
        self._loop = asyncio.new_event_loop()
        self._policy_updates = 0

    def _get_loop(self):
        return self._loop

    async def constitution_version(self):
        return {"checksum": "abc123", "version": 7}

    async def constitution_validate(self, payload):
        assert isinstance(payload, dict) and "document" in payload
        return {"status": "ok", "normalized": {"rules": 3}}

    async def constitution_load(self, payload):
        assert isinstance(payload, dict) and "document" in payload
        return {"status": "loaded", "checksum": "def456"}

    async def update_opa_policy(self):
        self._policy_updates += 1
        return {"policy_hash": "hash-001", "updated_at": "now"}

    async def opa_policy(self):
        return {"policy_hash": "hash-001", "updated_at": "now", "version": 1}


@pytest.fixture(autouse=True)
def patch_client(monkeypatch):
    # Patch SomaBrainClient.get() to return our fake
    from python.integrations import somabrain_client

    fake = FakeClient()
    monkeypatch.setattr(somabrain_client.SomaBrainClient, "get", staticmethod(lambda: fake))
    yield


def test_version_prints_json(capsys):
    ns = argparse.Namespace()
    ns.func = cli.cmd_version
    code = cli.cmd_version(ns)
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["checksum"] == "abc123"


def test_validate_reads_json(tmp_path, capsys):
    doc = {"rules": [1, 2, 3]}
    p = tmp_path / "const.json"
    p.write_text(json.dumps(doc))
    ns = argparse.Namespace(path=str(p))
    code = cli.cmd_validate(ns)
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "ok"


def test_load_requires_force(tmp_path, capsys):
    p = tmp_path / "const.json"
    p.write_text("{}")
    ns = argparse.Namespace(path=str(p), force=False)
    code = cli.cmd_load(ns)
    assert code != 0
    err = capsys.readouterr().err
    assert "Refusing to load" in err


def test_load_with_force(tmp_path, capsys):
    p = tmp_path / "const.json"
    p.write_text("{}")
    ns = argparse.Namespace(path=str(p), force=True)
    code = cli.cmd_load(ns)
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "loaded"


def test_load_triggers_policy_update(tmp_path, capsys):
    p = tmp_path / "const.json"
    p.write_text("{}")
    ns = argparse.Namespace(path=str(p), force=True)
    # Run load; stderr should include the policy update note
    code = cli.cmd_load(ns)
    assert code == 0
    read = capsys.readouterr()
    assert "opa_policy_updated:" in read.err


def test_status_prints_checksum_and_policy(capsys):
    code = cli.cmd_status(argparse.Namespace())
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "constitution" in data
    assert "policy" in data
