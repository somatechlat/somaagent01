"""ChatService must not fake memory success or use an empty tenant.

T-1 / tenant law: a request without a tenant is denied, never assigned to
"" or "default". Memory read failures must surface as ``MemoryRecallUnavailable``
— never as a silent empty list that is indistinguishable from "no memories".

C1 residual: ``send_message`` used to build a ``ChatTurn(tenant_id="")`` and
``recall_memories`` used to return ``[]`` on outage.
"""

from __future__ import annotations

import asyncio

import pytest

from services.common.chat_service import ChatService
from services.common.memory_contract import MemoryRecallUnavailable


def test_send_message_requires_nonempty_tenant():
    """A ChatTurn built with an empty tenant must be refused, not silently sent."""
    svc = ChatService()

    async def _run() -> None:
        # _load_capsule is the only DB touch; stub it so the test is pure.
        async def _fake_load(capsule_id: str):
            class _Cap:
                tenant_id = "t-1"
                id = capsule_id

            return _Cap()

        svc._load_capsule = _fake_load  # type: ignore[method-assign]
        with pytest.raises((ValueError, PermissionError)):
            # Callers that pass no tenant_id must be refused.
            agen = svc.send_message(
                conversation_id="c-1",
                agent_id="a-1",
                content="hello",
                user_id="u-1",
            )
            # send_message is an async generator — drive it to the first yield.
            async for _ in agen:
                break

    asyncio.run(_run())


def test_recall_memories_raises_on_unavailable(monkeypatch):
    """An outage must raise MemoryRecallUnavailable — never a silent []."""
    svc = ChatService()

    async def _boom(*_a, **_kw):
        raise MemoryRecallUnavailable("brain down")

    class _FakeGateway:
        recall = _boom

    import services.common.chat_service as cs

    monkeypatch.setattr(cs, "get_memory_gateway", lambda: _FakeGateway(), raising=False)
    # Patch the import site inside the method.
    import services.common.memory_gateway as mg

    monkeypatch.setattr(mg, "get_memory_gateway", lambda: _FakeGateway())

    async def _run() -> None:
        with pytest.raises(MemoryRecallUnavailable):
            await svc.recall_memories(
                agent_id="a-1",
                user_id="u-1",
                query="q",
                limit=5,
                tenant_id="t-1",
            )

    asyncio.run(_run())
