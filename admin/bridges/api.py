"""Channel Ninja CRUD — bridge Capsule channels (WP D2).

Endpoints under ``/api/v2/bridges``:
- ``GET    /channels``               list channels for the caller's tenant
- ``POST   /channels``               create a channel
- ``GET    /channels/{id}``          get one channel
- ``PATCH  /channels/{id}``          update a channel
- ``DELETE /channels/{id}``          delete a channel
- ``POST   /telegram/webhook/{id}``  Telegram bot webhook (secret-verified)

Fail-closed (T-5): tenant is taken from the auth token's explicit claims only.
There is NO default-tenant fallback — a missing tenant claim is 401. Channel
access is always scoped to the caller's tenant (cross-tenant reads → 404).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Router, Schema
from ninja.errors import HttpError

from admin.common.auth import AuthBearer
from services.common.authorization import authorize, authorize_sync

logger = logging.getLogger(__name__)
router = Router(tags=["bridges"])


# =============================================================================
# SCHEMAS
# =============================================================================


class ChannelOut(Schema):
    """Channel response schema."""

    id: str
    tenant_id: str
    capsule_id: Optional[str] = None
    kind: str
    status: str
    name: str
    config: dict
    credentials_ref: str
    created_at: str
    updated_at: str


class ChannelCreate(Schema):
    """Create channel body."""

    kind: str
    name: str = ""
    status: str = "disabled"
    config: dict = {}
    credentials_ref: str = ""
    capsule_id: Optional[str] = None


class ChannelUpdate(Schema):
    """Partial update body (all fields optional)."""

    name: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None
    credentials_ref: Optional[str] = None
    capsule_id: Optional[str] = None


class ChannelListOut(Schema):
    """Channel list envelope."""

    channels: list[ChannelOut]
    total: int


# =============================================================================
# HELPERS
# =============================================================================


def _require_tenant_id(request) -> str:
    """Resolve the caller's tenant — fail-closed, no default tenant.

    Uses explicit JWT claims (``tenant_id`` or ``tenant``) only. The special
    value ``default`` is rejected rather than mapped to AAAS_DEFAULT_TENANT_ID,
    so bridge data can never attach to a silent default tenant.
    """

    auth = getattr(request, "auth", None)
    if auth is None:
        raise HttpError(401, "Authentication required for channel operations")

    tenant_id = getattr(auth, "tenant_id", None) or getattr(auth, "tenant", None)
    if not tenant_id or str(tenant_id).strip() in {"", "default"}:
        raise HttpError(
            401,
            "Tenant context required (no default tenant): token must carry "
            "tenant_id or a non-default tenant claim",
        )
    return str(tenant_id)


def _channel_to_dict(obj) -> dict[str, Any]:
    return {
        "id": str(obj.id),
        "tenant_id": str(obj.tenant_id),
        "capsule_id": str(obj.capsule_id) if obj.capsule_id else None,
        "kind": obj.kind,
        "status": obj.status,
        "name": obj.name or "",
        "config": obj.config or {},
        "credentials_ref": obj.credentials_ref or "",
        "created_at": obj.created_at.isoformat(),
        "updated_at": obj.updated_at.isoformat(),
    }


def _validate_kind(kind: str) -> str:
    from admin.bridges.models import Channel

    valid = {choice[0] for choice in Channel.KIND_CHOICES}
    if kind not in valid:
        raise HttpError(422, f"invalid channel kind '{kind}'; expected one of {sorted(valid)}")
    return kind


def _validate_status(status: str) -> str:
    from admin.bridges.models import Channel

    valid = {choice[0] for choice in Channel.STATUS_CHOICES}
    if status not in valid:
        raise HttpError(422, f"invalid channel status '{status}'; expected one of {sorted(valid)}")
    return status


# =============================================================================
# ENDPOINTS — Channel CRUD
# =============================================================================


@router.get("/channels", response=ChannelListOut, summary="List channels", auth=AuthBearer())
def list_channels(request) -> dict:
    """List channels bound to the caller's tenant (real DB)."""

    authorize_sync(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    qs = Channel.objects.filter(tenant_id=tenant_id).order_by("-created_at")
    items = [_channel_to_dict(obj) for obj in qs]
    return {"channels": items, "total": len(items)}


@router.post("/channels", response=ChannelOut, summary="Create channel", auth=AuthBearer())
def create_channel(request, payload: ChannelCreate) -> dict:
    """Create a channel. Tenant comes from auth — never a default."""

    authorize_sync(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    kind = _validate_kind(payload.kind)
    status = _validate_status(payload.status or "disabled")

    from admin.aaas.models import Tenant
    from admin.bridges.models import Channel

    try:
        Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise HttpError(401, f"unknown tenant '{tenant_id}'") from None

    capsule_id = None
    if payload.capsule_id:
        try:
            capsule_id = UUID(str(payload.capsule_id))
        except ValueError:
            raise HttpError(422, f"invalid capsule_id '{payload.capsule_id}'") from None
        from admin.core.models import Capsule

        if not Capsule.objects.filter(id=capsule_id, tenant_id=tenant_id).exists():
            raise HttpError(422, f"capsule '{payload.capsule_id}' not found in tenant")

    try:
        obj = Channel.objects.create(
            tenant_id=tenant_id,
            capsule_id=capsule_id,
            kind=kind,
            status=status,
            name=payload.name or "",
            config=payload.config or {},
            credentials_ref=payload.credentials_ref or "",
        )
    except Exception as exc:
        logger.exception("channel create failed")
        raise HttpError(400, f"channel create failed: {exc}") from exc

    logger.info("channel created: %s kind=%s tenant=%s", obj.id, kind, tenant_id)
    return _channel_to_dict(obj)


@router.get("/channels/{channel_id}", response=ChannelOut, summary="Get channel", auth=AuthBearer())
def get_channel(request, channel_id: str) -> dict:
    """Get one channel (tenant-scoped)."""

    authorize_sync(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    try:
        obj = Channel.objects.get(id=channel_id, tenant_id=tenant_id)
    except Channel.DoesNotExist:
        raise HttpError(404, f"channel '{channel_id}' not found") from None
    return _channel_to_dict(obj)


@router.patch(
    "/channels/{channel_id}", response=ChannelOut, summary="Update channel", auth=AuthBearer()
)
def update_channel(request, channel_id: str, payload: ChannelUpdate) -> dict:
    """Update channel fields (tenant-scoped)."""

    authorize_sync(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    try:
        obj = Channel.objects.get(id=channel_id, tenant_id=tenant_id)
    except Channel.DoesNotExist:
        raise HttpError(404, f"channel '{channel_id}' not found") from None

    if payload.name is not None:
        obj.name = payload.name
    if payload.status is not None:
        obj.status = _validate_status(payload.status)
    if payload.config is not None:
        obj.config = payload.config
    if payload.credentials_ref is not None:
        obj.credentials_ref = payload.credentials_ref
    if payload.capsule_id is not None:
        if payload.capsule_id == "":
            obj.capsule = None
        else:
            try:
                capsule_id = UUID(str(payload.capsule_id))
            except ValueError:
                raise HttpError(422, f"invalid capsule_id '{payload.capsule_id}'") from None
            from admin.core.models import Capsule

            # Fetch the row once and assign through the relation. The code used
            # to do an .exists() query and then set `obj.capsule_id`, which is
            # Django's generated attname — it exists at runtime but no type
            # checker can see it. Assigning `obj.capsule` is the real field,
            # needs no second query, and cannot drift from the model.
            capsule = Capsule.objects.filter(id=capsule_id, tenant_id=tenant_id).first()
            if capsule is None:
                raise HttpError(422, f"capsule '{payload.capsule_id}' not found in tenant")
            obj.capsule = capsule

    obj.save()
    logger.info("channel updated: %s", obj.id)
    return _channel_to_dict(obj)


@router.delete("/channels/{channel_id}", summary="Delete channel", auth=AuthBearer())
def delete_channel(request, channel_id: str) -> dict:
    """Delete a channel (tenant-scoped)."""

    authorize_sync(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    count, _ = Channel.objects.filter(id=channel_id, tenant_id=tenant_id).delete()
    if count == 0:
        raise HttpError(404, f"channel '{channel_id}' not found")
    logger.info("channel deleted: %s", channel_id)
    return {"id": channel_id, "deleted": True}


# =============================================================================
# ENDPOINTS — Channel lifecycle (D7 / BR-05)
# =============================================================================


@router.post("/channels/{channel_id}/test", summary="Test channel connection", auth=AuthBearer())
async def test_channel(request, channel_id: str) -> dict:
    """Test connectivity for a channel (WhatsApp / Telegram)."""
    await authorize(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    obj = Channel.objects.filter(id=channel_id, tenant_id=tenant_id).first()
    if not obj:
        raise HttpError(404, f"channel '{channel_id}' not found")
    try:
        # Every bridge service is `async` and returns BridgeControlResult.
        # These handlers used to be sync and returned the coroutine object
        # un-awaited, so the endpoint responded with a serialized coroutine
        # instead of the result. Ninja supports `async def` handlers; await the
        # call and unwrap through to_dict() to honour the `-> dict` contract.
        if obj.kind == Channel.KIND_WHATSAPP:
            from admin.bridges.services.whatsapp_bridge import test_connection

            return (await test_connection(channel_id)).to_dict()
        if obj.kind == Channel.KIND_TELEGRAM:
            from admin.bridges.services.telegram_bridge import test_connection

            return (await test_connection(channel_id)).to_dict()
        raise HttpError(501, f"test_connection not implemented for kind '{obj.kind}'")
    except HttpError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("channel test failed: %s", channel_id)
        return {"ok": False, "status": "error", "message": str(exc)}


@router.post("/channels/{channel_id}/start", summary="Start channel", auth=AuthBearer())
async def start_channel(request, channel_id: str) -> dict:
    """Start a bridge channel runtime."""
    await authorize(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    obj = Channel.objects.filter(id=channel_id, tenant_id=tenant_id).first()
    if not obj:
        raise HttpError(404, f"channel '{channel_id}' not found")
    try:
        if obj.kind == Channel.KIND_WHATSAPP:
            from admin.bridges.services.whatsapp_bridge import start

            return (await start(channel_id)).to_dict()
        if obj.kind == Channel.KIND_TELEGRAM:
            from admin.bridges.services.telegram_bridge import start

            return (await start(channel_id)).to_dict()
        raise HttpError(501, f"start not implemented for kind '{obj.kind}'")
    except HttpError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("channel start failed: %s", channel_id)
        raise HttpError(500, f"start failed: {exc}") from exc


@router.post("/channels/{channel_id}/stop", summary="Stop channel", auth=AuthBearer())
async def stop_channel(request, channel_id: str) -> dict:
    """Stop a bridge channel runtime."""
    await authorize(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    obj = Channel.objects.filter(id=channel_id, tenant_id=tenant_id).first()
    if not obj:
        raise HttpError(404, f"channel '{channel_id}' not found")
    try:
        if obj.kind == Channel.KIND_WHATSAPP:
            from admin.bridges.services.whatsapp_bridge import stop

            return (await stop(channel_id)).to_dict()
        if obj.kind == Channel.KIND_TELEGRAM:
            from admin.bridges.services.telegram_bridge import stop

            return (await stop(channel_id)).to_dict()
        raise HttpError(501, f"stop not implemented for kind '{obj.kind}'")
    except HttpError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("channel stop failed: %s", channel_id)
        raise HttpError(500, f"stop failed: {exc}") from exc


@router.get("/channels/{channel_id}/qr", summary="Get pairing QR", auth=AuthBearer())
async def channel_qr(request, channel_id: str) -> dict:
    """Get pairing QR for WhatsApp (Baileys)."""
    await authorize(request, action="system:manage_integrations", resource="bridges")
    tenant_id = _require_tenant_id(request)
    from admin.bridges.models import Channel

    obj = Channel.objects.filter(id=channel_id, tenant_id=tenant_id).first()
    if not obj:
        raise HttpError(404, f"channel '{channel_id}' not found")
    if obj.kind != Channel.KIND_WHATSAPP:
        raise HttpError(501, "QR is only available for WhatsApp channels")
    from admin.bridges.services.whatsapp_bridge import get_qr

    return (await get_qr(channel_id)).to_dict()


# =============================================================================
# ENDPOINTS — Telegram webhook (BR-02 / Annex D.5)
# =============================================================================


@router.post(
    "/telegram/webhook/{channel_id}",
    summary="Telegram bot webhook (secret-verified)",
)
async def telegram_webhook(request: HttpRequest, channel_id: str) -> dict:
    """Receive a Telegram Bot API Update for a channel.

    Unauthenticated by design (Telegram's servers call this). Security is the
    webhook secret: the ``X-Telegram-Bot-Api-Secret-Token`` header (set via
    ``setWebhook.secret_token``) must match the channel's configured secret.
    A missing secret is rejected — fail-closed, never open.

    Body is persisted as an unprocessed ``InboundMessage``; the bridge worker
    dispatches it through the Capsule bound to the channel.
    """
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    secret_query = request.GET.get("secret", "")

    try:
        body = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        raise HttpError(400, "invalid JSON body") from None
    if not isinstance(body, dict):
        raise HttpError(400, "expected a Telegram Update object")

    from admin.bridges.services.telegram_bridge import handle_webhook

    try:
        result = handle_webhook(
            channel_id,
            body,
            secret_header=secret_header,
            secret_query=secret_query,
        )
    except Exception as exc:  # noqa: BLE001 — lifecycle errors are 4xx/5xx, not stack traces
        logger.exception("telegram webhook failed for channel %s", channel_id)
        detail = str(exc)
        if "not found" in detail:
            raise HttpError(404, detail) from exc
        if "no tenant" in detail or "no capsule" in detail:
            raise HttpError(422, detail) from exc
        raise HttpError(500, f"telegram webhook failed: {exc}") from exc

    if not result.ok:
        if result.status == "forbidden":
            raise HttpError(403, result.detail or "invalid webhook secret")
        if result.status == "disabled":
            raise HttpError(503, result.detail or "bridge disabled")
        raise HttpError(400, result.detail or "webhook rejected")

    return {"ok": True, "status": result.status, **result.data}
