"""Telegram bridge lifecycle service (WP D4 — BR-02 / BR-05).

Manages the Telegram Bot API driver for a Channel:

- ``start``            validate bot token (Vault/config), optionally register
                       the webhook (mode=webhook); set Channel.status
- ``stop``             delete webhook / mark channel disabled
- ``test_connection``  probe ``getMe`` (A0 ``api/test_connection.py``)
- ``status``           channel + bot + webhook state snapshot
- ``handle_webhook``   Telegram Update ingest with secret verification

A0 behaviour cloned (plugins/_telegram_integration):
- ``api/{test_connection,webhook}.py``  control surface
- ``helpers/handler.py``  allowlist / group_mode inputs persist here only;
  policy is enforced in the worker dispatcher (Python-side authoritative)

Fail-closed: missing Channel.tenant or Channel.capsule is a hard error on
start; feature flag ``bridge_telegram`` must be on; a webhook without a
configured secret is rejected.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TelegramBridgeError(Exception):
    """Lifecycle / configuration error for the Telegram bridge."""


@dataclass
class BridgeControlResult:
    """Lifecycle result envelope (same shape as the WhatsApp bridge)."""

    ok: bool
    status: str
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "detail": self.detail,
            **self.data,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _feature_enabled() -> bool:
    try:
        from services.common.features import build_default_registry

        return bool(build_default_registry().is_enabled("bridge_telegram"))
    except Exception as exc:  # noqa: BLE001 — fail-closed
        logger.error("bridge_telegram flag check failed: %s", exc)
        return False


def _require_channel(channel_id: str) -> Any:
    from admin.bridges.models import Channel

    channel = Channel.objects.filter(id=channel_id).select_related("tenant", "capsule").first()
    if channel is None:
        raise TelegramBridgeError(f"channel '{channel_id}' not found")
    return channel


def _require_binding(channel: Any) -> None:
    """Fail-closed on missing tenant or capsule (T-5 / BR-09)."""
    if not getattr(channel, "tenant_id", None):
        raise TelegramBridgeError(f"channel {channel.id} has no tenant binding — refuse to start")
    if not getattr(channel, "capsule_id", None):
        raise TelegramBridgeError(f"channel {channel.id} has no capsule binding — refuse to start")


def _channel_config(channel: Any) -> Dict[str, Any]:
    return dict(getattr(channel, "config", None) or {})


def _mode(config: Dict[str, Any]) -> str:
    return str(config.get("mode") or os.environ.get("TG_BRIDGE_MODE", "poll")).strip().lower()


def _build_driver(channel: Any):
    from services.bridge_worker.drivers.telegram import build_telegram_driver

    return build_telegram_driver(
        str(channel.id),
        _channel_config(channel),
        credentials_ref=str(getattr(channel, "credentials_ref", "") or ""),
    )


# ---------------------------------------------------------------------------
# Public lifecycle API
# ---------------------------------------------------------------------------


async def test_connection(channel_id: str) -> BridgeControlResult:
    """Probe the bot identity via ``getMe`` (A0 api/test_connection.py)."""
    channel = _require_channel(channel_id)
    config = _channel_config(channel)
    mode = _mode(config)

    try:
        driver = _build_driver(channel)
        me = await driver.get_me()
        await driver.stop()
    except Exception as exc:  # noqa: BLE001 — surface as connection failure
        return BridgeControlResult(
            False,
            "unreachable",
            f"telegram getMe failed: {exc}",
            {"mode": mode},
        )

    return BridgeControlResult(
        True,
        "ok",
        f"bot @{me.get('username')} reachable",
        {"mode": mode, "bot": me},
    )


async def start(channel_id: str) -> BridgeControlResult:
    """Start the Telegram bridge for a channel (A0 api/start.py parity).

    poll mode: verify the token (getMe) and clear any stale webhook; the
    bridge worker long-polls getUpdates.
    webhook mode: additionally register setWebhook with the secret token.
    """
    if not _feature_enabled():
        return BridgeControlResult(
            False, "disabled", "feature flag bridge_telegram is off (fail-closed)"
        )

    channel = _require_channel(channel_id)
    _require_binding(channel)
    config = _channel_config(channel)
    mode = _mode(config)

    if mode not in {"poll", "webhook"}:
        return BridgeControlResult(False, "error", f"unknown mode '{mode}' (expected poll|webhook)")

    try:
        driver = _build_driver(channel)
    except Exception as exc:  # noqa: BLE001
        _set_status(channel_id, "error", str(exc))
        return BridgeControlResult(False, "error", f"telegram driver config failed: {exc}")

    try:
        await driver.start()
    except Exception as exc:  # noqa: BLE001
        _set_status(channel_id, "error", str(exc))
        return BridgeControlResult(False, "error", f"telegram start failed: {exc}")

    data: Dict[str, Any] = {
        "mode": mode,
        "bot_username": driver._bot_username,
        "bot_id": driver._bot_id,
    }

    if mode == "webhook":
        webhook_url = str(
            config.get("webhook_url") or os.environ.get("TG_WEBHOOK_URL") or ""
        ).strip()
        if not webhook_url:
            await driver.stop()
            _set_status(
                channel_id, "error", "webhook mode requires config.webhook_url / TG_WEBHOOK_URL"
            )
            return BridgeControlResult(
                False,
                "error",
                "webhook mode requires config.webhook_url (public HTTPS endpoint)",
                {"mode": mode},
            )
        from services.bridge_worker.drivers.telegram import resolve_webhook_secret

        secret = resolve_webhook_secret(
            channel_config=config,
            credentials_ref=str(getattr(channel, "credentials_ref", "") or ""),
        )
        if not secret:
            await driver.stop()
            _set_status(channel_id, "error", "webhook mode requires a webhook secret (fail-closed)")
            return BridgeControlResult(
                False,
                "error",
                "webhook secret missing — set Channel.credentials_ref to the "
                "Vault path holding 'webhook_secret' (fail-closed)",
                {"mode": mode},
            )
        try:
            await driver.set_webhook(webhook_url, secret_token=secret)
            data["webhook_url"] = webhook_url
        except Exception as exc:  # noqa: BLE001
            await driver.stop()
            _set_status(channel_id, "error", f"setWebhook failed: {exc}")
            return BridgeControlResult(False, "error", f"setWebhook failed: {exc}", {"mode": mode})

    await driver.stop()
    _set_status(channel_id, "active", "")
    return BridgeControlResult(True, "active", f"bridge started ({mode})", data)


async def stop(channel_id: str) -> BridgeControlResult:
    """Delete the webhook (webhook mode) and disable the channel."""
    channel = _require_channel(channel_id)
    config = _channel_config(channel)
    mode = _mode(config)
    webhook_deleted = False

    if mode == "webhook":
        try:
            driver = _build_driver(channel)
            await driver.delete_webhook()
            await driver.stop()
            webhook_deleted = True
        except Exception as exc:  # noqa: BLE001 — still disable the channel
            logger.warning("deleteWebhook failed for %s: %s", channel_id, exc)

    _set_status(channel_id, "disabled", "stopped by operator")
    return BridgeControlResult(
        True,
        "disabled",
        "bridge stopped",
        {"mode": mode, "webhook_deleted": webhook_deleted},
    )


async def status(channel_id: str) -> BridgeControlResult:
    """Channel + bot + webhook snapshot for the UI/ops."""
    channel = _require_channel(channel_id)
    config = _channel_config(channel)
    mode = _mode(config)
    data: Dict[str, Any] = {
        "channel_id": str(channel.id),
        "channel_status": channel.status,
        "mode": mode,
        "kind": channel.kind,
    }

    try:
        driver = _build_driver(channel)
        me = await driver.get_me()
        data["bot"] = me
        if mode == "webhook":
            info = await driver.get_webhook_info()
            data["webhook"] = {
                "url": info.get("url"),
                "pending_update_count": info.get("pending_update_count"),
                "last_error_date": info.get("last_error_date"),
                "last_error_message": info.get("last_error_message"),
            }
        await driver.stop()
    except Exception as exc:  # noqa: BLE001
        return BridgeControlResult(
            False,
            "unreachable",
            f"telegram status probe failed: {exc}",
            data,
        )

    return BridgeControlResult(True, str(channel.status or "unknown"), "status fetched", data)


# ---------------------------------------------------------------------------
# Webhook ingest (Option B inbound)
# ---------------------------------------------------------------------------


def handle_webhook(
    channel_id: str,
    body: Dict[str, Any],
    *,
    secret_header: str = "",
    secret_query: str = "",
) -> BridgeControlResult:
    """Ingest one Telegram Update from the webhook route.

    Verifies the webhook secret (fail-closed), then persists a normalized
    ``InboundMessage`` row (processed_at=null) so the bridge worker
    ``TelegramBotDriver.poll_inbound`` can dispatch it.
    """
    if not _feature_enabled():
        return BridgeControlResult(False, "disabled", "bridge_telegram flag is off")

    channel = _require_channel(channel_id)
    _require_binding(channel)
    config = _channel_config(channel)

    from services.bridge_worker.drivers.telegram import (
        map_update_to_envelope,
        resolve_webhook_secret,
        verify_webhook_secret,
    )

    expected = resolve_webhook_secret(
        channel_config=config,
        credentials_ref=str(getattr(channel, "credentials_ref", "") or ""),
    )
    provided = (secret_header or secret_query or "").strip()
    if not verify_webhook_secret(expected, provided):
        return BridgeControlResult(False, "forbidden", "invalid webhook secret")

    bot_id = str(config.get("bot_id") or "")
    bot_username = str(config.get("bot_username") or "")
    if not bot_username:
        # Fall back to the bot identity so mention detection works in groups.
        me = _fetch_bot_identity_sync(channel)
        if me:
            bot_id = str(me.get("id") or bot_id)
            bot_username = str(me.get("username") or bot_username)

    env = map_update_to_envelope(body or {}, bot_id=bot_id, bot_username=bot_username)
    if env is None:
        return BridgeControlResult(True, "ignored", "update carried no user message")

    row_id = _store_inbound(channel=channel, envelope=env)
    if row_id is None:
        return BridgeControlResult(True, "duplicate", "update already stored")
    return BridgeControlResult(True, "accepted", "stored inbound message", {"inbound_id": row_id})


def _fetch_bot_identity_sync(channel: Any) -> Optional[Dict[str, Any]]:
    """Blocking getMe for webhook context (no running loop needed)."""
    try:
        import httpx

        from services.bridge_worker.drivers.telegram import resolve_bot_token

        token = resolve_bot_token(
            credentials_ref=str(getattr(channel, "credentials_ref", "") or ""),
            channel_config=_channel_config(channel),
        )
        # Channel config / env is the operator override; the Telegram bot API
        # host is a vendor protocol constant (SOMA-STD-CONFIG-001).
        from admin.core.helpers.vendor_api_bases import (
            TELEGRAM_API_BASE,
            effective_base,
        )

        override = _channel_config(channel).get("api_base") or os.environ.get("TG_API_BASE")
        api_base = effective_base(TELEGRAM_API_BASE, override)
        resp = httpx.post(
            f"{str(api_base).rstrip('/')}/bot{token}/getMe",
            json={},
            timeout=10.0,
        )
        data = resp.json() if resp.status_code == 200 else {}
        if isinstance(data, dict) and data.get("ok"):
            result = data.get("result") or {}
            return {
                "id": result.get("id"),
                "username": result.get("username"),
            }
    except Exception as exc:  # noqa: BLE001 — mention detection degrades gracefully
        logger.warning("getMe sync probe failed for channel %s: %s", channel.id, exc)
    return None


def _store_inbound(*, channel: Any, envelope: Any) -> Optional[str]:
    from admin.bridges.models import InboundMessage

    if (
        envelope.external_id
        and InboundMessage.objects.filter(
            channel_id=channel.id, external_id=envelope.external_id
        ).exists()
    ):
        return None

    row = InboundMessage.objects.create(
        channel_id=channel.id,
        external_id=envelope.external_id or "",
        direction="inbound",
        payload=envelope.to_payload(),
        attachments=[{"path": u, "media_type": envelope.media_type} for u in envelope.media_urls],
    )
    return str(row.id)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _set_status(channel_id: str, status: str, detail: str) -> None:
    from admin.bridges.models import Channel

    Channel.objects.filter(id=channel_id).update(status=status)
    if detail:
        ch = Channel.objects.filter(id=channel_id).first()
        if ch is not None:
            cfg = dict(ch.config or {})
            cfg["last_status_detail"] = detail[:500]
            ch.config = cfg
            ch.save(update_fields=["config", "updated_at"])
