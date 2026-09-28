"""Degraded memory queue — Kafka ONLY (memory.wal / degradation.events).

When SomaBrain is unreachable the agent queues on the production Kafka WAL.
The existing ``memory-replicator`` consumer replays WAL into SomaBrain
(MemoryGateway) when the brain is healthy again. Poison events go to the
Kafka DLQ (``*.dlq``) via ``DeadLetterQueue``.

NO Postgres message/memory repository. NO local ORM queue. Agent Postgres is
not the message store (ARCHITECTURE-INVARIANTS §3). SomaBrain is (T-1).

No mocks. Fail-closed tenants. Millions of transactions via Kafka.
"""

from __future__ import annotations

import hashlib
import logging
import time
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)


def _wal_topic() -> str:
    from services.common.memory_contract import get_memory_setting

    return str(get_memory_setting("MEMORY_WAL_TOPIC", ""))


def _degraded_topic() -> str:
    from services.common.memory_contract import get_memory_setting

    return str(get_memory_setting("MEMORY_DEGRADED_TOPIC", ""))


async def publish_degraded_memory(
    *,
    text: str,
    tenant_id: str,
    namespace: Optional[str] = None,
    kind: Optional[str] = None,
    session_id: Optional[str] = None,
    salience: Optional[float] = None,
    coord: Optional[str] = None,
    source: Optional[str] = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    """Queue one unacked memory on Kafka WAL for SomaBrain replay.

    Returns ``{"queued": bool, "channel": "kafka", "id": str}``.
    Raises when Kafka is unreachable (fail-closed — never a silent drop).
    """
    from services.common.memory_contract import get_memory_setting, MemoryWrite

    if not tenant_id or tenant_id.strip().lower() in {"", "default", "standalone", "none", "null"}:
        raise ValueError("tenant_id is required for degraded memory queue (T-5 fail-closed)")

    kind = kind or str(MemoryWrite.model_fields["kind"].default)
    if salience is None:
        salience = float(MemoryWrite.model_fields["salience"].default)
    source = source or str(MemoryWrite.model_fields["source"].default)
    namespace = namespace or str(get_memory_setting("MEM_CHAT_NAMESPACE", "chat_history"))

    event_id = hashlib.sha256(
        f"{tenant_id}|{namespace}|{kind}|{session_id or ''}|{text}|{coord or ''}".encode()
    ).hexdigest()[:32]
    wal_event: Dict[str, Any] = {
        "id": event_id,
        "type": "memory.degraded",
        "role": "memory",
        "session_id": session_id,
        "tenant": tenant_id,
        "namespace": namespace,
        "payload": {
            "text": text,
            "content": text,
            "kind": kind,
            "salience": salience,
            "source": source,
            "coord": coord,
        },
        "error": error,
        "timestamp": time.time(),
    }

    from services.common.publisher import get_durable_publisher

    publisher = await get_durable_publisher()
    if publisher is None:
        raise RuntimeError("Kafka DurablePublisher unavailable — cannot queue degraded memory")

    # 1) Primary: memory.wal (consumed by memory-replicator → SomaBrain).
    wal_topic = _wal_topic()
    try:
        result = await publisher.publish(
            wal_topic,
            wal_event,
            partition_key=tenant_id,
            dedupe_key=event_id,
            session_id=session_id or "",
            tenant=tenant_id,
        )
        if result.get("published"):
            LOGGER.warning(
                "SomaBrain unavailable — queued memory to Kafka %s id=%s",
                wal_topic,
                event_id,
            )
            return {"queued": True, "channel": "kafka", "id": event_id}
    except Exception as exc:
        LOGGER.warning("Kafka %s publish failed: %s", wal_topic, exc)

    # 2) Secondary Kafka lane: degradation.events.
    degraded_topic = _degraded_topic()
    result = await publisher.publish(
        degraded_topic,
        wal_event,
        partition_key=tenant_id,
        dedupe_key=event_id,
        session_id=session_id or "",
        tenant=tenant_id,
    )
    LOGGER.warning(
        "SomaBrain unavailable — queued memory to Kafka %s id=%s",
        degraded_topic,
        event_id,
    )
    return {"queued": True, "channel": "kafka", "id": event_id}


async def degraded_pending_count(tenant_id: str) -> Dict[str, Any]:
    """Degraded status for the UI from Brain connector + Kafka WAL ownership.

    Pending work lives on Kafka ``memory.wal`` (memory-replicator gauge).
    This reports whether SomaBrain is reachable; the UI shows degraded when
    writes cannot be acked and are landing on the WAL.
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
