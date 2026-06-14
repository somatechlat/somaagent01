"""WebSocket Chat Consumer for real-time messaging."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from admin.common.exceptions import UnauthorizedError, ValidationError
from admin.core.somabrain_client import SomaBrainClient
from services.gateway.consumers.chat_auth import ChatAuthMixin
from services.gateway.consumers.chat_handlers import ChatHandlersMixin
from services.gateway.consumers.chat_utils import (
    MSG_CHAT,
    MSG_CHAT_LEGACY,
    MSG_CHAT_SEND,
    MSG_CONNECTED,
    MSG_ERROR,
    MSG_FEEDBACK,
    MSG_PING,
    ChatUtilsMixin,
    WSMessage,
    _metrics,
)

logger = logging.getLogger(__name__)


class ChatConsumer(ChatAuthMixin, ChatHandlersMixin, ChatUtilsMixin, AsyncJsonWebsocketConsumer):
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
            self.perm_cache = await gate.check(
                self.capsule,
                action="chat:send",
                user_id=self.user_id,
                tenant_id=self.tenant_id,
            )
            if not self.perm_cache:
                logger.warning("Permission denied for capsule: %s", self.capsule.id)
                await self.close(code=4003)  # Permission denied
                return

            # Phase 6: SYNC NEUROMODULATORS WITH BRAIN
            try:
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

            # Determine subprotocol to accept (P3-04 backward compat)
            selected_subprotocol = None
            for proto in self.scope.get("subprotocols", []):
                if proto.startswith("soma-auth."):
                    selected_subprotocol = proto
                    break

            # Accept connection with subprotocol if client requested it
            await self.accept(subprotocol=selected_subprotocol)

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

            logger.info('WebSocket connected: user=%s, agent=%s', self.user_id, self.agent_id)

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

        logger.info('WebSocket disconnected: user=%s, code=%s', self.user_id, close_code)

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
