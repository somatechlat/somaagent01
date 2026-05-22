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


# =============================================================================
# CHAT CONSUMER
# =============================================================================


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

        # Phase 1-3: Pre-loaded at connection time (cached for entire session)
        self.capsule: Optional[Any] = None
        self.iq: Optional[Any] = None
        self.tool_registry: Optional[Any] = None
        self.perm_cache: Optional[bool] = None
        self._cached_history: List[Dict[str, str]] = []
        self._cached_memory: List[Dict[str, Any]] = []
        self._context_preload_task: Optional[asyncio.Task] = None

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

            # Authenticate from cookie
            auth_result = await self._authenticate()
            if not auth_result:
                await self.close(code=4001)  # Unauthorized
                return

            # Phase 2: LOAD CAPSULE (ONCE)
            from admin.core.models import Capsule

            self.capsule = await sync_to_async(
                lambda: Capsule.objects.filter(id=self.agent_id).first(),
                thread_sensitive=True,
            )()
            if not self.capsule:
                logger.warning("Capsule not found: %s", self.agent_id)
                await self.close(code=4004)  # Capsule not found
                return

            # Phase 3: DERIVE AGENT IQ (ONCE)
            from admin.core.agentiq import derive_all_settings

            self.iq = derive_all_settings(self.capsule)
            logger.info(
                "WebSocket IQ derived: tier=%s, auto=%s",
                self.iq.model_tier,
                self.iq.tool_approval,
            )

            # Phase 4: BUILD PER-CAPSULE TOOL REGISTRY (ONCE)
            from services.tool_executor.tool_registry import ToolRegistry

            self.tool_registry = ToolRegistry()
            self.tool_registry.load_from_capsule(self.capsule)
            logger.info(
                "WebSocket tool registry built: %d tools",
                len(list(self.tool_registry.list())),
            )

            # Phase 5: PERMISSION PRE-CHECK (ONCE, cached)
            from admin.core.agentiq import UnifiedGate

            gate = UnifiedGate()
            self.perm_cache = await gate.check(self.capsule, action="chat:send")
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
                        self.tenant_id or "default",
                        str(self.capsule.id),
                        self.capsule.neuromodulator_baseline or {},
                    )
                    logger.info("Neuromodulators synced to Brain for capsule %s", self.capsule.id)
            except Exception as neuro_exc:
                logger.debug("Neuromodulator sync skipped: %s", neuro_exc)

            # Phase 7: PRE-WARM CONTEXT (background, non-blocking)
            self._context_preload_task = asyncio.create_task(
                self._preload_context()
            )

            # Accept connection
            await self.accept()

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
                        "tools_available": len(list(self.tool_registry.list())) if self.tool_registry else 0,
                    },
                ).to_dict()
            )

            logger.info(f"WebSocket connected: user={self.user_id}, agent={self.agent_id}")

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
                from admin.core.somabrain_client import SomaBrainClient
                from asgiref.sync import sync_to_async

                brain_client = await SomaBrainClient.get_async()
                if brain_client:
                    neuro_state = await brain_client.get_neuromodulators(
                        tenant_id=self.tenant_id or "default",
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

        logger.info(f"WebSocket disconnected: user={self.user_id}, code={close_code}")

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
        """Authenticate user from JWT cookie.

        Per design.md Section 7.1:
        - Extract JWT from cookie
        - Validate token
        - Extract user context
        """
        from admin.common.auth import decode_token

        # Token sources: query string, Authorization header, cookie
        token = None
        cookies = {}

        query_string = self.scope.get("query_string", b"").decode("utf-8")
        if query_string:
            params = parse_qs(query_string)
            token_list = params.get("token")
            if token_list:
                token = token_list[0]

        if not token:
            for header_name, header_value in self.scope.get("headers", []):
                if header_name == b"authorization":
                    auth_value = header_value.decode("utf-8")
                    if auth_value.lower().startswith("bearer "):
                        token = auth_value[7:].strip()
                        break

        for header_name, header_value in self.scope.get("headers", []):
            if header_name == b"cookie":
                cookie_str = header_value.decode("utf-8")
                for cookie in cookie_str.split(";"):
                    if "=" in cookie:
                        key, value = cookie.strip().split("=", 1)
                        cookies[key] = value
                break

        if not token:
            token = cookies.get("access_token")

        if not token:
            logger.warning("WebSocket auth failed: No access token provided")
            return False

        try:
            # Decode and validate JWT
            payload = await decode_token(token)

            self.user_id = payload.sub
            self.tenant_id = payload.tenant_id
            self.session_id = cookies.get("session_id")

            logger.debug(f"WebSocket authenticated: user={self.user_id}")
            return True

        except UnauthorizedError as e:
            logger.warning(f"WebSocket auth failed: {e}")
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

    async def _handle_chat(self, content: dict):
        """Handle chat message.

        Per design.md Section 7.1:
        - Validate conversation
        - Send to SomaBrain
        - Stream response tokens
        """
        payload = content.get("payload") or content.get("data") or {}
        message_content = payload.get("content", "")
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
            from admin.core.chat_orchestrator import ChatTurn, get_chat_orchestrator

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

            turn = ChatTurn(
                capsule=self.capsule,
                iq_settings=self.iq,
                tool_registry=self.tool_registry,
                user_id=self.user_id or "",
                tenant_id=self.tenant_id or "",
                user_message=message_content,
                conversation_id=conversation_id,
                history=self._cached_history,
                capsule_id=self.agent_id,
            )

            async for token in orchestrator.stream_turn(turn):
                token_count += 1
                response_content.append(token)

                # Send delta
                await self.send_json(
                    WSMessage(
                        type=MSG_CHAT_DELTA,
                        payload={
                            "conversation_id": conversation_id,
                            "response_id": response_id,
                            "delta": token,
                            "index": token_count,
                        },
                    ).to_dict()
                )
                _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_CHAT_DELTA).inc()

            # Send done
            full_response = "".join(response_content)
            await self.send_json(
                WSMessage(
                    type=MSG_CHAT_DONE,
                    payload={
                        "conversation_id": conversation_id,
                        "response_id": response_id,
                        "token_count": token_count,
                        "content": full_response,
                    },
                ).to_dict()
            )
            _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_CHAT_DONE).inc()

            # Generate title if first message
            await self._maybe_generate_title(conversation_id, orchestrator)

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
                        "tenant_id": self.tenant_id or "default",
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

    async def _maybe_generate_title(self, conversation_id: str, chat_service):
        """Generate title after first message exchange.

        Per design.md Section 7.3:
        - Call utility model after first message
        - Update conversation title
        - Send title_update message
        """
        from asgiref.sync import sync_to_async

        from admin.chat.models import Conversation, Message

        @sync_to_async
        def get_conversation_data():
            """Retrieve conversation data."""

            try:
                conv = Conversation.objects.get(id=conversation_id)
                if conv.title:
                    return None, None  # Already has title

                messages = list(
                    Message.objects.filter(conversation_id=conversation_id).order_by("created_at")[
                        :5
                    ]
                )
                return conv, messages
            except Conversation.DoesNotExist:
                return None, None

        conv, messages = await get_conversation_data()

        if conv is None or not messages:
            return

        try:
            from services.common.chat_schemas import Message as MessageDC

            message_dcs = [
                MessageDC(
                    id=str(m.id),
                    conversation_id=str(m.conversation_id),
                    role=m.role,
                    content=m.content,
                    token_count=m.token_count,
                    model=m.model,
                    latency_ms=m.latency_ms,
                    created_at=m.created_at,
                )
                for m in messages
            ]

            title = await chat_service.generate_title(conversation_id, message_dcs)

            # Send title update
            await self.send_json(
                WSMessage(
                    type=MSG_TITLE_UPDATE,
                    payload={
                        "conversation_id": conversation_id,
                        "title": title,
                    },
                ).to_dict()
            )
            _metrics.WEBSOCKET_MESSAGES.labels(direction="outbound", type=MSG_TITLE_UPDATE).inc()

        except Exception:
            logger.exception("Title generation failed")

    # =========================================================================
    # HELPERS
    # =========================================================================

    async def _preload_context(self):
        """Pre-warm context in background while user is typing.

        Fetches conversation history and relevant memories so they are
        ready when the first message arrives.
        """
        try:
            if not self.conversation_id:
                return

            # Fetch last 20 messages from PostgreSQL
            from admin.chat.models import Message as MessageModel
            from asgiref.sync import sync_to_async

            @sync_to_async
            def _load_history():
                qs = MessageModel.objects.filter(
                    conversation_id=self.conversation_id
                ).order_by("-created_at")[:20]
                return [
                    {"role": m.role, "content": getattr(m, "content", None) or ""}
                    for m in reversed(list(qs))
                ]

            self._cached_history = await _load_history()

            # Fetch memories from SomaBrain (best effort)
            if self.capsule:
                from admin.core.somabrain_client import SomaBrainClient

                brain_client = await SomaBrainClient.get_async()
                if brain_client:
                    try:
                        mp = self.capsule.memory_pointer or {}
                        memories = await brain_client.recall(
                            query="",
                            top_k=mp.get("recall_limit", 10),
                            tenant=mp.get("tenant", self.tenant_id or "default"),
                            namespace=mp.get("namespace", "chat_history"),
                        )
                        self._cached_memory = memories or []
                    except Exception as exc:
                        logger.debug("Pre-warm memory recall failed: %s", exc)
        except Exception as exc:
            logger.debug("Context pre-warm failed: %s", exc)

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
