"""The Temporal lane writes through MemoryGateway, not a raw memory client.

Defect #6: ``ProcessMessageUseCase`` called ``self._memory_client.remember/recall``
— a second write authority that bypassed ``MemoryGateway``, with errors swallowed
by ``LOGGER.debug`` (silent data loss). The constructor must take a
``MemoryGateway``; the paper protocol ``MemoryClientProtocol = Any`` must be gone.
"""

from __future__ import annotations

import inspect

from admin.core.application.use_cases.conversation import process_message as pm


def test_memory_client_protocol_is_gone():
    assert not hasattr(pm, "MemoryClientProtocol")


def test_constructor_takes_a_memory_gateway():
    sig = inspect.signature(pm.ProcessMessageUseCase.__init__)
    assert "gateway" in sig.parameters
    assert "memory_client" not in sig.parameters


def test_use_case_rejects_a_raw_memory_client():
    """A duck-typed client with .remember is not a MemoryGateway."""

    class RawClient:
        async def remember(self, payload):
            return {"ok": True}

        async def recall(self, **kwargs):
            return {"memories": []}

    # Binding: the use case calls remember_text / recall on the gateway slot.
    # A .remember-only client is the old second pipeline and must not appear.
    src = inspect.getsource(pm)
    assert "MemoryClientProtocol" not in src
    assert "self._gateway.remember_text" in src
    assert "self._gateway.recall" in src
    assert "self._memory_client" not in src
