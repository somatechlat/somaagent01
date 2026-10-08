"""Status surface for the memory write outbox.

There is exactly **one** degraded path for a memory write, and it is not here:
it is the MemoryGateway seam's ``memory.wal`` outbox. ``FanoutMemoryGateway``
accepts every write into that outbox **before** its network hop (T-6 durable-
before-hop, ``memory_gateway.durable_accept_memory``); a successful ack
completes the row, a failed hop leaves it pending for the outbox drain and
``memory-replicator`` to replay. A caller whose write never reached the seam
queues through the same entry point. Two entry points would be two replay
authorities — see SOMA degradation doctrine (T-6 / one authority).

This module only reports that outbox's state to the UI. It deliberately does
not publish anything: an earlier ``publish_degraded_memory`` here wrote
straight to Kafka and was a second degraded path.

No mocks. Fail-closed tenants.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

LOGGER = logging.getLogger(__name__)


def _wal_topic() -> str:
    from services.common.memory_contract import get_memory_setting

    return str(get_memory_setting("MEMORY_WAL_TOPIC"))


async def degraded_pending_count(tenant_id: str) -> Dict[str, Any]:
    """Degraded status for the UI: brain reachability and WAL ownership.

    Pending work lives on ``memory.wal``, drained from the memory write
    outbox and replayed by memory-replicator. This reports whether SomaBrain
    is reachable; the UI shows degraded when writes cannot be acked and are
    sitting on that outbox.
    """
    healthy = False
    try:
        from admin.core.chat_orchestrator import _require_memory_gateway

        gateway = _require_memory_gateway()
        await gateway.recall("healthcheck", 1, tenant_id)
        healthy = True
    except Exception:
        healthy = False

    return {
        "tenant_id": tenant_id,
        "degraded": not healthy,
        "brain_reachable": healthy,
        "queue": _wal_topic(),
    }
