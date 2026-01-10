"""ChatService for LLM + memory integration and conversation management.


Per login-to-chat-journey design.md Section 6.1 (design doc missing from repo).

Implements:
- create_conversation() - PostgreSQL insert
- initialize_agent_session() - SomaBrain API call
- recall_memories() - SomaFractalMemory API call
- send_message() - Stream from SomaBrain
- store_memory() - Async memory storage
- generate_title() - Utility model for title generation

Personas:
- Django Architect: Django ORM integration, async operations
- Performance Engineer: Streaming, connection pooling
- Security Auditor: Tenant isolation, input validation
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Optional
from uuid import uuid4

import httpx
from asgiref.sync import sync_to_async
from prometheus_client import Counter, Histogram

from admin.agents.services.agentiq_governor import (
    create_governor,
    TurnContext,
)
from admin.agents.services.context_builder import ContextBuilder
from admin.core.observability.metrics import ContextBuilderMetrics
from admin.core.somabrain_client import SomaBrainClient
from services.common.budget_manager import BudgetManager
from services.common.capsule_store import CapsuleStore
from services.common.degradation_monitor import DegradationMonitor

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

CHAT_REQUESTS = Counter(
    "chat_service_requests_total",
    "Total ChatService requests",
    ["method", "result"],
)

CHAT_LATENCY = Histogram(
    "chat_service_duration_seconds",
    "ChatService request latency",
    ["method"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

CHAT_TOKENS = Counter(
    "chat_tokens_total",
    "Total tokens processed",
    ["direction"],  # "input" or "output"
)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Conversation:
    """Conversation record."""

    id: str
    agent_id: str
    user_id: str
    tenant_id: str
    title: Optional[str]
    status: str
    message_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class Message:
    """Message record."""

    id: str
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    token_count: int
    model: Optional[str]
    latency_ms: Optional[int]
    created_at: datetime


@dataclass
class AgentSession:
    """Agent session from SomaBrain."""

    session_id: str
    agent_id: str
    conversation_id: str
    created_at: datetime


@dataclass
class Memory:
    """Memory record from SomaFractalMemory."""

    id: str
    content: str
    memory_type: str
    relevance_score: float
    created_at: datetime


# =============================================================================
# CHAT SERVICE
# =============================================================================


class ChatService:
    """Service for chat operations with SomaBrain integration.

    Per design.md Section 6.1:
    - Conversation management in PostgreSQL
    - Agent session initialization in SomaBrain
    - Memory recall from SomaFractalMemory
    - Streaming message responses
    """

    def __init__(
        self,
        somabrain_url: Optional[str] = None,
        memory_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize ChatService.

        Args:
            somabrain_url: SomaBrain API URL. Defaults to Service Registry.
            memory_url: SomaFractalMemory API URL. Defaults to Service Registry.
            timeout: HTTP timeout in seconds.
        """
        from django.conf import settings

        self.somabrain_url = somabrain_url or settings.SOMABRAIN_URL
        self.memory_url = memory_url or settings.SOMAFRACTALMEMORY_URL
        self.memory_api_token = (
            os.getenv("SOMA_MEMORY_API_TOKEN") or os.getenv("SOMA_API_TOKEN") or ""
        )
        self.timeout = timeout

        # HTTP client for external services
        self._http_client: Optional[httpx.AsyncClient] = None

        # Governor dependencies
        self.degradation_monitor = DegradationMonitor()
        self.capsule_store = CapsuleStore()
        self.budget_manager = BudgetManager()
        self.governor = create_governor(
            capsule_store=self.capsule_store,
            degradation_monitor=self.degradation_monitor,
            budget_manager=self.budget_manager,
        )
        self.metrics = ContextBuilderMetrics()

    def _build_memory_headers(self, tenant_id: Optional[str]) -> dict:
        """Execute build memory headers.

            Args:
                tenant_id: The tenant_id.
            """

        headers = {"Content-Type": "application/json"}
        if self.memory_api_token:
            headers["Authorization"] = f"Bearer {self.memory_api_token}"
        if tenant_id:
            headers["X-Soma-Tenant"] = tenant_id
        return headers

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
        self,
        agent_id: str,
        user_id: str,
        tenant_id: str,
    ) -> Conversation:
        """Create new conversation record in PostgreSQL.

        Per design.md Section 6.1:
        - Creates conversation in database
        - Returns conversation object

        Args:
            agent_id: Agent ID
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            Created Conversation object
        """
        import time

        from admin.chat.models import Conversation as ConversationModel

        start_time = time.perf_counter()

        try:

            @sync_to_async
            def create_in_db():
                """Execute create in db.
                    """

                conv = ConversationModel.objects.create(
                    agent_id=agent_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    status="active",
                    message_count=0,
                )
                return conv

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

            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="create_conversation").observe(elapsed)
            CHAT_REQUESTS.labels(method="create_conversation", result="success").inc()

            logger.info(
                f"Conversation created: id={conversation.id}, " f"agent={agent_id}, user={user_id}"
            )

            return conversation

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="create_conversation").observe(elapsed)
            CHAT_REQUESTS.labels(method="create_conversation", result="error").inc()

            logger.error(f"Failed to create conversation: {e}")
            raise

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str,
    ) -> Optional[Conversation]:
        """Get conversation by ID.

        Args:
            conversation_id: Conversation ID
            user_id: User ID (for ownership check)

        Returns:
            Conversation if found and owned by user, None otherwise
        """
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def get_from_db():
            """Retrieve from db.
                """

            try:
                conv = ConversationModel.objects.get(
                    id=conversation_id,
                    user_id=user_id,
                )
                return conv
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
        """List user's conversations.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of Conversation objects
        """
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def list_from_db():
            """Execute list from db.
                """

            return list(
                ConversationModel.objects.filter(
                    user_id=user_id,
                    tenant_id=tenant_id,
                ).order_by(
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
        self,
        agent_id: str,
        conversation_id: str,
        user_context: dict,
    ) -> AgentSession:
        """Initialize agent session in local session store.

        Per design.md Section 6.1:
        - Creates Session model entry
        - Persists user context metadata

        Args:
            agent_id: Agent ID
            conversation_id: Conversation ID
            user_context: User context dict (user_id, tenant_id, etc.)

        Returns:
            AgentSession object
        """
        import time

        start_time = time.perf_counter()

        try:
            from admin.core.models import Session as SessionModel

            @sync_to_async
            def create_session():
                """Execute create session.
                    """

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

            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="initialize_agent_session").observe(elapsed)
            CHAT_REQUESTS.labels(method="initialize_agent_session", result="success").inc()

            logger.info(
                f"Agent session initialized: session={session.session_id}, "
                f"agent={agent_id}, conversation={conversation_id}"
            )

            return session

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="initialize_agent_session").observe(elapsed)
            CHAT_REQUESTS.labels(method="initialize_agent_session", result="error").inc()

            logger.error(f"Agent session init failed: {e}")
            raise

    async def send_message(
        self,
        conversation_id: str,
        agent_id: str,
        content: str,
        user_id: str,
    ) -> AsyncIterator[str]:
        """Send message and stream response tokens from LLM provider.

        Per design.md Section 6.1:
        - Builds context from conversation history
        - Streams response tokens from LiteLLM-backed provider
        - Stores messages in database

        Args:
            conversation_id: Conversation ID
            agent_id: Agent ID
            content: Message content
            user_id: User ID

        Yields:
            Response tokens as they arrive
        """
        import time

        from admin.chat.models import Conversation as ConversationModel, Message as MessageModel

        start_time = time.perf_counter()

        # Store user message
        @sync_to_async
        def store_user_message():
            """Execute store user message.
                """

            msg = MessageModel.objects.create(
                conversation_id=conversation_id,
                role="user",
                content=content,
                token_count=len(content.split()),  # Approximate
            )
            # Update conversation message count
            ConversationModel.objects.filter(id=conversation_id).update(
                message_count=MessageModel.objects.filter(conversation_id=conversation_id).count()
            )
            return str(msg.id)

        user_msg_id = await store_user_message()
        CHAT_TOKENS.labels(direction="input").inc(len(content.split()))

        try:
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

            from admin.core.helpers.settings_defaults import get_default_settings
            from admin.llm.services.litellm_client import get_chat_model, LLMNotConfiguredError

            settings = get_default_settings(agent_id=agent_id)
            provider = settings.chat_model_provider or ""
            model_name = settings.chat_model_name or ""
            if "/" in model_name:
                model_provider, model_value = model_name.split("/", 1)
                if not provider or provider == model_provider:
                    provider = model_provider
                    model_name = model_value

            chat_kwargs = dict(settings.chat_model_kwargs or {})
            if settings.chat_model_api_base:
                chat_kwargs.setdefault("api_base", settings.chat_model_api_base)
            if isinstance(chat_kwargs.get("temperature"), str):
                try:
                    chat_kwargs["temperature"] = float(chat_kwargs["temperature"])
                except ValueError:
                    pass

            llm = get_chat_model(provider=provider, name=model_name, **chat_kwargs)

            # --- AGENTIQ GOVERNOR & CONTEXT BUILDER INTEGRATION ---

            # 1. Prepare TurnContext
            # Load basic history first for the governor (without snippets)
            @sync_to_async
            def load_raw_history():
                """Execute load raw history.
                    """

                conv = (
                    ConversationModel.objects.filter(id=conversation_id).only("tenant_id").first()
                )
                if not conv:
                    # Should be handled by logic above, but safety first
                    raise ValueError(f"Conversation {conversation_id} not found")

                qs = MessageModel.objects.filter(conversation_id=conversation_id).order_by(
                    "-created_at"
                )[:20]
                return list(qs)[::-1], str(conv.tenant_id)

            raw_history_objs, current_tenant_id = await load_raw_history()
            raw_history = [{"role": m.role, "content": m.content} for m in raw_history_objs]

            turn_context = TurnContext(
                turn_id=str(uuid4()),
                session_id=str(
                    uuid4()
                ),  # We should probably reuse a session if we had one, but strict statelessness for now
                tenant_id=current_tenant_id,
                user_message=content,
                history=raw_history,
                system_prompt="You are SomaAgent01.",  # Default prompt
            )

            # 2. Govern
            # Execute governor logic to get lane plan and degradation decision
            max_total_tokens = int(settings.chat_model_ctx_length)
            decision = await self.governor.govern_with_fallback(
                turn=turn_context,
                max_tokens=max_total_tokens,
            )

            # 3. Build Context
            # Use ContextBuilder to retrieve snippets, summarize, and budget
            somabrain_client = await SomaBrainClient.get_async()

            # Simple token counter for Builder
            def simple_token_counter(text: str) -> int:
                """Execute simple token counter.

                    Args:
                        text: The text.
                    """

                return len(text.split())

            builder = ContextBuilder(
                somabrain=somabrain_client,
                metrics=self.metrics,
                token_counter=simple_token_counter,
            )

            # Pass turn dict as expected by builder
            turn_dict = {
                "tenant_id": current_tenant_id,
                "session_id": turn_context.session_id,
                "user_message": content,
                "history": raw_history,
                "system_prompt": turn_context.system_prompt,
            }

            built_context = await builder.build_for_turn(
                turn=turn_dict,
                max_prompt_tokens=max_total_tokens,
                lane_plan=decision.lane_plan,
            )

            # 4. Invoke LLM
            # Map BuiltContext messages to LangChain format
            lc_messages = []
            for msg in built_context.messages:
                role = msg.get("role")
                content = msg.get("content")
                if role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                elif role == "system":
                    lc_messages.append(SystemMessage(content=content))
                else:
                    lc_messages.append(HumanMessage(content=content))

            response_content = []
            async for chunk in llm._astream(messages=lc_messages):
                token = ""
                if hasattr(chunk, "message") and getattr(chunk.message, "content", None):
                    token = str(chunk.message.content)
                elif hasattr(chunk, "content"):
                    token = str(chunk.content)
                if token:
                    response_content.append(token)
                    yield token
            full_response = "".join(response_content)
            token_count = len(full_response.split())

            # Store assistant message
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            model_id = getattr(llm, "model_name", f"{provider}/{model_name}")

            @sync_to_async
            def store_assistant_message():
                """Execute store assistant message.
                    """

                msg = MessageModel.objects.create(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                    token_count=token_count,
                    latency_ms=elapsed_ms,
                    model=model_id,
                )
                # Update conversation
                ConversationModel.objects.filter(id=conversation_id).update(
                    message_count=MessageModel.objects.filter(
                        conversation_id=conversation_id
                    ).count()
                )
                return str(msg.id)

            await store_assistant_message()
            CHAT_TOKENS.labels(direction="output").inc(token_count)

            # Store interaction in memory (non-blocking)
            asyncio.create_task(
                self.store_interaction(
                    user_id=user_id,
                    agent_id=agent_id,
                    conversation_id=conversation_id,
                    user_message=content,
                    assistant_response=full_response,
                    tenant_id=current_tenant_id,  # Fixed: use tenant_id from conversation
                )
            )

            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="send_message").observe(elapsed)
            CHAT_REQUESTS.labels(method="send_message", result="success").inc()

            logger.info(
                f"Message exchange complete: conversation={conversation_id}, "
                f"tokens={token_count}, latency_ms={elapsed_ms}"
            )

        except LLMNotConfiguredError as e:
            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="send_message").observe(elapsed)
            CHAT_REQUESTS.labels(method="send_message", result="error").inc()

            logger.error(f"LLM not configured: {e}")
            raise
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="send_message").observe(elapsed)
            CHAT_REQUESTS.labels(method="send_message", result="error").inc()

            logger.error(f"Message send failed: {e}")
            raise

    # =========================================================================
    # MEMORY INTEGRATION
    # =========================================================================

    async def recall_memories(
        self,
        agent_id: str,
        user_id: str,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> list[Memory]:
        """Recall relevant memories from SomaFractalMemory.

        Per design.md Section 6.1:
        - Queries SomaFractalMemory /memories/search
        - Returns list of Memory objects
        - Graceful degradation if memory service unavailable

        Args:
            agent_id: Agent ID
            user_id: User ID
            query: Query string for semantic search
            limit: Max memories to return

        Returns:
            List of Memory objects (empty if service unavailable)
        """
        import time

        start_time = time.perf_counter()

        try:
            if not self.memory_api_token:
                logger.warning("Memory recall skipped: SOMA_MEMORY_API_TOKEN not set")
                return []

            client = await self._get_http_client()
            headers = self._build_memory_headers(tenant_id)
            response = await client.post(
                f"{self.memory_url}/memories/search",
                json={
                    "query": query,
                    "top_k": limit,
                    "memory_type": "episodic",
                    "filters": {
                        "agent_id": agent_id,
                        "user_id": user_id,
                    },
                },
                headers=headers,
                timeout=5.0,
            )

            if response.status_code != 200:
                logger.warning(f"Memory recall failed: status={response.status_code}")
                return []

            data = response.json()
            memories = []
            for item in data.get("memories", []):
                payload = item.get("payload") if isinstance(item, dict) else None
                payload = payload if isinstance(payload, dict) else {}
                content = payload.get("content") or ""
                created_at = payload.get("timestamp") or item.get(
                    "created_at", datetime.now(timezone.utc).isoformat()
                )
                try:
                    created_dt = (
                        created_at
                        if isinstance(created_at, datetime)
                        else datetime.fromisoformat(str(created_at))
                    )
                except ValueError:
                    created_dt = datetime.now(timezone.utc)

                coord = item.get("coordinate")
                if isinstance(coord, list):
                    coord_id = ",".join(str(c) for c in coord)
                else:
                    coord_id = str(coord or uuid4())

                memories.append(
                    Memory(
                        id=coord_id,
                        content=content,
                        memory_type=item.get("memory_type", "episodic"),
                        relevance_score=float(item.get("importance", 0.0)),
                        created_at=created_dt,
                    )
                )

            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="recall_memories").observe(elapsed)
            CHAT_REQUESTS.labels(method="recall_memories", result="success").inc()

            logger.debug(
                f"Memories recalled: agent={agent_id}, user={user_id}, " f"count={len(memories)}"
            )

            return memories

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="recall_memories").observe(elapsed)
            CHAT_REQUESTS.labels(method="recall_memories", result="error").inc()

            # Graceful degradation - return empty list
            logger.warning(f"Memory recall failed (graceful degradation): {e}")
            return []

    async def store_memory(
        self,
        agent_id: str,
        user_id: str,
        content: str,
        metadata: dict,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Store interaction in SomaFractalMemory.

        Per design.md Section 6.1:
        - Stores memory via /memories endpoint
        - Fire-and-forget (non-blocking)

        Args:
            agent_id: Agent ID
            user_id: User ID
            content: Memory content
            metadata: Additional metadata
        """
        try:
            if not self.memory_api_token:
                logger.warning("Memory store skipped: SOMA_MEMORY_API_TOKEN not set")
                return

            import hashlib

            seed = f"{content}|{metadata.get('conversation_id','')}|{metadata.get('timestamp','')}"
            digest = hashlib.sha256(seed.encode("utf-8")).digest()
            coord_values = [
                int.from_bytes(digest[i : i + 2], "big") / 65535.0 for i in range(0, 6, 2)
            ]
            coord = ",".join(f"{value:.6f}" for value in coord_values)
            payload = {
                "content": content,
                "agent_id": agent_id,
                "user_id": user_id,
                **metadata,
            }

            client = await self._get_http_client()
            headers = self._build_memory_headers(tenant_id)
            await client.post(
                f"{self.memory_url}/memories",
                json={
                    "coord": coord,
                    "payload": payload,
                    "memory_type": "episodic",
                },
                headers=headers,
                timeout=2.0,
            )

            logger.debug(f"Memory stored: agent={agent_id}, user={user_id}")

        except Exception as e:
            # Non-critical - log and continue
            logger.warning(f"Memory store failed (non-critical): {e}")

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
        """Store a full interaction in memory.

        Per design.md Section 6.1:
        - Stores combined user/assistant exchange
        - Includes conversation metadata
        """
        content = f"User: {user_message}\nAssistant: {assistant_response}"
        metadata = {
            "conversation_id": conversation_id,
            "user_message": user_message[:5000],
            "assistant_response": assistant_response[:5000],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self.store_memory(
            agent_id=agent_id,
            user_id=user_id,
            content=content,
            metadata=metadata,
            tenant_id=tenant_id,
        )

    # =========================================================================
    # TITLE GENERATION
    # =========================================================================

    async def generate_title(
        self,
        conversation_id: str,
        messages: list[Message],
    ) -> str:
        """Generate conversation title using utility model.

        Per design.md Section 6.1:
        - Calls utility model for title generation
        - Updates conversation title in database

        Args:
            conversation_id: Conversation ID
            messages: List of messages for context

        Returns:
            Generated title
        """
        import time

        from admin.chat.models import Conversation as ConversationModel

        start_time = time.perf_counter()

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            from admin.core.helpers.settings_defaults import get_default_settings
            from admin.llm.services.litellm_client import get_chat_model

            @sync_to_async
            def get_agent_id():
                """Retrieve agent id.
                    """

                conv = ConversationModel.objects.filter(id=conversation_id).only("agent_id").first()
                return str(conv.agent_id) if conv else "default"

            agent_id = await get_agent_id()
            settings = get_default_settings(agent_id=agent_id)

            provider = settings.util_model_provider or settings.chat_model_provider
            model_name = settings.util_model_name or settings.chat_model_name
            if "/" in model_name:
                model_provider, model_value = model_name.split("/", 1)
                if not provider or provider == model_provider:
                    provider = model_provider
                    model_name = model_value

            util_kwargs = dict(settings.util_model_kwargs or settings.chat_model_kwargs or {})
            if settings.util_model_api_base:
                util_kwargs.setdefault("api_base", settings.util_model_api_base)
            if isinstance(util_kwargs.get("temperature"), str):
                try:
                    util_kwargs["temperature"] = float(util_kwargs["temperature"])
                except ValueError:
                    pass

            llm = get_chat_model(provider=provider, name=model_name, **util_kwargs)

            # Build context from messages
            context = "\n".join(f"{m.role}: {m.content[:200]}" for m in messages[:5])

            title_tokens = []
            title_prompt = (
                "You generate short chat titles. Return a concise title (max 8 words), no quotes."
            )
            async for chunk in llm._astream(
                messages=[
                    SystemMessage(content=title_prompt),
                    HumanMessage(content=context),
                ]
            ):
                token = ""
                if hasattr(chunk, "message") and getattr(chunk.message, "content", None):
                    token = str(chunk.message.content)
                elif hasattr(chunk, "content"):
                    token = str(chunk.content)
                if token:
                    title_tokens.append(token)

            title = "".join(title_tokens).strip()
            if not title:
                title = messages[0].content[:50] if messages else "New Conversation"

            # Update database
            @sync_to_async
            def update_title():
                """Execute update title.
                    """

                ConversationModel.objects.filter(id=conversation_id).update(title=title)

            await update_title()

            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="generate_title").observe(elapsed)
            CHAT_REQUESTS.labels(method="generate_title", result="success").inc()

            logger.info(f"Title generated: conversation={conversation_id}, title={title}")

            return title

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            CHAT_LATENCY.labels(method="generate_title").observe(elapsed)
            CHAT_REQUESTS.labels(method="generate_title", result="error").inc()

            # Fallback
            title = messages[0].content[:50] if messages else "New Conversation"
            logger.warning(f"Title generation failed, using fallback: {e}")
            return title


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_chat_service_instance: Optional[ChatService] = None


async def get_chat_service() -> ChatService:
    """Get or create the singleton ChatService.

    Usage:
        service = await get_chat_service()
        conv = await service.create_conversation(agent_id, user_id, tenant_id)
    """
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance


__all__ = [
    "ChatService",
    "Conversation",
    "Message",
    "AgentSession",
    "Memory",
    "get_chat_service",
]