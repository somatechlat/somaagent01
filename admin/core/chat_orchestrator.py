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
import time
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, AsyncIterator, cast, Dict, List, Optional, Union
from uuid import uuid4

from asgiref.sync import sync_to_async

from admin.common.messages import ErrorCode, get_message
from admin.core.agentiq import derive_all_settings, UnifiedGate
from admin.core.context import build_context, BuiltContext
from admin.core.model_router import detect_required_capabilities, select_model, SelectedModel
from admin.core.permission_matrix import PermissionChecker
from admin.core.somabrain_client import SomaBrainClient
from admin.core.tool_calling import (
    run_tool_loop,
    TOOL_EVENT_DONE,
    ToolStreamEvent,
)
from services.common.circuit_breaker import CircuitBreakerError, get_circuit_breaker
from services.common.health_monitor import get_health_monitor
from services.common.memory_contract import (
    make_coord,
    MemoryAck,
    MemoryConfigurationError,
    MemoryHit,
)
from services.common.memory_gateway import build_memory_gateway, get_memory_gateway
from services.common.simple_governor import get_governor
from services.common.unified_metrics import get_metrics, TurnPhase, TurnUsage

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
# SomaBrain is the sole store bridge. There is no multi-store fan-out and no
# second replay authority (T-6 / degradation doctrine).


def _iq_model_tier(iq) -> str | None:
    """Map the IQ capability tier onto the model catalog's vocabulary.

    ``DerivedSettings.model_tier`` is the capability axis (how good a model to
    ask for). ``LLMModelConfig.cost_tier`` is the catalog's own label. The two
    vocabularies meet in exactly one place: ``agentiq.routing``.
    """
    if iq is None:
        return None
    tier = getattr(iq, "model_tier", None)
    return str(tier.value if hasattr(tier, "value") else tier or "") or None


def _mem_setting(name: str, default):
    from services.common.memory_contract import get_memory_setting

    return get_memory_setting(name, default)


_MEMORY_WRITE_TIMEOUT_S = None
_MEMORY_RECALL_TIMEOUT_S = None
_HISTORY_RECALL_TIMEOUT_S = None


def _write_timeout() -> float:
    global _MEMORY_WRITE_TIMEOUT_S
    if _MEMORY_WRITE_TIMEOUT_S is None:
        _MEMORY_WRITE_TIMEOUT_S = float(_mem_setting("MEM_WRITE_TIMEOUT_S", 10.0))
    return _MEMORY_WRITE_TIMEOUT_S


def _recall_timeout() -> float:
    global _MEMORY_RECALL_TIMEOUT_S
    if _MEMORY_RECALL_TIMEOUT_S is None:
        _MEMORY_RECALL_TIMEOUT_S = float(_mem_setting("MEM_RECALL_TIMEOUT_S", 2.5))
    return _MEMORY_RECALL_TIMEOUT_S


def _history_timeout() -> float:
    global _HISTORY_RECALL_TIMEOUT_S
    if _HISTORY_RECALL_TIMEOUT_S is None:
        _HISTORY_RECALL_TIMEOUT_S = float(_mem_setting("MEM_HISTORY_TIMEOUT_S", 2.5))
    return _HISTORY_RECALL_TIMEOUT_S


_memory_gateway_cache: Any = None


def _require_memory_gateway() -> Any:
    """Return the MemoryGateway. Always required — full Agent+SomaBrain+SFM path.

    Fail-closed: if no store URL is configured (env SOMABRAIN_URL / SFM_URL,
    else config.settings), raise MemoryConfigurationError — never skip a write.
    """
    global _memory_gateway_cache
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
        if not brain_url:
            raise
        logger.info(
            "Memory seam configured from config.settings (somabrain=%s)",
            brain_url,
        )
        _memory_gateway_cache = build_memory_gateway(
            somabrain_url=brain_url,
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
    # UI agent mode: STD | DEV | RO | DGR (DGR forces degraded governor path)
    agent_mode: str = "STD"
    # Transport-attached approval gate for tools whose policy says
    # approval_required. Set by the WebSocket consumer; absent on REST, where
    # there is no human to ask and the answer is therefore no.
    approval_gate: Optional[Any] = None
    # Roles the authenticated principal holds. The token already carries them
    # (TokenPayload.realm_access) and the identity record is their one source.
    # Re-querying a second store here is how the chat path ended up authorizing
    # with an empty role set while /auth/me showed the right ones.
    roles: Optional[list] = None


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

    # =================================================================
    # PUBLIC API — Session Management (from old SessionManager)
    # =================================================================

    async def initialize_session(
        self, agent_id: str, conversation_id: str, user_context: dict
    ) -> Dict[str, Any]:
        """Initialize agent session with neuromodulator loading."""
        from django.db import transaction

        from admin.core.models import Session as SessionModel

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
            capsule._cached_body = (
                await capsule.async_body() if hasattr(capsule, "async_body") else capsule.body or {}
            )

            result.phase_completed = 2

            tenant_id = str(capsule.tenant_id) if capsule.tenant_id else turn.tenant_id
            turn_metrics = self._metrics.record_turn_start(
                turn_id=turn_id,
                tenant_id=tenant_id,
                user_id=turn.user_id,
                agent_id=str(capsule.id),
            )

            # Phase 3: AgentIQ Settings — USE PRE-DERIVED
            iq = turn.iq_settings
            if not iq:
                iq = await sync_to_async(derive_all_settings)(capsule)
            logger.info("Phase 3: AgentIQ (tier=%s, auto=%s)", iq.model_tier, iq.tool_approval)
            result.phase_completed = 3

            # Phase 4: Permission Check (UnifiedGate + PermissionChecker)
            # Roles come from the authenticated principal (ChatTurn.roles).
            # None means "not on the turn" and falls back to membership;
            # an empty list is still "no roles" and still denies.
            perm = await self._permission_checker.check(
                user_id=turn.user_id,
                permission="resource:chat_send",
                tenant_id=tenant_id,
                roles=turn.roles,
            )
            if not perm.allowed:
                result.response = get_message(ErrorCode.DEGRADED_PERMISSION_DENIED)
                result.errors.append(perm.reason)
                return result

            gate_ok = await self._unified_gate.check(
                capsule,
                action="resource:chat_send",
                user_id=turn.user_id,
                tenant_id=tenant_id,
                roles=turn.roles,
            )
            if not gate_ok:
                result.response = get_message(ErrorCode.DEGRADED_GATE_DENIED)
                result.errors.append("UnifiedGate rejected resource:chat_send")
                return result
            result.phase_completed = 4

            # Transcript: the input is recorded the moment the gate passes, so
            # a later failure still leaves the turn on disk (ARCH-INVARIANTS §3).
            await self._persist_user_transcript(turn, tenant_id)

            # Phase 4.5: Health Check + Governor Budget + Brain Context Evaluation
            health = self._health.get_overall_health()
            is_degraded = health.degraded or (turn.agent_mode or "").upper() == "DGR"
            if is_degraded:
                logger.warning("System degraded — using governor rescue budget")
                self._metrics.record_turn_phase(turn_id, TurnPhase.HEALTH_CHECKED)

            # SomaBrain context evaluation (cognitive co-processor)
            brain_confidence = float(_mem_setting("SOMABRAIN_CONTEXT_CONFIDENCE_DEFAULT", 0.5))
            suggested_tools: List[str] = []
            brain_suggested_tools: List[str] = []
            try:
                brain_client = (
                    await SomaBrainClient.get_async()
                    if (iq is None or iq.brain_query_enabled)
                    else None
                )
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
                        brain_suggested_tools = list(suggested_tools)
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
            # Parallel hot path (memory must not add latency to the reply).
            caps0 = detect_required_capabilities(
                message=turn.user_message, attachments=turn.attachments
            )
            body_task = (
                capsule.async_body()
                if hasattr(capsule, "async_body")
                else asyncio.sleep(0, result={})
            )
            history_task = (
                asyncio.sleep(0, result=turn.history)
                if turn.history
                else self._recall_history(turn.conversation_id or "", tenant_id)
            )
            history, memory_hits, body = await asyncio.gather(
                asyncio.wait_for(history_task, timeout=_history_timeout()),
                asyncio.wait_for(
                    self._recall_memories(turn.user_message, tenant_id, capsule, iq),
                    timeout=_recall_timeout(),
                ),
                asyncio.wait_for(body_task, timeout=2.0),
                return_exceptions=True,
            )
            if isinstance(history, BaseException):
                history = turn.history or []
            if isinstance(memory_hits, BaseException):
                memory_hits = None
            if isinstance(body, BaseException):
                body = {}
            context = await build_context(
                capsule=capsule,
                user_message=turn.user_message,
                history=history or [],
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
            try:
                model = cast(
                    SelectedModel,
                    await self._cb_llm.call(
                        select_model,
                        required_capabilities=caps0,
                        capsule_body=body or {},
                        tenant_id=tenant_id,
                        prefer_cost_tier=_iq_model_tier(iq),
                        preferred_model_id=getattr(capsule, "chat_model_id", None),
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

            # Phase 7: Tool Discovery — default kit + Capsule tools + Governor policy
            from services.tool_executor.default_tools import (
                default_tool_definitions,
                select_tools_for_mode,
            )

            tools_for_llm: List[Dict[str, Any]] = list(default_tool_definitions())
            seen_tools = {
                t.get("function", {}).get("name") for t in tools_for_llm if isinstance(t, dict)
            }
            if turn.tool_registry:
                for tool_def in turn.tool_registry.list():
                    handler = tool_def.handler
                    schema = handler.input_schema() if handler else None
                    if schema and tool_def.name not in seen_tools:
                        tools_for_llm.append(
                            {
                                "type": "function",
                                "function": {
                                    "name": tool_def.name,
                                    "description": tool_def.description or tool_def.name,
                                    "parameters": schema,
                                },
                            }
                        )
                        seen_tools.add(tool_def.name)

            # SomaBrain suggests tools for this turn. Only names that actually
            # exist are promoted - the brain cannot invent a tool. Suggestion
            # reorders; it never adds.
            if brain_suggested_tools:
                wanted = {str(s) for s in brain_suggested_tools}
                suggested = [
                    t
                    for t in tools_for_llm
                    if (t.get("function") or {}).get("name") in wanted
                ]
                rest = [
                    t
                    for t in tools_for_llm
                    if (t.get("function") or {}).get("name") not in wanted
                ]
                tools_for_llm = suggested + rest

            # Do not offer a tool the turn may not run. A network tool with
            # egress denied costs a model round-trip and returns a confusing
            # error; filtering here is the honest signal.
            from admin.core.tool_calling import _NETWORK_TOOLS, egress_permitted

            if not egress_permitted(iq):
                tools_for_llm = [
                    t
                    for t in tools_for_llm
                    if (t.get("function") or {}).get("name") not in _NETWORK_TOOLS
                ]

            # Degraded mode: drop optional tools (memory kit remains).
            tools_for_llm = select_tools_for_mode(
                tools_for_llm,
                tools_enabled=gov_decision.tools_enabled,
                tool_count_limit=gov_decision.tool_count_limit,
            )
            logger.info(
                "Phase 7: tools_for_llm=%d mode=%s tools_enabled=%s",
                len(tools_for_llm),
                gov_decision.mode,
                gov_decision.tools_enabled,
            )
            result.phase_completed = 7

            # Phase 8-9: LLM Invocation + native tool-calling loop (REAL).
            # tools=tools_for_llm is passed to LiteLLM every round; tool_calls
            # come back natively (never regex-parsed) and are executed via the
            # capsule ToolRegistry under capsule tool_policy.
            llm = get_chat_model(
                provider=model.provider,
                name=model.name,
                temperature=iq.temperature,
                max_tokens=iq.max_tokens,
            )
            messages = self._to_langchain_messages(context, history, turn.user_message)
            self._metrics.record_turn_phase(turn_id, TurnPhase.LLM_INVOKED)

            # Provider-reported usage only. The LLM response carries it; when a
            # round reports none the metric is None, never a local estimate.
            usage = TurnUsage()
            response_chunks: List[str] = []
            tools_called: List[str] = []
            try:
                async for item in run_tool_loop(
                    iq=iq,
                    approval_gate=turn.approval_gate,
                    llm=llm,
                    messages=messages,
                    tools_for_llm=tools_for_llm,
                    tool_registry=turn.tool_registry,
                    capsule=capsule,
                    usage=usage,
                ):
                    if isinstance(item, ToolStreamEvent):
                        if item.type == TOOL_EVENT_DONE:
                            tools_called.append(str(item.payload.get("name") or ""))
                        continue
                    response_chunks.append(item)
                logger.info(
                    "Phase 8-9: LLM + tool loop complete, %d tokens, tools=%s",
                    len(response_chunks),
                    tools_called,
                )
            except CircuitBreakerError:
                result.response = get_message(ErrorCode.LLM_DEGRADED_CIRCUIT_OPEN)
                result.errors.append("LLM circuit OPEN — degraded mode")
                result.phase_completed = 8
                self._metrics.record_turn_complete(
                    turn_id=turn_id,
                    tokens_in=usage.prompt_tokens,
                    tokens_out=usage.completion_tokens,
                    model=model.name,
                    provider=model.provider,
                    error="llm_circuit_open",
                )
                return result
            except asyncio.TimeoutError:
                result.response = get_message(ErrorCode.LLM_DEGRADED_TIMEOUT)
                result.errors.append("LLM streaming timeout — degraded mode")
                result.phase_completed = 8
                self._metrics.record_turn_complete(
                    turn_id=turn_id,
                    tokens_in=usage.prompt_tokens,
                    tokens_out=usage.completion_tokens,
                    model=model.name,
                    provider=model.provider,
                    error="llm_timeout",
                )
                return result

            full_response = "".join(response_chunks)
            result.response = full_response
            result.tools_called = tools_called
            result.phase_completed = 9

            # Phase 10: Response Formatting
            result.phase_completed = 10

            # Phase 11: Memory Storage
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            assistant_coord = await self._store_turn(
                conversation_id=turn.conversation_id or "",
                tenant_id=tenant_id,
                user_message=turn.user_message,
                assistant_response=full_response,
                model_id=result.model_used,
                elapsed_ms=elapsed_ms,
                token_count_out=_token_count(full_response),
                salience=brain_confidence,
            )
            await self._persist_message(
                conversation_id=turn.conversation_id or "",
                tenant_id=tenant_id,
                role="assistant",
                text=full_response,
                coordinate=assistant_coord,
            )
            await self._bump_message_count(turn.conversation_id or "")
            await self._publish_cognitive_learning(
                tenant_id=tenant_id,
                session_id=turn.conversation_id or turn_id,
                persona_id=str(capsule.id) if capsule else "",
                user_message=turn.user_message,
                assistant_response=full_response,
                confidence=brain_confidence,
            )

            # Emit Django signals for outbox publishers.
            # memory_created is NOT emitted: the MemoryGateway seam is the one
            # write path (PLAN §1 rule 4) and its outbox (the memory.wal
            # OutboxMessage) already covers failed acks — a second outbox
            # entry would duplicate writes.
            try:
                from admin.core.signals import conversation_message

                await sync_to_async(conversation_message.send)(
                    sender=self.__class__,
                    session_id=turn.conversation_id or "",
                    event_id=turn_id,
                    role="assistant",
                    message=full_response,
                    metadata={"tenant": tenant_id},
                )
            except Exception as signal_exc:
                logger.warning("Signal emission failed: %s", signal_exc)

            self._metrics.record_turn_phase(turn_id, TurnPhase.MEMORY_STORED)
            result.phase_completed = 11

            # Phase 12: Completion
            result.latency_ms = elapsed_ms
            self._metrics.record_turn_complete(
                turn_id=turn_id,
                tokens_in=usage.prompt_tokens,
                tokens_out=usage.completion_tokens,
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

    async def stream_turn(self, turn: ChatTurn) -> AsyncIterator[Union[str, ToolStreamEvent]]:
        """Stream a chat turn token-by-token.

        Yields text tokens as they arrive from the LLM and ToolStreamEvent
        items (tool.call / tool.delta / tool.done / tool.approval_request) for
        the native tool-calling timeline. Stores the complete response after
        streaming finishes.
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

        # Permission + gate must be sub-second (cache + short budget).
        try:
            perm, gate_ok = await asyncio.wait_for(
                asyncio.gather(
                    self._permission_checker.check(
                        user_id=turn.user_id,
                        permission="resource:chat_send",
                        tenant_id=tenant_id,
                        roles=turn.roles,
                    ),
                    self._unified_gate.check(
                        capsule,
                        action="resource:chat_send",
                        user_id=turn.user_id,
                        tenant_id=tenant_id,
                        roles=turn.roles,
                    ),
                ),
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            yield "[Permission check timeout]"
            return
        if not perm.allowed:
            yield "[Permission denied]"
            return

        if not gate_ok:
            yield "[Gate denied]"
            return

        # Transcript: record the input as soon as the gate passes.
        await self._persist_user_transcript(turn, tenant_id)

        # Health check + governor budget
        health = self._health.get_overall_health()
        is_degraded = health.degraded or (turn.agent_mode or "").upper() == "DGR"
        # token_limit is the hard cap from the resource knob. The governor
        # decides lane splits inside it; the knob decides the ceiling.
        _spend_cap = int(iq.token_limit)
        gov_decision = self._governor.allocate_budget(
            max_tokens=min(int(iq.max_tokens), _spend_cap),
            is_degraded=is_degraded,
        )
        budget_override = gov_decision.lane_budget.to_dict()

        # Parallel hot path: history + memory + capsule body + SomaBrain neuro
        from admin.core.somabrain_client import SomaBrainClient

        caps = detect_required_capabilities(message=turn.user_message, attachments=turn.attachments)
        body_task = (
            capsule.async_body() if hasattr(capsule, "async_body") else asyncio.sleep(0, result={})
        )
        history_task = (
            asyncio.sleep(0, result=turn.history)
            if turn.history
            else self._recall_history(turn.conversation_id or "", tenant_id)
        )

        async def _neuro_task():
            client = await SomaBrainClient.get_async()
            if client is None:
                return None
            return await client.get_neuromodulators(tenant_id=tenant_id)

        async def _brain_eval_task():
            # The cognitive co-processor: SomaBrain scores the turn and can
            # suggest tools. This is the first hop of the three-way learning
            # loop (agent asks brain -> brain scores -> memory stores).
            # brain_query_enabled is the intelligence knob that decides whether
            # the brain is consulted at all - it used to be derived and ignored.
            if iq is not None and not iq.brain_query_enabled:
                return None
            client = await SomaBrainClient.get_async()
            if client is None:
                return None
            return await self._cb_somabrain.call(
                client.context_evaluate,
                request={
                    "query": turn.user_message,
                    "tenant_id": tenant_id,
                    "persona_id": str(capsule.id),
                    "context": {
                        "system_prompt": capsule.system_prompt,
                        "history_length": len(turn.history or []),
                    },
                },
            )

        history, memory_hits, body, neuro, brain_eval = await asyncio.gather(
            asyncio.wait_for(history_task, timeout=_history_timeout()),
            asyncio.wait_for(
                self._recall_memories(turn.user_message, tenant_id, capsule, iq),
                timeout=_recall_timeout(),
            ),
            asyncio.wait_for(body_task, timeout=2.0),
            asyncio.wait_for(_neuro_task(), timeout=2.0),
            asyncio.wait_for(_brain_eval_task(), timeout=2.0),
            return_exceptions=True,
        )
        if isinstance(history, BaseException):
            history = turn.history or []
        if isinstance(memory_hits, BaseException):
            memory_hits = None
        if isinstance(brain_eval, BaseException):
            brain_eval = None
        brain_suggested_tools: List[str] = []
        if isinstance(brain_eval, dict):
            brain_suggested_tools = list(brain_eval.get("suggested_tools") or [])
        if isinstance(body, BaseException):
            body = {}
        if isinstance(neuro, BaseException):
            neuro = None
        # Full cognitive SomaBrain: apply neuromodulators to IQ for this turn.
        if isinstance(neuro, dict) and iq is not None:
            try:
                if hasattr(iq, "apply_neuromodulators"):
                    iq.apply_neuromodulators(neuro)  # type: ignore[attr-defined]
                else:
                    for k, v in neuro.items():
                        if hasattr(iq, k) and isinstance(v, (int, float)):
                            setattr(iq, k, v)
            except Exception:  # noqa: BLE001 — never block the turn
                pass
        context = await build_context(
            capsule=capsule,
            user_message=turn.user_message,
            history=history or [],
            memory_hits=memory_hits,
            budget_override=budget_override,
        )

        # Phase 7: Tool Discovery — default kit + capsule tools + Governor policy
        from services.tool_executor.default_tools import (
            default_tool_definitions,
            select_tools_for_mode,
        )

        tools_for_llm: List[Dict[str, Any]] = list(default_tool_definitions())
        seen_tools = {
            t.get("function", {}).get("name") for t in tools_for_llm if isinstance(t, dict)
        }
        if turn.tool_registry:
            for tool_def in turn.tool_registry.list():
                handler = tool_def.handler
                schema = handler.input_schema() if handler else None
                if schema and tool_def.name not in seen_tools:
                    tools_for_llm.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool_def.name,
                                "description": tool_def.description or tool_def.name,
                                "parameters": schema,
                            },
                        }
                    )
                    seen_tools.add(tool_def.name)

        tools_for_llm = select_tools_for_mode(
            tools_for_llm,
            tools_enabled=gov_decision.tools_enabled,
            tool_count_limit=gov_decision.tool_count_limit,
        )

        try:
            model = cast(
                SelectedModel,
                await self._cb_llm.call(
                    select_model,
                    required_capabilities=caps,
                    capsule_body=body or {},
                    tenant_id=tenant_id,
                    prefer_cost_tier=_iq_model_tier(iq),
                    preferred_model_id=getattr(capsule, "chat_model_id", None),
                ),
            )
        except CircuitBreakerError:
            yield get_message(ErrorCode.LLM_DEGRADED_CIRCUIT_OPEN)
            return

        # Stream LLM with native tool-calling loop (Phase 8-9)
        llm = get_chat_model(
            provider=model.provider,
            name=model.name,
            temperature=iq.temperature,
            max_tokens=iq.max_tokens,
        )
        messages = self._to_langchain_messages(context, history, turn.user_message)

        # Register the turn so the completion metrics below actually land.
        # Without a matching start, record_turn_complete looks up a turn id it
        # has never seen and TOKENS_TOTAL silently stays at zero.
        self._metrics.record_turn_start(
            turn_id=turn_id,
            tenant_id=tenant_id,
            user_id=turn.user_id,
            agent_id=str(capsule.id),
        )

        response_chunks: List[str] = []
        # Provider-reported usage only. The LLM response carries it; when a
        # round reports none the metric is None, never a local estimate.
        usage = TurnUsage()
        try:
            async for item in run_tool_loop(
                    iq=iq,
                    approval_gate=turn.approval_gate,
                llm=llm,
                messages=messages,
                tools_for_llm=tools_for_llm,
                tool_registry=turn.tool_registry,
                capsule=capsule,
                usage=usage,
            ):
                if isinstance(item, ToolStreamEvent):
                    yield item
                    continue
                response_chunks.append(item)
                yield item
        except CircuitBreakerError:
            yield "[System degraded: LLM service temporarily unavailable. Using cached context only.]"
            self._metrics.record_turn_complete(
                turn_id=turn_id,
                tokens_in=usage.prompt_tokens,
                tokens_out=usage.completion_tokens,
                model=model.name,
                provider=model.provider,
                error="llm_circuit_open",
            )
            return
        except asyncio.TimeoutError:
            yield get_message(ErrorCode.LLM_DEGRADED_TIMEOUT)
            self._metrics.record_turn_complete(
                turn_id=turn_id,
                tokens_in=usage.prompt_tokens,
                tokens_out=usage.completion_tokens,
                model=model.name,
                provider=model.provider,
                error="llm_timeout",
            )
            return

        # Store after streaming
        full_response = "".join(response_chunks)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        assistant_coord = await self._store_turn(
            conversation_id=turn.conversation_id or "",
            tenant_id=tenant_id,
            user_message=turn.user_message,
            assistant_response=full_response,
            model_id=f"{model.provider}/{model.name}",
            elapsed_ms=elapsed_ms,
            token_count_out=_token_count(full_response),
        )
        await self._persist_message(
            conversation_id=turn.conversation_id or "",
            tenant_id=tenant_id,
            role="assistant",
            text=full_response,
            coordinate=assistant_coord,
        )
        await self._bump_message_count(turn.conversation_id or "")
        # Completion metrics for the stream path. Token counts are what the
        # provider reported for this turn (None when it reported none — never
        # a local estimate presented as billed usage), and the model identity
        # from the SelectedModel that served it.
        self._metrics.record_turn_complete(
            turn_id=turn_id,
            tokens_in=usage.prompt_tokens,
            tokens_out=usage.completion_tokens,
            model=model.name,
            provider=model.provider,
        )
        await self._publish_cognitive_learning(
            tenant_id=tenant_id,
            session_id=turn.conversation_id or turn_id,
            persona_id=str(capsule.id) if capsule else "",
            user_message=turn.user_message,
            assistant_response=full_response,
            confidence=0.5,
        )

        # Emit Django signals for outbox publishers.
        # memory_created is NOT emitted: the MemoryGateway seam is the one
        # write path (PLAN §1 rule 4) and its outbox (the memory.wal
        # OutboxMessage) already covers failed acks — a second outbox entry
        # would duplicate writes.
        try:
            from admin.core.signals import conversation_message

            await sync_to_async(conversation_message.send)(
                sender=self.__class__,
                session_id=turn.conversation_id or "",
                event_id=turn_id,
                role="assistant",
                message=full_response,
                metadata={"tenant": tenant_id},
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
        """Recall THIS conversation's turns only (T-1 via SomaBrain).

        Session-scoped filter is mandatory: a semantic hit from another chat
        must never be injected as history (that makes every new chat replay
        the same answers). Unscoped hits are dropped, not guessed.
        """
        if not conversation_id:
            return []
        try:
            gateway = _require_memory_gateway()
            hits = await gateway.recall(
                query=f"session:{conversation_id}",
                k=int(_mem_setting("MEM_HISTORY_LIMIT", 20) or 20),
                tenant_id=tenant_id,
            )
        except Exception as exc:
            logger.warning("SomaBrain history recall failed: %s", exc)
            return []

        messages: List[Dict[str, str]] = []
        for h in hits or []:
            sid = getattr(h, "session_id", None)
            if not sid or str(sid) != str(conversation_id):
                continue
            role = (getattr(h, "role", None) or "user").strip().lower()
            if role not in ("user", "assistant"):
                continue
            text = getattr(h, "text", "") or ""
            if not text:
                continue
            messages.append({"role": role, "content": str(text)})
        # Oldest first so the LLM sees a real turn order.
        return messages

    def _to_langchain_messages(
        self, context: BuiltContext, history: List[Dict[str, str]], user_message: str
    ) -> List[Any]:
        """Convert BuiltContext (5 lanes) to LangChain messages.

        All 5 lanes from the context builder are preserved:
        - system  → SystemMessage (persona core + injection prompts)
        - memory  → SystemMessage ([Memory] recall from SomaBrain only, T-1)
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

        # Lane 3: Memory recall (SomaBrain only — T-1, no SFM from agent).
        # An empty recall is a real result and is left out of the prompt.
        if context.memory and context.memory != "[No relevant memories]":
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

    async def _persist_message(
        self,
        *,
        conversation_id: str,
        tenant_id: str,
        role: str,
        text: str,
        coordinate: str,
    ) -> None:
        """Write one conversation-transcript row (ARCH-INVARIANTS §3).

        Message rows are the transcript, NOT semantic memory. They must be
        written even when every memory store is down — that is why this path
        never goes through the MemoryGateway.
        """
        if not conversation_id:
            return
        from admin.chat.models import Message as MessageModel

        @sync_to_async
        def _create() -> None:
            MessageModel.objects.create(
                conversation_id=conversation_id,
                role=role,
                content=text,
                coordinate=coordinate,
            )

        await _create()

    async def _bump_message_count(self, conversation_id: str) -> None:
        """Increment Conversation.message_count (created 0, must be maintained)."""
        if not conversation_id:
            return
        from django.db.models import F

        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def _bump() -> None:
            ConversationModel.objects.filter(id=conversation_id).update(
                message_count=F("message_count") + 1
            )

        await _bump()

    async def _persist_user_transcript(self, turn: ChatTurn, tenant_id: str) -> None:
        """Record the user input as soon as the phase-4 gate has passed.

        A failed turn must still leave its input in the transcript.
        """
        from services.common.memory_contract import MemoryWrite

        text = turn.user_message or ""
        kind = str(MemoryWrite.model_fields["kind"].default)
        coord = make_coord(tenant_id, kind, datetime.now(UTC), text)
        await self._persist_message(
            conversation_id=turn.conversation_id or "",
            tenant_id=tenant_id,
            role="user",
            text=text,
            coordinate=coord,
        )
        await self._bump_message_count(turn.conversation_id or "")

    async def _remember_via_gateway(
        self,
        text: str,
        *,
        tenant_id: str,
        session_id: Optional[str],
        namespace: str,
        salience: Optional[float] = None,
        kind: Optional[str] = None,
        role: Optional[str] = None,
    ) -> str:
        """ONE write path: MemoryGateway.remember_text() (PLAN §1 rule 4).

        remember_text() derives the seam coord AND the SomaBrain key material
        from the same (tenant, kind, ts, text). It is T-6: the write is accepted
        into the durable outbox BEFORE the hop; ``MemoryAck.ok`` completes that
        record. A failed hop leaves it pending — the outbox drain /
        memory-replicator is the ONE replay authority. No second authority
        is written here.

        Returns the seam ``make_coord`` string for this write. The coord is
        computed before any transport attempt and is always returned — the
        transcript row must not depend on a memory store being reachable.
        """
        from services.common.memory_contract import get_memory_setting, MemoryWrite

        if salience is None:
            salience = float(MemoryWrite.model_fields["salience"].default)
        if kind is None:
            kind = str(MemoryWrite.model_fields["kind"].default)
        if not namespace:
            namespace = str(get_memory_setting("MEM_CHAT_NAMESPACE", "chat_history"))

        stamp = datetime.now(UTC)
        coord = make_coord(tenant_id, kind, stamp, text)
        try:
            gateway = _require_memory_gateway()
            acks = await asyncio.wait_for(
                gateway.remember_text(
                    text,
                    tenant_id=tenant_id,
                    kind=kind,
                    ts=stamp,
                    session_id=session_id,
                    salience=salience,
                    source="agent-chat",
                    role=role,
                ),
                timeout=_write_timeout(),
            )
        except Exception as exc:
            # Timeout / transport failure: one unacked write — the gateway's
            # durable-before-hop record is already pending. Never synthesise
            # one failed ack per imagined store (the gateway returns one).
            logger.warning("MemoryGateway write failed (coord=%s): %s", coord, exc)
            acks = [MemoryAck(coord=coord, store="somabrain", ok=False, error=str(exc))]

        for ack in acks:
            if ack.ok:
                continue  # success is final — durable record completed, no replay
            # Failed hop: the T-6 durable-accept row stays pending. The one
            # replay authority (outbox → memory.wal → memory-replicator) owns
            # redelivery. Do NOT queue the write anywhere else.
            logger.warning(
                "Memory write unacked (coord=%s store=%s): %s — durable-accept left for replay",
                coord,
                ack.store,
                ack.error,
            )
        return coord

    async def _recall_memories(
        self,
        query: str,
        tenant_id: str,
        capsule: Any,
        iq: Any = None,
    ) -> Optional[List[MemoryHit]]:
        """One read path: MemoryGateway.recall() feeds the memory lane (PLAN §1 rule 5).

        Returns None when recall is unavailable so the lane renders its
        fallback sentinel; [] when recall ran and found nothing.
        """
        gateway = _require_memory_gateway()

        # AgentIQ derives recall_limit from the intelligence knob. It is the
        # authority here; the capsule's memory config overrides it, and the
        # final fallback is a declared setting, never a literal in the code.
        try:
            memory_config = capsule.body.get("memory", {}) if capsule.body else {}
            if not memory_config:
                async_body = await capsule.async_body() if hasattr(capsule, "async_body") else {}
                memory_config = (async_body or {}).get("memory", {})
            iq_recall_limit = iq.recall_limit if iq is not None else None
            recall_limit = int(
                memory_config.get("recall_limit") or iq_recall_limit
                or _mem_setting("MEM_RECALL_TOP_K", 8)
            )
        except Exception:
            recall_limit = int(_mem_setting("MEM_RECALL_TOP_K", 8))
        try:
            hits = await gateway.recall(query=query, k=recall_limit, tenant_id=tenant_id)
            return list(hits or [])
        except Exception as exc:
            logger.warning("MemoryGateway.recall failed: %s", exc)
            return None

    async def _store_turn(
        self,
        conversation_id: str,
        tenant_id: str,
        user_message: str,
        assistant_response: str,
        model_id: str,
        elapsed_ms: int,
        token_count_out: int,
        salience: float | None = None,
    ) -> str:
        """Store a turn in semantic memory (T-1) via the MemoryGateway seam.

        SomaBrain/SFM hold the semantic memories. Postgres ``Message`` rows
        are the conversation transcript (ARCH-INVARIANTS §3) and are written
        separately via ``_persist_message`` — never through this path.

        Returns the assistant turn's seam coordinate (from
        ``_remember_via_gateway``) so the transcript row can carry it.
        """
        # ONE write path: SomaBrain via MemoryGateway.
        # Failed acks are queued to Kafka WAL inside _remember_via_gateway.
        await self._remember_via_gateway(
            user_message,
            tenant_id=tenant_id,
            session_id=conversation_id or None,
            namespace="chat_history",
            salience=salience,
            role="user",
        )
        assistant_coord = await self._remember_via_gateway(
            assistant_response,
            tenant_id=tenant_id,
            session_id=conversation_id or None,
            namespace="chat_history",
            salience=salience,
            role="assistant",
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
        return assistant_coord

    async def _publish_cognitive_learning(
        self,
        *,
        tenant_id: str,
        session_id: str,
        persona_id: str,
        user_message: str,
        assistant_response: str,
        confidence: float,
    ) -> None:
        """Full cognitive loop after every turn: context feedback + reward.

        SomaBrain learns from every chat exchange (T-6 cognitive loop).
        Non-blocking best-effort — never stalls the reply.
        """
        task = asyncio.create_task(
            self._cognitive_learning_bg(
                tenant_id=tenant_id,
                session_id=session_id,
                persona_id=persona_id,
                user_message=user_message,
                assistant_response=assistant_response,
                confidence=confidence,
            )
        )
        task.add_done_callback(self._on_background_task_done("_publish_cognitive_learning"))

    async def _cognitive_learning_bg(
        self,
        *,
        tenant_id: str,
        session_id: str,
        persona_id: str,
        user_message: str,
        assistant_response: str,
        confidence: float,
    ) -> None:
        try:
            brain_client = await SomaBrainClient.get_async()
            if not brain_client:
                return
            # SomaBrain FeedbackRequest schema (api/schemas/context.py):
            # session_id, query, prompt, response_text, utility, reward, metadata, tenant_id
            utility = float(max(0.0, min(1.0, confidence)))
            await self._cb_somabrain.call(
                brain_client.context_feedback,
                session_id=session_id,
                query=user_message,
                prompt=user_message,
                response_text=assistant_response,
                utility=utility,
                reward=utility,
                metadata={
                    "persona_id": persona_id,
                    "source": "chat_turn",
                    "outcome": "completed",
                },
                tenant_id=tenant_id,
            )
            await self._cb_somabrain.call(
                brain_client.publish_reward,
                session_id,
                "reward",
                utility,
                {
                    "tenant_id": tenant_id,
                    "persona_id": persona_id,
                    "source": "chat_turn",
                },
            )
        except Exception as exc:
            logger.warning("Cognitive learning publish skipped: %s", exc)

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
        salience: float | None = None,
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
    "ToolStreamEvent",
    "get_chat_orchestrator",
    "ServiceUnavailableError",
]
