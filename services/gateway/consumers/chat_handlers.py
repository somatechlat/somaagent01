"""Inbound message handlers for the WebSocket chat consumer."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from asgiref.sync import sync_to_async

from admin.common.exceptions import UnauthorizedError, ValidationError
from admin.core.chat_orchestrator import ChatTurn, get_chat_orchestrator
from admin.core.somabrain_client import SomaBrainClient
from services.gateway.consumers.chat_utils import (
    MSG_CHAT,
    MSG_CHAT_DELTA,
    MSG_CHAT_DONE,
    MSG_CHAT_LEGACY,
    MSG_CHAT_SEND,
    MSG_FEEDBACK,
    MSG_PING,
    MSG_PONG,
    MSG_TITLE_UPDATE,
    MSG_TYPING,
    WSMessage,
    _metrics,
)

logger = logging.getLogger(__name__)


class ChatHandlersMixin:
    """Message handling mixin for ChatConsumer."""

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
        from admin.chat.models import Conversation, Message
        from services.common.chat_schemas import Message as MessageDC

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
