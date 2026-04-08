from __future__ import annotations

import os
import sys
import types
from types import SimpleNamespace

import pytest

from admin.chat.api import chat as chat_api
from admin.common.exceptions import UnauthorizedError
from admin.common.session_manager import SessionManager
from services.gateway import auth as gateway_auth


@pytest.mark.asyncio
async def test_authorize_request_fails_closed_when_auth_disabled_without_explicit_bypass(monkeypatch):
    monkeypatch.setattr(
        gateway_auth,
        "settings",
        SimpleNamespace(
            AUTH_REQUIRED=False,
            ALLOW_INSECURE_AUTH_BYPASS=False,
            IS_DEV_ENV=True,
        ),
    )
    request = SimpleNamespace(headers={})

    with pytest.raises(UnauthorizedError):
        await gateway_auth.authorize_request(request)


@pytest.mark.asyncio
async def test_authorize_request_allows_explicit_dev_bypass(monkeypatch):
    monkeypatch.setattr(
        gateway_auth,
        "settings",
        SimpleNamespace(
            AUTH_REQUIRED=False,
            ALLOW_INSECURE_AUTH_BYPASS=True,
            IS_DEV_ENV=True,
        ),
    )
    request = SimpleNamespace(headers={})

    payload = await gateway_auth.authorize_request(request)
    assert payload["user_id"] == "test_user"


@pytest.mark.asyncio
async def test_send_message_stream_mode_returns_generated_id(monkeypatch):
    class _ConversationManager:
        @staticmethod
        def get(id):
            return SimpleNamespace(agent_id="agent-test-id")

    async def _run_sync(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    def _sync_to_async(fn):
        async def _wrapper(*args, **kwargs):
            return await _run_sync(fn, *args, **kwargs)

        return _wrapper

    monkeypatch.setattr(chat_api, "get_current_user", lambda _request: SimpleNamespace(sub="user-1"))
    monkeypatch.setattr(chat_api.Conversation, "objects", _ConversationManager())
    monkeypatch.setattr("asgiref.sync.sync_to_async", _sync_to_async)

    response = await chat_api.send_message(
        request=SimpleNamespace(),
        conversation_id="conv-1",
        payload=chat_api.SendMessageRequest(content="hello", stream=True),
    )

    assert response["status"] == "streaming"
    assert response["conversation_id"] == "conv-1"
    assert isinstance(response["id"], str)
    assert response["id"]


@pytest.mark.asyncio
async def test_resolve_permissions_fails_closed_when_spicedb_unavailable(monkeypatch):
    module = types.ModuleType("services.common.spicedb_client")

    async def _broken_client():
        raise RuntimeError("spicedb unavailable")

    module.get_spicedb_client = _broken_client
    sys.modules["services.common.spicedb_client"] = module
    monkeypatch.setenv("SA01_AUTHZ_FAIL_OPEN", "false")

    manager = SessionManager(redis_url="redis://localhost:6379/0")
    permissions = await manager.resolve_permissions("user-1", "tenant-1", ["admin"])
    assert permissions == []


@pytest.mark.asyncio
async def test_resolve_permissions_can_optionally_fail_open(monkeypatch):
    class _FakeSpiceDb:
        async def get_permissions(self, *_args, **_kwargs):
            raise RuntimeError("down")

    module = types.ModuleType("services.common.spicedb_client")

    async def _fake_client():
        return _FakeSpiceDb()

    module.get_spicedb_client = _fake_client
    sys.modules["services.common.spicedb_client"] = module
    monkeypatch.setenv("SA01_AUTHZ_FAIL_OPEN", "true")

    manager = SessionManager(redis_url="redis://localhost:6379/0")
    permissions = await manager.resolve_permissions("user-1", "tenant-1", ["admin"])
    assert "manage" in permissions


def test_verify_script_no_longer_contains_hardcoded_bearer_token():
    verify_script = os.path.join(os.getcwd(), "verify_int.py")
    with open(verify_script, encoding="utf-8") as f:
        content = f.read()
    assert "sbk_proof_123456" not in content
