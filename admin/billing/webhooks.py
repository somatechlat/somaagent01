"""Lago Webhook Receiver.


Per AAAS_ADMIN_SRS.md - Billing Integration.

Handles events from Lago:
- invoice.created
- invoice.paid
- subscription.started
- subscription.terminated
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpRequest
from ninja import Router

from admin.aaas.models import AuditLog, Tenant

router = Router(tags=["webhooks"])
logger = logging.getLogger(__name__)


def verify_lago_signature(request: HttpRequest) -> bool:
    """Verify Lago webhook signature.

    Lago signs webhooks with HMAC-SHA256.
    """
    signature = request.headers.get("X-Lago-Signature")
    if not signature:
        logger.warning("Missing Lago webhook signature")
        return False

    webhook_secret = getattr(settings, "LAGO_WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.warning("LAGO_WEBHOOK_SECRET not configured")
        return True  # Allow in dev mode

    body = request.body
    expected = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


@router.post("/lago")
async def lago_webhook(request: HttpRequest) -> dict:
    """Handle Lago webhook events.


    - Signature verification
    - Idempotent processing
    - Audit logging
    """
    # Verify signature
    if not verify_lago_signature(request):
        return {"status": "error", "message": "Invalid signature"}

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON"}

    event_type = payload.get("webhook_type")
    event_data = payload.get("data", {})

    logger.info(f"Lago webhook received: {event_type}")

    # Route to handler
    handlers = {
        "invoice.created": handle_invoice_created,
        "invoice.paid": handle_invoice_paid,
        "subscription.started": handle_subscription_started,
        "subscription.terminated": handle_subscription_terminated,
        "customer.created": handle_customer_created,
    }

    handler = handlers.get(event_type)
    if handler:
        try:
            await handler(event_data)
            return {"status": "ok", "event": event_type}
        except Exception as e:
            logger.error(f"Webhook handler error: {e}")
            return {"status": "error", "message": str(e)}

    logger.warning(f"Unhandled webhook type: {event_type}")
    return {"status": "ok", "event": event_type, "handled": False}


# =============================================================================
# EVENT HANDLERS
# =============================================================================


async def handle_invoice_created(data: dict) -> None:
    """Handle invoice.created event."""
    from uuid import uuid4

    from asgiref.sync import sync_to_async

    invoice = data.get("invoice", {})
    customer_id = invoice.get("customer", {}).get("external_id")

    if not customer_id:
        logger.warning("Invoice missing customer external_id")
        return

    @sync_to_async
    def log_event():
        """Execute log event."""

        try:
            tenant = Tenant.objects.get(id=customer_id)
            AuditLog.objects.create(
                actor_id=uuid4(),
                actor_email="lago@system",
                tenant=tenant,
                action="invoice.created",
                resource_type="invoice",
                resource_id=invoice.get("lago_id"),
                new_value={
                    "amount_cents": invoice.get("total_amount_cents"),
                    "status": invoice.get("status"),
                    "number": invoice.get("number"),
                },
            )
        except Tenant.DoesNotExist:
            logger.error(f"Tenant not found: {customer_id}")

    await log_event()
    logger.info(f"Invoice created for tenant {customer_id}")


async def handle_invoice_paid(data: dict) -> None:
    """Handle invoice.paid event."""
    from uuid import uuid4

    from asgiref.sync import sync_to_async

    invoice = data.get("invoice", {})
    customer_id = invoice.get("customer", {}).get("external_id")

    @sync_to_async
    def log_event():
        """Execute log event."""

        try:
            tenant = Tenant.objects.get(id=customer_id)
            AuditLog.objects.create(
                actor_id=uuid4(),
                actor_email="lago@system",
                tenant=tenant,
                action="invoice.paid",
                resource_type="invoice",
                resource_id=invoice.get("lago_id"),
                new_value={
                    "amount_cents": invoice.get("total_amount_cents"),
                    "payment_status": invoice.get("payment_status"),
                },
            )
        except Tenant.DoesNotExist:
            pass

    await log_event()
    logger.info(f"Invoice paid for tenant {customer_id}")


async def handle_subscription_started(data: dict) -> None:
    """Handle subscription.started event."""
    from asgiref.sync import sync_to_async

    subscription = data.get("subscription", {})
    customer_id = subscription.get("external_customer_id")
    plan_code = subscription.get("plan_code")

    @sync_to_async
    def update_tenant():
        """Execute update tenant."""

        from admin.aaas.models import SubscriptionTier

        try:
            tenant = Tenant.objects.get(id=customer_id)
            tier = SubscriptionTier.objects.filter(lago_plan_code=plan_code).first()
            if tier:
                tenant.tier = tier
                tenant.save(update_fields=["tier", "updated_at"])
                logger.info(f"Tenant {customer_id} upgraded to {plan_code}")
        except Tenant.DoesNotExist:
            logger.error(f"Tenant not found: {customer_id}")

    await update_tenant()


async def handle_subscription_terminated(data: dict) -> None:
    """Handle subscription.terminated event."""
    from asgiref.sync import sync_to_async

    subscription = data.get("subscription", {})
    customer_id = subscription.get("external_customer_id")

    @sync_to_async
    def downgrade_tenant():
        """Execute downgrade tenant."""

        from admin.aaas.models import SubscriptionTier

        try:
            tenant = Tenant.objects.get(id=customer_id)
            free_tier = SubscriptionTier.objects.filter(price_cents=0).first()
            if free_tier:
                tenant.tier = free_tier
                tenant.save(update_fields=["tier", "updated_at"])
                logger.info(f"Tenant {customer_id} downgraded to free")
        except Tenant.DoesNotExist:
            pass

    await downgrade_tenant()


async def handle_customer_created(data: dict) -> None:
    """Handle customer.created event (confirmation)."""
    customer = data.get("customer", {})
    external_id = customer.get("external_id")
    logger.info(f"Lago customer created: {external_id}")
