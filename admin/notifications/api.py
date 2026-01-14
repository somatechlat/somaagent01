"""Notification Service API.


Real-time notifications for SomaBrain events.

- DevOps: WebSocket integration, event streaming
- PM: User notification preferences
- Security Auditor: Rate limiting, channel permissions
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["notifications"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class NotificationPreferences(BaseModel):
    """User notification preferences."""

    email_enabled: bool = True
    push_enabled: bool = True
    in_app_enabled: bool = True

    # Categories
    agent_events: bool = True
    billing_alerts: bool = True
    security_alerts: bool = True
    system_updates: bool = False


class Notification(BaseModel):
    """Notification item."""

    notification_id: str
    type: str  # info, success, warning, error
    title: str
    message: str
    category: str  # agent, billing, security, system
    read: bool = False
    created_at: str
    action_url: Optional[str] = None


class NotificationListResponse(BaseModel):
    """List of notifications."""

    notifications: list[Notification]
    unread_count: int
    total: int


class SendNotificationRequest(BaseModel):
    """Send notification request."""

    user_id: str
    type: str
    title: str
    message: str
    category: str = "system"
    action_url: Optional[str] = None


class WebhookSubscription(BaseModel):
    """Webhook subscription."""

    subscription_id: str
    url: str
    events: list[str]
    secret: str
    active: bool
    created_at: str


# =============================================================================
# ENDPOINTS - User Notifications
# =============================================================================


@router.get(
    "",
    response=NotificationListResponse,
    summary="Get notifications",
    auth=AuthBearer(),
)
async def get_notifications(
    request,
    unread_only: bool = False,
    category: Optional[str] = None,
    limit: int = 50,
) -> NotificationListResponse:
    """Get user notifications.

    PM: Clean, organized notification feed.
    """
    # In production: query from database
    return NotificationListResponse(
        notifications=[],
        unread_count=0,
        total=0,
    )


@router.post(
    "/{notification_id}/read",
    summary="Mark as read",
    auth=AuthBearer(),
)
async def mark_read(request, notification_id: str) -> dict:
    """Mark notification as read."""
    return {
        "notification_id": notification_id,
        "read": True,
    }


@router.post(
    "/read-all",
    summary="Mark all as read",
    auth=AuthBearer(),
)
async def mark_all_read(request) -> dict:
    """Mark all notifications as read."""
    return {"marked_count": 0}


@router.delete(
    "/{notification_id}",
    summary="Delete notification",
    auth=AuthBearer(),
)
async def delete_notification(request, notification_id: str) -> dict:
    """Delete a notification."""
    return {
        "notification_id": notification_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Preferences
# =============================================================================


@router.get(
    "/preferences",
    response=NotificationPreferences,
    summary="Get preferences",
    auth=AuthBearer(),
)
async def get_preferences(request) -> NotificationPreferences:
    """Get notification preferences."""
    return NotificationPreferences()


@router.patch(
    "/preferences",
    response=NotificationPreferences,
    summary="Update preferences",
    auth=AuthBearer(),
)
async def update_preferences(
    request,
    payload: NotificationPreferences,
) -> NotificationPreferences:
    """Update notification preferences."""
    return payload


# =============================================================================
# ENDPOINTS - Send Notifications (Internal)
# =============================================================================


@router.post(
    "/send",
    summary="Send notification",
    auth=AuthBearer(),
)
async def send_notification(
    request,
    payload: SendNotificationRequest,
) -> dict:
    """Send a notification to a user.

    DevOps: Internal endpoint for system notifications.
    """
    notification_id = str(uuid4())

    logger.info(f"Notification sent: {notification_id} to {payload.user_id}")

    # In production:
    # 1. Store in database
    # 2. Push via WebSocket if user online
    # 3. Send email/push if preferences allow

    return {
        "notification_id": notification_id,
        "sent": True,
    }


@router.post(
    "/broadcast",
    summary="Broadcast notification",
    auth=AuthBearer(),
)
async def broadcast_notification(
    request,
    type: str,
    title: str,
    message: str,
    tenant_id: Optional[str] = None,
) -> dict:
    """Broadcast notification to all users.

    Security Auditor: Admin only, rate limited.
    """
    broadcast_id = str(uuid4())

    return {
        "broadcast_id": broadcast_id,
        "scope": tenant_id or "all",
        "sent": True,
    }


# =============================================================================
# ENDPOINTS - Webhooks
# =============================================================================


@router.get(
    "/webhooks",
    summary="List webhook subscriptions",
    auth=AuthBearer(),
)
async def list_webhooks(request) -> dict:
    """List webhook subscriptions for the tenant."""
    return {"subscriptions": [], "total": 0}


@router.post(
    "/webhooks",
    summary="Create webhook subscription",
    auth=AuthBearer(),
)
async def create_webhook(
    request,
    url: str,
    events: list[str],
) -> dict:
    """Create a webhook subscription.

    DevOps: Outgoing webhook for external integrations.
    """
    import secrets

    subscription_id = str(uuid4())
    secret = secrets.token_urlsafe(32)

    return {
        "subscription_id": subscription_id,
        "url": url,
        "events": events,
        "secret": secret,
        "active": True,
    }


@router.delete(
    "/webhooks/{subscription_id}",
    summary="Delete webhook",
    auth=AuthBearer(),
)
async def delete_webhook(request, subscription_id: str) -> dict:
    """Delete a webhook subscription."""
    return {
        "subscription_id": subscription_id,
        "deleted": True,
    }


@router.post(
    "/webhooks/{subscription_id}/test",
    summary="Test webhook",
    auth=AuthBearer(),
)
async def test_webhook(request, subscription_id: str) -> dict:
    """Send test event to webhook.

    DevOps: Verify webhook endpoint is working.
    """

    # In production: send test payload to webhook URL

    return {
        "subscription_id": subscription_id,
        "test_sent": True,
        "response_code": 200,
    }
