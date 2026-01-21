"""Message service for ChatService.

Extracted from chat_service.py per VIBE Rule 245 (650-line max).
Contains the core send_message logic.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import AsyncIterator, Optional, TYPE_CHECKING
from uuid import uuid4

from asgiref.sync import sync_to_async

from admin.core.somabrain_client import SomaBrainClient
from services.common.health_monitor import get_health_monitor
from services.common.model_router import (
    detect_required_capabilities,
    NoCapableModelError,
    select_model,
    SelectedModel,
)
from services.common.simple_context_builder import BuiltContext, create_context_builder
from services.common.simple_governor import get_governor, GovernorDecision
from services.common.unified_metrics import get_metrics, TurnPhase

if TYPE_CHECKING:
    import httpx

from services.common.chat.metrics import CHAT_LATENCY, CHAT_REQUESTS, CHAT_TOKENS

logger = logging.getLogger(__name__)

# Deployment mode detection
DEPLOYMENT_MODE = os.environ.get("SA01_DEPLOYMENT_MODE", "dev").upper()
SAAS_MODE = DEPLOYMENT_MODE == "SAAS"
STANDALONE_MODE = DEPLOYMENT_MODE == "STANDALONE"


class MessageService:
    """Service for message sending and LLM interaction.

    Extracted from ChatService to enforce 650-line limit.
    Contains the complete send_message flow.
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def send_message(
        self, conversation_id: str, agent_id: str, content: str, user_id: str
    ) -> AsyncIterator[str]:
        """Send message and stream response tokens from LLM provider.

        Production-simplified flow:
        1. Store user message
        2. Load conversation data and history
        3. Check health status
        4. Allocate budget via SimpleGovernor
        5. Build context via ContextBuilder
        6. Invoke LLM and stream tokens
        7. Store assistant message and record metrics
        """
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        from admin.chat.models import (
            Conversation as ConversationModel,
            Message as MessageModel,
        )
        from admin.llm.services.litellm_client import get_chat_model

        start_time = time.perf_counter()
        turn_id = str(uuid4())

        # 1. Initialize metrics
        metrics = get_metrics()
        turn_metrics = metrics.record_turn_start(
            turn_id=turn_id,
            tenant_id="",  # Will be loaded from DB
            user_id=user_id,
            agent_id=agent_id,
        )

        # 2. Store user message in SomaBrain + trace in PostgreSQL
        tenant_id = ""
        try:
            somabrain_client = await SomaBrainClient.get_async()

            # Get tenant_id first
            @sync_to_async
            def get_tenant():
                conv = ConversationModel.objects.filter(id=conversation_id).only("tenant_id").first()
                if not conv:
                    raise ValueError(f"Conversation {conversation_id} not found")
                return str(conv.tenant_id)

            tenant_id = await get_tenant()

            memory_result = await somabrain_client.remember(
                payload={
                    "role": "user",
                    "content": content,
                    "conversation_id": conversation_id,
                    "timestamp": time.time(),
                },
                tenant=tenant_id,
                namespace="chat_history",
            )
            user_coordinate = memory_result.get("coordinate", "")

            @sync_to_async
            def store_user_trace():
                try:
                    msg = MessageModel.objects.create(
                        conversation_id=conversation_id,
                        role="user",
                        coordinate=user_coordinate,
                        token_count=len(content.split()),
                    )
                    ConversationModel.objects.filter(id=conversation_id).update(
                        message_count=MessageModel.objects.filter(
                            conversation_id=conversation_id
                        ).count()
                    )
                    return str(msg.id)
                except Exception as e:
                    logger.error(f"Failed to store user message trace: {e}", exc_info=True)
                    raise

            await store_user_trace()
        except Exception as e:
            logger.error(f"Failed to store user message in SomaBrain: {e}", exc_info=True)
            raise
        turn_metrics.tokens_in = len(content.split())

        # 3. Recall message history from SomaBrain
        raw_history = await self._recall_history(
            conversation_id, tenant_id
        )

        turn_metrics.tenant_id = tenant_id
        metrics.record_turn_phase(turn_id, TurnPhase.AUTH_VALIDATED)

        # 4. Load Capsule for system_prompt and model constraints
        from admin.core.models import Capsule

        @sync_to_async
        def load_capsule():
            return Capsule.objects.filter(id=agent_id).first()

        capsule = await load_capsule()
        capsule_config = capsule.config if capsule and capsule.config else {}
        capsule_body = {
            "allowed_models": capsule_config.get("allowed_models", []),
        }

        system_prompt = capsule.system_prompt if capsule else ""
        if not system_prompt:
            logger.warning(
                f"No system_prompt in Capsule {agent_id} - agent may behave unexpectedly"
            )

        # 5. Detect required capabilities and select model
        required_caps = detect_required_capabilities(message=content, attachments=None)
        logger.info(f"Detected capabilities for turn: {required_caps}")

        llm = None
        selected_model: SelectedModel | None = None
        try:
            selected_model = await select_model(
                required_capabilities=required_caps,
                capsule_body=capsule_body,
                tenant_id=tenant_id,
            )
            logger.info(
                f"Model Router selected: {selected_model.provider}/{selected_model.name}"
            )

            llm = get_chat_model(
                provider=selected_model.provider,
                name=selected_model.name,
            )
        except NoCapableModelError as e:
            logger.error(f"No capable model found: {e}")
            raise ValueError(f"No LLM model available with capabilities: {required_caps}")
        except Exception as e:
            logger.error(f"Model selection failed: {e}", exc_info=True)
            raise

        # 6. Get health status and allocate budget
        health_monitor = get_health_monitor()
        overall_health = health_monitor.get_overall_health()
        is_degraded = overall_health.degraded

        metrics.record_turn_phase(turn_id, TurnPhase.HEALTH_CHECKED)

        from admin.core.helpers.settings_defaults import get_default_settings

        agent_settings = get_default_settings(agent_id=agent_id)
        governor = get_governor()
        max_total_tokens = int(agent_settings.chat_model_ctx_length)

        decision: GovernorDecision = governor.allocate_budget(
            max_tokens=max_total_tokens,
            is_degraded=is_degraded,
        )

        metrics.record_turn_phase(turn_id, TurnPhase.BUDGET_ALLOCATED)

        # 7. Build context via ContextBuilder
        built = await self._build_context(
            content, raw_history, system_prompt, tenant_id, decision, is_degraded
        )

        metrics.record_turn_phase(turn_id, TurnPhase.CONTEXT_BUILT)

        # 8. Invoke LLM
        lc_messages = []
        for msg in built.messages:
            role, content_val = msg.get("role"), msg.get("content")
            if role == "assistant":
                lc_messages.append(AIMessage(content=content_val or ""))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content_val or ""))
            else:
                lc_messages.append(HumanMessage(content=content_val or ""))

        metrics.record_turn_phase(turn_id, TurnPhase.LLM_INVOKED)

        # Stream response
        response_content = []
        try:
            async for chunk in llm._astream(messages=lc_messages):
                token = (
                    str(chunk.message.content)
                    if hasattr(chunk, "message") and hasattr(chunk.message, "content")
                    else ""
                )
                if token:
                    response_content.append(token)
                    yield token
        except asyncio.TimeoutError:
            logger.warning(f"LLM streaming timeout")
        except Exception as e:
            logger.error(f"LLM streaming error: {e}", exc_info=True)

        metrics.record_turn_phase(
            turn_id, TurnPhase.COMPLETED if response_content else TurnPhase.ERROR
        )

        full_response = "".join(response_content)
        token_count_out = len(full_response.split())

        # 9. Store assistant message in SomaBrain + PostgreSQL trace
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        model_id = f"{selected_model.provider}/{selected_model.name}"

        await self._store_assistant_message(
            conversation_id, tenant_id, full_response, model_id,
            elapsed_ms, token_count_out
        )

        # 10. Record completion metrics
        metrics.record_turn_complete(
            turn_id=turn_id,
            tokens_in=turn_metrics.tokens_in,
            tokens_out=token_count_out,
            model=model_id,
            provider=selected_model.provider,
            error=None,
        )

        # 11. Non-blocking: store interaction and RL signals
        await self._run_background_tasks(
            agent_id=agent_id,
            user_id=user_id,
            conversation_id=conversation_id,
            content=content,
            full_response=full_response,
            tenant_id=tenant_id,
            model_id=model_id,
            elapsed_ms=elapsed_ms,
            raw_history=raw_history,
            capsule=capsule,
            turn_metrics=turn_metrics,
            token_count_out=token_count_out,
            start_time=start_time,
            response_content=response_content,
        )

    async def _recall_history(
        self, conversation_id: str, tenant_id: str
    ) -> list[dict]:
        """Recall message history from SomaBrain."""
        from admin.chat.models import Message as MessageModel

        @sync_to_async
        def load_traces():
            qs = MessageModel.objects.filter(conversation_id=conversation_id).order_by(
                "-created_at"
            )[:20]
            return list(reversed(qs))

        raw_trace_objs = await load_traces()
        raw_history = []

        if raw_trace_objs:
            try:
                somabrain_client = await SomaBrainClient.get_async()
                for trace in raw_trace_objs:
                    if trace.coordinate:
                        memory_result = await somabrain_client.recall(
                            query=trace.coordinate,
                            top_k=1,
                            tenant=tenant_id,
                            namespace="chat_history",
                        )
                        memories = memory_result.get("memories", [])
                        if memories:
                            payload = memories[0].get("payload", {})
                            raw_history.append({
                                "role": payload.get("role", trace.role),
                                "content": payload.get("content", "")
                            })
            except Exception as e:
                logger.warning(f"Failed to recall message history: {e}")

        return raw_history

    async def _build_context(
        self,
        content: str,
        raw_history: list[dict],
        system_prompt: str,
        tenant_id: str,
        decision: GovernorDecision,
        is_degraded: bool,
    ) -> BuiltContext:
        """Build context for LLM invocation."""
        somabrain_client: SomaBrainClient | None = None
        try:
            somabrain_client = await SomaBrainClient.get_async()
        except Exception as e:
            logger.error(f"SomaBrainClient initialization failed: {e}", exc_info=True)

        def simple_token_counter(text: str) -> int:
            return len(text.split())

        if somabrain_client is None:
            return BuiltContext(
                system_prompt="You are SomaAgent01.",
                messages=[
                    {"role": "system", "content": "You are SomaAgent01."},
                    {"role": "user", "content": content},
                ],
                token_counts={"system": 50, "history": 0, "memory": 0, "user": len(content.split())},
                lane_actual={"system_policy": 50, "history": 0, "memory": 0, "tools": 0, "tool_results": 0, "buffer": 200},
            )

        builder = create_context_builder(
            somabrain=somabrain_client,
            token_counter=simple_token_counter,
        )

        turn_dict = {
            "tenant_id": tenant_id,
            "session_id": str(uuid4()),
            "user_message": content,
            "history": raw_history,
            "system_prompt": system_prompt,
        }

        try:
            return await builder.build_for_turn(
                turn=turn_dict,
                lane_budget=decision.lane_budget.to_dict(),
                is_degraded=is_degraded,
            )
        except Exception as e:
            logger.error(f"Context build failed: {e}", exc_info=True)
            fallback_system = system_prompt or "Assistant ready."
            return BuiltContext(
                system_prompt=fallback_system,
                messages=[
                    {"role": "system", "content": fallback_system},
                    {"role": "user", "content": content},
                ],
                token_counts={"system": len(fallback_system.split()), "history": 0, "memory": 0, "user": len(content.split())},
                lane_actual={"system_policy": len(fallback_system.split()), "history": 0, "memory": 0, "tools": 0, "tool_results": 0, "buffer": 200},
            )

    async def _store_assistant_message(
        self,
        conversation_id: str,
        tenant_id: str,
        full_response: str,
        model_id: str,
        elapsed_ms: int,
        token_count_out: int,
    ) -> None:
        """Store assistant message in SomaBrain and PostgreSQL."""
        from admin.chat.models import (
            Conversation as ConversationModel,
            Message as MessageModel,
        )

        try:
            somabrain_client = await SomaBrainClient.get_async()
            memory_result = await somabrain_client.remember(
                payload={
                    "role": "assistant",
                    "content": full_response,
                    "conversation_id": conversation_id,
                    "model": model_id,
                    "latency_ms": elapsed_ms,
                    "timestamp": time.time(),
                },
                tenant=tenant_id,
                namespace="chat_history",
            )
            assistant_coordinate = memory_result.get("coordinate", "")

            @sync_to_async
            def store_trace():
                MessageModel.objects.create(
                    conversation_id=conversation_id,
                    role="assistant",
                    coordinate=assistant_coordinate,
                    token_count=token_count_out,
                    latency_ms=elapsed_ms,
                    model=model_id,
                )
                ConversationModel.objects.filter(id=conversation_id).update(
                    message_count=MessageModel.objects.filter(
                        conversation_id=conversation_id
                    ).count()
                )

            await store_trace()
        except Exception as e:
            logger.error(f"Failed to store assistant message: {e}", exc_info=True)

    async def _run_background_tasks(
        self,
        agent_id: str,
        user_id: str,
        conversation_id: str,
        content: str,
        full_response: str,
        tenant_id: str,
        model_id: str,
        elapsed_ms: int,
        raw_history: list[dict],
        capsule,
        turn_metrics,
        token_count_out: int,
        start_time: float,
        response_content: list[str],
    ) -> None:
        """Run non-blocking background tasks."""
        from services.common.chat_memory import store_interaction
        from services.common.implicit_signals import signal_follow_up, signal_long_response

        asyncio.create_task(
            store_interaction(
                agent_id=agent_id,
                user_id=user_id,
                conversation_id=conversation_id,
                user_message=content,
                assistant_response=full_response,
                tenant_id=tenant_id,
                model=model_id,
                latency_ms=elapsed_ms,
            )
        )

        learning_config = capsule.learning_config if capsule else {}

        if len(raw_history) >= 2:
            last_role = raw_history[-1].get("role") if raw_history else None
            if last_role == "assistant":
                time_since_estimate = min(60 * 5, 30 * len(raw_history))
                asyncio.create_task(
                    signal_follow_up(
                        conversation_id, time_since_estimate, learning_config=learning_config
                    )
                )

        if len(content) > 200:
            asyncio.create_task(
                signal_long_response(conversation_id, len(content), learning_config=learning_config)
            )

        CHAT_TOKENS.labels(direction="input").inc(turn_metrics.tokens_in)
        CHAT_TOKENS.labels(direction="output").inc(token_count_out)
        CHAT_LATENCY.labels(method="send_message").observe(time.perf_counter() - start_time)
        CHAT_REQUESTS.labels(
            method="send_message", result="success" if response_content else "error"
        ).inc()


__all__ = ["MessageService"]
