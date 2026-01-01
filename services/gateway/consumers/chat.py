"""WebSocket Chat Consumer for real-time messaging.

VIBE COMPLIANT - Real Django Channels implementation, no mocks.
Per login-to-chat-journey design.md Section 7.1

Implements:
- Connection authentication (JWT from cookie)
- Message handling per WebSocket protocol spec (Appendix B)
- Heartbeat (ping/pong every 30 seconds)
- Streaming response from SomaBrain

Personas:
- Django Architect: Django Channels async consumer
- Security Auditor: JWT validation, tenant isolation
- Performance Engineer: Streaming, connection management
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qs
from uuid import uuid4

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

WS_CONNECTIONS = Gauge(
    "websocket_connections_active",
    "Active WebSocket connections",
    ["agent_id"],
)

WS_MESSAGES = Counter(
    "websocket_messages_total",
    "Total WebSocket messages",
    ["direction", "type"],
)

WS_LATENCY = Histogram(
    "websocket_message_latency_seconds",
    "WebSocket message processing latency",
    ["type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)


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
        if not self.id:
            self.id = str(uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
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
        super().__init__(*args, **kwargs)
        self.user_id: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.agent_id: Optional[str] = None
        self.conversation_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.is_streaming: bool = False

    async def connect(self):
        """Handle WebSocket connection.

        Per design.md Section 7.1:
        - Validate JWT from cookie
        - Extract user context
        - Start heartbeat
        """
        try:
            # Extract agent_id from URL route
            self.agent_id = self.scope["url_route"]["kwargs"].get("agent_id")

            # Authenticate from cookie
            auth_result = await self._authenticate()
            if not auth_result:
                await self.close(code=4001)  # Unauthorized
                return

            # Accept connection
            await self.accept()

            # Track connection
            WS_CONNECTIONS.labels(agent_id=self.agent_id or "unknown").inc()

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
                    },
                ).to_dict()
            )

            logger.info(
                f"WebSocket connected: user={self.user_id}, agent={self.agent_id}"
            )

        except Exception as e:
            logger.error(f"WebSocket connect error: {e}")
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

        # Track disconnection
        WS_CONNECTIONS.labels(agent_id=self.agent_id or "unknown").dec()

        logger.info(
            f"WebSocket disconnected: user={self.user_id}, code={close_code}"
        )

    async def receive_json(self, content: dict, **kwargs):
        """Handle incoming WebSocket message.

        Per design.md Appendix B:
        - chat: User message
        - ping: Heartbeat request
        """
        start_time = time.perf_counter()
        msg_type = content.get("type", "unknown")

        WS_MESSAGES.labels(direction="inbound", type=msg_type).inc()

        try:
            if msg_type == MSG_PING:
                await self._handle_ping(content)

            elif msg_type in {MSG_CHAT, MSG_CHAT_SEND, MSG_CHAT_LEGACY}:
                await self._handle_chat(content)

            else:
                await self._send_error(f"Unknown message type: {msg_type}")

        except Exception as e:
            logger.error(f"WebSocket message error: {e}")
            await self._send_error(str(e))

        finally:
            elapsed = time.perf_counter() - start_time
            WS_LATENCY.labels(type=msg_type).observe(elapsed)

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

        except Exception as e:
            logger.warning(f"WebSocket auth failed: {e}")
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
        WS_MESSAGES.labels(direction="outbound", type=MSG_PONG).inc()

    async def _handle_chat(self, content: dict):
        """Handle chat message.

        Per design.md Section 7.1:
        - Validate conversation
        - Send to SomaBrain
        - Stream response tokens
        """
        payload = content.get("payload") or content.get("data") or {}
        message_content = payload.get("content", "")
        conversation_id = payload.get("conversation_id") or payload.get("session_id") or self.conversation_id

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

            # Get ChatService and stream response
            from services.common.chat_service import get_chat_service

            chat_service = await get_chat_service()

            # Resolve conversation + agent
            conversation = await chat_service.get_conversation(
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

            # Stream tokens
            response_id = str(uuid4())
            token_count = 0
            response_content: list[str] = []

            async for token in chat_service.send_message(
                conversation_id=conversation_id,
                agent_id=self.agent_id,
                content=message_content,
                user_id=self.user_id or "",
            ):
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
                WS_MESSAGES.labels(direction="outbound", type=MSG_CHAT_DELTA).inc()

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
            WS_MESSAGES.labels(direction="outbound", type=MSG_CHAT_DONE).inc()

            # Generate title if first message
            await self._maybe_generate_title(conversation_id, chat_service)

        except asyncio.TimeoutError:
            await self._send_error("Response timeout", code="timeout")

        except Exception as e:
            logger.error(f"Chat message error: {e}")
            await self._send_error(str(e))

        finally:
            self.is_streaming = False

    async def _maybe_generate_title(self, conversation_id: str, chat_service):
        """Generate title after first message exchange.

        Per design.md Section 7.3:
        - Call utility model after first message
        - Update conversation title
        - Send title_update message
        """
        from admin.chat.models import Conversation, Message

        from asgiref.sync import sync_to_async

        @sync_to_async
        def get_conversation_data():
            try:
                conv = Conversation.objects.get(id=conversation_id)
                if conv.title:
                    return None, None  # Already has title

                messages = list(
                    Message.objects.filter(conversation_id=conversation_id)
                    .order_by("created_at")[:5]
                )
                return conv, messages
            except Conversation.DoesNotExist:
                return None, None

        conv, messages = await get_conversation_data()

        if conv is None or not messages:
            return

        try:
            # Convert to dataclass format
            from services.common.chat_service import Message as MessageDC

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
            WS_MESSAGES.labels(direction="outbound", type=MSG_TITLE_UPDATE).inc()

        except Exception as e:
            logger.warning(f"Title generation failed: {e}")

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
        WS_MESSAGES.labels(direction="outbound", type=MSG_ERROR).inc()

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
                    WS_MESSAGES.labels(direction="outbound", type=MSG_PING).inc()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Heartbeat error: {e}")
                break
