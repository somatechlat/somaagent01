"""Telegram driver — Bot API parity (SOMA-A0-PARITY-001 §4.5 BR-02, Annex D.5).

Two production modes (A0 ``plugins/_telegram_integration`` behaviour):

Option A — ``poll`` (default)
    Long-poll ``getUpdates`` against ``https://api.telegram.org/bot<token>/…``.
    Offset is advanced per batch so an update is consumed exactly once.

Option B — ``webhook``
    Telegram posts Updates to
    ``POST /api/v2/bridges/telegram/webhook/{channel_id}`` with the
    ``X-Telegram-Bot-Api-Secret-Token`` header. The route (admin.bridges.api)
    verifies the secret and persists ``InboundMessage`` rows via
    ``admin.bridges.services.telegram_bridge.handle_webhook``; this driver
    drains unprocessed rows (same contract as the WhatsApp Cloud driver).

Policy (A0 ``helpers/handler.py``):
- ``allowed_users``  allowlist: empty = allow all; entries are numeric user id,
  ``@username`` or bare username
- ``group_mode``     ``mention`` (default) | ``all`` | ``off``
- per-user BridgeSession mapping is done by the dispatcher on
  (channel, external_user_id=telegram user id, external_chat_id=chat id)

Outbound: ``sendMessage`` with Markdown parse mode, 4096-char chunking and a
plain-text fallback on parse errors (A0 ``telegram_client.send_text``).
Typing: ``sendChatAction`` (one-shot) and ``typing_session`` (keeps the
indicator alive while the agent runs).
"""

from __future__ import annotations

import asyncio
import hmac
import logging
import os
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from services.bridge_worker.drivers.base import (
    BridgeDriver,
    BridgeSendError,
    DriverHealth,
    InboundEnvelope,
    OutboundPayload,
)

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = os.environ.get("TG_API_BASE", "https://api.telegram.org").rstrip("/")
MAX_MESSAGE_LENGTH = 4096

_POLL_TIMEOUT = 15.0  # HTTP timeout for one getUpdates call
_SEND_TIMEOUT = 30.0
_HEALTH_TIMEOUT = 10.0
_TYPING_INTERVAL = 4.0  # sendChatAction is valid ~5s — refresh before it expires

# Media types we surface in InboundEnvelope.media_type.
_TG_MEDIA_KINDS = {
    "photo": "image",
    "video": "video",
    "animation": "animation",
    "audio": "audio",
    "voice": "voice",
    "document": "document",
    "sticker": "sticker",
    "video_note": "video_note",
}


def _cfg(channel_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return dict(channel_config or {})


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default) or default


# ---------------------------------------------------------------------------
# Credentials — Channel.credentials_ref (Vault) → config → env
# ---------------------------------------------------------------------------


def resolve_bot_token(
    *,
    credentials_ref: str = "",
    channel_config: Optional[Dict[str, Any]] = None,
) -> str:
    """Resolve the bot token. Order: Vault ``credentials_ref`` → config → env.

    ``credentials_ref`` format: ``<vault-path>`` or ``<vault-path>#<key>``
    (default key ``bot_token``). The raw token is never logged.

    Raises ``TelegramConfigError`` when nothing resolves — fail-closed.
    """
    cfg = _cfg(channel_config)

    if credentials_ref:
        token = _vault_token(credentials_ref)
        if token:
            return token
        raise TelegramConfigError(
            f"credentials_ref '{credentials_ref}' did not yield a bot token — fail-closed"
        )

    for key in ("bot_token", "token", "api_token"):
        value = str(cfg.get(key) or "").strip()
        if value:
            return value

    for name in ("TG_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "SA01_TELEGRAM_BOT_TOKEN"):
        value = _env(name).strip()
        if value:
            return value

    raise TelegramConfigError(
        "no Telegram bot token: set Channel.credentials_ref (Vault), "
        "config.bot_token, or TG_BOT_TOKEN"
    )


def _vault_token(credentials_ref: str) -> str:
    """Read the token from Vault KV v2 via ``credentials_ref``."""
    ref = credentials_ref.strip()
    if not ref:
        return ""
    path, _, key = ref.partition("#")
    key = (key or "bot_token").strip() or "bot_token"
    path = path.strip()
    if not path:
        return ""
    try:
        from services.common.vault_secrets import load_kv_secret

        value = load_kv_secret(path=path, key=key)
    except Exception as exc:  # noqa: BLE001 — Vault outage must fail closed
        logger.error("vault read failed for credentials_ref %s: %s", path, exc)
        return ""
    return (value or "").strip()


class TelegramConfigError(Exception):
    """Missing/invalid Telegram channel configuration (fail-closed)."""


# ---------------------------------------------------------------------------
# Allowlist + group policy (A0 helpers/handler._is_allowed + group gating)
# ---------------------------------------------------------------------------


@dataclass
class UserAllowlist:
    """Parsed ``allowed_users``. Empty = allow all (A0 parity)."""

    ids: set[str] = field(default_factory=set)
    usernames: set[str] = field(default_factory=set)  # lowercased, no '@'

    def allows(self, user_id: str, username: str = "") -> bool:
        if not self.ids and not self.usernames:
            return True
        if user_id and str(user_id) in self.ids:
            return True
        uname = (username or "").lstrip("@").lower()
        return bool(uname) and uname in self.usernames


def normalize_allowed_users(value: object) -> UserAllowlist:
    """Accept list/tuple/set or comma-delimited string of ids / @usernames."""
    if isinstance(value, str):
        candidates: List[object] = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        candidates = list(value)
    else:
        return UserAllowlist()
    allow = UserAllowlist()
    for item in candidates:
        entry = str(item or "").strip()
        if not entry:
            continue
        if entry.startswith("@"):
            allow.usernames.add(entry[1:].lower())
        elif entry.isdigit() or (entry.startswith("-") and entry[1:].isdigit()):
            allow.ids.add(entry)
        else:
            allow.usernames.add(entry.lower())
    return allow


@dataclass
class PolicyDecision:
    accept: bool
    reason: str = ""


def evaluate_group_mode(msg: InboundEnvelope, group_mode: str) -> PolicyDecision:
    """``group_mode``: off → drop groups; mention → only addressed; all → any."""
    if not msg.is_group:
        return PolicyDecision(True)
    mode = (group_mode or "mention").strip().lower()
    if mode == "off":
        return PolicyDecision(False, "group messages disabled (group_mode=off)")
    if mode == "all":
        return PolicyDecision(True)
    # default: mention
    if not msg.mentioned_me and not msg.replied_to_me:
        return PolicyDecision(False, "group message not addressed to bot (group_mode=mention)")
    return PolicyDecision(True)


# ---------------------------------------------------------------------------
# Bot API client
# ---------------------------------------------------------------------------


class TelegramBotDriver:
    """Telegram Bot API driver (poll getUpdates or webhook-fed DB drain)."""

    kind = "telegram"

    def __init__(
        self,
        *,
        channel_id: str,
        token: str,
        mode: str = "poll",
        channel_config: Optional[Dict[str, Any]] = None,
        api_base: str = TELEGRAM_API_BASE,
    ):
        self.channel_id = channel_id
        self.token = token
        self.mode = (mode or "poll").strip().lower()
        self.config = _cfg(channel_config)
        self.api_base = api_base.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None
        self._offset = int(self.config.get("start_offset") or 0)
        self._bot_id: str = ""
        self._bot_username: str = ""
        self._started_at = asyncio.get_event_loop().time() if _loop_running() else 0.0

    # -- HTTP ---------------------------------------------------------------

    def _url(self, method: str) -> str:
        return f"{self.api_base}/bot{self.token}/{method}"

    def _http(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=_POLL_TIMEOUT)
        return self._client

    async def _call(
        self,
        method: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        timeout: float = _SEND_TIMEOUT,
    ) -> Dict[str, Any]:
        try:
            resp = await self._http().post(self._url(method), json=payload or {}, timeout=timeout)
        except httpx.HTTPError as exc:
            raise BridgeSendError(
                f"telegram {method} transport error: {exc}", retryable=True
            ) from exc
        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get("ok", False):
            # 429 / 5xx retryable; 400 (bad request) and 401/403 (bad token) not.
            retryable = resp.status_code == 429 or resp.status_code >= 500
            description = str(data.get("description") or resp.text[:300] or resp.status_code)
            raise BridgeSendError(
                f"telegram {method} failed: {description}",
                status_code=resp.status_code,
                retryable=retryable,
            )
        result = data.get("result")
        return result if isinstance(result, dict) else {"result": result}

    # -- lifecycle ----------------------------------------------------------

    async def start(self) -> None:
        if not self.token:
            raise TelegramConfigError("telegram bot token missing — fail-closed")
        if self.mode not in {"poll", "webhook"}:
            raise TelegramConfigError(
                f"unknown telegram bridge mode '{self.mode}' (expected poll|webhook)"
            )
        self._http()
        me = await self.get_me()
        self._bot_id = str(me.get("id") or "")
        self._bot_username = str(me.get("username") or "")
        if self.mode == "poll":
            # A stale webhook makes getUpdates return 409 — clear it.
            await self.delete_webhook()
        logger.info(
            "telegram driver started (channel=%s mode=%s bot=@%s)",
            self.channel_id,
            self.mode,
            self._bot_username or "?",
        )

    async def stop(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    async def get_me(self) -> Dict[str, Any]:
        data = await self._call("getMe", timeout=_HEALTH_TIMEOUT)
        return {
            "id": data.get("id"),
            "is_bot": data.get("is_bot"),
            "first_name": data.get("first_name"),
            "username": data.get("username"),
        }

    async def delete_webhook(self) -> None:
        try:
            await self._call(
                "deleteWebhook",
                {"drop_pending_updates": False},
                timeout=_HEALTH_TIMEOUT,
            )
        except BridgeSendError as exc:
            logger.warning("deleteWebhook failed (continuing with polling): %s", exc)

    async def set_webhook(self, url: str, secret_token: str = "") -> Dict[str, Any]:
        payload: Dict[str, Any] = {"url": url, "allowed_updates": ["message", "callback_query"]}
        if secret_token:
            payload["secret_token"] = secret_token
        return await self._call("setWebhook", payload, timeout=_HEALTH_TIMEOUT)

    async def get_webhook_info(self) -> Dict[str, Any]:
        try:
            return await self._call("getWebhookInfo", timeout=_HEALTH_TIMEOUT)
        except BridgeSendError as exc:
            return {"error": str(exc)}

    # -- inbound ------------------------------------------------------------

    async def poll_inbound(self) -> List[InboundEnvelope]:
        """Drain inbound traffic.

        poll mode: long-poll getUpdates (offset advanced per batch).
        webhook mode: unprocessed InboundMessage rows written by the webhook.
        """
        if self.mode == "webhook":
            return await self._poll_db()
        return await self._poll_updates()

    async def _poll_updates(self) -> List[InboundEnvelope]:
        timeout = int(self.config.get("get_updates_timeout", _env("TG_GET_UPDATES_TIMEOUT", "1")))
        payload: Dict[str, Any] = {
            "offset": self._offset,
            "timeout": max(0, timeout),
            "allowed_updates": ["message", "callback_query"],
        }
        try:
            resp = await self._http().post(
                self._url("getUpdates"), json=payload, timeout=_POLL_TIMEOUT + timeout
            )
        except httpx.HTTPError as exc:
            logger.warning("telegram getUpdates failed: %s", exc)
            return []
        data = _safe_json(resp)
        if resp.status_code != 200 or not data.get("ok", False):
            logger.warning(
                "telegram getUpdates status %s: %s", resp.status_code, data.get("description")
            )
            return []
        updates = data.get("result") or []
        if not isinstance(updates, list) or not updates:
            return []

        if not self._bot_id:
            try:
                me = await self.get_me()
                self._bot_id = str(me.get("id") or "")
                self._bot_username = str(me.get("username") or "")
            except BridgeSendError:
                pass

        envelopes: List[InboundEnvelope] = []
        max_update_id = self._offset - 1 if self._offset else -1
        for item in updates:
            if not isinstance(item, dict):
                continue
            uid = int(item.get("update_id") or 0)
            if uid > max_update_id:
                max_update_id = uid
            env = map_update_to_envelope(item, bot_id=self._bot_id, bot_username=self._bot_username)
            if env is not None:
                envelopes.append(env)
        # Advance offset so a crashed consumer does not loop on the same batch
        # forever — the dispatcher also dedupes on (channel, external_id).
        self._offset = max_update_id + 1
        return envelopes

    async def _poll_db(self) -> List[InboundEnvelope]:
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

    # -- policy hook (used by the dispatcher) -------------------------------

    def check_inbound_policy(self, msg: InboundEnvelope) -> PolicyDecision:
        allow = normalize_allowed_users(
            self.config.get("allowed_users", self.config.get("allowlist"))
        )
        sender = msg.sender_id or msg.sender_number
        if not allow.allows(sender, msg.sender_name or _username_from_raw(msg.raw)):
            return PolicyDecision(False, f"sender {sender} not in allowed_users")
        return evaluate_group_mode(msg, str(self.config.get("group_mode") or "mention"))

    # -- outbound -----------------------------------------------------------

    async def send_outbound(self, payload: OutboundPayload) -> Dict[str, Any]:
        chat_id = str(payload.chat_id or "").strip()
        if not chat_id:
            raise BridgeSendError("telegram outbound missing chat_id", retryable=False)

        if payload.media_path:
            return await self._send_media(payload)

        text = payload.text or payload.caption or ""
        if not text:
            raise BridgeSendError("empty outbound text", retryable=False)

        last: Dict[str, Any] = {}
        for chunk in _split_text(text, MAX_MESSAGE_LENGTH):
            last = await self._send_text(chat_id, chunk, reply_to=payload.reply_to)
        return last

    async def _send_text(self, chat_id: str, text: str, *, reply_to: str = "") -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": str(self.config.get("parse_mode") or "Markdown"),
        }
        if reply_to:
            body["reply_to_message_id"] = _as_int_or_none(reply_to)
            if body["reply_to_message_id"] is None:
                body.pop("reply_to_message_id")
        try:
            return await self._call("sendMessage", body)
        except BridgeSendError as exc:
            # A0 parity: Markdown parse errors fall back to plain text.
            if exc.status_code == 400 and "parse" in str(exc).lower():
                plain = re.sub(r"<[^>]+>", "", text)
                plain = re.sub(r"[*_`\\]", "", plain)
                fallback = {"chat_id": chat_id, "text": plain}
                if body.get("reply_to_message_id") is not None:
                    fallback["reply_to_message_id"] = body["reply_to_message_id"]
                return await self._call("sendMessage", fallback)
            raise

    async def _send_media(self, payload: OutboundPayload) -> Dict[str, Any]:
        caption = (payload.caption or payload.text or "")[:1024]
        media_type = (payload.media_type or "").lower()
        method = "sendPhoto" if media_type in {"image", "photo"} else "sendDocument"
        # Local file upload via multipart — real send, no placeholder URL.
        try:
            with open(payload.media_path, "rb") as fh:
                files = {"photo" if method == "sendPhoto" else "document": fh}
                data: Dict[str, Any] = {"chat_id": payload.chat_id}
                if caption:
                    data["caption"] = caption
                if payload.file_name and method == "sendDocument":
                    files = {"document": (payload.file_name, fh)}
                if payload.reply_to:
                    reply_int = _as_int_or_none(payload.reply_to)
                    if reply_int is not None:
                        data["reply_to_message_id"] = reply_int
                resp = await self._http().post(
                    self._url(method), data=data, files=files, timeout=_SEND_TIMEOUT
                )
        except OSError as exc:
            raise BridgeSendError(f"telegram media not readable: {exc}", retryable=False) from exc
        result = _safe_json(resp)
        if resp.status_code != 200 or not result.get("ok", False):
            retryable = resp.status_code == 429 or resp.status_code >= 500
            raise BridgeSendError(
                f"telegram {method} failed: {result.get('description') or resp.status_code}",
                status_code=resp.status_code,
                retryable=retryable,
            )
        return result.get("result") if isinstance(result.get("result"), dict) else {"ok": True}

    async def send_typing(self, chat_id: str, paused: bool = False) -> None:
        """One-shot typing indicator (never fatal)."""
        if paused or not chat_id:
            return
        try:
            await self._call(
                "sendChatAction", {"chat_id": chat_id, "action": "typing"}, timeout=_HEALTH_TIMEOUT
            )
        except Exception:  # noqa: BLE001 — typing is best-effort
            pass

    @asynccontextmanager
    async def typing_session(self, chat_id: str) -> AsyncIterator[None]:
        """Keep ``sendChatAction/typing`` alive while the agent runs (A0 loop)."""
        stop = asyncio.Event()
        task = asyncio.create_task(self._typing_loop(chat_id, stop))
        try:
            yield
        finally:
            stop.set()
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

    async def _typing_loop(self, chat_id: str, stop: asyncio.Event) -> None:
        while not stop.is_set():
            await self.send_typing(chat_id)
            try:
                await asyncio.wait_for(stop.wait(), timeout=_TYPING_INTERVAL)
            except asyncio.TimeoutError:
                continue

    # -- health / qr --------------------------------------------------------

    async def health(self) -> DriverHealth:
        if not self.token:
            return DriverHealth(status="misconfigured", detail="bot token missing")
        try:
            me = await self.get_me()
        except BridgeSendError as exc:
            return DriverHealth(status="unreachable", detail=str(exc))
        extra: Dict[str, Any] = {
            "mode": self.mode,
            "bot_id": me.get("id"),
            "bot_username": me.get("username"),
        }
        if self.mode == "webhook":
            info = await self.get_webhook_info()
            extra["webhook"] = {
                "url": info.get("url"),
                "has_custom_certificate": info.get("has_custom_certificate"),
                "pending_update_count": info.get("pending_update_count"),
                "last_error_date": info.get("last_error_date"),
                "last_error_message": info.get("last_error_message"),
            }
        return DriverHealth(status="ok", detail=f"bot @{me.get('username')}", extra=extra)

    async def get_qr(self) -> Optional[Dict[str, Any]]:
        # Token-based auth — QR pairing is WhatsApp/Baileys-only.
        return {
            "status": "not_applicable",
            "qr": None,
            "detail": "Telegram uses a bot token; QR pairing is WhatsApp-only",
        }


def _loop_running() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


# ---------------------------------------------------------------------------
# Update → InboundEnvelope mapping
# ---------------------------------------------------------------------------


def map_update_to_envelope(
    update: Dict[str, Any], *, bot_id: str = "", bot_username: str = ""
) -> Optional[InboundEnvelope]:
    """Map a Bot API Update to InboundEnvelope. None for non-user traffic."""
    msg = update.get("message") or update.get("edited_message")
    if not isinstance(msg, dict):
        return None
    # new_chat_members / service messages without text: handled by welcome path
    # later; skip here so the agent never sees empty service events.
    sender = msg.get("from") or {}
    if not isinstance(sender, dict) or sender.get("is_bot"):
        return None

    chat = msg.get("chat") or {}
    if not isinstance(chat, dict):
        chat = {}

    text = str(msg.get("text") or msg.get("caption") or "")
    media_type = _detect_media(msg)
    chat_type = str(chat.get("type") or "")
    is_group = chat_type in {"group", "supergroup", "channel"}

    user_id = str(sender.get("id") or "")
    chat_id = str(chat.get("id") or user_id)
    message_id = str(msg.get("message_id") or "")
    external_id = f"{chat_id}:{message_id}" if message_id else ""

    sender_name = " ".join(
        p for p in (str(sender.get("first_name") or ""), str(sender.get("last_name") or "")) if p
    ).strip() or str(sender.get("username") or user_id or "Unknown")
    username = str(sender.get("username") or "")

    mentioned_me, replied_to_me = _addressing_flags(msg, bot_id=bot_id, bot_username=bot_username)

    return InboundEnvelope(
        external_id=external_id,
        chat_id=chat_id,
        sender_id=user_id,
        sender_number=user_id,
        sender_name=sender_name,
        chat_name=str(chat.get("title") or chat.get("username") or ""),
        is_group=is_group,
        mentioned_me=mentioned_me,
        replied_to_me=replied_to_me,
        body=text,
        has_media=bool(media_type),
        media_type=media_type,
        media_urls=[],
        timestamp=msg.get("date"),
        raw={
            "update_id": update.get("update_id"),
            "message_id": message_id,
            "chat_type": chat_type,
            "username": username,
            "entities": msg.get("entities") or msg.get("caption_entities") or [],
            "reply_to_message_id": str((msg.get("reply_to_message") or {}).get("message_id") or ""),
            "raw_update": update,
        },
    )


def _detect_media(msg: Dict[str, Any]) -> str:
    for tg_type, label in _TG_MEDIA_KINDS.items():
        if msg.get(tg_type):
            return label
    return ""


def _addressing_flags(msg: Dict[str, Any], *, bot_id: str, bot_username: str) -> tuple[bool, bool]:
    """mentioned_me / replied_to_me — A0 group gating inputs."""
    text = str(msg.get("text") or msg.get("caption") or "")
    mentioned = False
    if bot_username:
        uname = bot_username.lstrip("@").lower()
        mentioned = f"@{uname}" in text.lower()
    entities = msg.get("entities") or msg.get("caption_entities") or []
    if not mentioned and isinstance(entities, list):
        for ent in entities:
            if not isinstance(ent, dict):
                continue
            etype = str(ent.get("type") or "")
            if etype == "text_mention":
                ent_user = ent.get("user") or {}
                if bot_id and str(ent_user.get("id") or "") == str(bot_id):
                    mentioned = True
            elif etype == "mention" and bot_username:
                offset = int(ent.get("offset") or 0)
                length = int(ent.get("length") or 0)
                segment = text[offset : offset + length].lstrip("@").lower()
                if segment and segment == bot_username.lstrip("@").lower():
                    mentioned = True

    reply = msg.get("reply_to_message") or {}
    reply_from = reply.get("from") or {} if isinstance(reply, dict) else {}
    replied = False
    if isinstance(reply_from, dict) and reply_from:
        if bot_id and str(reply_from.get("id") or "") == str(bot_id):
            replied = True
        elif (
            bot_username
            and str(reply_from.get("username") or "").lstrip("@").lower()
            == bot_username.lstrip("@").lower()
        ):
            replied = True
    return mentioned, replied


def _username_from_raw(raw: Dict[str, Any]) -> str:
    return str((raw or {}).get("username") or "")


# ---------------------------------------------------------------------------
# Webhook secret (fail-closed)
# ---------------------------------------------------------------------------


def verify_webhook_secret(expected: str, provided: str) -> bool:
    """Constant-time secret check. Missing expected secret → reject (fail-closed)."""
    if not expected or not provided:
        return False
    return hmac.compare_digest(str(expected), str(provided))


def resolve_webhook_secret(
    *, channel_config: Optional[Dict[str, Any]] = None, credentials_ref: str = ""
) -> str:
    """Webhook secret: config → Vault (``credentials_ref`` key ``webhook_secret``) → env."""
    cfg = _cfg(channel_config)
    secret = str(cfg.get("webhook_secret") or "").strip()
    if secret:
        return secret
    if credentials_ref:
        secret = _vault_key(credentials_ref, "webhook_secret")
        if secret:
            return secret
    return _env("TG_WEBHOOK_SECRET").strip()


def _vault_key(credentials_ref: str, key: str) -> str:
    ref = credentials_ref.strip()
    if not ref:
        return ""
    path, _, _ = ref.partition("#")
    path = path.strip()
    if not path:
        return ""
    try:
        from services.common.vault_secrets import load_kv_secret

        return (load_kv_secret(path=path, key=key) or "").strip()
    except Exception:  # noqa: BLE001
        return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_json(resp: httpx.Response) -> Dict[str, Any]:
    try:
        data = resp.json()
        return data if isinstance(data, dict) else {"raw": data}
    except Exception:  # noqa: BLE001
        return {"raw": resp.text[:500]}


def _split_text(text: str, limit: int = MAX_MESSAGE_LENGTH) -> List[str]:
    """Split on newlines first (A0 telegram_client._split_text behaviour)."""
    if len(text) <= limit:
        return [text] if text else []
    chunks: List[str] = []
    current = ""
    for line in text.splitlines(keepends=True):
        if len(current) + len(line) > limit and current:
            chunks.append(current)
            current = ""
        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]
        current += line
    if current:
        chunks.append(current)
    return chunks


def _as_int_or_none(value: str) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

TelegramDriver = TelegramBotDriver


def build_telegram_driver(
    channel_id: str,
    channel_config: Optional[Dict[str, Any]] = None,
    *,
    credentials_ref: str = "",
) -> TelegramBotDriver:
    """Factory — poll or webhook mode from config/env.

    Fail-closed: missing token raises ``TelegramConfigError``; unknown mode
    raises ``ValueError``.
    """
    cfg = _cfg(channel_config)
    mode = str(cfg.get("mode") or _env("TG_BRIDGE_MODE", "poll")).strip().lower()
    token = resolve_bot_token(credentials_ref=credentials_ref, channel_config=cfg)
    api_base = str(cfg.get("api_base") or _env("TG_API_BASE", TELEGRAM_API_BASE))
    return TelegramBotDriver(
        channel_id=channel_id,
        token=token,
        mode=mode,
        channel_config=cfg,
        api_base=api_base,
    )


# Type-check the protocol conformance at import time (documentation aid).
def _protocol_check() -> None:
    assert isinstance(TelegramBotDriver, type)
    _: BridgeDriver  # noqa: F841 — structural type only


_protocol_check()
