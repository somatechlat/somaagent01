"""
Audit wire-tap publisher for policy/tool/task decisions.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.common.messaging_utils import build_headers, idempotency_key
from services.common.publisher import DurablePublisher
import os


class AuditPublisher:
    def __init__(self, publisher: DurablePublisher, topic: Optional[str] = None) -> None:
        self.publisher = publisher
        self.topic = topic or os.environ.get("AUDIT_TOPIC", "audit.events")

    async def publish(
        self,
        event: Dict[str, Any],
        *,
        tenant: Optional[str] = None,
        session_id: Optional[str] = None,
        persona_id: Optional[str] = None,
        correlation: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = build_headers(
            tenant=tenant,
            session_id=session_id,
            persona_id=persona_id,
            event_type=event.get("type"),
            event_id=event.get("event_id"),
            schema=event.get("version") or event.get("schema"),
            correlation=correlation or event.get("correlation_id"),
        )
        return await self.publisher.publish(
            self.topic,
            {**event, "correlation_id": headers["correlation_id"]},
            headers=headers,
            dedupe_key=idempotency_key(event, seed=correlation),
            session_id=session_id,
            tenant=tenant,
        )
