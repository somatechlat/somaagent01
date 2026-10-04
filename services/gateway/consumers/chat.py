"""WebSocket Chat Consumer for real-time messaging."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs
from uuid import uuid4

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from admin.common.exceptions import UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)

def _require_tenant_id_value(tenant_id) -> str:
    """Memory/authz tenant. Missing denies — never "default"."""
    text = str(tenant_id).strip() if tenant_id is not None else ""
    if not text:
        raise PermissionError(
            "Missing tenant_id on an authorization/memory path. "
            "A request without a tenant is denied, never assigned to \"default\"."
        )
    return text


# =============================================================================
# UNIFIED METRICS
# =============================================================================
# VIBE: Use UnifiedMetrics singleton to avoid duplicate metric registration
# VIBE: Multiple services defining same metric names causes registry conflicts
from services.common.unified_metrics import UnifiedMetrics

# Initialize metrics singleton on module load
_metrics = UnifiedMetrics.get_instance()

# Metric shortcuts for backwards compatibility
WS_CONNECTIONS = _metrics.WEBSOCKET_CONNECTIONS
WS_MESSAGES = _metrics.WEBSOCKET_MESSAGES
WS_LATENCY = _metrics.WEBSOCKET_MESSAGE_LATENCY


# =============================================================================
# MESSAGE TYPES (Per Appendix B)
# =============================================================================


@dataclass
class WSMessage:
    """WebSocket message structure."""

    type: str
    payload: dict
    id: str = ""
    timestamp: str = ""

    def __post_init__(self):
        """Execute post init  ."""

        if not self.id:
            self.id = str(uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Execute to dict."""

        return {
            "type": self.type,
            "id": self.id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


# Message types
MSG_CHAT = "chat.message"
MSG_CHAT_SEND = "chat.send"
MSG_CHAT_LEGACY = "chat"
MSG_CHAT_RESPONSE = "chat.message"
MSG_CHAT_DELTA = "chat.delta"
MSG_CHAT_DONE = "chat.done"
MSG_TITLE_UPDATE = "title_update"
MSG_ERROR = "error"
MSG_PING = "ping"
MSG_PONG = "pong"
MSG_CONNECTED = "connected"
MSG_TYPING = "typing"
MSG_FEEDBACK = "feedback"

# Tool timeline (native function calling) — C1 / CH-11. Emitted while the
# orchestrator runs its model→tool→model loop so the UI can render a live
# tool-call timeline. C2 styles these.
MSG_TOOL_CALL = "tool.call"
MSG_TOOL_DELTA = "tool.delta"
MSG_TOOL_DONE = "tool.done"
MSG_TOOL_APPROVAL_REQUEST = "tool.approval_request"
MSG_TOOL_APPROVAL = "tool.approval"

# Chat control (C4 / CH-04) — pause, nudge, stop, reset the running turn.
MSG_CHAT_PAUSE = "chat.pause"
MSG_CHAT_RESUME = "chat.resume"
MSG_CHAT_NUDGE = "chat.nudge"
MSG_CHAT_STOP = "chat.stop"
MSG_CHAT_RESET = "chat.reset"

TOOL_MSG_TYPES = {
    MSG_TOOL_CALL,
    MSG_TOOL_DELTA,
    MSG_TOOL_DONE,
    MSG_TOOL_APPROVAL_REQUEST,
}

CONTROL_MSG_TYPES = {
    MSG_CHAT_PAUSE,
    MSG_CHAT_RESUME,
    MSG_CHAT_NUDGE,
    MSG_CHAT_STOP,
    MSG_CHAT_RESET,
    MSG_TOOL_APPROVAL,
}


# =============================================================================
# CHAT CONSUMER
# =============================================================================


# Stream coalescing. A WebSocket frame per token is the dominant cost of a
# stream turn: one JSON serialise + one frame + one metrics label lookup for
# every few characters. Tokens are buffered and flushed together either when
# the buffer is full or when this deadline expires - both far below the
# ~100ms human perception threshold, so nothing looks slower.
def _stream_setting(name: str, default):
    """Resolve one runtime knob through the real chain.

    Capsule -> AgentSetting -> SettingsModel -> schema default
    (``admin.core.helpers.settings.get_settings``). The declared value lives on
    ``SettingsModel``; the ``default`` here is only the last-resort fallback if
    a name is ever removed from the model.
    """
    from admin.core.helpers.settings import get_settings

    model = get_settings()
    value = getattr(model, name.lower(), None)
    return default if value is None else value




# Stream coalescing. A WebSocket frame per token is the dominant cost of a
# stream turn. Tokens are buffered and flushed together either when the buffer
# is full or when this deadline expires - both far below the ~100ms human
# perception threshold. Both values are settings, not literals.
_FLUSH_INTERVAL_S = float(_stream_setting("WS_STREAM_FLUSH_INTERVAL_S", 0.02))
_FLUSH_MAX_CHARS = int(_stream_setting("WS_STREAM_FLUSH_MAX_CHARS", 512))


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time chat.

    Per design.md Section 7.1:
    - JWT authentication from cookie
    - Message streaming from SomaBrain
    - Heartbeat every 30 seconds
    - Reconnection support
    """

    HEARTBEAT_INTERVAL = 30  # seconds
    MESSAGE_TIMEOUT = 30  # seconds

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""

        super().__init__(*args, **kwargs)
        self.user_id: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.agent_id: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.is_streaming: bool = False

        # Chat control state (C4)
        self._paused: bool = False
        self._stop_requested: bool = False
        self._nudge_queue: List[str] = []
        self._turn_task: Optional[asyncio.Task] = None
        self._tool_approvals: Dict[str, asyncio.Future] = {}
        # Roles the authenticated principal holds (TokenPayload.realm_access).
        self._roles: list | None = None

        # Phase 1-3: Pre-loaded at connection time (cached for entire session)
        self.capsule: Optional[Any] = None
        self.iq: Optional[Any] = None
        self.tool_registry: Optional[Any] = None
        self.perm_cache: Optional[bool] = None
        self._cached_history: List[Dict[str, str]] = []

    async def connect(self):
        """Handle WebSocket connection.

        Per design.md Section 7.1:
        - Validate JWT from cookie
        - Extract user context
        - Start heartbeat
        """
        try:
            # Extract agent_id from URL route
            url_route = self.scope.get("url_route") or {}
            self.agent_id = url_route.get("kwargs", {}).get("agent_id")

            # Determine subprotocol to accept (P3-04 backward compat)
            selected_subprotocol = None
            for proto in self.scope.get("subprotocols", []):
                if proto.startswith("soma-auth."):
                    selected_subprotocol = proto
                    break

            # Accept connection FIRST so we can send error messages gracefully
            await self.accept(subprotocol=selected_subprotocol)

            # Authenticate from cookie/query/header
            auth_result = await self._authenticate()
            if not auth_result:
                await self._send_error("Unauthorized", code="unauthorized")
                await self.close(code=4001)
                return

            # Phase 2: LOAD CAPSULE (ONCE)
            # Agent ID (from URL) → Agent → primary_capsule (different UUIDs)
            from admin.aaas.models import Agent as AgentModel
            from admin.core.models import Capsule

            if not self.agent_id:
                # No agent in URL: use user's first active agent
                agent = await sync_to_async(
                    lambda: AgentModel.objects.filter(tenant_id=self.tenant_id, status="active")
                    .select_related("primary_capsule")
                    .first(),
                    thread_sensitive=True,
                )()
                if agent:
                    self.agent_id = str(agent.id)
                    logger.info("Auto-resolved agent=%s for user=%s", self.agent_id, self.user_id)

            # Resolve capsule: try direct Capsule ID first, then Agent lookup
            self.capsule = await sync_to_async(
                lambda: Capsule.objects.filter(id=self.agent_id).first(),
                thread_sensitive=True,
            )()
            if not self.capsule:
                # agent_id is an Agent UUID, not Capsule — look up via Agent
                agent = await sync_to_async(
                    lambda: AgentModel.objects.filter(id=self.agent_id)
                    .select_related("primary_capsule")
                    .first(),
                    thread_sensitive=True,
                )()
                if agent and agent.primary_capsule:
                    capsule = agent.primary_capsule
                    self.capsule = capsule
                    logger.info("Resolved agent %s → capsule %s", self.agent_id, capsule.id)
            if not self.capsule:
                logger.warning("Capsule not found for agent: %s", self.agent_id)
                await self.close(code=4004)
                return

            # Phase 2.5: Pre-cache capsule body (avoids SynchronousOnlyOperation)
            if hasattr(self.capsule, "async_body"):
                self.capsule._cached_body = await self.capsule.async_body()
            else:
                self.capsule._cached_body = self.capsule.body or {}

            # Phase 3: DERIVE AGENT IQ (ONCE)
            from admin.core.agentiq import derive_all_settings

            self.iq = await sync_to_async(derive_all_settings)(self.capsule)
            logger.info(
                "WebSocket IQ derived: tier=%s, auto=%s",
                self.iq.model_tier,
                self.iq.tool_approval,
            )

            # Phase 4: BUILD PER-CAPSULE TOOL REGISTRY (ONCE)
            try:
                from services.tool_executor.tool_registry import ToolRegistry

                self.tool_registry = ToolRegistry()
                self.tool_registry.load_from_capsule(self.capsule)
                logger.info(
                    "WebSocket tool registry built: %d tools",
                    len(list(self.tool_registry.list())),
                )
            except Exception:
                # Tool stack must never block chat (optional deps).
                logger.exception("ToolRegistry load failed; continuing without tools")
                self.tool_registry = None

            # Phase 5: PERMISSION PRE-CHECK (ONCE, cached)
            from admin.core.agentiq import UnifiedGate

            gate = UnifiedGate()
            self.perm_cache = await gate.check(
                self.capsule,
                action="resource:chat_send",
                user_id=self.user_id,
                tenant_id=self.tenant_id,
            )
            if not self.perm_cache:
                logger.warning("Permission denied for capsule: %s", self.capsule.id)
                await self.close(code=4003)  # Permission denied
                return

            # Phase 6: SYNC NEUROMODULATORS WITH BRAIN
            try:
                from admin.core.somabrain_client import SomaBrainClient

                brain_client = await SomaBrainClient.get_async()
                if brain_client and self.capsule:
                    await brain_client.update_neuromodulators(
                        _require_tenant_id_value(self.tenant_id),
                        str(self.capsule.id),
                        self.capsule.neuromodulator_baseline or {},
                    )
                    logger.info("Neuromodulators synced to Brain for capsule %s", self.capsule.id)
            except Exception as neuro_exc:
                logger.debug("Neuromodulator sync skipped: %s", neuro_exc)

            # Track connection
            _metrics.WEBSOCKET_CONNECTIONS.labels(agent_id=self.agent_id or "unknown").inc()

            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            # Send connected message
            await self.send_json(
                WSMessage(
                    type=MSG_CONNECTED,
                    payload={
                        "user_id": self.user_id,
                        "agent_id": self.agent_id,
                        "session_id": self.session_id,
                        "iq_tier": self.iq.model_tier if self.iq else None,
                        "tools_available": (
                            len(list(self.tool_registry.list())) if self.tool_registry else 0
                        ),
                    },
                ).to_dict()
            )

            logger.info("WebSocket connected: user=%s, agent=%s", self.user_id, self.agent_id)

        except UnauthorizedError:
            logger.warning("WebSocket auth failed: unauthorized")
            await self.close(code=4001)
        except (TimeoutError, ValidationError):
            logger.exception("WebSocket connect error")
            await self._send_error("internal_error", code="internal_error")
            await self.close(code=4000)
        except Exception:
            logger.exception("WebSocket connect error: unexpected exception")
            await self._send_error("internal_error", code="internal_error")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Cancel heartbeat
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Pull adapted neuromodulator state from Brain
        if self.capsule:
            try:
                from asgiref.sync import sync_to_async

                from admin.core.somabrain_client import SomaBrainClient

                brain_client = await SomaBrainClient.get_async()
                if brain_client:
                    neuro_state = await brain_client.get_neuromodulators(
                        tenant_id=_require_tenant_id_value(self.tenant_id),
                        persona_id=str(self.capsule.id),
                    )
                    if neuro_state:
                        self.capsule.neuromodulator_state = {
                            **neuro_state,
                            "last_synced_at": datetime.now(timezone.utc).isoformat(),
                        }
                        await sync_to_async(self.capsule.save, thread_sensitive=True)(
                            update_fields=["neuromodulator_state"]
                        )
                        logger.info(
                            "Neuromodulators pulled from Brain and saved for capsule %s",
                            self.capsule.id,
                        )
            except Exception as neuro_exc:
                logger.debug("Neuromodulator pull on disconnect skipped: %s", neuro_exc)

        # Track disconnection
        _metrics.WEBSOCKET_CONNECTIONS.labels(agent_id=self.agent_id or "unknown").dec()

        logger.info("WebSocket disconnected: user=%s, code=%s", self.user_id, close_code)

    async def receive_json(self, content: dict, **kwargs):
        """Handle incoming WebSocket message.

        Per design.md Appendix B:
        - chat: User message
        - ping: Heartbeat request
        """
        start_time = time.perf_counter()
        msg_type = content.get("type", "unknown")

        _metrics.WEBSOCKET_MESSAGES.labels(direction="inbound", type=msg_type).inc()

        try:
            if msg_type == MSG_PING:
                await self._handle_ping(content)

            elif msg_type in {MSG_CHAT, MSG_CHAT_SEND, MSG_CHAT_LEGACY}:
                await self._handle_chat(content)

            elif msg_type == MSG_FEEDBACK:
                await self._handle_feedback(content)

            elif msg_type in CONTROL_MSG_TYPES:
                await self._handle_control(content)

            else:
                await self._send_error(f"Unknown message type: {msg_type}")

        except (TimeoutError, ValidationError):
            logger.exception("WebSocket message error")
            await self._send_error("internal_error", code="internal_error")
            await self.close(code=4000)
        except Exception:
            logger.exception("WebSocket message error: unexpected exception")
            await self._send_error("internal_error", code="internal_error")
            await self.close(code=4000)

        finally:
            elapsed = time.perf_counter() - start_time
            _metrics.WEBSOCKET_MESSAGE_LATENCY.labels(type=msg_type).observe(elapsed)

    # =========================================================================
    # AUTHENTICATION
    # =========================================================================

    async def _authenticate(self) -> bool:
        """Authenticate user from JWT subprotocol or cookie.

        Per design.md Section 7.1 & P3-04:
        - Extract JWT from Sec-WebSocket-Protocol subprotocol (preferred)
        - Fallback to query string, Authorization header, cookie
        - Validate token
        - Extract user context
        """
        from admin.common.auth import decode_token

        # Token sources: subprotocol (P3-04), query string, Authorization header, cookie
        token = None
        cookies = {}

        # 1. Subprotocol auth (P3-04 preferred)
        for proto in self.scope.get("subprotocols", []):
            if proto.startswith("soma-auth."):
                token = proto[len("soma-auth.") :]
                break

        # 2. Query string fallback
        if not token:
            query_string = self.scope.get("query_string", b"").decode("utf-8")
            if query_string:
                params = parse_qs(query_string)
                token_list = params.get("token")
                if token_list:
                    token = token_list[0]

        # 3. Authorization header fallback
        if not token:
            for header_name, header_value in self.scope.get("headers", []):
                if header_name == b"authorization":
                    auth_value = header_value.decode("utf-8")
                    if auth_value.lower().startswith("bearer "):
                        token = auth_value[7:].strip()
                        break

        # Parse cookies regardless (needed for session_id)
        for header_name, header_value in self.scope.get("headers", []):
            if header_name == b"cookie":
                cookie_str = header_value.decode("utf-8")
                for cookie in cookie_str.split(";"):
                    if "=" in cookie:
                        key, value = cookie.strip().split("=", 1)
                        cookies[key] = value
                break

        # 4. Cookie fallback
        if not token:
            token = cookies.get("access_token")

        if not token:
            logger.warning("WebSocket auth failed: No access token provided")
            return False

        try:
            # Decode and validate JWT
            payload = await decode_token(token)

            self.user_id = payload.sub
            realm = getattr(payload, "realm_access", None) or {}
            # None means "resolve the roles from the store"; an empty list means
            # "this subject holds nothing". A token with no realm roles is not a
            # subject with no roles — passing [] here denied every chat. Only a
            # token that actually names roles is trusted as the list (T-5: the
            # token names the principal, the store decides).
            claimed = list(realm.get("roles") or []) if isinstance(realm, dict) else []
            self._roles = claimed or None
            self.tenant_id = payload.tenant_id
            self.session_id = cookies.get("session_id")

            logger.debug("WebSocket authenticated: user=%s", self.user_id)
            return True

        except UnauthorizedError as e:
            logger.warning("WebSocket auth failed: %s", e)
            return False
        except Exception:
            logger.exception("WebSocket auth failed: unexpected exception")
            return False

    # =========================================================================
    # MESSAGE HANDLERS
    # =========================================================================

    async def _handle_ping(self, content: dict):
        """Handle ping message."""
        await self.send_json(
            WSMessage(
                type=MSG_PONG,
                payload={"timestamp": datetime.now(timezone.utc).isoformat()},
            ).to_dict()
        )
        _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_PONG).inc()

    class _ApprovalGate:
        """Resolve tool approvals over the WebSocket.

        One future per ``tool.approval_request``. The client answers with
        ``tool.approval``; a timeout or a missing answer is a refusal.
        """

        def __init__(self, owner: "ChatConsumer") -> None:
            self._owner = owner

        async def wait(self, tool_call_id: str, timeout_s: float) -> bool:
            loop = asyncio.get_running_loop()
            future: asyncio.Future = loop.create_future()
            self._owner._tool_approvals[tool_call_id] = future
            try:
                return bool(await asyncio.wait_for(future, timeout=timeout_s))
            except (asyncio.TimeoutError, asyncio.CancelledError):
                return False
            finally:
                self._owner._tool_approvals.pop(tool_call_id, None)

    async def _flush_deltas(
        self,
        tokens: list[str],
        conversation_id: str,
        response_id: str,
        index: int,
    ) -> None:
        """Send one coalesced chat.delta for a batch of tokens.

        One frame for many tokens, one metrics increment for many tokens.
        The UI appends ``delta`` to its running buffer exactly as it does for
        a single token, so the rendered output is identical.
        """
        if not tokens:
            return
        await self.send_json(
            WSMessage(
                type=MSG_CHAT_DELTA,
                payload={
                    "conversation_id": conversation_id,
                    "response_id": response_id,
                    "delta": "".join(tokens),
                    "index": index,
                },
            ).to_dict()
        )
        _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_CHAT_DELTA).inc()

    async def _handle_chat(self, content: dict):
        """Handle chat message.

        Per design.md Section 7.1:
        - Validate conversation
        - Send to SomaBrain
        - Stream response tokens
        """
        payload = content.get("payload") or content.get("data") or {}
        message_content = payload.get("content", "")
        agent_mode = str(payload.get("mode") or "STD").upper()
        conversation_id = (
            payload.get("conversation_id") or payload.get("session_id") or self.conversation_id
        )

        if not message_content:
            await self._send_error("Message content is required")
            return

        if not conversation_id:
            await self._send_error("Conversation ID is required")
            return

        self.conversation_id = conversation_id
        self.is_streaming = True

        try:
            # Send typing indicator
            await self.send_json(
                WSMessage(
                    type=MSG_TYPING,
                    payload={"conversation_id": conversation_id},
                ).to_dict()
            )

            # Get V3 Chat Orchestrator and stream response
            from admin.core.chat_orchestrator import (
                ChatTurn,
                get_chat_orchestrator,
                ToolStreamEvent,
            )

            orchestrator = await get_chat_orchestrator()

            # Resolve conversation + agent
            conversation = await orchestrator.get_conversation(
                conversation_id=conversation_id,
                user_id=self.user_id or "",
            )

            if not conversation:
                await self._send_error("Conversation not found")
                return

            if self.tenant_id and conversation.tenant_id != self.tenant_id:
                await self._send_error("Conversation access denied")
                return

            self.agent_id = conversation.agent_id

            # Stream tokens via V3 orchestrator
            response_id = str(uuid4())
            token_count = 0
            response_content: list[str] = []
            pending: list[str] = []
            last_flush = 0.0
            loop = asyncio.get_running_loop()

            # Attachments ride on the turn so detect_required_capabilities can
            # see vision/audio/document instead of always concluding {"text"}.
            # The composer sends {name, type, size}; the seam reads content_type.
            raw_attachments = payload.get("attachments") or []
            attachments = [
                {
                    **a,
                    "content_type": a.get("content_type") or a.get("type") or "",
                }
                for a in raw_attachments
                if isinstance(a, dict)
            ]

            turn = ChatTurn(
                capsule=self.capsule,
                iq_settings=self.iq,
                tool_registry=self.tool_registry,
                user_id=self.user_id or "",
                tenant_id=_require_tenant_id_value(self.tenant_id),
                user_message=message_content,
                conversation_id=conversation_id,
                attachments=attachments,
                history=self._cached_history,
                agent_mode=agent_mode,
                roles=self._roles,
                approval_gate=ChatConsumer._ApprovalGate(self),
            )

            async for item in orchestrator.stream_turn(turn):
                if self._stop_requested:
                    break

                # Pause gate (C4): hold token emission without dropping the
                # turn; resume flushes the backlog naturally.
                while self._paused and not self._stop_requested:
                    await asyncio.sleep(0.05)

                if isinstance(item, ToolStreamEvent):
                    # Tool timeline (tool.call / tool.delta / tool.done /
                    # tool.approval_request) — forward so the UI can render
                    # the live tool-call timeline (CH-11).
                    await self.send_json(
                        WSMessage(
                            type=item.type,
                            payload={
                                "conversation_id": conversation_id,
                                "response_id": response_id,
                                **item.payload,
                            },
                        ).to_dict()
                    )
                    _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=item.type).inc()
                    continue

                token_count += 1
                response_content.append(item)
                pending.append(item)

                now = loop.time()
                if (
                    sum(len(x) for x in pending) >= _FLUSH_MAX_CHARS
                    or now - last_flush >= _FLUSH_INTERVAL_S
                ):
                    await self._flush_deltas(
                        pending, conversation_id, response_id, token_count
                    )
                    pending = []
                    last_flush = now

            if pending:
                await self._flush_deltas(
                    pending, conversation_id, response_id, token_count
                )
                pending = []

            # Done is metadata only. The UI already accumulated the streamed
            # body (saas-chat.ts keeps _streamContent and falls back to it with
            # `chunk.content ?? this._streamContent`), so re-sending the whole
            # response here would double the bytes of every turn for nothing.
            await self.send_json(
                WSMessage(
                    type=MSG_CHAT_DONE,
                    payload={
                        "conversation_id": conversation_id,
                        "response_id": response_id,
                        "token_count": token_count,
                    },
                ).to_dict()
            )
            _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_CHAT_DONE).inc()

        except asyncio.TimeoutError:
            await self._send_error("Response timeout", code="timeout")

        except (UnauthorizedError, ValidationError):
            logger.exception("Chat message error")
            await self._send_error("internal_error", code="internal_error")
            await self.close(code=4000)
        except Exception:
            logger.exception("Chat message error: unexpected exception")
            await self._send_error("internal_error", code="internal_error")
            await self.close(code=4000)

        finally:
            self.is_streaming = False

    async def _handle_control(self, content: dict):
        """Handle chat control + tool approval (C4 / C2).

        - ``chat.pause`` / ``chat.resume`` — freeze or unfreeze token emission
        - ``chat.nudge`` — inject a user nudge into the running turn (if any)
        - ``chat.stop`` — cancel the running turn (fail-closed: no-op if idle)
        - ``chat.reset`` — clear local conversation stream state
        - ``tool.approval`` — resolve a pending tool approval future
        """
        msg_type = content.get("type", "")
        payload = content.get("payload") or content.get("data") or {}

        if msg_type == MSG_CHAT_PAUSE:
            self._paused = True
            await self.send_json(WSMessage(type="chat.paused", payload={"paused": True}).to_dict())
            return

        if msg_type == MSG_CHAT_RESUME:
            self._paused = False
            await self.send_json(WSMessage(type="chat.paused", payload={"paused": False}).to_dict())
            return

        if msg_type == MSG_CHAT_NUDGE:
            nudge_text = payload.get("content") or payload.get("text") or "Please continue."
            if self.is_streaming:
                self._nudge_queue.append(nudge_text)
                await self.send_json(
                    WSMessage(type="chat.nudged", payload={"queued": True}).to_dict()
                )
            else:
                await self._send_error("No running turn to nudge", code="not_streaming")
            return

        if msg_type == MSG_CHAT_STOP:
            if self._turn_task and not self._turn_task.done():
                self._turn_task.cancel()
                self._stop_requested = True
            self._paused = False
            await self.send_json(
                WSMessage(type="chat.stopped", payload={"stopped": True}).to_dict()
            )
            return

        if msg_type == MSG_CHAT_RESET:
            self._paused = False
            self._stop_requested = False
            self._nudge_queue.clear()
            if self._turn_task and not self._turn_task.done():
                self._turn_task.cancel()
            await self.send_json(WSMessage(type="chat.reset", payload={"ok": True}).to_dict())
            return

        if msg_type == MSG_TOOL_APPROVAL:
            tool_call_id = payload.get("tool_call_id") or payload.get("toolCallId") or ""
            approved = bool(payload.get("approved"))
            future = self._tool_approvals.pop(tool_call_id, None)
            if future is not None and not future.done():
                future.set_result(approved)
            await self.send_json(
                WSMessage(
                    type="tool.approval_resolved",
                    payload={"tool_call_id": tool_call_id, "approved": approved},
                ).to_dict()
            )
            return

        await self._send_error(f"Unhandled control type: {msg_type}")

    async def _handle_feedback(self, content: dict):
        """Handle user feedback (thumbs up/down).

        Publishes reward signal to SomaBrain for online learning.
        """
        payload = content.get("payload") or content.get("data") or {}
        signal = payload.get("signal", "neutral")  # "positive", "negative", "neutral"
        response_id = payload.get("response_id", "")

        if not self.capsule:
            return

        try:
            from admin.core.somabrain_client import SomaBrainClient

            brain_client = await SomaBrainClient.get_async()
            if brain_client:
                await brain_client.publish_reward(
                    self.session_id or "",
                    "reward" if signal == "positive" else "punish",
                    1.0 if signal == "positive" else -1.0,
                    {
                        "tenant_id": _require_tenant_id_value(self.tenant_id),
                        "persona_id": str(self.capsule.id),
                        "response_id": response_id,
                        "original_signal": signal,
                    },
                )
                logger.info(
                    "Feedback published to Brain: signal=%s, capsule=%s",
                    signal,
                    self.capsule.id,
                )
        except Exception as exc:
            logger.debug("Feedback publish skipped: %s", exc)

    # =========================================================================
    # HELPERS
    # =========================================================================

    async def _send_error(self, message: str, code: str = "error"):
        """Send error message."""
        await self.send_json(
            WSMessage(
                type=MSG_ERROR,
                payload={
                    "code": code,
                    "message": message,
                },
            ).to_dict()
        )
        _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_ERROR).inc()

    async def _heartbeat_loop(self):
        """Send periodic heartbeat pings.

        Per design.md Section 7.1:
        - Ping every 30 seconds
        - Detect stale connections
        """
        while True:
            try:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)

                # Don't send ping during streaming
                if not self.is_streaming:
                    await self.send_json(
                        WSMessage(
                            type=MSG_PING,
                            payload={"timestamp": datetime.now(timezone.utc).isoformat()},
                        ).to_dict()
                    )
                    _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_PING).inc()

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Heartbeat error")
                break
