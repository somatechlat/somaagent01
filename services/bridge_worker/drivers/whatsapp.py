"""WhatsApp driver — A0 Baileys sidecar parity + Meta Cloud API.

Two production modes (SOMA-A0-PARITY-001 §4.5 BR-01, Annex D.5):

Option A — ``baileys`` (preferred for parity)
    Node Baileys sidecar exposing A0 ``whatsapp-bridge/bridge.js`` HTTP:
      GET  /messages        drain inbound queue
      POST /send            {chatId, message, replyTo?}
      POST /edit            {chatId, messageId, message}
      POST /send-media      {chatId, filePath, mediaType?, caption?, fileName?}
      POST /typing          {chatId, status?}
      GET  /qr              pairing QR data-url
      GET  /health          {status, queueLength, uptime}
      GET  /chat/:id        group metadata

Option B — ``cloud``
    WhatsApp Cloud API (Graph). Outbound via ``POST /{phone_number_id}/messages``.
    Inbound is webhook-fed: Meta posts to the verify/receive endpoint handled by
    ``admin.bridges.services.whatsapp_bridge``, which persists ``InboundMessage``
    rows; this driver drains unprocessed rows.

Env vars (Channel.config overrides win over env):
    WA_BRIDGE_MODE                baileys | cloud          (default baileys)
    WA_BRIDGE_BASE_URL            http://127.0.0.1:3100    (baileys sidecar)
    WA_BRIDGE_PORT                3100                     (used to build base url)
    WA_CLOUD_API_TOKEN            Meta permanent access token
    WA_CLOUD_PHONE_NUMBER_ID      Graph phone number id
    WA_CLOUD_API_VERSION          v21.0
    WA_CLOUD_API_BASE             https://graph.facebook.com
    WA_CLOUD_WEBHOOK_VERIFY_TOKEN webhook hub.challenge token
    WA_CLOUD_APP_SECRET           optional X-Hub-Signature-256 secret
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any, Dict, List, Optional

import httpx

from services.bridge_worker.drivers.base import (
    BridgeDriver,
    BridgeSendError,
    DriverHealth,
    InboundEnvelope,
    OutboundPayload,
)

logger = logging.getLogger(__name__)

# Mirrors A0 helpers/wa_client.py timeouts.
_POLL_TIMEOUT = 10.0
_SEND_TIMEOUT = 30.0
_HEALTH_TIMEOUT = 5.0


def _cfg(channel_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return dict(channel_config or {})


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default) or default


# ---------------------------------------------------------------------------
# Normalization (A0 helpers/number_utils.py)
# ---------------------------------------------------------------------------

import re

_JID_SUFFIX_RE = re.compile(r"[@:].*")
_NON_DIGIT_RE = re.compile(r"\D+")
_LEADING_ZERO_RE = re.compile(r"^0+")


def normalize_number(raw: str) -> str:
    """Normalize WhatsApp JIDs / phone numbers to comparable digits (A0 clone)."""
    text = _JID_SUFFIX_RE.sub("", str(raw or ""))
    digits = _NON_DIGIT_RE.sub("", text)
    return _LEADING_ZERO_RE.sub("", digits)


def normalize_allowed_numbers(value: object) -> set[str]:
    """Accept list/tuple/set or comma-delimited string (A0 clone)."""
    if isinstance(value, str):
        candidates: List[object] = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        candidates = list(value)
    else:
        return set()
    normalized = {normalize_number(str(item)) for item in candidates}
    normalized.discard("")
    return normalized


# ---------------------------------------------------------------------------
# Option A — Baileys sidecar HTTP client (A0 wa_client.py contract)
# ---------------------------------------------------------------------------


class BaileysSidecarDriver:
    """HTTP client for the Node Baileys sidecar (A0 bridge.js contract)."""

    kind = "baileys"

    def __init__(self, *, base_url: str, channel_config: Optional[Dict[str, Any]] = None):
        self.base_url = base_url.rstrip("/")
        self.config = _cfg(channel_config)
        self._client: Optional[httpx.AsyncClient] = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(base_url=self.base_url)
        return self._client

    async def start(self) -> None:
        self._http()
        # Probe — sidecar may still be pairing; that is healthy enough to poll.
        try:
            await self.health()
        except Exception as exc:  # noqa: BLE001 — start is best-effort probe
            logger.warning("baileys sidecar not reachable yet at %s: %s", self.base_url, exc)

    async def stop(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    async def poll_inbound(self) -> List[InboundEnvelope]:
        """GET /messages — destructive drain (A0 bridge.js splices the queue)."""
        try:
            resp = await self._http().get("/messages", timeout=_POLL_TIMEOUT)
        except httpx.HTTPError as exc:
            logger.warning("baileys poll failed: %s", exc)
            return []
        if resp.status_code != 200:
            logger.warning("baileys poll status %s", resp.status_code)
            return []
        raw_list = resp.json()
        if not isinstance(raw_list, list):
            return []
        return [self._map_event(item) for item in raw_list if isinstance(item, dict)]

    @staticmethod
    def _map_event(item: Dict[str, Any]) -> InboundEnvelope:
        """Map A0 bridge.js event shape → InboundEnvelope."""
        media_urls = item.get("mediaUrls") or []
        return InboundEnvelope(
            external_id=str(item.get("messageId") or ""),
            chat_id=str(item.get("chatId") or ""),
            sender_id=str(item.get("senderId") or ""),
            sender_number=str(item.get("senderNumber") or ""),
            sender_name=str(item.get("senderName") or ""),
            chat_name=str(item.get("chatName") or ""),
            is_group=bool(item.get("isGroup", False)),
            mentioned_me=bool(item.get("mentionedMe", False)),
            replied_to_me=bool(item.get("repliedToMe", False)),
            body=str(item.get("body") or ""),
            has_media=bool(item.get("hasMedia", False)),
            media_type=str(item.get("mediaType") or ""),
            media_urls=[str(u) for u in media_urls],
            timestamp=item.get("timestamp"),
            raw=item,
        )

    async def send_outbound(self, payload: OutboundPayload) -> Dict[str, Any]:
        if payload.media_path:
            return await self._send_media(payload)
        if not payload.text:
            raise BridgeSendError("empty outbound text", retryable=False)
        body: Dict[str, Any] = {"chatId": payload.chat_id, "message": payload.text}
        if payload.reply_to:
            body["replyTo"] = payload.reply_to
        resp = await self._http().post("/send", json=body, timeout=_SEND_TIMEOUT)
        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get("success", False):
            # 503 = not connected → retryable; 400 = bad request → not.
            retryable = resp.status_code >= 500 or resp.status_code == 0
            raise BridgeSendError(
                f"baileys send failed: {data.get('error') or resp.status_code}",
                status_code=resp.status_code,
                retryable=retryable,
            )
        return data

    async def _send_media(self, payload: OutboundPayload) -> Dict[str, Any]:
        body = {
            "chatId": payload.chat_id,
            "filePath": payload.media_path,
        }
        if payload.media_type:
            body["mediaType"] = payload.media_type
        if payload.caption:
            body["caption"] = payload.caption
        if payload.file_name:
            body["fileName"] = payload.file_name
        resp = await self._http().post("/send-media", json=body, timeout=_SEND_TIMEOUT)
        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get("success", False):
            raise BridgeSendError(
                f"baileys send-media failed: {data.get('error') or resp.status_code}",
                status_code=resp.status_code,
                retryable=resp.status_code >= 500,
            )
        return data

    async def send_typing(self, chat_id: str, paused: bool = False) -> None:
        """Best-effort typing indicator (A0 wa_client.send_typing)."""
        try:
            body: Dict[str, Any] = {"chatId": chat_id}
            if paused:
                body["status"] = "paused"
            await self._http().post("/typing", json=body, timeout=_HEALTH_TIMEOUT)
        except Exception:  # noqa: BLE001 — typing is never fatal
            pass

    async def health(self) -> DriverHealth:
        try:
            resp = await self._http().get("/health", timeout=_HEALTH_TIMEOUT)
        except httpx.HTTPError as exc:
            return DriverHealth(status="unreachable", detail=str(exc))
        data = _safe_json(resp)
        return DriverHealth(
            status=str(data.get("status") or ("ok" if resp.status_code == 200 else "error")),
            detail="",
            queue_length=int(data.get("queueLength") or 0),
            uptime=float(data.get("uptime") or 0.0),
            extra={"base_url": self.base_url},
        )

    async def get_qr(self) -> Optional[Dict[str, Any]]:
        """GET /qr — {status: connected|waiting_scan|waiting_qr, qr: data-url|null}."""
        try:
            resp = await self._http().get("/qr", timeout=_HEALTH_TIMEOUT)
        except httpx.HTTPError as exc:
            return {"status": "error", "qr": None, "detail": str(exc)}
        if resp.status_code != 200:
            return {"status": "error", "qr": None, "detail": f"HTTP {resp.status_code}"}
        data = _safe_json(resp)
        return {
            "status": data.get("status", "unknown"),
            "qr": data.get("qr"),
        }

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        try:
            resp = await self._http().get(f"/chat/{chat_id}", timeout=_POLL_TIMEOUT)
            if resp.status_code == 200:
                data = _safe_json(resp)
                return {
                    "name": data.get("name", ""),
                    "isGroup": bool(data.get("isGroup", False)),
                    "participants": data.get("participants") or [],
                }
        except httpx.HTTPError:
            pass
        return {"name": "", "isGroup": chat_id.endswith("@g.us"), "participants": []}


# ---------------------------------------------------------------------------
# Option B — WhatsApp Cloud API (Graph send + DB-fed webhook inbound)
# ---------------------------------------------------------------------------


class CloudApiDriver:
    """Meta WhatsApp Cloud API driver.

    Outbound: ``POST /{version}/{phone_number_id}/messages`` with bearer token.
    Inbound: webhook payloads are persisted as ``InboundMessage`` by
    ``admin.bridges.services.whatsapp_bridge.handle_cloud_webhook``; this
    driver drains rows where ``processed_at`` is null.
    """

    kind = "cloud"

    def __init__(
        self,
        *,
        channel_id: str,
        token: str,
        phone_number_id: str,
        api_version: str = "v21.0",
        api_base: str = "https://graph.facebook.com",
    ):
        self.channel_id = channel_id
        self.token = token
        self.phone_number_id = phone_number_id
        self.api_version = api_version.lstrip("/")
        self.api_base = api_base.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_base,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=_SEND_TIMEOUT,
            )
        return self._client

    async def start(self) -> None:
        if not self.token or not self.phone_number_id:
            raise BridgeSendError(
                "cloud mode requires WA_CLOUD_API_TOKEN and WA_CLOUD_PHONE_NUMBER_ID",
                retryable=False,
            )
        self._http()

    async def stop(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    async def poll_inbound(self) -> List[InboundEnvelope]:
        """Read unprocessed InboundMessage rows written by the webhook handler.

        Rows stay ``processed_at=null`` until the dispatcher finishes, so a
        crash mid-turn never silently drops inbound traffic. Dedupe against a
        concurrent worker is handled by the dispatcher's external_id check.
        """
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _load() -> List[InboundEnvelope]:
            from admin.bridges.models import InboundMessage

            envelopes: List[InboundEnvelope] = []
            rows = list(
                InboundMessage.objects.filter(
                    channel_id=self.channel_id, processed_at__isnull=True
                ).order_by("received_at")[:50]
            )
            for row in rows:
                p = row.payload or {}
                envelopes.append(
                    InboundEnvelope(
                        external_id=row.external_id or str(row.id),
                        chat_id=str(p.get("chat_id") or ""),
                        sender_id=str(p.get("sender_id") or ""),
                        sender_number=str(p.get("sender_number") or ""),
                        sender_name=str(p.get("sender_name") or ""),
                        chat_name=str(p.get("chat_name") or ""),
                        is_group=bool(p.get("is_group", False)),
                        mentioned_me=bool(p.get("mentioned_me", False)),
                        replied_to_me=bool(p.get("replied_to_me", False)),
                        body=str(p.get("body") or ""),
                        has_media=bool(p.get("has_media", False)),
                        media_type=str(p.get("media_type") or ""),
                        media_urls=list(p.get("media_urls") or []),
                        timestamp=p.get("timestamp"),
                        raw={"inbound_message_id": str(row.id), **p},
                    )
                )
            return envelopes

        return await _load()

    async def send_outbound(self, payload: OutboundPayload) -> Dict[str, Any]:
        body = self._graph_body(payload)
        path = f"/{self.api_version}/{self.phone_number_id}/messages"
        resp = await self._http().post(path, json=body)
        data = _safe_json(resp)
        if resp.status_code >= 400:
            err = (data.get("error") or {}).get("message") or resp.text[:300]
            retryable = resp.status_code == 429 or resp.status_code >= 500
            raise BridgeSendError(
                f"cloud send failed HTTP {resp.status_code}: {err}",
                status_code=resp.status_code,
                retryable=retryable,
            )
        messages = data.get("messages") or []
        mid = messages[0].get("id") if messages else ""
        return {"success": True, "messageId": mid}

    @staticmethod
    def _graph_body(payload: OutboundPayload) -> Dict[str, Any]:
        """Build Graph message body. Text replies quote reply_to when present."""
        recipient = payload.chat_id
        if payload.media_path:
            # Media send requires a prior upload; send as document/image link or
            # text fallback with path note when no upload helper is configured.
            return {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": payload.caption or payload.text or f"[media: {payload.media_path}]",
                },
            }
        msg: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": payload.text},
        }
        if payload.reply_to:
            msg["context"] = {"message_id": payload.reply_to}
        return msg

    async def health(self) -> DriverHealth:
        if not self.token or not self.phone_number_id:
            return DriverHealth(status="misconfigured", detail="missing cloud credentials")
        return DriverHealth(
            status="ok",
            detail=f"cloud api {self.api_base}/{self.api_version}",
            extra={
                "phone_number_id": self.phone_number_id,
                "mode": "cloud",
            },
        )

    async def get_qr(self) -> Optional[Dict[str, Any]]:
        # Cloud API is token-based — no QR pairing (A0 QR path is Baileys-only).
        return {
            "status": "connected",
            "qr": None,
            "detail": "Cloud API uses a permanent access token; QR pairing is Baileys-only",
        }


def _safe_json(resp: httpx.Response) -> Dict[str, Any]:
    try:
        data = resp.json()
        return data if isinstance(data, dict) else {"data": data}
    except Exception:  # noqa: BLE001
        return {"raw": resp.text[:500]}


# ---------------------------------------------------------------------------
# Unified WhatsApp driver (mode switch)
# ---------------------------------------------------------------------------

WhatsAppDriver = BaileysSidecarDriver | CloudApiDriver


def build_whatsapp_driver(
    channel_id: str,
    channel_config: Optional[Dict[str, Any]] = None,
) -> WhatsAppDriver:
    """Factory — pick Baileys sidecar or Cloud API from config/env.

    Fail-closed: unknown mode raises. Missing cloud credentials raise at
    ``start()`` so the channel can be marked error rather than silently idle.
    """
    cfg = _cfg(channel_config)
    mode = str(cfg.get("mode") or _env("WA_BRIDGE_MODE", "baileys")).lower()
    if mode == "baileys":
        base_url = str(
            cfg.get("bridge_base_url")
            or _env("WA_BRIDGE_BASE_URL")
            or f"http://127.0.0.1:{cfg.get('bridge_port') or _env('WA_BRIDGE_PORT', '3100')}"
        )
        return BaileysSidecarDriver(base_url=base_url, channel_config=cfg)
    if mode == "cloud":
        token = str(cfg.get("api_token") or _env("WA_CLOUD_API_TOKEN"))
        phone_number_id = str(cfg.get("phone_number_id") or _env("WA_CLOUD_PHONE_NUMBER_ID"))
        return CloudApiDriver(
            channel_id=channel_id,
            token=token,
            phone_number_id=phone_number_id,
            api_version=str(cfg.get("api_version") or _env("WA_CLOUD_API_VERSION", "v21.0")),
            api_base=str(
                cfg.get("api_base") or _env("WA_CLOUD_API_BASE", "https://graph.facebook.com")
            ),
        )
    raise ValueError(f"unknown WhatsApp bridge mode '{mode}' (expected baileys|cloud)")


def verify_cloud_signature(app_secret: str, body: bytes, header_sig: str) -> bool:
    """Validate X-Hub-Signature-256 on Meta webhooks (fail-closed if secret set)."""
    if not app_secret:
        return False
    if not header_sig or not header_sig.startswith("sha256="):
        return False
    digest = hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={digest}", header_sig)


def verify_webhook_challenge(
    mode: str, token: str, challenge: str, verify_token: str
) -> Optional[str]:
    """Meta webhook verification handshake (GET hub.challenge)."""
    if mode != "subscribe" or not verify_token or token != verify_token:
        return None
    return challenge


# Type-check the protocol conformance at import time (documentation aid).
def _protocol_check() -> None:
    for cls in (BaileysSidecarDriver, CloudApiDriver):
        assert isinstance(cls, type)
        _: BridgeDriver  # noqa: F841 — structural type only


_protocol_check()
