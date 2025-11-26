"""
Server‑Sent Events (SSE) router – extracted from the original gateway monolith.

Provides the `/v1/session/{session_id}/events` endpoint used by the UI to
receive real‑time conversation updates. The implementation mirrors the legacy
behaviour (Kafka consumer per connection, JSON‑encoded events) but lives in a
dedicated, testable module.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from services.common.event_bus import iterate_topic, KafkaSettings

# Re‑use the configuration helper from the monolith.
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)

router = APIRouter()


def _sse_disabled() -> bool:
    """Return True when SSE is disabled via the feature flag.

    The original gateway consulted the `SA01_SSE_ENABLED` env var. We retain the
    same logic so existing deployments behave identically.
    """
    return cfg.env("SA01_SSE_ENABLED").lower() not in {"true", "1", "yes"}


@router.get("/v1/session/{session_id}/events")
async def sse_session_events(session_id: str) -> StreamingResponse:
    """Stream outbound conversation events for a session via Server‑Sent Events.

    * Consumes from the ``CONVERSATION_OUTBOUND`` Kafka topic.
    * Filters events by ``session_id``.
    * Returns a ``text/event‑stream`` response.
    """
    if _sse_disabled():
        raise HTTPException(status_code=503, detail="SSE disabled")

    topic = cfg.env("CONVERSATION_OUTBOUND")
    group_base = f"sse-{session_id}"

    async def event_iter() -> AsyncIterator[bytes]:
        # Unique consumer group per connection prevents cross‑client interference.
        group_id = f"{group_base}-{uuid.uuid4().hex[:8]}"
        try:
            async for payload in iterate_topic(
                topic=topic, group_id=group_id, settings=KafkaSettings.from_env()
            ):
                try:
                    sid = payload.get("session_id") or (payload.get("payload") or {}).get(
                        "session_id"
                    )
                    if sid != session_id:
                        continue
                    data = json.dumps(payload, ensure_ascii=False)
                    yield (f"data: {data}\n\n").encode("utf-8")
                except Exception:
                    # Skip malformed payloads – continue streaming.
                    continue
        except Exception:
            # On iterator failure, close the stream gracefully.
            return

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(event_iter(), media_type="text/event-stream", headers=headers)
