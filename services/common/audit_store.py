"""Audit Store — persistent audit event storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class AuditStore(BaseStore[Dict[str, Any]]):
    """Django ORM-backed store for audit events."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def record(
        self,
        event_type: str,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist an audit event."""
        from admin.platform.models import AuditLog

        await AuditLog.objects.acreate(
            action=event_type,
            actor_id=actor or None,
            resource_type=resource or "",
            # Not ``resource or None``: ``resource`` here is a resource *name*
            # ("auth", "tenant"), and ``resource_id`` is a UUIDField. Writing
            # a name into it raises, and callers around this store swallow the
            # error, so the event vanishes. This API carries no resource id.
            resource_id=None,
            new_value=payload or {},
        )

    async def log(
        self,
        *,
        request_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tenant: Optional[str] = None,
        subject: Optional[str] = None,
        action: str,
        resource: str,
        target_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        diff: Optional[Dict[str, Any]] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Persist a rich audit event.

        Mirrors the call shape used by tool-executor and the LLM invoke
        path.  Non-UUID context (session id, tenant name, trace id, a
        non-UUID subject or target) is kept in the ``new_value`` payload
        because the matching columns are UUID / IP-typed and writing a
        free-form string into them raises — the event would vanish.

        Raises on persistence failure; callers decide whether that is
        fatal.  Audit evidence is never silently dropped.
        """
        import uuid as _uuid

        from admin.platform.models import AuditLog

        def _as_uuid(value: Optional[str]) -> Optional[_uuid.UUID]:
            if not value:
                return None
            try:
                return _uuid.UUID(str(value))
            except (ValueError, AttributeError, TypeError):
                return None

        payload: Dict[str, Any] = dict(details or {})
        for key, val in (
            ("session_id", session_id),
            ("trace_id", trace_id),
            ("tenant", tenant),
            ("subject", subject),
            ("target_id", target_id),
        ):
            if val is not None:
                payload.setdefault(key, val)

        await AuditLog.objects.acreate(
            action=action,
            actor_id=_as_uuid(subject),
            resource_type=resource or "",
            resource_id=_as_uuid(target_id),
            new_value=payload,
            old_value=diff,
            request_id=request_id or "",
            ip_address=ip,
            user_agent=user_agent or "",
        )

    async def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single audit event by ID."""
        from admin.platform.models import AuditLog

        event = await AuditLog.objects.filter(id=identifier).afirst()
        if not event:
            return None
        return self._serialize(event)

    async def list(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List audit events."""
        from admin.platform.models import AuditLog

        qs = AuditLog.objects.all().order_by("-created_at")
        if event_type:
            qs = qs.filter(action=event_type)
        qs = qs[:limit]

        results = []
        async for event in qs:
            results.append(self._serialize(event))
        return results

    @staticmethod
    def _serialize(event: Any) -> Dict[str, Any]:
        """Map an AuditLog row to the dict shape API callers serialize.

        Keeps both the store-generic keys (``event_type``, ``payload``)
        and the richer keys the NDJSON export emits, so one row shape
        serves every reader.
        """
        payload = event.new_value or {}
        return {
            "id": str(event.id),
            "event_type": event.action,
            "actor": str(event.actor_id) if event.actor_id else None,
            "resource": event.resource_type,
            "action": event.action,
            "payload": payload,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "timestamp": event.created_at.isoformat() if event.created_at else None,
            "session_id": payload.get("session_id"),
            "tenant": payload.get("tenant"),
            "details": payload,
            "trace_id": payload.get("trace_id"),
            "request_id": event.request_id or payload.get("request_id"),
            "ip": event.ip_address or payload.get("ip"),
            "user_agent": event.user_agent or payload.get("user_agent"),
        }

    async def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a new audit event."""
        await self.record(
            event_type=record.get("event_type", "unknown"),
            actor=record.get("actor"),
            resource=record.get("resource"),
            action=record.get("action"),
            payload=record.get("payload"),
        )
        return record

    async def update(self, identifier: str, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Audit events are immutable."""
        raise RuntimeError("Audit events are immutable")

    async def delete(self, identifier: str) -> bool:
        """Remove an audit event."""
        from admin.platform.models import AuditLog

        deleted, _ = await AuditLog.objects.filter(id=identifier).adelete()
        return deleted > 0


def from_env() -> AuditStore:
    """Create an AuditStore from environment variables."""
    return AuditStore()
