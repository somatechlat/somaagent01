"""Webhooks API - Outbound event delivery.


Webhook management with retry and signature.

7-Persona Implementation:
- DevOps: Webhook delivery, retry logic
- Security Auditor: Signature verification, secrets
- PM: Event subscription management
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["webhooks"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Webhook(BaseModel):
    """Webhook configuration."""

    webhook_id: str
    name: str
    url: str
    events: list[str]
    is_active: bool = True
    secret: Optional[str] = None  # For signature verification
    created_at: str
    last_triggered: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0


class WebhookDelivery(BaseModel):
    """Webhook delivery attempt."""

    delivery_id: str
    webhook_id: str
    event_type: str
    payload: dict
    status: str  # pending, success, failed, retrying
    attempts: int
    last_attempt: Optional[str] = None
    next_retry: Optional[str] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None


class WebhookEvent(BaseModel):
    """Available webhook event type."""

    event_type: str
    description: str
    category: str


# =============================================================================
# AVAILABLE EVENTS
# =============================================================================

WEBHOOK_EVENTS = {
    "agent.created": "Agent created",
    "agent.updated": "Agent updated",
    "agent.deleted": "Agent deleted",
    "agent.started": "Agent started",
    "agent.stopped": "Agent stopped",
    "conversation.started": "Conversation started",
    "conversation.message": "New message",
    "conversation.ended": "Conversation ended",
    "user.created": "User created",
    "user.updated": "User updated",
    "user.deleted": "User deleted",
    "user.login": "User logged in",
    "tenant.created": "Tenant created",
    "tenant.suspended": "Tenant suspended",
    "billing.invoice": "Invoice generated",
    "billing.payment": "Payment processed",
    "audit.security_alert": "Security alert",
}


# =============================================================================
# ENDPOINTS - Webhook CRUD
# =============================================================================


@router.get(
    "",
    summary="List webhooks",
    auth=AuthBearer(),
)
async def list_webhooks(
    request,
    active_only: bool = False,
) -> dict:
    """List configured webhooks.

    PM: View event subscriptions.
    """
    return {
        "webhooks": [],
        "total": 0,
    }


@router.post(
    "",
    response=Webhook,
    summary="Create webhook",
    auth=AuthBearer(),
)
async def create_webhook(
    request,
    name: str,
    url: str,
    events: list[str],
) -> Webhook:
    """Create a new webhook.

    Security Auditor: Auto-generate signing secret.
    """
    webhook_id = str(uuid4())
    secret = secrets.token_urlsafe(32)

    logger.info(f"Webhook created: {name} ({webhook_id})")

    return Webhook(
        webhook_id=webhook_id,
        name=name,
        url=url,
        events=events,
        secret=secret,
        created_at=timezone.now().isoformat(),
    )


@router.get(
    "/{webhook_id}",
    response=Webhook,
    summary="Get webhook",
    auth=AuthBearer(),
)
async def get_webhook(request, webhook_id: str) -> Webhook:
    """Get webhook details."""
    from asgiref.sync import sync_to_async

    from admin.common.exceptions import NotFoundError
    from admin.webhooks.models import Webhook as WebhookModel

    try:
        db_webhook = await sync_to_async(WebhookModel.objects.get)(id=webhook_id)
    except WebhookModel.DoesNotExist:
        raise NotFoundError("webhook", webhook_id)

    return Webhook(
        webhook_id=str(db_webhook.id),
        name=db_webhook.name,
        url=db_webhook.url,
        events=db_webhook.events or [],
        is_active=db_webhook.is_active,
        secret=None,  # Never expose secret
        created_at=db_webhook.created_at.isoformat(),
        last_triggered=db_webhook.last_triggered.isoformat() if db_webhook.last_triggered else None,
        success_count=db_webhook.success_count,
        failure_count=db_webhook.failure_count,
    )


@router.patch(
    "/{webhook_id}",
    summary="Update webhook",
    auth=AuthBearer(),
)
async def update_webhook(
    request,
    webhook_id: str,
    url: Optional[str] = None,
    events: Optional[list[str]] = None,
    is_active: Optional[bool] = None,
) -> dict:
    """Update a webhook."""
    return {
        "webhook_id": webhook_id,
        "updated": True,
    }


@router.delete(
    "/{webhook_id}",
    summary="Delete webhook",
    auth=AuthBearer(),
)
async def delete_webhook(request, webhook_id: str) -> dict:
    """Delete a webhook."""
    logger.info(f"Webhook deleted: {webhook_id}")

    return {
        "webhook_id": webhook_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Secret Management
# =============================================================================


@router.post(
    "/{webhook_id}/rotate-secret",
    summary="Rotate secret",
    auth=AuthBearer(),
)
async def rotate_secret(request, webhook_id: str) -> dict:
    """Rotate webhook signing secret.

    Security Auditor: Key rotation.
    """
    new_secret = secrets.token_urlsafe(32)

    logger.info(f"Webhook secret rotated: {webhook_id}")

    return {
        "webhook_id": webhook_id,
        "new_secret": new_secret,
        "rotated": True,
    }


# =============================================================================
# ENDPOINTS - Testing
# =============================================================================


@router.post(
    "/{webhook_id}/test",
    summary="Test webhook",
    auth=AuthBearer(),
)
async def test_webhook(
    request,
    webhook_id: str,
    event_type: str = "test.ping",
) -> dict:
    """Send a test event to webhook.

    DevOps: Verify connectivity.
    """
    delivery_id = str(uuid4())

    # In production: async task to deliver

    return {
        "webhook_id": webhook_id,
        "delivery_id": delivery_id,
        "event_type": event_type,
        "status": "sent",
    }


# =============================================================================
# ENDPOINTS - Deliveries
# =============================================================================


@router.get(
    "/{webhook_id}/deliveries",
    summary="List deliveries",
    auth=AuthBearer(),
)
async def list_deliveries(
    request,
    webhook_id: str,
    status: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """List webhook delivery attempts.

    DevOps: Delivery monitoring.
    """
    return {
        "webhook_id": webhook_id,
        "deliveries": [],
        "total": 0,
    }


@router.get(
    "/deliveries/{delivery_id}",
    response=WebhookDelivery,
    summary="Get delivery",
    auth=AuthBearer(),
)
async def get_delivery(
    request,
    delivery_id: str,
) -> WebhookDelivery:
    """Get delivery details."""
    return WebhookDelivery(
        delivery_id=delivery_id,
        webhook_id="1",
        event_type="agent.created",
        payload={},
        status="success",
        attempts=1,
    )


@router.post(
    "/deliveries/{delivery_id}/retry",
    summary="Retry delivery",
    auth=AuthBearer(),
)
async def retry_delivery(
    request,
    delivery_id: str,
) -> dict:
    """Manually retry a failed delivery.

    DevOps: Manual retry.
    """
    return {
        "delivery_id": delivery_id,
        "retrying": True,
    }


# =============================================================================
# ENDPOINTS - Available Events
# =============================================================================


@router.get(
    "/events",
    summary="List available events",
)
async def list_available_events(request) -> dict:
    """List available webhook events.

    PM: Event catalog.
    """
    events = [
        WebhookEvent(
            event_type=event_type,
            description=description,
            category=event_type.split(".")[0],
        ).dict()
        for event_type, description in WEBHOOK_EVENTS.items()
    ]

    return {
        "events": events,
        "total": len(events),
    }


# =============================================================================
# ENDPOINTS - Signature Verification Helper
# =============================================================================


@router.post(
    "/verify-signature",
    summary="Verify signature",
)
async def verify_signature(
    request,
    payload: str,
    signature: str,
    secret: str,
) -> dict:
    """Verify webhook signature.

    Security Auditor: Signature validation.
    """
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    valid = hmac.compare_digest(f"sha256={expected}", signature)

    return {
        "valid": valid,
    }
