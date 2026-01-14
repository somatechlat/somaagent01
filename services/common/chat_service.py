"""ChatService for LLM + memory integration and conversation management.

Production-simplified architecture using unified layers:
- unified_metrics.py: Single source of truth for observability
- simple_governor.py: Binary healthy/degraded budget allocation
- health_monitor.py: Simple health status tracking
- simple_context_builder.py: Efficient context assembly (150 lines)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import AsyncIterator, Optional
from uuid import uuid4

import httpx
from asgiref.sync import sync_to_async
from prometheus_client import Counter, Histogram

from admin.core.somabrain_client import SomaBrainClient
from services.common.chat_schemas import AgentSession, Conversation, Memory, Message
from services.common.health_monitor import get_health_monitor
from services.common.simple_context_builder import BuiltContext, create_context_builder
from services.common.simple_governor import get_governor, GovernorDecision
from services.common.unified_metrics import get_metrics, TurnPhase
from services.common.unified_secret_manager import get_secret_manager

logger = logging.getLogger(__name__)

# Deployment mode detection - consistent with simple_context_builder.py
DEPLOYMENT_MODE = os.environ.get("SA01_DEPLOYMENT_MODE", "dev").upper()
SAAS_MODE = DEPLOYMENT_MODE == "SAAS"
STANDALONE_MODE = DEPLOYMENT_MODE == "STANDALONE"

logger.info(
    f"ChatService deployment mode: {DEPLOYMENT_MODE}",
    extra={"deployment_mode": DEPLOYMENT_MODE}
)

# Prometheus Metrics
CHAT_REQUESTS = Counter(
    "chat_service_requests_total", "Total ChatService requests", ["method", "result"]
)
CHAT_LATENCY = Histogram(
    "chat_service_duration_seconds",
    "ChatService request latency",
    ["method"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)
CHAT_TOKENS = Counter("chat_tokens_total", "Total tokens processed", ["direction"])


class ChatService:
    """Service for chat operations with SomaBrain integration.

    Simplified architecture - production-grade, minimal complexity.
    """

    def __init__(
        self,
        somabrain_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize ChatService.

        Memory operations use SomaBrainClient directly (no direct SFM access).
        """
        from django.conf import settings

        self.somabrain_url = somabrain_url or getattr(settings, "SOMABRAIN_URL", "http://localhost:9696")
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()

    # =========================================================================
    # CONVERSATION MANAGEMENT
    # =========================================================================

    async def create_conversation(
        self, agent_id: str, user_id: str, tenant_id: str
    ) -> Conversation:
        """Create new conversation record in PostgreSQL."""
        from admin.chat.models import Conversation as ConversationModel

        start_time = time.perf_counter()
        try:

            @sync_to_async
            def create_in_db():
                return ConversationModel.objects.create(
                    agent_id=agent_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    status="active",
                    message_count=0,
                )

            db_conv = await create_in_db()
            conversation = Conversation(
                id=str(db_conv.id),
                agent_id=str(db_conv.agent_id),
                user_id=str(db_conv.user_id),
                tenant_id=str(db_conv.tenant_id),
                title=db_conv.title,
                status=db_conv.status,
                message_count=db_conv.message_count,
                created_at=db_conv.created_at,
                updated_at=db_conv.updated_at,
            )
            CHAT_LATENCY.labels(method="create_conversation").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="create_conversation", result="success").inc()
            return conversation
        except Exception as e:
            CHAT_LATENCY.labels(method="create_conversation").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="create_conversation", result="error").inc()
            raise

    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def get_from_db():
            try:
                return ConversationModel.objects.get(id=conversation_id, user_id=user_id)
            except ConversationModel.DoesNotExist:
                return None

        db_conv = await get_from_db()
        if db_conv is None:
            return None
        return Conversation(
            id=str(db_conv.id),
            agent_id=str(db_conv.agent_id),
            user_id=str(db_conv.user_id),
            tenant_id=str(db_conv.tenant_id),
            title=db_conv.title,
            status=db_conv.status,
            message_count=db_conv.message_count,
            created_at=db_conv.created_at,
            updated_at=db_conv.updated_at,
        )

    async def list_conversations(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """List user's conversations."""
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def list_from_db():
            return list(
                ConversationModel.objects.filter(user_id=user_id, tenant_id=tenant_id).order_by(
                    "-updated_at"
                )[offset : offset + limit]
            )

        db_convs = await list_from_db()
        return [
            Conversation(
                id=str(conv.id),
                agent_id=str(conv.agent_id),
                user_id=str(conv.user_id),
                tenant_id=str(conv.tenant_id),
                title=conv.title,
                status=conv.status,
                message_count=conv.message_count,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in db_convs
        ]

    # =========================================================================
    # SOMABRAIN INTEGRATION
    # =========================================================================

    async def initialize_agent_session(
        self, agent_id: str, conversation_id: str, user_context: dict
    ) -> AgentSession:
        """Initialize agent session in local session store."""
        from admin.core.models import Session as SessionModel

        start_time = time.perf_counter()
        try:

            @sync_to_async
            def create_session():
                session_id = str(uuid4())
                return SessionModel.objects.create(
                    session_id=session_id,
                    tenant=user_context.get("tenant_id"),
                    persona_id=user_context.get("persona_id"),
                    metadata={
                        "agent_id": agent_id,
                        "conversation_id": conversation_id,
                        "user_id": user_context.get("user_id"),
                    },
                )

            session_record = await create_session()
            session = AgentSession(
                session_id=session_record.session_id,
                agent_id=agent_id,
                conversation_id=conversation_id,
                created_at=session_record.created_at,
            )
            CHAT_LATENCY.labels(method="initialize_agent_session").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="initialize_agent_session", result="success").inc()
            return session
        except Exception as e:
            CHAT_LATENCY.labels(method="initialize_agent_session").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="initialize_agent_session", result="error").inc()
            raise

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

        from admin.chat.models import Conversation as ConversationModel, Message as MessageModel
        from admin.core.helpers.settings_defaults import get_default_settings
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

        # 2. Store user message
        # CHAT-003: Database operations with deployment mode context
        @sync_to_async
        def store_user_message():
            try:
                msg = MessageModel.objects.create(
                    conversation_id=conversation_id,
                    role="user",
                    content=content,
                    token_count=len(content.split()),
                )
                ConversationModel.objects.filter(id=conversation_id).update(
                    message_count=MessageModel.objects.filter(conversation_id=conversation_id).count()
                )
                return str(msg.id)
            except Exception as e:
                db_error_msg = f"{DEPLOYMENT_MODE} mode: Failed to store user message: {e}"
                if SAAS_MODE:
                    db_error_msg += " (SAAS: Check PostgreSQL connection pool)"
                elif STANDALONE_MODE:
                    db_error_msg += " (STANDALONE: Check local database connectivity)"
                logger.error(db_error_msg, exc_info=True)
                raise

        user_msg_id = await store_user_message()
        turn_metrics.tokens_in = len(content.split())

        # 3. Get conversation data
        @sync_to_async
        def load_conversation():
            conv = ConversationModel.objects.filter(id=conversation_id).only("tenant_id").first()
            if not conv:
                raise ValueError(f"Conversation {conversation_id} not found")
            qs = MessageModel.objects.filter(conversation_id=conversation_id).order_by(
                "-created_at"
            )[:20]
            return str(conv.tenant_id), list(reversed(qs))

        tenant_id, raw_history_objs = await load_conversation()
        raw_history = [{"role": m.role, "content": m.content} for m in raw_history_objs]

        # Update turn metrics with tenant_id
        turn_metrics.tenant_id = tenant_id
        metrics.record_turn_phase(turn_id, TurnPhase.AUTH_VALIDATED)

        # 4. Load LLM model
        # CHAT-003: LLM initialization with deployment mode error handling
        llm = None
        try:
            settings = get_default_settings(agent_id=agent_id)
            provider = settings.chat_model_provider or ""
            model_name = settings.chat_model_name or ""
            if "/" in model_name:
                model_provider, model_value = model_name.split("/", 1)
                if not provider or provider == model_provider:
                    provider, model_name = model_provider, model_value

            chat_kwargs = dict(settings.chat_model_kwargs or {})
            if settings.chat_model_api_base:
                chat_kwargs.setdefault("api_base", settings.chat_model_api_base)

            llm = get_chat_model(provider=provider, name=model_name, **chat_kwargs)
        except Exception as e:
            llm_error_msg = f"{DEPLOYMENT_MODE} mode: Failed to load LLM model: {e}"
            if SAAS_MODE:
                llm_error_msg += " (SAAS: Check LLM provider API key and connectivity)"
            elif STANDALONE_MODE:
                llm_error_msg += " (STANDALONE: Check local LLM model configuration)"
            logger.error(llm_error_msg, exc_info=True)
            raise

        # 5. Get health status
        health_monitor = get_health_monitor()
        overall_health = health_monitor.get_overall_health()
        is_degraded = overall_health.degraded

        metrics.record_turn_phase(turn_id, TurnPhase.HEALTH_CHECKED)

        # 6. Allocate budget via SimpleGovernor
        governor = get_governor()
        max_total_tokens = int(settings.chat_model_ctx_length)

        decision: GovernorDecision
        if is_degraded:
            decision = governor.allocate_budget(
                max_tokens=max_total_tokens,
                is_degraded=True,
            )
        else:
            decision = governor.allocate_budget(
                max_tokens=max_total_tokens,
                is_degraded=False,
            )

        metrics.record_turn_phase(turn_id, TurnPhase.BUDGET_ALLOCATED)

        # 7. Build context via ContextBuilder
        # CHAT-003: Deployment mode SomaBrain connection with error handling
        somabrain_client = None
        try:
            somabrain_client = await SomaBrainClient.get_async()
            if SAAS_MODE:
                logger.debug(f"SAAS mode: SomaBrainClient initialized for {tenant_id}")
            elif STANDALONE_MODE:
                logger.debug(f"STANDALONE mode: SomaBrainClient uses embedded modules")
        except Exception as e:
            error_msg = f"{DEPLOYMENT_MODE} mode: SomaBrainClient initialization failed: {e}"
            if SAAS_MODE:
                error_msg += " (HTTP client likely unavailable - check SomaBrain service)"
            elif STANDALONE_MODE:
                error_msg += " (Embedded modules import failed - check somabrain installation)"
            logger.error(error_msg, exc_info=True)
            # Non-critical error - will continue with minimal context

        # Simple token counter
        def simple_token_counter(text: str) -> int:
            return len(text.split())

        builder = create_context_builder(
            somabrain=somabrain_client,
            token_counter=simple_token_counter,
        )

        turn_dict = {
            "tenant_id": tenant_id,
            "session_id": str(uuid4()),
            "user_message": content,
            "history": raw_history,
            "system_prompt": "You are SomaAgent01.",
        }

        built: BuiltContext
        try:
            built = await builder.build_for_turn(
                turn=turn_dict,
                lane_budget=decision.lane_budget.to_dict(),
                is_degraded=is_degraded,
            )
        except Exception as e:
            error_msg = f"{DEPLOYMENT_MODE} mode: Context build failed: {e}"
            if SAAS_MODE:
                error_msg += " (SAAS: Check SomaBrain HTTP connectivity)"
            elif STANDALONE_MODE:
                error_msg += " (STANDALONE: Check embedded SomaBrain imports)"
            logger.error(error_msg, exc_info=True)
            # Fallback to minimal context
            built = BuiltContext(
                system_prompt="You are SomaAgent01.",
                messages=[
                    {"role": "system", "content": "You are SomaAgent01."},
                    {"role": "user", "content": content},
                ],
                token_counts={
                    "system": 50,
                    "history": 0,
                    "memory": 0,
                    "user": len(content.split()),
                },
                lane_actual={
                    "system_policy": 50,
                    "history": 0,
                    "memory": 0,
                    "tools": 0,
                    "tool_results": 0,
                    "buffer": 200,
                },
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
        # CHAT-003: Add timeout handling for SAAS mode
        llm_timeout = settings.chat_model_kwargs.get("timeout", 30.0) if settings.chat_model_kwargs else 30.0
        if SAAS_MODE:
            llm_timeout = min(llm_timeout, 60.0)  # Cap at 60s for SAAS mode

        response_content = []
        try:
            async for chunk in llm._astream(messages=lc_messages):
                token = ""
                if hasattr(chunk, "message") and getattr(chunk.message, "content", None):
                    token = str(chunk.message.content)
                elif hasattr(chunk, "content"):
                    token = str(chunk.content)

                if token:
                    response_content.append(token)
                    yield token
        except asyncio.TimeoutError as e:
            timeout_msg = f"{DEPLOYMENT_MODE} mode: LLM streaming timeout after {llm_timeout}s"
            if SAAS_MODE:
                timeout_msg += " (SAAS: Network latency or remote service unresponsive)"
            logger.warning(timeout_msg, exc_info=True)
            # Stream ended gracefully - client should handle incomplete response
        except Exception as e:
            stream_error_msg = f"{DEPLOYMENT_MODE} mode: LLM streaming error: {e}"
            if SAAS_MODE and "timeout" in str(e).lower():
                stream_error_msg += " (SAAS: HTTP timeout from LLM provider)"
            logger.error(stream_error_msg, exc_info=True)
            # Stream ended - error logged for monitoring

        metrics.record_turn_phase(
            turn_id, TurnPhase.COMPLETED if response_content else TurnPhase.ERROR
        )

        full_response = "".join(response_content)
        token_count_out = len(full_response.split())

        # 9. Store assistant message
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        model_id = getattr(llm, "model_name", f"{provider}/{model_name}")

        @sync_to_async
        def store_assistant_message():
            MessageModel.objects.create(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                token_count=token_count_out,
                latency_ms=elapsed_ms,
                model=model_id,
            )
            ConversationModel.objects.filter(id=conversation_id).update(
                message_count=MessageModel.objects.filter(conversation_id=conversation_id).count()
            )

        await store_assistant_message()

        # 10. Record completion metrics
        metrics.record_turn_complete(
            turn_id=turn_id,
            tokens_in=turn_metrics.tokens_in,
            tokens_out=token_count_out,
            model=model_id,
            provider=provider,
            error=None,
        )

        # 11. Non-blocking: store interaction in memory via SomaBrain
        from services.common.chat_memory import store_interaction

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

        # Track overall metrics
        CHAT_TOKENS.labels(direction="input").inc(turn_metrics.tokens_in)
        CHAT_TOKENS.labels(direction="output").inc(token_count_out)
        CHAT_LATENCY.labels(method="send_message").observe(time.perf_counter() - start_time)
        CHAT_REQUESTS.labels(
            method="send_message", result="success" if response_content else "error"
        ).inc()

    # =========================================================================
    # MEMORY INTEGRATION (delegated to chat_memory.py)
    # =========================================================================

    async def recall_memories(
        self,
        agent_id: str,
        user_id: str,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> list[Memory]:
        """Recall relevant memories via SomaBrain."""
        from services.common.chat_memory import recall_memories

        return await recall_memories(agent_id, user_id, query, limit, tenant_id)

    async def store_memory(
        self,
        agent_id: str,
        user_id: str,
        content: str,
        metadata: dict,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Store interaction via SomaBrain."""
        from services.common.chat_memory import store_memory

        await store_memory(agent_id, user_id, content, metadata, tenant_id)

    async def store_interaction(
        self,
        *,
        agent_id: str,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Store a full interaction in memory via SomaBrain."""
        from services.common.chat_memory import store_interaction

        await store_interaction(
            agent_id=agent_id,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=assistant_response,
            tenant_id=tenant_id,
        )

    # =========================================================================
    # TITLE GENERATION
    # =========================================================================

    async def generate_title(self, conversation_id: str, messages: list[Message]) -> str:
        """Generate conversation title using utility model."""
        from langchain_core.messages import HumanMessage, SystemMessage

        from admin.chat.models import Conversation as ConversationModel
        from admin.core.helpers.settings_defaults import get_default_settings
        from admin.llm.services.litellm_client import get_chat_model

        start_time = time.perf_counter()
        try:

            @sync_to_async
            def get_agent_id():
                conv = ConversationModel.objects.filter(id=conversation_id).only("agent_id").first()
                return str(conv.agent_id) if conv else "default"

            agent_id = await get_agent_id()
            settings = get_default_settings(agent_id=agent_id)
            provider = settings.util_model_provider or settings.chat_model_provider
            model_name = settings.util_model_name or settings.chat_model_name
            if "/" in model_name:
                model_provider, model_value = model_name.split("/", 1)
                if not provider or provider == model_provider:
                    provider, model_name = model_provider, model_value

            util_kwargs = dict(settings.util_model_kwargs or settings.chat_model_kwargs or {})
            if settings.util_model_api_base:
                util_kwargs.setdefault("api_base", settings.util_model_api_base)

            llm = get_chat_model(provider=provider, name=model_name, **util_kwargs)
            context = "\n".join(f"{m.role}: {m.content[:200]}" for m in messages[:5])
            title_tokens = []
            async for chunk in llm._astream(
                messages=[
                    SystemMessage(
                        content="You generate short chat titles. Return a concise title (max 8 words), no quotes."
                    ),
                    HumanMessage(content=context),
                ]
            ):
                token = (
                    str(chunk.message.content)
                    if hasattr(chunk, "message") and getattr(chunk.message, "content", None)
                    else (str(chunk.content) if hasattr(chunk, "content") else "")
                )
                if token:
                    title_tokens.append(token)

            title = "".join(title_tokens).strip() or (
                messages[0].content[:50] if messages else "New Conversation"
            )

            @sync_to_async
            def update_title():
                ConversationModel.objects.filter(id=conversation_id).update(title=title)

            await update_title()
            CHAT_LATENCY.labels(method="generate_title").observe(time.perf_counter() - start_time)
            CHAT_REQUESTS.labels(method="generate_title", result="success").inc()
            return title
        except Exception as e:
            CHAT_LATENCY.labels(method="generate_title").observe(time.perf_counter() - start_time)
            CHAT_REQUESTS.labels(method="generate_title", result="error").inc()
            return messages[0].content[:50] if messages else "New Conversation"


# Singleton
_chat_service_instance: Optional[ChatService] = None


async def get_chat_service() -> ChatService:
    """Get or create the singleton ChatService."""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance


__all__ = ["ChatService", "Conversation", "Message", "AgentSession", "Memory", "get_chat_service"]
