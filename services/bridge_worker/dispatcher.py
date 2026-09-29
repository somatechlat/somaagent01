"""Bridge dispatcher — inbound → BridgeSession → V3 turn → outbound.

Clones A0 ``plugins/_whatsapp_integration/helpers/handler.py`` behaviour:

- allowlist filtering is authoritative on the Python side (not the sidecar)
- group messages require ``allow_group`` AND (mentionedMe OR repliedToMe)
- jid→chat routing: find existing BridgeSession by (channel, external chat/user)
- user message envelope (``fw.wa.user_message.md`` / ``..._group.md``)
- channel context injected into the prompt (BR-06 / ``fw.wa.system_context*.md``)
- outbound reply with retry + never silent-drop (BR-07)

Fail-closed (T-5 / BR-09): missing ``Channel.capsule`` or ``Channel.tenant``
hard-fails dispatch. The per-kind feature flag (``bridge_whatsapp`` /
``bridge_telegram``) is checked first.
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

from services.bridge_worker.drivers.base import (
    BridgeSendError,
    InboundEnvelope,
    OutboundPayload,
    SupportsSendTyping,
    SupportsTypingSession,
)

logger = logging.getLogger(__name__)

# BR-07 outbound retry policy.
MAX_SEND_ATTEMPTS = int(os.environ.get("SA01_BRIDGE_MAX_SEND_ATTEMPTS", "5"))
BACKOFF_BASE_SECONDS = float(os.environ.get("SA01_BRIDGE_BACKOFF_BASE", "2.0"))
BACKOFF_CAP_SECONDS = float(os.environ.get("SA01_BRIDGE_BACKOFF_CAP", "60.0"))


# ---------------------------------------------------------------------------
# Feature flag gate
# ---------------------------------------------------------------------------


def _flag_enabled(flag: str) -> bool:
    """Check a bridge feature flag. Fail-closed when registry errors."""
    try:
        from services.common.features import build_default_registry

        return bool(build_default_registry().is_enabled(flag))
    except Exception as exc:  # noqa: BLE001 — fail-closed on registry failure
        logger.error("feature flag check failed for %s, bridge disabled: %s", flag, exc)
        return False


def is_whatsapp_bridge_enabled() -> bool:
    """Check ``bridge_whatsapp`` feature flag. Fail-closed when registry errors."""
    return _flag_enabled("bridge_whatsapp")


def is_telegram_bridge_enabled() -> bool:
    """Check ``bridge_telegram`` feature flag. Fail-closed when registry errors."""
    return _flag_enabled("bridge_telegram")


_KIND_FLAGS = {
    "whatsapp": is_whatsapp_bridge_enabled,
    "telegram": is_telegram_bridge_enabled,
}


def is_bridge_enabled(kind: str) -> bool:
    """Per-channel-kind flag gate (unknown kind → fail-closed)."""
    check = _KIND_FLAGS.get(str(kind or "").lower())
    if check is None:
        return False
    return check()


# ---------------------------------------------------------------------------
# Channel context (BR-06) — A0 fw.wa.system_context*.md parity
# ---------------------------------------------------------------------------

# A0: prompts/fw.wa.system_context.md
_WA_SYSTEM_CONTEXT = """\
whatsapp session user communicates via whatsapp
response is sent back as a whatsapp message — keep it concise and chat-friendly
break the reply when done and wait for the user's next message
always keep the user informed: say what you are doing now and what comes next
"""

# A0: prompts/fw.wa.system_context_reply.md (group / multi-turn guidance)
_WA_SYSTEM_CONTEXT_REPLY = """\
# WhatsApp session behavior
user communicates via whatsapp
reply text is delivered to the WhatsApp chat
in group chats quote the triggering message when relevant
include file paths when attachments must be sent to the user
"""

# A0: prompts/fw.wa.user_message.md
_USER_MESSAGE_DM = (
    "[WhatsApp from {sender_name} {sender_number}]\n\n{body}\n\n[End WhatsApp message]"
)

# A0: prompts/fw.wa.user_message_group.md
_USER_MESSAGE_GROUP = (
    '[WhatsApp group "{group_name}" from {sender_name} id:{message_id}]\n\n'
    "{body}\n\n[End WhatsApp message]"
)

# A0: prompts/fw.telegram.* parity (BR-02 / Annex D.5)
_TG_SYSTEM_CONTEXT = """\
telegram session user communicates via telegram
response is sent back as a telegram message — keep it concise and chat-friendly
break the reply when done and wait for the user's next message
always keep the user informed: say what you are doing now and what comes next
"""

_TG_SYSTEM_CONTEXT_REPLY = """\
# Telegram session behavior
user communicates via telegram
reply text is delivered to the Telegram chat
in group chats quote the triggering message when relevant
include file paths when attachments must be sent to the user
"""

_USER_MESSAGE_TG_DM = (
    "[Telegram from {sender_name} {sender_number}]\n\n{body}\n\n[End Telegram message]"
)

_USER_MESSAGE_TG_GROUP = (
    '[Telegram group "{group_name}" from {sender_name} id:{message_id}]\n\n'
    "{body}\n\n[End Telegram message]"
)

_KIND_LABELS = {"whatsapp": "WhatsApp", "telegram": "Telegram"}


def build_channel_context(
    *,
    is_group: bool,
    sender_name: str,
    sender_number: str,
    chat_name: str,
    agent_instructions: str = "",
    channel_kind: str = "whatsapp",
) -> str:
    """Build the channel-context block injected into the turn (BR-06).

    Mirrors A0 ``system_prompt/_20_wa_context.py`` which appends
    ``fw.wa.system_context_reply.md`` + ``fw.wa.user_message_instructions.md``.
    """
    kind = (channel_kind or "whatsapp").lower()
    label = _KIND_LABELS.get(kind, kind)
    if kind == "telegram":
        parts = [
            "[Channel context: Telegram]",
            _TG_SYSTEM_CONTEXT,
            _TG_SYSTEM_CONTEXT_REPLY,
            f"Chat type: {'group' if is_group else 'direct message'}",
            f"Contact: {sender_name or 'Unknown'} ({sender_number or 'n/a'})",
        ]
    else:
        parts = [
            "[Channel context: WhatsApp]",
            _WA_SYSTEM_CONTEXT,
            _WA_SYSTEM_CONTEXT_REPLY,
            f"Chat type: {'group' if is_group else 'direct message'}",
            f"Contact: {sender_name or 'Unknown'} ({sender_number or 'n/a'})",
        ]
    if is_group and chat_name:
        parts.append(f'Group: "{chat_name}"')
    if agent_instructions:
        parts.append(f"Channel agent instructions:\n{agent_instructions}")
    return "\n".join(parts)


def build_user_envelope(msg: InboundEnvelope, channel_kind: str = "whatsapp") -> str:
    """Wrap the inbound body in the A0 channel message envelope."""
    kind = (channel_kind or "whatsapp").lower()
    if kind == "telegram":
        if msg.is_group:
            return _USER_MESSAGE_TG_GROUP.format(
                group_name=msg.chat_name or msg.chat_id,
                sender_name=msg.sender_name or msg.sender_number or "Unknown",
                message_id=msg.external_id or "unknown",
                body=msg.body or "",
            )
        return _USER_MESSAGE_TG_DM.format(
            sender_name=msg.sender_name or "Unknown",
            sender_number=msg.sender_number or msg.sender_id or "",
            body=msg.body or "",
        )
    if msg.is_group:
        return _USER_MESSAGE_GROUP.format(
            group_name=msg.chat_name or msg.chat_id,
            sender_name=msg.sender_name or msg.sender_number or "Unknown",
            message_id=msg.external_id or "unknown",
            body=msg.body or "",
        )
    return _USER_MESSAGE_DM.format(
        sender_name=msg.sender_name or "Unknown",
        sender_number=msg.sender_number or msg.sender_id or "",
        body=msg.body or "",
    )


# ---------------------------------------------------------------------------
# Allowlist / group policy (A0 handler.poll_messages + _dispatch_message)
# ---------------------------------------------------------------------------


@dataclass
class DispatchDecision:
    accept: bool
    reason: str = ""


def evaluate_inbound(
    msg: InboundEnvelope, channel_config: Dict[str, Any], driver: Any = None
) -> DispatchDecision:
    """A0 allowlist + group gating. Python-side is authoritative (A0 clone).

    Drivers may supply their own policy via ``check_inbound_policy`` (Telegram
    ``allowed_users`` / ``group_mode``); the WhatsApp number allowlist remains
    the default.
    """
    hook = getattr(driver, "check_inbound_policy", None)
    if callable(hook):
        decision = hook(msg)
        return DispatchDecision(
            bool(getattr(decision, "accept", False)),
            str(getattr(decision, "reason", "") or ""),
        )

    from services.bridge_worker.drivers.whatsapp import (
        normalize_allowed_numbers,
        normalize_number,
    )

    allowed_raw = channel_config.get("allowed_numbers", channel_config.get("allowlist"))
    allowed_set = normalize_allowed_numbers(allowed_raw)
    if allowed_set:
        sender_num = normalize_number(msg.sender_number or msg.sender_id)
        if sender_num not in allowed_set:
            return DispatchDecision(False, f"sender {sender_num} not in allowlist")

    if msg.is_group:
        if not bool(channel_config.get("allow_group", False)):
            return DispatchDecision(False, "group messages disabled (allow_group=false)")
        # A0: skip unless mentioned or replied-to the bot.
        if not msg.mentioned_me and not msg.replied_to_me:
            return DispatchDecision(False, "group message not addressed to bot (no mention/reply)")

    return DispatchDecision(True)


# ---------------------------------------------------------------------------
# Outbound queue + retry (BR-07: never silent-drop)
# ---------------------------------------------------------------------------


class OutboundSender:
    """Queues outbound replies and delivers them with exponential backoff.

    Every reply is persisted as ``OutboundMessage`` BEFORE the first send
    attempt. Failures after max attempts mark the row ``failed`` and push to
    the DLQ store — the message is never dropped silently.
    """

    def __init__(self, driver: Any, channel_id: str):
        self.driver = driver
        self.channel_id = channel_id

    async def send_reply(
        self,
        *,
        session_id: Optional[str],
        chat_id: str,
        text: str,
        reply_to: str = "",
        media_path: str = "",
        media_type: str = "",
        caption: str = "",
        idempotency_key: str = "",
    ) -> Dict[str, Any]:
        """Queue + send with retry. Returns delivery result dict."""
        outbound_id = await self._queue_outbound(
            session_id=session_id,
            chat_id=chat_id,
            text=text,
            reply_to=reply_to,
            media_path=media_path,
            media_type=media_type,
            caption=caption,
            idempotency_key=idempotency_key or str(uuid.uuid4()),
        )
        return await self._deliver(outbound_id)

    async def _queue_outbound(
        self,
        *,
        session_id: Optional[str],
        chat_id: str,
        text: str,
        reply_to: str,
        media_path: str,
        media_type: str,
        caption: str,
        idempotency_key: str,
    ) -> str:
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _create() -> str:
            from admin.bridges.models import OutboundMessage

            # Idempotency: reuse existing row if the key was already queued.
            existing = OutboundMessage.objects.filter(
                channel_id=self.channel_id, idempotency_key=idempotency_key
            ).first()
            if existing is not None:
                return str(existing.id)

            row = OutboundMessage.objects.create(
                channel_id=self.channel_id,
                session_id=session_id,
                payload={
                    "chat_id": chat_id,
                    "text": text,
                    "reply_to": reply_to,
                    "media_path": media_path,
                    "media_type": media_type,
                    "caption": caption,
                },
                status=OutboundMessage.STATUS_QUEUED,
                idempotency_key=idempotency_key,
            )
            return str(row.id)

        return await _create()

    async def _deliver(self, outbound_id: str) -> Dict[str, Any]:
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _load() -> Optional[Dict[str, Any]]:
            from admin.bridges.models import OutboundMessage

            try:
                row = OutboundMessage.objects.get(id=outbound_id)
            except OutboundMessage.DoesNotExist:
                return None
            return {
                "id": str(row.id),
                "payload": row.payload or {},
                "attempts": row.attempts,
                "status": row.status,
            }

        state = await _load()
        if state is None:
            raise BridgeSendError(f"outbound {outbound_id} vanished", retryable=False)

        payload = OutboundPayload(
            chat_id=str((state["payload"] or {}).get("chat_id") or ""),
            text=str((state["payload"] or {}).get("text") or ""),
            reply_to=str((state["payload"] or {}).get("reply_to") or ""),
            media_path=str((state["payload"] or {}).get("media_path") or ""),
            media_type=str((state["payload"] or {}).get("media_type") or ""),
            caption=str((state["payload"] or {}).get("caption") or ""),
        )

        attempts = int(state["attempts"] or 0)
        last_error = ""
        while attempts < MAX_SEND_ATTEMPTS:
            attempts += 1
            try:
                result = await self.driver.send_outbound(payload)
                await self._mark_sent(outbound_id, attempts)
                return {"status": "sent", "attempts": attempts, "result": result}
            except BridgeSendError as exc:
                last_error = str(exc)
                logger.warning(
                    "outbound %s attempt %d/%d failed: %s",
                    outbound_id,
                    attempts,
                    MAX_SEND_ATTEMPTS,
                    exc,
                )
                if not exc.retryable:
                    break
                if attempts < MAX_SEND_ATTEMPTS:
                    delay = min(
                        BACKOFF_BASE_SECONDS * (2 ** (attempts - 1)),
                        BACKOFF_CAP_SECONDS,
                    )
                    await asyncio.sleep(delay)
            except Exception as exc:  # noqa: BLE001 — treat as retryable transport error
                last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("outbound %s attempt %d crashed", outbound_id, attempts)
                if attempts < MAX_SEND_ATTEMPTS:
                    delay = min(
                        BACKOFF_BASE_SECONDS * (2 ** (attempts - 1)),
                        BACKOFF_CAP_SECONDS,
                    )
                    await asyncio.sleep(delay)

        await self._mark_failed(outbound_id, attempts, last_error)
        await self._dlq(outbound_id, payload, attempts, last_error)
        # Never silent-drop: caller can see status=failed; row + DLQ retain the payload.
        return {"status": "failed", "attempts": attempts, "error": last_error}

    async def _mark_sent(self, outbound_id: str, attempts: int) -> None:
        from asgiref.sync import sync_to_async
        from django.utils import timezone

        @sync_to_async
        def _update() -> None:
            from admin.bridges.models import OutboundMessage

            OutboundMessage.objects.filter(id=outbound_id).update(
                status=OutboundMessage.STATUS_SENT,
                attempts=attempts,
                sent_at=timezone.now(),
                last_error="",
            )

        await _update()

    async def _mark_failed(self, outbound_id: str, attempts: int, last_error: str) -> None:
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _update() -> None:
            from admin.bridges.models import OutboundMessage

            # Stay on the OutboundMessage table (DLQ visibility) — status=failed
            # with attempts + last_error is the never-silent-drop contract.
            OutboundMessage.objects.filter(id=outbound_id).update(
                status=OutboundMessage.STATUS_FAILED,
                attempts=attempts,
                last_error=last_error[:4000],
            )

        await _update()

    async def _dlq(
        self, outbound_id: str, payload: OutboundPayload, attempts: int, last_error: str
    ) -> None:
        """Push failed outbound into the DLQ store (BR-07)."""
        try:
            from services.common.dlq_store import DLQStore

            store = DLQStore()
            await store.ensure_schema()
            # DLQStore.add signature is (topic, event, error) — topic names the
            # dead-letter stream, event carries the failed record.
            await store.add(
                topic="bridge_outbound",
                event={
                    "channel_id": self.channel_id,
                    "outbound_id": outbound_id,
                    "payload": payload.to_payload(),
                    "attempts": attempts,
                    "error": last_error,
                },
                error=last_error,
            )
        except Exception:  # noqa: BLE001 — DLQ push must not mask the failed send
            logger.exception("DLQ push failed for outbound %s", outbound_id)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


class BridgeDispatcher:
    """Dispatch one inbound envelope end-to-end.

    Responsibilities (A0 handler._dispatch_message / _start_new_chat /
    _route_to_chat, plus Soma Capsule binding):
      1. feature flag gate (fail-closed)
      2. Channel.tenant + Channel.capsule required (fail-closed)
      3. allowlist + group policy
      4. find/create BridgeSession (jid→chat)
      5. persist InboundMessage
      6. build ChatTurn with channel context (BR-06)
      7. V3ChatOrchestrator.process_turn (or stream_turn)
      8. OutboundSender with retry / DLQ
    """

    def __init__(self, driver: Any, channel: Any):
        self.driver = driver
        self.channel = channel
        self.channel_id = str(channel.id)
        self.kind = str(getattr(channel, "kind", "") or "whatsapp").lower()
        self.config: Dict[str, Any] = dict(getattr(channel, "config", None) or {})
        self.sender = OutboundSender(driver, self.channel_id)

    # -- fail-closed guards -------------------------------------------------

    def _require_binding(self) -> Dict[str, Any]:
        """Return {tenant_id, capsule} or raise. Fail-closed (T-5, BR-09)."""
        tenant_id = getattr(self.channel, "tenant_id", None)
        capsule_id = getattr(self.channel, "capsule_id", None)
        if not tenant_id:
            raise RuntimeError(f"channel {self.channel_id} has no tenant binding — fail-closed")
        if not capsule_id:
            raise RuntimeError(f"channel {self.channel_id} has no capsule binding — fail-closed")
        from admin.core.models import Capsule

        capsule = Capsule.objects.select_related("tenant").filter(id=capsule_id).first()
        if capsule is None:
            raise RuntimeError(
                f"channel {self.channel_id} capsule {capsule_id} not found — fail-closed"
            )
        return {"tenant_id": str(tenant_id), "capsule": capsule}

    # -- session routing ----------------------------------------------------

    async def _get_or_create_session(self, msg: InboundEnvelope) -> Any:
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _run() -> Any:
            from admin.bridges.models import BridgeSession

            chat_id = msg.chat_id or msg.sender_id
            qs = BridgeSession.objects.filter(
                channel_id=self.channel_id,
                external_user_id=msg.sender_id or msg.sender_number or chat_id,
                external_chat_id=chat_id,
            )
            session = qs.order_by("-updated_at").first()
            if session is not None:
                return session
            return BridgeSession.objects.create(
                channel_id=self.channel_id,
                external_user_id=msg.sender_id or msg.sender_number or chat_id,
                external_chat_id=chat_id,
                state=BridgeSession.STATE_ACTIVE,
                context={
                    "is_group": msg.is_group,
                    "chat_name": msg.chat_name,
                    "sender_name": msg.sender_name,
                    "sender_number": msg.sender_number,
                },
            )

        return await _run()

    async def _ensure_conversation(self, session: Any, tenant_id: str) -> Optional[str]:
        """Bind a Soma Conversation to the BridgeSession (created once)."""
        ctx = dict(getattr(session, "context", None) or {})
        if ctx.get("conversation_id"):
            return str(ctx["conversation_id"])

        from admin.core.chat_orchestrator import get_chat_orchestrator

        orch = await get_chat_orchestrator()
        label = _KIND_LABELS.get(self.kind, self.kind)
        summary = await orch.create_conversation(
            agent_id=str(getattr(self.channel, "capsule_id", "")),
            user_id=f"bridge:{session.external_user_id}",
            tenant_id=tenant_id,
            title=f"{label} {session.external_chat_id or session.external_user_id}"[:255],
        )

        from asgiref.sync import sync_to_async

        @sync_to_async
        def _store() -> str:
            session.context = {**ctx, "conversation_id": summary.id}
            session.save(update_fields=["context", "updated_at"])
            return summary.id

        return await _store()

    async def _persist_inbound(
        self, msg: InboundEnvelope, session: Any, processed: bool = False
    ) -> Optional[str]:
        """Store InboundMessage. Dedupe on (channel, external_id).

        Cloud webhook rows already exist (``raw.inbound_message_id``) — those
        are reused and only linked to the session, never duplicated.
        """
        from asgiref.sync import sync_to_async
        from django.utils import timezone

        @sync_to_async
        def _run() -> Optional[str]:
            from admin.bridges.models import InboundMessage

            existing_id = str((msg.raw or {}).get("inbound_message_id") or "")
            if existing_id:
                InboundMessage.objects.filter(id=existing_id).update(
                    session_id=getattr(session, "id", None)
                )
                return existing_id

            if msg.external_id:
                existing = InboundMessage.objects.filter(
                    channel_id=self.channel_id, external_id=msg.external_id
                ).first()
                if existing is not None:
                    return str(existing.id)

            row = InboundMessage.objects.create(
                channel_id=self.channel_id,
                session_id=getattr(session, "id", None),
                external_id=msg.external_id or "",
                direction="inbound",
                payload=msg.to_payload(),
                attachments=[{"path": u, "media_type": msg.media_type} for u in msg.media_urls],
            )
            if processed:
                InboundMessage.objects.filter(id=row.id).update(processed_at=timezone.now())
            return str(row.id)

        return await _run()

    async def _mark_processed(self, inbound_id: str) -> None:
        if not inbound_id:
            return
        from asgiref.sync import sync_to_async
        from django.utils import timezone

        @sync_to_async
        def _run() -> None:
            from admin.bridges.models import InboundMessage

            InboundMessage.objects.filter(id=inbound_id).update(processed_at=timezone.now())

        await _run()

    # -- channel context / agent instructions ------------------------------

    def _agent_instructions(self, capsule: Any) -> str:
        persona = getattr(capsule, "persona_config", None) or {}
        if not isinstance(persona, dict):
            return ""
        channel_ctx = persona.get("channel_context") or {}
        if isinstance(channel_ctx, dict):
            return str(
                channel_ctx.get("instructions")
                or channel_ctx.get(self.kind)
                or channel_ctx.get("whatsapp")
                or ""
            )
        return str(channel_ctx or "")

    # -- main entry --------------------------------------------------------

    @asynccontextmanager
    async def _typing_indicator(self, chat_id: str) -> AsyncIterator[None]:
        """Typing while the agent runs: driver typing_session if available
        (Telegram sendChatAction loop), else a one-shot best-effort poke."""
        # Structural capability checks — drivers that implement the method
        # advertise it; getattr+callable narrowed to `object` and hid the
        # async CM / coroutine shapes.
        if isinstance(self.driver, SupportsTypingSession):
            async with self.driver.typing_session(chat_id):
                yield
            return
        if isinstance(self.driver, SupportsSendTyping):
            try:
                await self.driver.send_typing(chat_id)
            except Exception:  # noqa: BLE001 — typing is never fatal
                pass
        yield

    async def dispatch(self, msg: InboundEnvelope) -> Dict[str, Any]:
        """Process one inbound message. Returns a result dict (never raises for
        policy skips; raises only on fail-closed binding violations)."""
        if not is_bridge_enabled(self.kind):
            logger.info("bridge_%s disabled — skipping inbound on %s", self.kind, self.channel_id)
            # Claim any pre-stored cloud row so it is not re-polled forever.
            await self._mark_processed(str((msg.raw or {}).get("inbound_message_id") or ""))
            return {"status": "skipped", "reason": "feature_disabled"}

        binding = self._require_binding()
        tenant_id = binding["tenant_id"]
        capsule = binding["capsule"]

        decision = evaluate_inbound(msg, self.config, self.driver)
        if not decision.accept:
            logger.info("inbound rejected (%s) on %s", decision.reason, self.channel_id)
            await self._mark_processed(str((msg.raw or {}).get("inbound_message_id") or ""))
            return {"status": "rejected", "reason": decision.reason}

        session = await self._get_or_create_session(msg)
        inbound_id = await self._persist_inbound(msg, session, processed=False)

        conversation_id = await self._ensure_conversation(session, tenant_id)

        envelope = build_user_envelope(msg, self.kind)
        channel_ctx = build_channel_context(
            is_group=msg.is_group,
            sender_name=msg.sender_name,
            sender_number=msg.sender_number,
            chat_name=msg.chat_name,
            agent_instructions=self._agent_instructions(capsule),
            channel_kind=self.kind,
        )
        # BR-06: channel + contact context reaches the model. ChatTurn has no
        # system field, so the A0 system_context is prepended to the turn text
        # (same information the system_prompt extension would inject).
        composed = f"{channel_ctx}\n\n{envelope}"

        attachments = [
            {"path": u, "media_type": msg.media_type, "source": self.kind} for u in msg.media_urls
        ]

        # Typing indicator (A0 handler starts typing before communicate).
        async with self._typing_indicator(msg.chat_id or msg.sender_id):
            result = await self._run_turn(
                capsule=capsule,
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                composed=composed,
                attachments=attachments,
            )

        reply_text = (result.get("response") or "").strip()
        if not reply_text:
            reply_text = "(no response)"

        # Group replies auto-quote the triggering message (A0 handler).
        reply_to = msg.external_id if msg.is_group else ""
        idem_prefix = "tg" if self.kind == "telegram" else "wa"

        delivery = await self.sender.send_reply(
            session_id=str(getattr(session, "id", "") or "") or None,
            chat_id=msg.chat_id or msg.sender_id,
            text=reply_text,
            reply_to=reply_to,
            idempotency_key=f"{idem_prefix}:{self.channel_id}:{msg.external_id or inbound_id}",
        )

        if inbound_id:
            await self._mark_processed(inbound_id)

        # Persist assistant outbound mirror for audit (already queued by sender).
        return {
            "status": delivery.get("status", "sent"),
            "inbound_id": inbound_id,
            "conversation_id": conversation_id,
            "delivery": delivery,
            "errors": result.get("errors") or [],
        }

    async def _run_turn(
        self,
        *,
        capsule: Any,
        tenant_id: str,
        conversation_id: Optional[str],
        composed: str,
        attachments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        from admin.core.chat_orchestrator import ChatTurn, get_chat_orchestrator

        orch = await get_chat_orchestrator()
        turn = ChatTurn(
            capsule=capsule,
            user_id=f"bridge:{capsule.id}",
            tenant_id=tenant_id,
            user_message=composed,
            conversation_id=conversation_id,
            attachments=attachments,
            capsule_id=str(capsule.id),
        )
        result = await orch.process_turn(turn)
        return {
            "response": result.response,
            "model_used": result.model_used,
            "errors": list(result.errors or []),
            "turn_id": result.turn_id,
        }
