"""Chat context and memory management.

Handles history recall, message formatting, and the memory storage hierarchy
(SomaBrain primary → SomaFractalMemory fallback → PendingMemory queue).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import uuid4

from asgiref.sync import sync_to_async

from admin.core.context import BuiltContext
from admin.core.somabrain_client import SomaBrainClient
from services.common.circuit_breaker import CircuitBreakerError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# tiktoken — accurate token counting
# ---------------------------------------------------------------------------
import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")


def token_count(text: str) -> int:
    """Accurate LLM token count."""
    return len(_ENCODING.encode(text))


@dataclass
class ConversationSummary:
    """Conversation metadata."""

    id: str
    title: str
    agent_id: str
    user_id: str
    tenant_id: str
    status: str
    message_count: int
    created_at: Any
    updated_at: Any


def make_coordinate(seed: str) -> tuple[float, float, float]:
    """Generate a deterministic 3D fractal coordinate from a seed string."""
    h = hashlib.md5(seed.encode()).hexdigest()
    return (
        (int(h[0:8], 16) / 0xFFFFFFFF) * 2 - 1,
        (int(h[8:16], 16) / 0xFFFFFFFF) * 2 - 1,
        (int(h[16:24], 16) / 0xFFFFFFFF) * 2 - 1,
    )


def to_langchain_messages(
    context: BuiltContext, history: List[Dict[str, str]], user_message: str
) -> List[Any]:
    """Convert BuiltContext to LangChain messages."""
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    msgs: List[Any] = []
    if context.system:
        msgs.append(SystemMessage(content=context.system))
    for h in history:
        role, content = h.get("role"), h.get("content", "")
        if role == "assistant":
            msgs.append(AIMessage(content=content))
        else:
            msgs.append(HumanMessage(content=content))
    msgs.append(HumanMessage(content=user_message))
    return msgs


class ChatContextManager:
    """Manages chat history recall and the memory storage hierarchy."""

    def __init__(
        self,
        sfm_adapter: Optional[Any] = None,
        cb_somabrain: Optional[Any] = None,
    ) -> None:
        self._sfm_adapter = sfm_adapter
        self._cb_somabrain = cb_somabrain

    # =================================================================
    # Conversation CRUD
    # =================================================================

    async def create_conversation(
        self, agent_id: str, user_id: str, tenant_id: str, title: Optional[str] = None
    ) -> ConversationSummary:
        """Create a new conversation."""
        from django.db import transaction

        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def _create() -> ConversationSummary:
            with transaction.atomic():
                db = ConversationModel.objects.create(
                    agent_id=agent_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    status="active",
                    message_count=0,
                    title=title or f"Conversation {str(uuid4())[:8]}",
                )
                return ConversationSummary(
                    id=str(db.id),
                    title=db.title,
                    agent_id=str(db.agent_id),
                    user_id=str(db.user_id),
                    tenant_id=str(db.tenant_id),
                    status=db.status,
                    message_count=db.message_count,
                    created_at=db.created_at,
                    updated_at=db.updated_at,
                )

        return await _create()

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[ConversationSummary]:
        """Get conversation with ownership check."""
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def _get() -> Optional[ConversationSummary]:
            try:
                db = ConversationModel.objects.get(id=conversation_id)
                if str(db.user_id) != user_id:
                    return None
                return ConversationSummary(
                    id=str(db.id),
                    title=db.title,
                    agent_id=str(db.agent_id),
                    user_id=str(db.user_id),
                    tenant_id=str(db.tenant_id),
                    status=db.status,
                    message_count=db.message_count,
                    created_at=db.created_at,
                    updated_at=db.updated_at,
                )
            except ConversationModel.DoesNotExist:
                return None

        return await _get()

    async def list_conversations(
        self, user_id: str, tenant_id: str, limit: int = 50, offset: int = 0
    ) -> List[ConversationSummary]:
        """List user's conversations."""
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def _list() -> List[ConversationSummary]:
            qs = ConversationModel.objects.filter(user_id=user_id, tenant_id=tenant_id).order_by(
                "-updated_at"
            )[offset : offset + limit]
            return [
                ConversationSummary(
                    id=str(c.id),
                    title=c.title,
                    agent_id=str(c.agent_id),
                    user_id=str(c.user_id),
                    tenant_id=str(c.tenant_id),
                    status=c.status,
                    message_count=c.message_count,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
                for c in qs
            ]

        return await _list()

    async def recall_history(self, conversation_id: str, tenant_id: str) -> List[Dict[str, str]]:
        """Recall last 20 messages from PostgreSQL trace."""
        if not conversation_id:
            return []
        from admin.chat.models import Message as MessageModel

        @sync_to_async
        def _load():
            qs = MessageModel.objects.filter(conversation_id=conversation_id).order_by(
                "-created_at"
            )[:20]
            return [
                {"role": m.role, "content": getattr(m, "content", None) or ""}
                for m in reversed(list(qs))
            ]

        return await _load()

    async def store_to_sfm(
        self,
        content: str,
        conversation_id: str,
        tenant_id: str,
        namespace: str,
        metadata: dict,
    ) -> None:
        """Store memory to SomaFractalMemory (independent from SomaBrain)."""
        adapter = self._sfm_adapter
        if adapter is None:
            return

        coordinate = make_coordinate(f"{conversation_id}:{content[:50]}")
        payload = {
            "content": content,
            "conversation_id": conversation_id,
            **metadata,
        }

        try:
            # HTTP adapter has store_async; Direct adapter has store (sync)
            if hasattr(adapter, "store_async"):
                await adapter.store_async(
                    coordinate=coordinate,
                    payload=payload,
                    tenant=tenant_id,
                    namespace=namespace,
                )
            else:
                # Wrap sync store in thread for non-blocking
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: adapter.store(
                        coordinate=coordinate,
                        payload=payload,
                        tenant=tenant_id,
                        namespace=namespace,
                    ),
                )
            logger.debug("SFM store OK: %s", conversation_id)
        except Exception as exc:
            logger.warning("SFM store failed: %s", exc)

    async def queue_pending_memory(
        self,
        tenant_id: str,
        namespace: str,
        payload: Dict[str, Any],
    ) -> None:
        """Queue memory to PendingMemory for sync when SomaBrain recovers.

        Best-effort: logs on failure, never blocks the chat turn.
        """
        from uuid import uuid4

        from django.db import transaction

        from admin.core.models import PendingMemory

        idempotency_key = (
            f"chat:{tenant_id}:{payload.get('conversation_id', '')}:{str(uuid4())[:8]}"
        )

        @sync_to_async
        def _create() -> None:
            try:
                with transaction.atomic():
                    PendingMemory.objects.get_or_create(
                        idempotency_key=idempotency_key,
                        defaults={
                            "tenant_id": tenant_id,
                            "namespace": namespace,
                            "payload": payload,
                        },
                    )
            except Exception as exc:
                logger.warning("PendingMemory queue failed: %s", exc)

        await _create()

    async def store_episodic_bg(
        self,
        tenant_id: str,
        user_message: str,
        assistant_response: str,
        conversation_id: str,
        model_id: str,
        elapsed_ms: int,
    ) -> None:
        """Non-blocking episodic memory storage.

        Hierarchy: SomaBrain primary → SomaFractalMemory fallback.
        SFM is independent from Brain and can queue for Brain sync internally.
        """
        content = f"User: {user_message}\nAssistant: {assistant_response}"
        brain_stored = False

        try:
            client = await SomaBrainClient.get_async()
            if client is None:
                logger.debug("SomaBrain not configured; skipping episodic memory store")
            else:
                await self._cb_somabrain.call(
                    client.remember,
                    payload={
                        "content": content,
                        "conversation_id": conversation_id,
                        "model": model_id,
                        "latency_ms": elapsed_ms,
                    },
                    tenant=tenant_id,
                    namespace="episodic",
                )
                brain_stored = True
        except Exception as e:
            logger.debug("Episodic Brain store failed: %s", e)

        if not brain_stored:
            await self.store_to_sfm(
                content=content,
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                namespace="episodic",
                metadata={"model": model_id, "latency_ms": elapsed_ms},
            )

    async def store_turn(
        self,
        conversation_id: str,
        tenant_id: str,
        user_message: str,
        assistant_response: str,
        model_id: str,
        elapsed_ms: int,
        token_count_out: int,
    ) -> None:
        """Store user + assistant messages.

        Storage hierarchy:
        1. PostgreSQL — ALWAYS (persistence layer)
        2. SomaBrain — PRIMARY (cognitive + memory)
        3. SomaFractalMemory — FALLBACK (pure memory, independent from Brain)
        """
        from django.db import transaction

        from admin.chat.models import Conversation as ConversationModel, Message as MessageModel

        # Store user message trace (ALWAYS — Zero Data Loss)
        @sync_to_async
        def _store_user():
            with transaction.atomic():
                MessageModel.objects.create(
                    conversation_id=conversation_id,
                    role="user",
                    coordinate=user_message,
                    token_count=token_count(user_message),
                )

        await _store_user()

        # SomaBrain memory (PRIMARY — cognitive + memory)
        brain_stored = False
        try:
            client = await SomaBrainClient.get_async()
            if client is None:
                logger.debug("SomaBrain not configured; skipping primary memory store")
            else:
                await self._cb_somabrain.call(
                    client.remember,
                    payload={
                        "role": "assistant",
                        "content": assistant_response,
                        "conversation_id": conversation_id,
                        "model": model_id,
                        "latency_ms": elapsed_ms,
                    },
                    tenant=tenant_id,
                    namespace="chat_history",
                )
                brain_stored = True
        except CircuitBreakerError:
            logger.warning(
                "SomaBrain circuit OPEN — falling back to SomaFractalMemory + PendingMemory"
            )
        except Exception as e:
            logger.warning(
                "SomaBrain store failed: %s — falling back to SomaFractalMemory + PendingMemory", e
            )

        # SomaFractalMemory fallback (independent from Brain)
        if not brain_stored:
            await self.store_to_sfm(
                content=assistant_response,
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                namespace="chat_history",
                metadata={"role": "assistant", "model": model_id, "latency_ms": elapsed_ms},
            )
            # Queue to PendingMemory for later sync when Brain recovers
            await self.queue_pending_memory(
                tenant_id=tenant_id,
                namespace="chat_history",
                payload={
                    "role": "assistant",
                    "content": assistant_response,
                    "conversation_id": conversation_id,
                    "model": model_id,
                    "latency_ms": elapsed_ms,
                },
            )

        # Store assistant trace (ALWAYS — Zero Data Loss)
        @sync_to_async
        def _store_assistant():
            with transaction.atomic():
                MessageModel.objects.create(
                    conversation_id=conversation_id,
                    role="assistant",
                    coordinate=assistant_response,
                    token_count=token_count_out,
                    latency_ms=elapsed_ms,
                    model=model_id,
                )
                ConversationModel.objects.filter(id=conversation_id).update(
                    message_count=MessageModel.objects.filter(
                        conversation_id=conversation_id
                    ).count()
                )

        await _store_assistant()

    async def emit_signals(
        self,
        sender_cls: type,
        conversation_id: str,
        message_id: str,
        full_response: str,
        model_used: str,
        elapsed_ms: int,
        tenant_id: str,
    ) -> None:
        """Emit Django signals for outbox publishers."""
        try:
            from admin.core.signals import conversation_message, memory_created

            await sync_to_async(conversation_message.send)(
                sender=sender_cls,
                conversation_id=conversation_id,
                message_id=message_id,
                role="assistant",
                content=full_response,
            )
            await sync_to_async(memory_created.send)(
                sender=sender_cls,
                payload={
                    "role": "assistant",
                    "content": full_response,
                    "conversation_id": conversation_id,
                    "model": model_used,
                    "latency_ms": elapsed_ms,
                },
                tenant_id=tenant_id,
                namespace="chat_history",
            )
        except Exception as signal_exc:
            logger.warning("Signal emission failed: %s", signal_exc)

    async def trigger_sleep_cycle(self, tenant_id: str, persona_id: str) -> None:
        """Trigger a SomaBrain sleep/consolidation cycle.

        This should be called periodically (e.g., every 6 hours) by a
        background scheduler to consolidate memories and update graph
        relationships.
        """
        try:
            brain_client = await SomaBrainClient.get_async()
            if brain_client:
                await self._cb_somabrain.call(
                    brain_client.brain_sleep_mode,
                    "deep",
                    ttl_seconds=600,
                )
                logger.info("Sleep cycle triggered for persona=%s", persona_id)
        except Exception as exc:
            logger.debug("Sleep cycle trigger skipped: %s", exc)


# =============================================================================
# Module-level helpers
# =============================================================================


def background_task_done_callback(task_name: str):
    """Create a callback that logs exceptions from background tasks.

    Usage:
        task = asyncio.create_task(...)
        task.add_done_callback(background_task_done_callback("task_name"))
    """

    def _callback(task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.error("Background task %s failed: %s", task_name, exc, exc_info=True)

    return _callback


async def load_neuromodulators(agent_id: str, user_context: dict) -> None:
    """Load neuromodulator baseline from Capsule."""
    from admin.core.models import Capsule

    @sync_to_async
    def _get():
        c = Capsule.objects.filter(id=agent_id).first()
        return c.neuromodulator_baseline if c else None

    try:
        baseline = await _get()
        neuro = baseline or {
            "dopamine": 0.5,
            "serotonin": 0.5,
            "norepinephrine": 0.5,
            "acetylcholine": 0.5,
        }
        logger.info("[GMD] Neuromodulators for %s: %s", agent_id[:8], neuro)
    except Exception as e:
        logger.warning("[GMD] Failed: %s", e)


__all__ = [
    "ChatContextManager",
    "ConversationSummary",
    "token_count",
    "make_coordinate",
    "to_langchain_messages",
    "background_task_done_callback",
    "load_neuromodulators",
]
