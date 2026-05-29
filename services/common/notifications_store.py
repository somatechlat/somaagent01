"""Notifications store — persistent notification storage.

VIBE COMPLIANT: Uses Django ORM exclusively.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.utils import timezone

from services.common.store_base import BaseStore

LOGGER = logging.getLogger(__name__)


class NotificationsStore(BaseStore[Dict[str, Any]]):
    """Django ORM-backed store for notifications."""

    async def ensure_schema(self) -> None:
        """Schema managed by Django migrations."""
        pass

    async def get(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get a notification by ID."""
        from admin.core.models import Notification

        n = await Notification.objects.filter(id=identifier).afirst()
        if not n:
            return None
        return {
            "id": str(n.id),
            "user_id": n.user_id,
            "title": n.title,
            "body": n.message,
            "severity": n.notification_type,
            "read_at": n.read_at.isoformat() if n.read_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }

    async def delete(self, identifier: str) -> bool:
        """Remove a notification."""
        from admin.core.models import Notification

        deleted, _ = await Notification.objects.filter(id=identifier).adelete()
        return deleted > 0

    async def list(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 50,
        unread_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """List notifications for tenant/user."""
        from admin.core.models import Notification

        qs = Notification.objects.filter(tenant=tenant_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if unread_only:
            qs = qs.filter(is_read=False)
        qs = qs.order_by("-created_at")[:limit]

        results = []
        async for n in qs:
            results.append(
                {
                    "id": str(n.id),
                    "user_id": n.user_id,
                    "title": n.title,
                    "body": n.message,
                    "severity": n.notification_type,
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
            )
        return results

    async def create(
        self,
        tenant_id: str,
        user_id: Optional[str],
        ntype: str,
        title: str,
        body: str,
        severity: str = "info",
        ttl_seconds: Optional[int] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a notification."""
        from admin.core.models import Notification

        obj = await Notification.objects.acreate(
            tenant=tenant_id,
            user_id=user_id or "",
            notification_type=severity,
            title=title,
            message=body,
            data=meta or {},
        )
        return str(obj.id)

    async def mark_read(
        self,
        tenant_id: str,
        notif_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Mark a notification as read."""
        from admin.core.models import Notification

        qs = Notification.objects.filter(id=notif_id, tenant=tenant_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        await qs.aupdate(is_read=True, read_at=timezone.now())

    async def clear(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
    ) -> None:
        """Clear all notifications."""
        from admin.core.models import Notification

        qs = Notification.objects.filter(tenant=tenant_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        await qs.adelete()
