"""Fail‑safe persistence helper used by services that produce events.

The helper implements the *VIBE* principle of a **single source of truth** for
event persistence while the external Somabrain service may be unavailable.

Workflow:
1. Store the raw ``event`` in the Redis transient buffer (``services.common.redis_client``).
2. Publish the event to the write‑ahead‑log (Kafka) via the provided ``publisher``.
3. The background ``degraded_syncer`` (not part of this patch) will later read
   from Redis, call Somabrain, and clean the buffer once the enrichment has
   succeeded.

All configuration (topic name, tenant) is passed in by the caller so the helper
remains stateless and easily unit‑testable.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from services.common.publisher import DurablePublisher
from services.common.redis_client import set_event

LOGGER = logging.getLogger(__name__)


async def persist_event(
    *,
    event: Dict[str, Any],
    service_name: str,
    publisher: DurablePublisher,
    wal_topic: str,
    tenant: str | None = None,
) -> None:
    """Persist *event* in a degradation‑aware manner.

    Parameters
    ----------
    event:
        The event dictionary that will be sent to the Kafka WAL.
    service_name:
        Identifier used for circuit‑breaker lookup (e.g. ``"gateway"``).  The
        current implementation does not use the breaker directly but keeping the
        argument allows future extensions without breaking the API.
    publisher:
        Instance of :class:`DurablePublisher` that knows how to write to Kafka.
    wal_topic:
        Kafka topic name for the write‑ahead‑log (usually ``memory.wal``).
    tenant:
        Optional tenant identifier forwarded to the publisher.
    """
    # 1️⃣ Store in Redis so the event is not lost if Somabrain fails.
    event_id = str(event.get("event_id"))
    try:
        await set_event(event_id, event)
    except Exception as exc:  # pragma: no cover – defensive, should not happen
        LOGGER.error("Failed to write event %s to Redis buffer: %s", event_id, exc)
        raise

    # 2️⃣ Publish to the WAL.  Errors here are considered critical – the caller
    #    (gateway) will surface them as HTTP 500.
    try:
        await publisher.publish(
            wal_topic,
            event,
            dedupe_key=event_id,
            session_id=str(event.get("session_id")),
            tenant=tenant,
        )
    except Exception as exc:  # pragma: no cover – let the caller handle
        LOGGER.error("Failed to publish event %s to WAL: %s", event_id, exc)
        raise

    # 3️⃣ No direct Somabrain call – the background syncer will handle it.
    return None
