from types import SimpleNamespace

import pytest

from services.common.authorization import authorize


class DummyRequest(SimpleNamespace):
    headers: dict


@pytest.mark.asyncio
async def test_operations_admin_allow(monkeypatch):
    # Monkeypatch PolicyClient.evaluate to allow ops.memory.list
    from services.common import authorization as auth_mod

    async def allow_eval(self, request):  # type: ignore[unused-argument]
        assert request.action == "ops.memory.list"
        return True

    monkeypatch.setattr(auth_mod.PolicyClient, "evaluate", allow_eval)
    # Reset internal singleton if present
    auth_mod._POLICY_CLIENT = None  # type: ignore[attr-defined]
    req = DummyRequest(headers={})
    await authorize(
        request=req,
        action="ops.memory.list",
        resource="OperationsAdministration",
        context={"tenant": "t1"},
    )


@pytest.mark.asyncio
async def test_operations_admin_deny(monkeypatch):
    from services.common import authorization as auth_mod

    async def deny_eval(self, request):  # type: ignore[unused-argument]
        return False

    monkeypatch.setattr(auth_mod.PolicyClient, "evaluate", deny_eval)
    req = DummyRequest(headers={})
    with pytest.raises(Exception):
        await authorize(
            request=req,
            action="ops.memory.list",
            resource="OperationsAdministration",
            context={"tenant": "t1"},
        )
