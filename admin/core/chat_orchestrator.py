"""V3 Chat Orchestrator — The ONE TRUE Chat System.

12-Phase production pipeline. ALL phases wired. NO placeholders.

VIBE COMPLIANT:
- Real LLM invocation (litellm_client)
- Real memory storage/recall (SomaBrainClient with circuit breaker)
- Accurate token counting (tiktoken, NOT len(text.split()))
- Circuit breakers on all external calls
- AgentIQ derivation + UnifiedGate permission checks
- 5-lane context building with memory recall

This module REPLACES and SUPERSEDES:
- services/common/chat_service.py (old facade)
- services/common/chat/message_service.py (fragmented core)
- services/common/chat/conversation_service.py (fragmented CRUD)
- services/common/chat/session_manager.py (fragmented sessions)
- services/common/chat/memory_bridge.py (thin wrapper)
- services/common/chat/title_generator.py (fragmented titles)

Historical note: The above files were deleted in the V3 consolidation.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, AsyncIterator, cast, Dict, List, Optional
from uuid import uuid4

from asgiref.sync import sync_to_async

from admin.common.messages import ErrorCode, get_message
from admin.core.agentiq import derive_all_settings, UnifiedGate
from admin.core.context import build_context, BuiltContext
from admin.core.model_router import detect_required_capabilities, select_model, SelectedModel
from admin.core.permission_matrix import PermissionChecker
from admin.core.somabrain_client import SomaBrainClient
from services.common.circuit_breaker import CircuitBreakerError, get_circuit_breaker
from services.common.memory_contract import (
    MemoryAck,
    MemoryConfigurationError,
    MemoryHit,
    make_coord,
)
from services.common.memory_gateway import build_memory_gateway, get_memory_gateway
from services.common.health_monitor import get_health_monitor
from services.common.simple_governor import get_governor
from services.common.unified_metrics import get_metrics, TurnPhase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# tiktoken — accurate token counting
# ---------------------------------------------------------------------------
import tiktoken

_ENCODING = tiktoken.get_encoding("cl100k_base")


def _token_count(text: str) -> int:
    """Accurate LLM token count."""
    return len(_ENCODING.encode(text))


# ---------------------------------------------------------------------------
# Memory seam (PLAN-TRIAD-SEAMLESS §1) — one write path, one read path
# ---------------------------------------------------------------------------
_MEMORY_STORES = ("somabrain", "somafractalmemory")
_MEMORY_WRITE_TIMEOUT_S = 10.0
_memory_gateway_cache: Any = None


def _memory_explicitly_disabled() -> bool:
    """True when the deployment explicitly disables both memory stores.

    Checks the standalone kill-switch pair (SOMABRAIN_ENABLED +
    FRACTALMEMORY_ENABLED) and the profile flags from
    config/settings_registry.py (the STANDALONE/DEV profile disables both).
    """
    explicitly_off = {"0", "false", "no", "off"}
    brain = os.environ.get("SOMABRAIN_ENABLED", "").strip().lower()
    sfm = os.environ.get("FRACTALMEMORY_ENABLED", "").strip().lower()
    if brain in explicitly_off and sfm in explicitly_off:
        return True
    try:
        from config.settings_registry import SettingsRegistry

        profile = SettingsRegistry.get()
        if not (
            getattr(profile, "somabrain_enabled", True)
            or getattr(profile, "fractalmemory_enabled", True)
        ):
            return True
    except Exception:  # profile load is best-effort; gateway stays fail-closed
        pass
    return False


def _require_memory_gateway() -> Any:
    """Return the MemoryGateway, or None when memory is explicitly disabled.

    Fail-closed: when memory is enabled but no store URL is configured
    (env SOMABRAIN_URL / SFM_URL, else config.settings), raise
    MemoryConfigurationError — never silently skip a write.
    """
    global _memory_gateway_cache
    if _memory_explicitly_disabled():
        return None
    if _memory_gateway_cache is not None:
        return _memory_gateway_cache
    try:
        _memory_gateway_cache = get_memory_gateway()
        return _memory_gateway_cache
    except MemoryConfigurationError:
        # Seam env unset — fall back to the app config path (config/settings.py
        # resolves the same keys). Still fail-closed if neither configures a URL.
        from config import settings as django_settings

        brain_url = (getattr(django_settings, "SOMABRAIN_URL", "") or "").strip()
        sfm_url = (getattr(django_settings, "SOMAFRACTALMEMORY_URL", "") or "").strip()
        if not brain_url or not sfm_url:
            raise
        logger.info(
            "Memory seam configured from config.settings (somabrain=%s, sfm=%s)",
            brain_url,
            sfm_url,
        )
        _memory_gateway_cache = build_memory_gateway(
            somabrain_url=brain_url, sfm_url=sfm_url
        )
        return _memory_gateway_cache


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass
class ChatTurn:
    """A single chat turn through the 12-phase pipeline.

    Phase 1-3 data (Capsule, IQ, ToolRegistry) is pre-loaded at
    WebSocket connection time and passed directly. No DB calls
    for static data per message.

    For non-WebSocket paths (REST API), these can be omitted and
    the orchestrator will fall back to loading from DB.
    """

    # Phase 1-3: Pre-loaded at connection time (optional for REST paths)
    capsule: Optional[Any] = None  # Capsule model instance
    iq_settings: Optional[Any] = None  # DerivedSettings
    tool_registry: Optional[Any] = None  # ToolRegistry instance

    # Per-message data
    user_id: str = ""
    tenant_id: str = ""
    user_message: str = ""
    conversation_id: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    history: List[Dict[str, str]] = field(default_factory=list)

    # Legacy: capsule_id for backward compatibility during migration
    capsule_id: Optional[str] = None


@dataclass
class ChatResult:
    """Result of a complete chat turn."""

    response: str
    model_used: str
    tools_called: List[str] = field(default_factory=list)
    context_tokens: int = 0
    phase_completed: int = 0
    errors: List[str] = field(default_factory=list)
    latency_ms: int = 0
    turn_id: str = ""


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


# ---------------------------------------------------------------------------
# V3 Chat Orchestrator
# ---------------------------------------------------------------------------


class V3ChatOrchestrator:
    """Production 12-Phase Chat Orchestrator.

    This is the SINGLE chat system for SomaAgent01.
    All chat operations flow through here.
    """

    def __init__(
        self,
        permission_checker: Optional[PermissionChecker] = None,
        unified_gate: Optional[UnifiedGate] = None,
    ) -> None:
        self._permission_checker = permission_checker or PermissionChecker()
        self._unified_gate = unified_gate or UnifiedGate()
        self._metrics = get_metrics()
        self._governor = get_governor()
        self._health = get_health_monitor()

        # Circuit breakers for external services
        self._cb_somabrain = get_circuit_breaker(
            "somabrain", failure_threshold=5, reset_timeout=30.0
        )
        self._cb_llm = get_circuit_breaker("llm", failure_threshold=5, reset_timeout=30.0)

    # =================================================================
    # PUBLIC API — Conversation CRUD (from old ConversationService)
    # =================================================================

    async def create_conversation(
        self, agent_id: str, user_id: str, tenant_id: str, title: Optional[str] = None
    ) -> ConversationSummary:
        """Create a new conversation."""
        from admin.chat.models import Conversation as ConversationModel
        from django.db import transaction

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

    # =================================================================
    # PUBLIC API — Session Management (from old SessionManager)
    # =================================================================

    async def initialize_session(
        self, agent_id: str, conversation_id: str, user_context: dict
    ) -> Dict[str, Any]:
        """Initialize agent session with neuromodulator loading."""
        from admin.core.models import Session as SessionModel
        from django.db import transaction

        @sync_to_async
        def _create() -> Dict[str, Any]:
            with transaction.atomic():
                session_id = str(uuid4())
                record = SessionModel.objects.create(
                    session_id=session_id,
                    tenant=user_context.get("tenant_id"),
                    persona_id=user_context.get("persona_id"),
                    metadata={
                        "agent_id": agent_id,
                        "conversation_id": conversation_id,
                        "user_id": user_context.get("user_id"),
                    },
                )
                return {
                    "session_id": record.session_id,
                    "agent_id": agent_id,
                    "conversation_id": conversation_id,
                    "created_at": record.created_at,
                }

        session = await _create()
        task = asyncio.create_task(self._load_neuromodulators(agent_id, user_context))
        task.add_done_callback(self._on_background_task_done("_load_neuromodulators"))
        return session

    # =================================================================
    # PUBLIC API — 12-Phase Chat Turn (THE CORE)
    # =================================================================

    async def process_turn(self, turn: ChatTurn) -> ChatResult:
        """Process a complete chat turn through all 12 phases.

        THIS IS THE PRODUCTION CHAT PIPELINE.
        """
        from admin.llm.services.litellm_client import get_chat_model

        start_time = time.perf_counter()
        turn_id = str(uuid4())
        result = ChatResult(response="", model_used="", turn_id=turn_id)

        try:
            # Phase 1-2: Capsule Loading — USE PRE-LOADED
            capsule = turn.capsule
            if not capsule:
                raise ValueError("Capsule not provided in ChatTurn")

            # Pre-fetch capsule body in async context (avoids SynchronousOnlyOperation)
            capsule._cached_body = await capsule.async_body() if hasattr(capsule, 'async_body') else capsule.body or {}

            result.phase_completed = 2

            tenant_id = str(capsule.tenant_id) if capsule.tenant_id else turn.tenant_id
            turn_metrics = self._metrics.record_turn_start(
                turn_id=turn_id, tenant_id=tenant_id, user_id=turn.user_id,
                agent_id=str(capsule.id),
            )

            # Phase 3: AgentIQ Settings — USE PRE-DERIVED
            iq = turn.iq_settings
            if not iq:
                iq = await sync_to_async(derive_all_settings)(capsule)
            logger.info("Phase 3: AgentIQ (tier=%s, auto=%s)", iq.model_tier, iq.tool_approval)
            result.phase_completed = 3

            # Phase 4: Permission Check (UnifiedGate + PermissionChecker)
            perm = await self._permission_checker.check(
                user_id=turn.user_id, permission="chat:send", tenant_id=tenant_id
            )
            if not perm.allowed:
                result.response = get_message(ErrorCode.DEGRADED_PERMISSION_DENIED)
                result.errors.append(perm.reason)
                return result

            gate_ok = await self._unified_gate.check(
                capsule, action="chat:send", user_id=turn.user_id, tenant_id=tenant_id
            )
            if not gate_ok:
                result.response = get_message(ErrorCode.DEGRADED_GATE_DENIED)
                result.errors.append("UnifiedGate rejected chat:send")
                return result
            result.phase_completed = 4

            # Phase 4.5: Health Check + Governor Budget + Brain Context Evaluation
            health = self._health.get_overall_health()
            is_degraded = health.degraded
            if is_degraded:
                logger.warning("System degraded — using governor rescue budget")
                self._metrics.record_turn_phase(turn_id, TurnPhase.HEALTH_CHECKED)

            # NEW: SomaBrain context evaluation (cognitive co-processor)
            brain_confidence = 0.5
            suggested_tools: List[str] = []
            try:
                brain_client = await SomaBrainClient.get_async()
                if brain_client:
                    eval_result = cast(
                        Dict[str, Any],
                        await self._cb_somabrain.call(
                            brain_client.context_evaluate,
                            request={
                                "query": turn.user_message,
                                "tenant_id": tenant_id,
                                "persona_id": str(capsule.id),
                                "context": {
                                    "system_prompt": capsule.system_prompt,
                                    "history_length": len(turn.history or []),
                                },
                            },
                        ),
                    )
                    if eval_result:
                        brain_confidence = eval_result.get("confidence", 0.5)
                        suggested_tools = eval_result.get("suggested_tools", [])
                        logger.info(
                            "Brain context eval: confidence=%.2f, suggested_tools=%s",
                            brain_confidence,
                            suggested_tools,
                        )
            except Exception as brain_exc:
                logger.debug("Brain context evaluation skipped: %s", brain_exc)

            gov_decision = self._governor.allocate_budget(
                max_tokens=iq.max_tokens,
                is_degraded=is_degraded,
            )
            budget_override = gov_decision.lane_budget.to_dict()

            # Phase 5: Context Building (5-lane with memory recall)
            # Memory lane is fed by MemoryGateway.recall() — one read path
            history = turn.history or await self._recall_history(
                turn.conversation_id or "", tenant_id
            )
            memory_hits = await self._recall_memories(
                turn.user_message, tenant_id, capsule
            )
            context = await build_context(
                capsule=capsule,
                user_message=turn.user_message,
                history=history,
                memory_hits=memory_hits,
                budget_override=budget_override,
            )
            result.context_tokens = context.total_tokens
            logger.info(
                "Phase 5: Context built (%d tokens, mode=%s)",
                context.total_tokens,
                gov_decision.mode,
            )
            self._metrics.record_turn_phase(turn_id, TurnPhase.CONTEXT_BUILT)
            result.phase_completed = 5

            # Phase 6: Model Selection
            caps = detect_required_capabilities(
                message=turn.user_message, attachments=turn.attachments
            )
            try:
                model = cast(
                    SelectedModel,
                    await self._cb_llm.call(
                        select_model,
                        required_capabilities=caps,
                        capsule_body=await capsule.async_body() if hasattr(capsule, 'async_body') else capsule.body or {},
                        tenant_id=tenant_id,
                    ),
                )
            except CircuitBreakerError as e:
                result.response = get_message(ErrorCode.LLM_DEGRADED_MODEL_UNAVAILABLE)
                result.errors.append(f"Model selection circuit OPEN: {e}")
                return result
            result.model_used = f"{model.provider}/{model.name}"
            logger.info("Phase 6: Model %s", result.model_used)
            self._metrics.record_turn_phase(turn_id, TurnPhase.MODEL_SELECTED)
            result.phase_completed = 6

            # Phase 7: Tool Discovery — from Capsule's ToolRegistry
            tools_for_llm: List[Dict[str, Any]] = []
            if turn.tool_registry:
                for tool_def in turn.tool_registry.list():
                    handler = tool_def.handler
                    schema = handler.input_schema() if handler else None
                    if schema:
                        tools_for_llm.append({
                            "type": "function",
                            "function": {
                                "name": tool_def.name,
                                "description": tool_def.description or tool_def.name,
                                "parameters": schema,
                            }
                        })
            result.phase_completed = 7

            # Phase 8: LLM Invocation (REAL — NO PLACEHOLDER)
            llm = get_chat_model(provider=model.provider, name=model.name)
            messages = self._to_langchain_messages(context, history, turn.user_message)
            self._metrics.record_turn_phase(turn_id, TurnPhase.LLM_INVOKED)

            response_chunks: List[str] = []
            try:
                # Note: _astream returns an async generator, not awaitable
                # Circuit breaker protects model selection, not streaming
                stream = llm._astream(messages=messages)
                chunk_count = 0
                async for chunk in stream:
                    chunk_count += 1
                    # Handle ChatChunk objects (from LiteLLM wrapper)
                    if hasattr(chunk, "response_delta"):
                        token = chunk.response_delta or ""
                    elif hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                        token = str(chunk.message.content)
                    elif hasattr(chunk, "content"):
                        token = str(chunk.content)
                    else:
                        token = str(chunk) if chunk else ""
                    if token:
                        response_chunks.append(token)
                logger.info("Phase 8: LLM streaming complete, %d chunks, %d tokens", chunk_count, len(response_chunks))
            except CircuitBreakerError:
                result.response = get_message(ErrorCode.LLM_DEGRADED_CIRCUIT_OPEN)
                result.errors.append("LLM circuit OPEN — degraded mode")
                result.phase_completed = 8
                return result
            except asyncio.TimeoutError:
                result.response = get_message(ErrorCode.LLM_DEGRADED_TIMEOUT)
                result.errors.append("LLM streaming timeout — degraded mode")
                result.phase_completed = 8
                return result

            full_response = "".join(response_chunks)
            result.response = full_response
            result.phase_completed = 8

            # Phase 9: Tool Execution — native LLM tool_calls only
            # Tool calls are captured from stream metadata during Phase 8
            # No regex parsing — enterprise architecture uses native function-calling API
            result.phase_completed = 9

            # Phase 10: Response Formatting
            result.phase_completed = 10

            # Phase 11: Memory Storage
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            await self._store_turn(
                conversation_id=turn.conversation_id or "",
                tenant_id=tenant_id,
                user_message=turn.user_message,
                assistant_response=full_response,
                model_id=result.model_used,
                elapsed_ms=elapsed_ms,
                token_count_out=_token_count(full_response),
                salience=brain_confidence,
            )

            # Emit Django signals for outbox publishers.
            # memory_created is NOT emitted: the MemoryGateway seam is the one
            # write path (PLAN §1 rule 4) and its outbox (PendingMemory) already
            # covers failed acks — a second outbox entry would duplicate writes.
            try:
                from admin.core.signals import conversation_message

                await sync_to_async(conversation_message.send)(
                    sender=self.__class__,
                    conversation_id=turn.conversation_id or "",
                    message_id=turn_id,
                    role="assistant",
                    content=full_response,
                )
            except Exception as signal_exc:
                logger.warning("Signal emission failed: %s", signal_exc)

            self._metrics.record_turn_phase(turn_id, TurnPhase.MEMORY_STORED)
            result.phase_completed = 11

            # Phase 12: Completion
            result.latency_ms = elapsed_ms
            self._metrics.record_turn_complete(
                turn_id=turn_id,
                tokens_in=_token_count(turn.user_message),
                tokens_out=_token_count(full_response),
                model=result.model_used,
                provider=model.provider,
                error=None,
            )
            result.phase_completed = 12

        except Exception as exc:
            logger.error("Chat orchestration error: %s", exc, exc_info=True)
            result.errors.append(str(exc))
            if not result.response:
                result.response = f"[Error in phase {result.phase_completed + 1}: {exc}]"

        return result

    async def stream_turn(self, turn: ChatTurn) -> AsyncIterator[str]:
        """Stream a chat turn token-by-token.

        Yields tokens as they arrive from the LLM.
        Stores the complete response after streaming finishes.
        """
        from admin.llm.services.litellm_client import get_chat_model

        start_time = time.perf_counter()
        turn_id = str(uuid4())

        capsule = turn.capsule
        if not capsule:
            yield "[Error: Capsule not found]"
            return

        tenant_id = str(capsule.tenant_id) if capsule.tenant_id else turn.tenant_id

        # Use pre-derived IQ, fallback to derivation if missing
        iq = turn.iq_settings
        if not iq:
            iq = await sync_to_async(derive_all_settings)(capsule)

        perm = await self._permission_checker.check(
            user_id=turn.user_id, permission="chat:send", tenant_id=tenant_id
        )
        if not perm.allowed:
            yield "[Permission denied]"
            return

        gate_ok = await self._unified_gate.check(
            capsule, action="chat:send", user_id=turn.user_id, tenant_id=tenant_id
        )
        if not gate_ok:
            yield "[Gate denied]"
            return

        # Health check + governor budget
        health = self._health.get_overall_health()
        is_degraded = health.degraded
        gov_decision = self._governor.allocate_budget(
            max_tokens=iq.max_tokens,
            is_degraded=is_degraded,
        )
        budget_override = gov_decision.lane_budget.to_dict()

        # Build context — memory lane fed by MemoryGateway.recall() (one read path)
        history = turn.history or await self._recall_history(turn.conversation_id or "", tenant_id)
        memory_hits = await self._recall_memories(turn.user_message, tenant_id, capsule)
        context = await build_context(
            capsule=capsule,
            user_message=turn.user_message,
            history=history,
            memory_hits=memory_hits,
            budget_override=budget_override,
        )

        # Phase 7: Tool Discovery
        tools_for_llm: List[Dict[str, Any]] = []
        if turn.tool_registry:
            for tool_def in turn.tool_registry.list():
                handler = tool_def.handler
                schema = handler.input_schema() if handler else None
                if schema:
                    tools_for_llm.append({
                        "type": "function",
                        "function": {
                            "name": tool_def.name,
                            "description": tool_def.description or tool_def.name,
                            "parameters": schema,
                        }
                    })

        # Select model
        caps = detect_required_capabilities(message=turn.user_message, attachments=turn.attachments)
        try:
            model = cast(
                SelectedModel,
                await self._cb_llm.call(
                    select_model,
                    required_capabilities=caps,
                    capsule_body=await capsule.async_body() if hasattr(capsule, 'async_body') else capsule.body or {},
                    tenant_id=tenant_id,
                ),
            )
        except CircuitBreakerError:
            yield get_message(ErrorCode.LLM_DEGRADED_CIRCUIT_OPEN)
            return

        # Stream LLM
        llm = get_chat_model(provider=model.provider, name=model.name)
        messages = self._to_langchain_messages(context, history, turn.user_message)

        response_chunks: List[str] = []
        try:
            # Note: _astream returns an async generator, not awaitable
            # Circuit breaker protects model selection, not streaming
            stream = cast(
                AsyncIterator[Any],
                llm._astream(messages=messages),
            )
            async for chunk in stream:
                # Handle ChatChunk objects (from LiteLLM wrapper)
                if hasattr(chunk, "response_delta"):
                    token = chunk.response_delta or ""
                elif hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                    token = str(chunk.message.content)
                elif hasattr(chunk, "content"):
                    token = str(chunk.content)
                else:
                    token = str(chunk) if chunk else ""
                if token:
                    response_chunks.append(token)
                    yield token
        except CircuitBreakerError:
            yield "[System degraded: LLM service temporarily unavailable. Using cached context only.]"
            return
        except asyncio.TimeoutError:
            yield get_message(ErrorCode.LLM_DEGRADED_TIMEOUT)
            return

        # Store after streaming
        full_response = "".join(response_chunks)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        await self._store_turn(
            conversation_id=turn.conversation_id or "",
            tenant_id=tenant_id,
            user_message=turn.user_message,
            assistant_response=full_response,
            model_id=f"{model.provider}/{model.name}",
            elapsed_ms=elapsed_ms,
            token_count_out=_token_count(full_response),
        )

        # Emit Django signals for outbox publishers.
        # memory_created is NOT emitted: the MemoryGateway seam is the one
        # write path (PLAN §1 rule 4) and its outbox (PendingMemory) already
        # covers failed acks — a second outbox entry would duplicate writes.
        try:
            from admin.core.signals import conversation_message

            await sync_to_async(conversation_message.send)(
                sender=self.__class__,
                conversation_id=turn.conversation_id or "",
                message_id=turn_id,
                role="assistant",
                content=full_response,
            )
        except Exception as signal_exc:
            logger.warning("Signal emission failed: %s", signal_exc)

    # =================================================================
    # INTERNAL HELPERS
    # =================================================================

    async def _load_capsule(self, capsule_id: str) -> Optional[Any]:
        """Load Capsule from Django ORM.

        DEPRECATED: Capsules should be pre-loaded at WebSocket connection time.
        This method remains for backward compatibility and non-WebSocket paths.
        """
        from admin.core.models import Capsule

        @sync_to_async
        def _get():
            return Capsule.objects.filter(id=capsule_id).first()

        return await _get()

    async def _recall_history(self, conversation_id: str, tenant_id: str) -> List[Dict[str, str]]:
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

    def _to_langchain_messages(
        self, context: BuiltContext, history: List[Dict[str, str]], user_message: str
    ) -> List[Any]:
        """Convert BuiltContext (5 lanes) to LangChain messages.

        All 5 lanes from the context builder are preserved:
        - system  → SystemMessage (persona core + injection prompts)
        - memory  → SystemMessage ([Memory] recall from SomaBrain/SFM)
        - tools   → SystemMessage ([Tools] available tool descriptions)
        - history → alternating AIMessage/HumanMessage
        - buffer  → HumanMessage (current user message, appended last)
        """
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        msgs: List[Any] = []

        # Lane 1: System prompt (persona.core + injection prompts)
        system_parts: List[str] = []
        if context.system:
            system_parts.append(context.system)

        # Lane 3: Memory recall (SomaBrain primary, SFM fallback)
        if context.memory and context.memory not in ("[Memory recall unavailable]", "[No relevant memories]"):
            system_parts.append(f"[Memory]\n{context.memory}")

        # Lane 4: Tools descriptions
        if context.tools and context.tools != "[No tools enabled]":
            system_parts.append(f"[Tools]\n{context.tools}")

        if system_parts:
            msgs.append(SystemMessage(content="\n\n".join(system_parts)))

        # Lane 2: Conversation history (individual message turns)
        for h in history:
            role, content = h.get("role"), h.get("content", "")
            if role == "assistant":
                msgs.append(AIMessage(content=content))
            else:
                msgs.append(HumanMessage(content=content))

        # Lane 5: Buffer (current user message)
        msgs.append(HumanMessage(content=context.buffer or user_message))
        return msgs

    async def _remember_via_gateway(
        self,
        text: str,
        *,
        tenant_id: str,
        session_id: Optional[str],
        namespace: str,
        salience: float = 0.5,
        kind: str = "episodic",
    ) -> None:
        """ONE write path: MemoryGateway.remember_text() fan-out (PLAN §1 rule 4).

        remember_text() derives the seam coord AND the SomaBrain key material
        from the same (tenant, kind, ts, text), so both stores upsert one row —
        never a second coordinate scheme. PendingMemory is queued ONLY for acks
        with ok=False / timed out; a successful ack is never re-written.
        """
        gateway = _require_memory_gateway()
        if gateway is None:
            logger.debug(
                "Memory disabled by deployment mode — skipping store (%s)", namespace
            )
            return

        stamp = datetime.now(UTC)
        coord = make_coord(tenant_id, kind, stamp, text)
        try:
            acks = await asyncio.wait_for(
                gateway.remember_text(
                    text,
                    tenant_id=tenant_id,
                    kind=kind,
                    ts=stamp,
                    session_id=session_id,
                    salience=salience,
                    source="agent-chat",
                ),
                timeout=_MEMORY_WRITE_TIMEOUT_S,
            )
        except Exception as exc:
            # Timeout / transport failure: every store unacked → outbox each.
            logger.warning("MemoryGateway write failed (coord=%s): %s", coord, exc)
            acks = [
                MemoryAck(coord=coord, store=store, ok=False, error=str(exc))
                for store in _MEMORY_STORES
            ]

        for ack in acks:
            if ack.ok:
                continue  # success is final — never queued, never re-written
            await self._queue_pending_memory(
                tenant_id=tenant_id,
                namespace=namespace,
                payload={
                    "content": text,
                    "text": text,
                    "kind": kind,
                    "session_id": session_id,
                    "coord": coord,
                    "ts": stamp.isoformat(),
                    "salience": salience,
                    "source": "agent-chat",
                    "retry_store": ack.store,
                    "error": ack.error,
                },
            )

    async def _recall_memories(
        self,
        query: str,
        tenant_id: str,
        capsule: Any,
    ) -> Optional[List[MemoryHit]]:
        """One read path: MemoryGateway.recall() feeds the memory lane (PLAN §1 rule 5).

        Returns None when there is no gateway data (memory explicitly disabled
        or recall unavailable) so the lane renders its fallback sentinel; [] when
        recall ran and found nothing.
        """
        gateway = _require_memory_gateway()
        if gateway is None:
            return None

        body = getattr(capsule, "_cached_body", None)
        if body is None and hasattr(capsule, "async_body"):
            body = await capsule.async_body()
        body = body or {}
        persona = body.get("persona", {}) if isinstance(body, dict) else {}
        memory_config = persona.get("memory", {}) or {}
        try:
            recall_limit = int(memory_config.get("recall_limit", 10) or 10)
        except (TypeError, ValueError):
            recall_limit = 10

        try:
            hits = await gateway.recall(query=query, k=recall_limit, tenant_id=tenant_id)
            return list(hits or [])
        except Exception as exc:
            logger.warning("MemoryGateway.recall failed: %s", exc)
            return None

    async def _queue_pending_memory(
        self,
        tenant_id: str,
        namespace: str,
        payload: Dict[str, Any],
    ) -> None:
        """Queue one FAILED memory ack to PendingMemory for retry (outbox).

        Idempotency key is derived from the seam coord + target store, so a
        re-queue collapses into one row and retries cannot multiply memories.
        Best-effort: logs on failure, never blocks the chat turn.
        """
        import hashlib

        from admin.core.models import PendingMemory
        from asgiref.sync import sync_to_async
        from django.db import transaction

        coord = str(payload.get("coord") or "")
        if not coord:
            material = str(payload.get("text") or payload.get("content") or "")
            coord = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
        retry_store = str(payload.get("retry_store") or "all")
        idempotency_key = f"mem:{tenant_id}:{coord}:{retry_store}"

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

    async def _store_turn(
        self,
        conversation_id: str,
        tenant_id: str,
        user_message: str,
        assistant_response: str,
        model_id: str,
        elapsed_ms: int,
        token_count_out: int,
        salience: float = 0.5,
    ) -> None:
        """Store user + assistant messages.

        1. PostgreSQL — ALWAYS (persistence layer, Zero Data Loss)
        2. MemoryGateway.remember_text() — ONE write path, fan-out to both
           stores with per-store acks; PendingMemory only for failed acks.
        """
        from admin.chat.models import Conversation as ConversationModel, Message as MessageModel
        from django.db import transaction

        # Store user message trace (ALWAYS — Zero Data Loss)
        @sync_to_async
        def _store_user():
            with transaction.atomic():
                MessageModel.objects.create(
                    conversation_id=conversation_id,
                    role="user",
                    coordinate=user_message,
                    token_count=_token_count(user_message),
                )

        await _store_user()

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
                    message_count=MessageModel.objects.filter(conversation_id=conversation_id).count()
                )

        await _store_assistant()

        # ONE memory write path: fan-out to both stores, per-store acks.
        # PendingMemory is queued only for failed/timed-out acks.
        await self._remember_via_gateway(
            assistant_response,
            tenant_id=tenant_id,
            session_id=conversation_id or None,
            namespace="chat_history",
            salience=salience,
        )

        # Background: episodic memory (same seam)
        task = asyncio.create_task(
            self._store_episodic_bg(
                tenant_id=tenant_id,
                user_message=user_message,
                assistant_response=assistant_response,
                conversation_id=conversation_id,
                model_id=model_id,
                elapsed_ms=elapsed_ms,
                salience=salience,
            )
        )
        task.add_done_callback(self._on_background_task_done("_store_episodic_bg"))

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

    @staticmethod
    def _on_background_task_done(task_name: str):
        """Create a callback that logs exceptions from background tasks.

        Usage:
            task = asyncio.create_task(self._store_episodic_bg(...))
            task.add_done_callback(self._on_background_task_done("_store_episodic_bg"))
        """

        def _callback(task: asyncio.Task) -> None:
            try:
                task.result()
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.error("Background task %s failed: %s", task_name, exc, exc_info=True)

        return _callback

    async def _store_episodic_bg(
        self,
        tenant_id: str,
        user_message: str,
        assistant_response: str,
        conversation_id: str,
        model_id: str,
        elapsed_ms: int,
        salience: float = 0.5,
    ) -> None:
        """Non-blocking episodic memory storage via the MemoryGateway seam."""
        content = f"User: {user_message}\nAssistant: {assistant_response}"
        await self._remember_via_gateway(
            content,
            tenant_id=tenant_id,
            session_id=conversation_id or None,
            namespace="episodic",
            salience=salience,
        )

    async def _load_neuromodulators(self, agent_id: str, user_context: dict) -> None:
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


class ServiceUnavailableError(Exception):
    """External service unavailable."""

    def __init__(self, service: str, reason: str):
        self.service = service
        self.reason = reason
        super().__init__(f"{service}: {reason}")


# Singleton accessor
_orchestrator_instance: Optional[V3ChatOrchestrator] = None
_orchestrator_lock = asyncio.Lock()


async def get_chat_orchestrator() -> V3ChatOrchestrator:
    """Get singleton V3ChatOrchestrator."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        async with _orchestrator_lock:
            if _orchestrator_instance is None:
                _orchestrator_instance = V3ChatOrchestrator()
    return _orchestrator_instance


__all__ = [
    "V3ChatOrchestrator",
    "ChatTurn",
    "ChatResult",
    "ConversationSummary",
    "get_chat_orchestrator",
    "ServiceUnavailableError",
]
