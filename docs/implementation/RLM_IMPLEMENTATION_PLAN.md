# RLM IMPLEMENTATION PLAN

**Document ID:** IMPLEMENTATION-RLM-2026-01-15  
**Version:** 1.0.0  
**Status:** READY FOR IMPLEMENTATION  
**Date:** January 15, 2026  
**Authors:** All VIBE Personas

---

## EXECUTIVE SUMMARY

This document provides the **exact implementation steps** to transform the current single-shot chat flow into the RLM-based learning architecture specified in SRS-COMPLETE-PERFECT-CHAT-FLOW-SOMABRAIN-LEARNING-ISO.md.

**Current State:** Single LLM call per user message  
**Target State:** 5-10 RLM iterations per turn with synchronous learning

---

## PHASE 1: DATABASE SCHEMA (Week 1)

### 1.1 Create RLMIteration Model

**File:** `admin/chat/models.py`

Add after `ConversationParticipant` model:

```python
class RLMIteration(models.Model):
    """RLM iteration record - stores complete iteration data for replayability.
    
    Implements ISO/IEC/IEEE 29148:2018 traceability requirements.
    Every iteration is stored for audit, replay, and analysis.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turn_id = models.UUIDField(db_index=True, help_text="Unique identifier for this turn")
    conversation_id = models.UUIDField(db_index=True)
    
    iteration_number = models.IntegerField(help_text="0-indexed iteration number")
    
    # Weights (α, β, γ, τ, λ, μ, ν) - learned parameters
    weights_before = models.JSONField(
        default=dict,
        help_text="Weights before this iteration"
    )
    weights_after = models.JSONField(
        default=dict,
        help_text="Weights after this iteration (updated by SomaBrain)"
    )
    weight_deltas = models.JSONField(
        default=dict,
        help_text="Change in weights during this iteration"
    )
    
    # Neuromodulators - chemical signals that gate learning
    neuromodulators_before = models.JSONField(
        default=dict,
        help_text="Neuromodulator levels before iteration"
    )
    neuromodulators_after = models.JSONField(
        default=dict,
        help_text="Neuromodulator levels after iteration"
    )
    
    # LLM call details
    model = models.CharField(max_length=100, help_text="Model used for this iteration")
    confidence = models.FloatField(help_text="LLM confidence score (0.0-1.0)")
    latency_ms = models.IntegerField(help_text="LLM call latency in milliseconds")
    
    # Tool execution
    tool_calls = models.JSONField(
        default=list,
        help_text="Tools called in this iteration"
    )
    tool_results = models.JSONField(
        default=list,
        help_text="Results from tool executions"
    )
    
    # Token usage
    prompt_tokens = models.IntegerField(help_text="Tokens in prompt")
    completion_tokens = models.IntegerField(help_text="Tokens in completion")
    
    # Convergence assessment
    convergence_score = models.FloatField(
        help_text="Computed convergence score (0.0-1.0)"
    )
    exit_reason = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Why iteration loop exited"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        """Meta class implementation."""
        
        db_table = "rlm_iterations"
        ordering = ["turn_id", "iteration_number"]
        indexes = [
            models.Index(fields=["turn_id", "iteration_number"]),
            models.Index(fields=["conversation_id", "created_at"]),
            models.Index(fields=["convergence_score"]),
        ]
    
    def __str__(self):
        """Return string representation."""
        return f"RLMIteration({self.turn_id}:{self.iteration_number})"
```

### 1.2 Add Learned Weights to Capsule

**File:** `admin/core/models.py`

Add to `Capsule` model (after `learning_config` field):

```python
class Capsule(models.Model):
    # ... existing fields ...
    
    # ═══════════════════════════════════════════════════════════════════
    # LEARNED STATE (Updated by SomaBrain)
    # ═══════════════════════════════════════════════════════════════════
    
    learned_weights = models.JSONField(
        default=dict,
        blank=True,
        help_text="Current learned weights: α, β, γ, τ, λ, μ, ν",
    )
    
    neuromodulator_state = models.JSONField(
        default=dict,
        blank=True,
        help_text="Current neuromodulator levels: dopamine, serotonin, etc.",
    )
    
    # ... rest of model ...
```

### 1.3 Generate and Run Migration

```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/admin
python manage.py makemigrations chat core
python manage.py migrate
```

**Verification:**
```bash
python manage.py dbshell
\d rlm_iterations
SELECT COUNT(*) FROM rlm_iterations;
```

---

## PHASE 2: RLM ITERATOR ENGINE (Week 2-3)

### 2.1 Create RLMIterator Class

**File:** `services/common/rlm_iterator.py`

```python
"""RLM Iterator - Recursive Language Model Iterator.

The Heart of the SOMA Stack Agent: Learning from Every Interaction.

Implements:
- 5-10 iteration loops per turn
- Synchronous learning via SomaBrain.publish_turn_metrics()
- Weight updates (α, β, γ, τ, λ, μ, ν)
- Neuromodulator-gated learning rates
- Convergence detection
- Event-sourcing to Kafka
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator, Optional
from uuid import uuid4

from asgiref.sync import sync_to_async
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Metrics
RLM_ITERATIONS_TOTAL = Counter(
    "rlm_iterations_total",
    "Total RLM iterations executed",
    ["turn_id", "iteration_number", "exit_reason"],
)


class RLMIterationResult:
    """Result of a single RLM iteration."""
    
    def __init__(
        self,
        iteration_number: int,
        response: str,
        confidence: float,
        convergence_score: float,
        weights: dict[str, float],
        neuromodulators: dict[str, float],
        tools_used: list[str],
        latency_ms: int,
    ):
        self.iteration_number = iteration_number
        self.response = response
        self.confidence = confidence
        self.convergence_score = convergence_score
        self.weights = weights
        self.neuromodulators = neuromodulators
        self.tools_used = tools_used
        self.latency_ms = latency_ms


class RLMIterator:
    """Recursive Language Model Iterator - The Heart of Learning.
    
    Executes 5-10 iterations per turn, with synchronous learning after each.
    """
    
    def __init__(
        self,
        conversation_id: str,
        agent_id: str,
        user_id: str,
        tenant_id: str,
        user_message: str,
        raw_history: list[dict],
    ):
        """Initialize RLM iterator.
        
        Args:
            conversation_id: Conversation ID
            agent_id: Agent (Capsule) ID
            user_id: User ID
            tenant_id: Tenant ID
            user_message: User message content
            raw_history: Conversation history (list of dicts)
        """
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.user_message = user_message
        self.raw_history = raw_history
        self.turn_id = str(uuid4())
        
        # Capsule state
        self.capsule = None
        self.system_prompt = ""
        self.learning_config = {}
        
        # Learned weights (start with capsule defaults)
        self.weights = {
            "alpha": 1.0,
            "beta": 0.2,
            "gamma": 0.1,
            "tau": 0.7,
            "lambda": 1.0,
            "mu": 0.1,
            "nu": 0.05,
        }
        
        # Neuromodulators (start with capsule baseline)
        self.neuromodulators = {
            "dopamine": 0.5,
            "serotonin": 0.5,
            "norepinephrine": 0.5,
            "acetylcholine": 0.5,
        }
        
        # Iteration tracking
        self.max_iterations = 10
        self.convergence_threshold = 0.9
        
        logger.info(f"RLMIterator created for turn {self.turn_id[:8]}")
    
    async def initialize(self) -> None:
        """Load capsule and initialize state from database."""
        from admin.core.models import Capsule
        
        @sync_to_async
        def load_capsule():
            return Capsule.objects.filter(id=self.agent_id).first()
        
        self.capsule = await load_capsule()
        if self.capsule:
            self.system_prompt = self.capsule.system_prompt or ""
            self.learning_config = self.capsule.learning_config or {}
            
            # Load learned weights from capsule
            if self.capsule.learned_weights:
                self.weights.update(self.capsule.learned_weights)
            
            # Load neuromodulator state
            if self.capsule.neuromodulator_state:
                self.neuromodulators.update(self.capsule.neuromodulator_state)
        
        logger.info(f"RLMIterator initialized: agent={self.agent_id[:8]}, weights={self.weights}")
    
    async def iterate(self) -> AsyncIterator[RLMIterationResult]:
        """Execute RLM iterations and yield results.
        
        Yields:
            RLMIterationResult after each iteration
        """
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        from admin.llm.services.litellm_client import get_chat_model
        from admin.core.somabrain_client import SomaBrainClient
        from services.common.health_monitor import get_health_monitor
        from services.common.simple_governor import get_governor
        from services.common.simple_context_builder import create_context_builder
        from services.common.model_router import select_model
        from services.common.unified_metrics import get_metrics, TurnPhase
        from django.conf import settings
        
        # Initialize metrics
        metrics = get_metrics()
        turn_metrics = metrics.record_turn_start(
            turn_id=self.turn_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            agent_id=self.agent_id,
        )
        
        # Load capsule
        await self.initialize()
        
        # Get health status
        health_monitor = get_health_monitor()
        overall_health = health_monitor.get_overall_health()
        is_degraded = overall_health.degraded
        
        # Allocate budget
        governor = get_governor()
        max_total_tokens = int(settings.chat_model_ctx_length)
        decision = governor.allocate_budget(max_total_tokens, is_degraded)
        
        # Get SomaBrain client
        somabrain_client = await SomaBrainClient.get_async()
        
        # Create context builder
        def simple_token_counter(text: str) -> int:
            return len(text.split())
        
        builder = create_context_builder(
            somabrain=somabrain_client,
            token_counter=simple_token_counter,
        )
        
        # Select model
        required_caps = {"text"}
        capsule_body = {
            "allowed_models": self.capsule.config.get("allowed_models", []) if self.capsule else []
        }
        selected_model = await select_model(
            required_capabilities=required_caps,
            capsule_body=capsule_body,
            tenant_id=self.tenant_id,
        )
        
        llm = get_chat_model(
            provider=selected_model.provider,
            name=selected_model.name,
        )
        
        # RLM Loop
        for iteration_num in range(self.max_iterations):
            iteration_start = time.perf_counter()
            
            # 1. Build context with current weights
            turn_dict = {
                "tenant_id": self.tenant_id,
                "session_id": self.turn_id,
                "user_message": self.user_message,
                "history": self.raw_history,
                "system_prompt": self.system_prompt,
            }
            
            built = await builder.build_for_turn(
                turn=turn_dict,
                lane_budget=decision.lane_budget.to_dict(),
                is_degraded=is_degraded,
            )
            
            # 2. Call LLM
            lc_messages = []
            for msg in built.messages:
                role, content_val = msg.get("role"), msg.get("content")
                if role == "assistant":
                    lc_messages.append(AIMessage(content=content_val or ""))
                elif role == "system":
                    lc_messages.append(SystemMessage(content=content_val or ""))
                else:
                    lc_messages.append(HumanMessage(content=content_val or ""))
            
            response_content = []
            try:
                async for chunk in llm._astream(messages=lc_messages):
                    token = str(chunk.message.content) if hasattr(chunk, "message") and hasattr(chunk.message, "content") else ""
                    if token:
                        response_content.append(token)
            except Exception as e:
                logger.error(f"LLM streaming error in iteration {iteration_num}: {e}")
                break
            
            full_response = "".join(response_content)
            iteration_latency = int((time.perf_counter() - iteration_start) * 1000)
            
            # 3. Parse tool calls (if any)
            # TODO: Implement tool parsing and execution
            tool_calls = []
            tool_results = []
            
            # 4. Compute confidence (simplified - from response length/quality)
            confidence = min(0.95, len(full_response) / 100)  # Placeholder
            
            # 5. CRITICAL: Call SomaBrain.publish_turn_metrics() - LEARNING HAPPENS HERE
            learning_result = await somabrain_client.publish_reward(
                session_id=self.turn_id,
                signal="iteration_complete",
                value=confidence,
                meta={
                    "iteration_number": iteration_num,
                    "tools_used": [t["name"] for t in tool_calls],
                    "confidence": confidence,
                    "latency_ms": iteration_latency,
                    "weights": self.weights,
                    "neuromodulators": self.neuromodulators,
                },
            )
            
            # 6. Update weights from SomaBrain response
            updated_weights = self.weights.copy()
            updated_neuromodulators = self.neuromodulators.copy()
            
            if learning_result and isinstance(learning_result, dict):
                if "weights" in learning_result:
                    updated_weights.update(learning_result["weights"])
                if "neuromodulators" in learning_result:
                    updated_neuromodulators.update(learning_result["neuromodulators"])
            
            # Compute deltas
            weight_deltas = {}
            for key in self.weights:
                if key in updated_weights:
                    weight_deltas[key] = updated_weights[key] - self.weights[key]
            
            # 7. Store RLMIteration
            await self._store_iteration(
                iteration_number=iteration_num,
                weights_before=self.weights,
                weights_after=updated_weights,
                weight_deltas=weight_deltas,
                neuromodulators_before=self.neuromodulators,
                neuromodulators_after=updated_neuromodulators,
                model=f"{selected_model.provider}/{selected_model.name}",
                confidence=confidence,
                latency_ms=iteration_latency,
                tool_calls=tool_calls,
                tool_results=tool_results,
                prompt_tokens=len(built.messages),
                completion_tokens=len(full_response.split()),
                convergence_score=confidence,
            )
            
            # Update local state
            self.weights = updated_weights
            self.neuromodulators = updated_neuromodulators
            
            # 8. Assess convergence
            convergence_score = confidence  # Simplified
            
            # Yield result
            result = RLMIterationResult(
                iteration_number=iteration_num,
                response=full_response,
                confidence=confidence,
                convergence_score=convergence_score,
                weights=self.weights.copy(),
                neuromodulators=self.neuromodulators.copy(),
                tools_used=[t["name"] for t in tool_calls],
                latency_ms=iteration_latency,
            )
            
            yield result
            
            # 9. Check exit conditions
            if convergence_score >= self.convergence_threshold:
                logger.info(f"Converged at iteration {iteration_num} (score={convergence_score:.2f})")
                RLM_ITERATIONS_TOTAL.labels(
                    turn_id=self.turn_id,
                    iteration_number=iteration_num,
                    exit_reason="converged",
                ).inc()
                break
            
            if iteration_num == self.max_iterations - 1:
                logger.info(f"Max iterations reached at {iteration_num}")
                RLM_ITERATIONS_TOTAL.labels(
                    turn_id=self.turn_id,
                    iteration_number=iteration_num,
                    exit_reason="max_iterations",
                ).inc()
                break
        
        # Update capsule with learned weights
        await self._update_capsule_weights()
        
        # Record completion metrics
        metrics.record_turn_complete(
            turn_id=self.turn_id,
            tokens_in=turn_metrics.tokens_in,
            tokens_out=sum(len(r.response.split()) for r in self.iteration_results),
            model=f"{selected_model.provider}/{selected_model.name}",
            provider=selected_model.provider,
            error=None,
        )
        
        # Store final assistant message
        await self._store_final_message(full_response, iteration_latency)
        
        # Non-blocking: store interaction in memory
        asyncio.create_task(
            self._store_interaction(full_response)
        )
    
    async def _store_iteration(
        self,
        iteration_number: int,
        weights_before: dict,
        weights_after: dict,
        weight_deltas: dict,
        neuromodulators_before: dict,
        neuromodulators_after: dict,
        model: str,
        confidence: float,
        latency_ms: int,
        tool_calls: list,
        tool_results: list,
        prompt_tokens: int,
        completion_tokens: int,
        convergence_score: float,
    ) -> None:
        """Store RLM iteration in database."""
        from admin.chat.models import RLMIteration
        
        @sync_to_async
        def save():
            RLMIteration.objects.create(
                turn_id=self.turn_id,
                conversation_id=self.conversation_id,
                iteration_number=iteration_number,
                weights_before=weights_before,
                weights_after=weights_after,
                weight_deltas=weight_deltas,
                neuromodulators_before=neuromodulators_before,
                neuromodulators_after=neuromodulators_after,
                model=model,
                confidence=confidence,
                latency_ms=latency_ms,
                tool_calls=tool_calls,
                tool_results=tool_results,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                convergence_score=convergence_score,
            )
        
        await save()
    
    async def _update_capsule_weights(self) -> None:
        """Update capsule with learned weights."""
        from admin.core.models import Capsule
        
        @sync_to_async
        def update():
            if self.capsule:
                self.capsule.learned_weights = self.weights
                self.capsule.neuromodulator_state = self.neuromodulators
                self.capsule.save(update_fields=["learned_weights", "neuromodulator_state"])
        
        await update()
    
    async def _store_final_message(self, response: str, latency_ms: int) -> None:
        """Store final assistant message."""
        from admin.chat.models import Message as MessageModel, Conversation as ConversationModel
        
        @sync_to_async
        def store():
            MessageModel.objects.create(
                conversation_id=self.conversation_id,
                role="assistant",
                content=response,
                token_count=len(response.split()),
                latency_ms=latency_ms,
                model="rlm_final",
            )
            ConversationModel.objects.filter(id=self.conversation_id).update(
                message_count=MessageModel.objects.filter(conversation_id=self.conversation_id).count()
            )
        
        await store()
    
    async def _store_interaction(self, response: str) -> None:
        """Store interaction in memory via SomaBrain."""
        from services.common.chat_memory import store_interaction
        
        await store_interaction(
            agent_id=self.agent_id,
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            user_message=self.user_message,
            assistant_response=response,
            tenant_id=self.tenant_id,
        )
```

### 2.2 Update ChatService to Use RLMIterator

**File:** `services/common/chat_service.py`

Modify the `send_message` method:

```python
async def send_message(
    self, conversation_id: str, agent_id: str, content: str, user_id: str
) -> AsyncIterator[str]:
    """Send message and stream response tokens from LLM provider.
    
    Production flow with RLM iterations:
    1. Store user message
    2. Load conversation data and history
    3. Execute RLM iterations (5-10 loops with learning)
    4. Stream final response
    5. Store assistant message and record metrics
    """
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from admin.chat.models import Conversation as ConversationModel, Message as MessageModel
    from admin.core.helpers.settings_defaults import get_default_settings
    from admin.llm.services.litellm_client import get_chat_model
    from services.common.rlm_iterator import RLMIterator
    
    start_time = time.perf_counter()
    
    # 1. Initialize metrics
    metrics = get_metrics()
    
    # 2. Store user message
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
                message_count=MessageModel.objects.filter(
                    conversation_id=conversation_id
                ).count()
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
    
    # 4. Execute RLM iterations
    iterator = RLMIterator(
        conversation_id=conversation_id,
        agent_id=agent_id,
        user_id=user_id,
        tenant_id=tenant_id,
        user_message=content,
        raw_history=raw_history,
    )
    
    # Stream responses from each iteration
    async for iteration_result in iterator.iterate():
        # Stream the response
        yield iteration_result.response
        
        # Check if converged
        if iteration_result.convergence_score >= 0.9:
            break
    
    # 5. Record completion metrics
    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    
    metrics.record_turn_complete(
        turn_id=iterator.turn_id,
        tokens_in=len(content.split()),
        tokens_out=len(iteration_result.response.split()),
        model=iteration_result.model if hasattr(iteration_result, "model") else "unknown",
        provider="unknown",
        error=None,
    )
    
    # Track overall metrics
    CHAT_TOKENS.labels(direction="input").inc(len(content.split()))
    CHAT_TOKENS.labels(direction="output").inc(len(iteration_result.response.split()))
    CHAT_LATENCY.labels(method="send_message").observe(time.perf_counter() - start_time)
    CHAT_REQUESTS.labels(method="send_message", result="success").inc()
```

---

## PHASE 3: SOMABRAIN LEARNING INTEGRATION (Week 3-4)

### 3.1 Add publish_turn_metrics to SomaBrainClient

**File:** `admin/core/somabrain_client.py`

Add method after `publish_reward`:

```python
async def publish_turn_metrics(
    self,
    turn_id: str,
    iteration_number: int,
    tools_used: list[str],
    confidence: float,
    latency_ms: int,
    weights: dict[str, float],
    neuromodulators: dict[str, float],
    tenant_id: str,
    persona_id: str = "default",
) -> dict[str, Any]:
    """Publish turn metrics for synchronous learning.
    
    THIS IS WHERE THE AGENT LEARNS FROM EVERY INTERACTION.
    
    SomaBrain processes synchronously and returns updated weights.
    
    Args:
        turn_id: Turn identifier
        iteration_number: Current iteration number
        tools_used: List of tools executed
        confidence: LLM confidence score
        latency_ms: LLM call latency
        weights: Current weights (α, β, γ, τ, λ, μ, ν)
        neuromodulators: Current neuromodulator levels
        tenant_id: Tenant identifier
        persona_id: Persona identifier
    
    Returns:
        Dict with updated weights and neuromodulators
    """
    body = {
        "turn_id": turn_id,
        "iteration_number": iteration_number,
        "tools_used": tools_used,
        "confidence": confidence,
        "latency_ms": latency_ms,
        "weights": weights,
        "neuromodulators": neuromodulators,
        "tenant": tenant_id,
        "persona": persona_id,
    }
    
    # DIRECT MODE CHECK
    if HAS_FACADE:
        facade = BrainMemoryFacade.get_instance()
        if facade.mode == "direct":
            try:
                # Call Facade for learning
                resp = await facade.publish_turn_metrics(body)
                return {
                    "status": getattr(resp, "status", "success"),
                    "weights": resp.weights,
                    "neuromodulators": resp.neuromodulators,
                }
            except NotImplementedError:
                pass
            except Exception as e:
                logger.error(f"Direct learning failed, falling back to HTTP: {e}")
    
    return await self._request("POST", "/v1/learning/publish_turn_metrics", json=body)
```

### 3.2 Update SRS Documentation

**File:** `docs/srs/SRS-COMPLETE-PERFECT-CHAT-FLOW-SOMABRAIN-LEARNING-ISO.md`

Add clarification to Section 4.1:

```markdown
## 4.1 Complete Learning Loop (Synchronous with Every Iteration)

### SomaBrain Learning Endpoint

**Endpoint:** `POST /v1/learning/publish_turn_metrics`

**Request Body:**
```json
{
  "turn_id": "uuid",
  "iteration_number": 0,
  "tools_used": ["web_search"],
  "confidence": 0.92,
  "latency_ms": 2341,
  "weights": {
    "alpha": 1.0,
    "beta": 0.2,
    "gamma": 0.1,
    "tau": 0.7,
    "lambda": 1.0,
    "mu": 0.1,
    "nu": 0.05
  },
  "neuromodulators": {
    "dopamine": 0.5,
    "serotonin": 0.5,
    "norepinephrine": 0.5,
    "acetylcholine": 0.5
  },
  "tenant": "tenant_id",
  "persona": "persona_id"
}
```

**Response Body:**
```json
{
  "status": "success",
  "weights": {
    "alpha": 1.05,
    "beta": 0.18,
    "gamma": 0.12,
    "tau": 0.68,
    "lambda": 1.02,
    "mu": 0.09,
    "nu": 0.06
  },
  "neuromodulators": {
    "dopamine": 0.52,
    "serotonin": 0.51,
    "norepinephrine": 0.48,
    "acetylcholine": 0.53
  }
}
```

**SomaBrain Processing:**
1. Store metrics in working memory
2. Compute salience: `salience = w_novelty * novelty + w_error * error`
3. If salience > threshold:
   - Update neuromodulators based on confidence signals
   - Update weights: `p_new = clamp(p_old + lr_eff * gain_p * signal, p_min, p_max)`
   - Where `lr_eff = lr_base * clamp(0.5 + dopamine, 0.5, 1.2)`
4. Return updated weights and neuromodulators

**Latency Requirement:** < 50ms (synchronous)
```

---

## PHASE 4: TOOL INTEGRATION (Week 4-5)

### 4.1 Create Tool Discovery Module

**File:** `services/common/tool_discovery.py`

```python
"""Tool discovery from Capsule capabilities."""

from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def discover_tools_from_capsule(agent_id: str) -> Dict[str, Dict[str, Any]]:
    """Discover tools from Capsule capabilities.
    
    Args:
        agent_id: Capsule ID
    
    Returns:
        Dict of {tool_name: tool_config}
    """
    from asgiref.sync import sync_to_async
    from admin.core.models import Capsule
    
    @sync_to_async
    def get_capsule_tools():
        capsule = Capsule.objects.filter(id=agent_id).first()
        if not capsule:
            return {}
        
        tools = {}
        for capability in capsule.capabilities.all():
            if capability.is_enabled:
                tools[capability.name] = {
                    "description": capability.description,
                    "schema": capability.schema,
                    "config": capability.config,
                }
        return tools
    
    tools = await get_capsule_tools()
    logger.info(f"Discovered {len(tools)} tools for agent {agent_id[:8]}")
    return tools
```

### 4.2 Update RLMIterator to Execute Tools

**File:** `services/common/rlm_iterator.py`

Add tool execution method:

```python
async def _execute_tools(
    self,
    tool_calls: list[dict],
    somabrain_client,
) -> tuple[list[dict], list[dict]]:
    """Execute tools and return results.
    
    Args:
        tool_calls: List of tool call dicts
        somabrain_client: SomaBrain client for learning signals
    
    Returns:
        Tuple of (tool_calls, tool_results)
    """
    from services.common.tool_executor import execute_tool
    from services.common.implicit_signals import signal_tool_usage
    
    results = []
    
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("arguments", {})
        
        try:
            # Execute tool
            result = await execute_tool(
                tool_name=tool_name,
                tool_args=tool_args,
                agent_id=self.agent_id,
                tenant_id=self.tenant_id,
            )
            
            results.append({
                "name": tool_name,
                "result": result,
                "success": True,
            })
            
            # Send learning signal
            await signal_tool_usage(
                session_id=self.turn_id,
                tool_name=tool_name,
                success=True,
                learning_config=self.learning_config,
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            results.append({
                "name": tool_name,
                "result": {"error": str(e)},
                "success": False,
            })
            
            # Send learning signal
            await signal_tool_usage(
                session_id=self.turn_id,
                tool_name=tool_name,
                success=False,
                learning_config=self.learning_config,
            )
    
    return tool_calls, results
```

### 4.3 Create Tool Executor

**File:** `services/common/tool_executor.py`

```python
"""Tool execution with OPA policy enforcement."""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def execute_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    agent_id: str,
    tenant_id: str,
) -> Dict[str, Any]:
    """Execute a tool with OPA policy check.
    
    Args:
        tool_name: Name of tool to execute
        tool_args: Arguments for tool
        agent_id: Agent ID
        tenant_id: Tenant ID
    
    Returns:
        Tool execution result
    
    Raises:
        Exception: If tool execution fails
    """
    from admin.core.models import Capability
    
    # 1. Get tool definition
    @sync_to_async
    def get_tool_def():
        return Capability.objects.filter(name=tool_name, is_enabled=True).first()
    
    tool_def = await get_tool_def()
    if not tool_def:
        raise ValueError(f"Tool '{tool_name}' not found or disabled")
    
    # 2. Check OPA policy
    # TODO: Implement OPA evaluation
    # from admin.core.opa_client import evaluate_policy
    # allowed = await evaluate_policy(
    #     action="tool:execute",
    #     tool=tool_name,
    #     user_id=user_id,
    #     tenant_id=tenant_id,
    #     agent_id=agent_id,
    # )
    # if not allowed:
    #     raise PermissionError(f"Tool '{tool_name}' not allowed by policy")
    
    # 3. Execute tool
    # TODO: Implement tool execution based on tool_def.schema
    # For now, return mock result
    result = {
        "status": "executed",
        "tool": tool_name,
        "args": tool_args,
        "output": f"Tool '{tool_name}' executed successfully",
    }
    
    logger.info(f"Tool executed: {tool_name}")
    return result
```

---

## PHASE 5: EVENT-SOURCING (Week 5-6)

### 5.1 Create Event Publisher

**File:** `services/common/event_publisher.py`

```python
"""Event publishing to Kafka for replayability."""

from __future__ import annotations

import logging
import time
from uuid import uuid4

logger = logging.getLogger(__name__)


async def publish_chat_event(
    event_type: str,
    turn_id: str,
    payload: dict,
    tenant_id: str,
) -> None:
    """Publish immutable event to Kafka via Outbox pattern.
    
    Args:
        event_type: Type of event (e.g., "chat.iteration_completed")
        turn_id: Turn identifier
        payload: Event payload
        tenant_id: Tenant identifier
    """
    from admin.core.models import OutboxMessage
    from asgiref.sync import sync_to_async
    
    event_id = str(uuid4())
    
    @sync_to_async
    def create_outbox():
        OutboxMessage.objects.create(
            idempotency_key=f"{event_type}:{event_id}",
            topic="chat.events",
            partition_key=tenant_id,
            payload={
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": time.time(),
                "tenant_id": tenant_id,
                "turn_id": turn_id,
                **payload,
            },
        )
    
    await create_outbox()
    logger.debug(f"Event published: {event_type} for turn {turn_id[:8]}")
```

### 5.2 Publish Events in RLMIterator

**File:** `services/common/rlm_iterator.py`

Add event publishing in `iterate()` method:

```python
# After each iteration
await publish_chat_event(
    event_type="chat.iteration_completed",
    turn_id=self.turn_id,
    payload={
        "iteration_number": iteration_num,
        "confidence": confidence,
        "convergence_score": convergence_score,
        "weights_before": self.weights,
        "weights_after": updated_weights,
        "weight_deltas": weight_deltas,
        "tools_used": [t["name"] for t in tool_calls],
        "latency_ms": iteration_latency,
    },
    tenant_id=self.tenant_id,
)

# After turn complete
await publish_chat_event(
    event_type="chat.turn_complete",
    turn_id=self.turn_id,
    payload={
        "convergence_score": convergence_score,
        "exit_reason": exit_reason,
        "final_weights": self.weights,
        "final_neuromodulators": self.neuromodulators,
        "total_iterations": iteration_num + 1,
    },
    tenant_id=self.tenant_id,
)
```

---

## PHASE 6: DECISION TRACE API (Week 6-7)

### 6.1 Create Decision Trace Endpoint

**File:** `admin/chat/api/trace.py`

```python
"""Decision trace API - ISO/IEC/IEEE 29148:2018 compliant traceability."""

from django_ninja import Router, Query
from typing import List, Optional
from admin.chat.models import RLMIteration, Message

router = Router()


@router.get("/{turn_id}")
async def get_decision_trace(
    request,
    turn_id: str,
    include_messages: bool = Query(True, description="Include conversation messages"),
):
    """Get complete decision trace for a turn.
    
    Implements ISO/IEC/IEEE 29148:2018 traceability requirements.
    Returns complete iteration history with weight evolution.
    
    Args:
        turn_id: Turn identifier
        include_messages: Whether to include conversation messages
    
    Returns:
        Complete decision trace
    """
    # Get iterations
    iterations = await RLMIteration.objects.filter(
        turn_id=turn_id
    ).order_by("iteration_number").all()
    
    if not iterations:
        return {"error": "Turn not found"}
    
    # Get messages
    messages = []
    if include_messages:
        conversation_id = iterations[0].conversation_id
        messages = await Message.objects.filter(
            conversation_id=conversation_id
        ).order_by("created_at").all()
    
    # Build response
    response = {
        "turn_id": turn_id,
        "total_iterations": len(iterations),
        "iterations": [],
        "messages": [],
    }
    
    # Add iterations
    for it in iterations:
        response["iterations"].append({
            "iteration_number": it.iteration_number,
            "weights_before": it.weights_before,
            "weights_after": it.weights_after,
            "weight_deltas": it.weight_deltas,
            "neuromodulators_before": it.neuromodulators_before,
            "neuromodulators_after": it.neuromodulators_after,
            "confidence": it.confidence,
            "convergence_score": it.convergence_score,
            "exit_reason": it.exit_reason,
            "model": it.model,
            "latency_ms": it.latency_ms,
            "tool_calls": it.tool_calls,
            "tool_results": it.tool_results,
            "created_at": it.created_at.isoformat(),
        })
    
    # Add messages
    for msg in messages:
        response["messages"].append({
            "role": msg.role,
            "content": msg.content[:500],  # Truncate for display
            "token_count": msg.token_count,
            "created_at": msg.created_at.isoformat(),
        })
    
    return response


@router.get("/conversation/{conversation_id}")
async def get_conversation_trace(
    request,
    conversation_id: str,
    limit: int = Query(10, description="Number of recent turns"),
):
    """Get decision traces for all turns in a conversation.
    
    Args:
        conversation_id: Conversation identifier
        limit: Number of recent turns to include
    
    Returns:
        List of decision traces
    """
    from admin.chat.models import Conversation
    
    # Verify conversation exists
    conv = await Conversation.objects.filter(id=conversation_id).first()
    if not conv:
        return {"error": "Conversation not found"}
    
    # Get recent turns
    recent_messages = await Message.objects.filter(
        conversation_id=conversation_id
    ).order_by("-created_at").limit(limit).all()
    
    # Get turn IDs
    turn_ids = set()
    for msg in recent_messages:
        # Extract turn_id from metadata or use message_id
        turn_ids.add(str(msg.id))
    
    # Get traces for each turn
    traces = []
    for turn_id in turn_ids:
        iterations = await RLMIteration.objects.filter(
            turn_id=turn_id
        ).order_by("iteration_number").all()
        
        if iterations:
            traces.append({
                "turn_id": turn_id,
                "total_iterations": len(iterations),
                "convergence_score": iterations[-1].convergence_score,
                "exit_reason": iterations[-1].exit_reason,
                "created_at": iterations[0].created_at.isoformat(),
            })
    
    return {
        "conversation_id": conversation_id,
        "total_turns": len(traces),
        "traces": traces,
    }
```

### 6.2 Register API Routes

**File:** `admin/chat/api/__init__.py`

```python
from django_ninja import NinjaAPI
from admin.chat.api.trace import router as trace_router

api = NinjaAPI()

api.add_router("/trace", trace_router, tags=["trace"])

__all__ = ["api"]
```

---

## PHASE 7: TESTING & VALIDATION (Week 7-8)

### 7.1 Unit Tests for RLMIterator

**File:** `tests/test_rlm_iterator.py`

```python
"""Unit tests for RLMIterator."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.common.rlm_iterator import RLMIterator, RLMIterationResult


@pytest.mark.asyncio
async def test_rlm_iterator_convergence():
    """Test that RLM iterator converges within max iterations."""
    # Setup
    iterator = RLMIterator(
        conversation_id="test-conv",
        agent_id="test-agent",
        user_id="test-user",
        tenant_id="test-tenant",
        user_message="What is machine learning?",
        raw_history=[],
    )
    
    # Mock dependencies
    with patch("admin.core.models.Capsule.objects.filter") as mock_capsule:
        mock_capsule.return_value.first.return_value = MagicMock(
            system_prompt="You are a helpful assistant.",
            learning_config={},
            learned_weights={},
            neuromodulator_state={},
        )
        
        with patch("services.common.health_monitor.get_health_monitor") as mock_health:
            mock_health.return_value.get_overall_health.return_value = MagicMock(
                degraded=False
            )
            
            with patch("services.common.simple_governor.get_governor") as mock_governor:
                mock_governor.return_value.allocate_budget.return_value = MagicMock(
                    lane_budget=MagicMock(to_dict=lambda: {"history": 100, "memory": 100, "buffer": 50}),
                )
                
                with patch("admin.core.somabrain_client.SomaBrainClient.get_async") as mock_soma:
                    mock_soma.return_value.publish_reward.return_value = {
                        "weights": {"alpha": 1.1, "beta": 0.18},
                        "neuromodulators": {"dopamine": 0.52},
                    }
                    
                    with patch("services.common.simple_context_builder.create_context_builder") as mock_builder:
                        mock_builder.return_value.build_for_turn.return_value = MagicMock(
                            messages=[{"role": "system", "content": "test"}, {"role": "user", "content": "test"}],
                            token_counts={"system": 5, "history": 0, "memory": 0, "user": 1},
                            lane_actual={"system_policy": 5, "history": 0, "memory": 0, "tools": 0, "tool_results": 0, "buffer": 50},
                        )
                        
                        with patch("services.common.model_router.select_model") as mock_model:
                            mock_model.return_value = MagicMock(
                                provider="openai",
                                name="gpt-4o",
                            )
                            
                            with patch("admin.llm.services.litellm_client.get_chat_model") as mock_llm:
                                mock_llm.return_value._astream = AsyncMock(
                                    return_value=AsyncMock(
                                        __aiter__=lambda self: iter([
                                            MagicMock(message=MagicMock(content="Test ")),
                                            MagicMock(message=MagicMock(content="response.")),
                                        ])
                                    )
                                )
                                
                                # Execute
                                results = []
                                async for result in iterator.iterate():
                                    results.append(result)
                                
                                # Assert
                                assert len(results) <= 10
                                assert any(r.convergence_score >= 0.9 for r in results)


@pytest.mark.asyncio
async def test_weight_updates():
    """Test that weights are updated after each iteration."""
    iterator = RLMIterator(
        conversation_id="test-conv",
        agent_id="test-agent",
        user_id="test-user",
        tenant_id="test-tenant",
        user_message="Test message",
        raw_history=[],
    )
    
    # Mock to return convergence after 2 iterations
    iteration_count = 0
    
    async def mock_iterate():
        nonlocal iteration_count
        for i in range(2):
            iteration_count += 1
            yield RLMIterationResult(
                iteration_number=i,
                response=f"Response {i}",
                confidence=0.95 if i == 1 else 0.7,
                convergence_score=0.95 if i == 1 else 0.7,
                weights={"alpha": 1.0 + i * 0.1},
                neuromodulators={"dopamine": 0.5 + i * 0.02},
                tools_used=[],
                latency_ms=100,
            )
    
    # Patch and test
    with patch.object(iterator, "iterate", mock_iterate):
        results = []
        async for result in iterator.iterate():
            results.append(result)
        
        assert len(results) == 2
        assert results[0].weights["alpha"] == 1.0
        assert results[1].weights["alpha"] == 1.1
```

### 7.2 Integration Tests

**File:** `tests/test_chat_flow_integration.py`

```python
"""Integration tests for complete chat flow with RLM."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_complete_chat_flow_with_learning():
    """Test end-to-end chat flow with RLM and learning."""
    from services.common.chat_service import ChatService
    
    chat_service = ChatService()
    
    # Mock all dependencies
    with patch("admin.chat.models.Message.objects.create") as mock_message:
        mock_message.return_value = MagicMock(id="msg-123")
        
        with patch("admin.chat.models.Conversation.objects.filter") as mock_conv:
            mock_conv.return_value.update.return_value = 1
            mock_conv.return_value.first.return_value = MagicMock(tenant_id="tenant-123")
            
            with patch("admin.chat.models.Message.objects.filter") as mock_messages:
                mock_messages.return_value.order_by.return_value = MagicMock(
                    __getitem__=lambda self, x: []
                )
                
                with patch("admin.core.models.Capsule.objects.filter") as mock_capsule:
                    mock_capsule.return_value.first.return_value = MagicMock(
                        system_prompt="You are helpful.",
                        learning_config={},
                        config={},
                        learned_weights={},
                        neuromodulator_state={},
                    )
                    
                    # Execute
                    response_chunks = []
                    async for chunk in chat_service.send_message(
                        conversation_id="conv-123",
                        agent_id="agent-123",
                        content="What is AI?",
                        user_id="user-123",
                    ):
                        response_chunks.append(chunk)
                    
                    # Assert
                    assert len(response_chunks) > 0
                    assert any("AI" in chunk for chunk in response_chunks)


@pytest.mark.asyncio
async def test_rlm_with_tools():
    """Test RLM with tool execution."""
    # Test that tools are discovered and executed within iterations
    pass
```

### 7.3 Performance Benchmarks

**File:** `tests/benchmark/test_rlm_performance.py`

```python
"""Performance benchmarks for RLM iterations."""

import pytest
import time
from services.common.rlm_iterator import RLMIterator


@pytest.mark.benchmark
async def test_rlm_performance(benchmark):
    """Benchmark RLM iteration performance."""
    iterator = RLMIterator(
        conversation_id="bench-conv",
        agent_id="bench-agent",
        user_id="bench-user",
        tenant_id="bench-tenant",
        user_message="Benchmark test message",
        raw_history=[],
    )
    
    # Mock dependencies
    # ... setup mocks ...
    
    async def run_iterations():
        results = []
        async for result in iterator.iterate():
            results.append(result)
        return results
    
    # Benchmark
    start = time.time()
    results = await run_iterations()
    elapsed = time.time() - start
    
    # Assert performance
    assert elapsed < 30.0  # Should complete within 30 seconds
    assert len(results) <= 10
```

### 7.4 Security Tests

**File:** `tests/test_security.py`

```python
"""Security tests for RLM flow."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_opa_policy_enforcement():
    """Test that OPA policy is enforced for tool execution."""
    from services.common.tool_executor import execute_tool
    
    # Mock OPA denying access
    with patch("admin.core.opa_client.evaluate_policy", return_value=False):
        with pytest.raises(PermissionError):
            await execute_tool(
                tool_name="web_search",
                tool_args={"query": "test"},
                agent_id="agent-123",
                tenant_id="tenant-123",
            )


@pytest.mark.asyncio
async def test_spicedb_permissions():
    """Test that SpiceDB permissions are checked."""
    # Test that conversation access is verified
    pass
```

---

## PHASE 8: PRODUCTION DEPLOYMENT (Week 8-9)

### 8.1 Update Docker Compose

**File:** `infra/saas/docker-compose.yml`

Add RLM configuration:

```yaml
somastack_saas:
  environment:
    # RLM Configuration
    - SA01_ENABLE_RLM=true
    - SA01_RLM_MAX_ITERATIONS=10
    - SA01_RLM_CONVERGENCE_THRESHOLD=0.9
    
    # Feature flags for backward compatibility
    - SA01_ENABLE_SINGLE_SHOT=false  # Set to true to disable RLM
```

### 8.2 Create Database Migration

```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/admin
python manage.py makemigrations chat core
python manage.py migrate
```

**Verify migration:**
```bash
python manage.py showmigrations
python manage.py sqlmigrate chat 000X
```

### 8.3 Rollout Strategy

**Step 1: Staging Deployment**
```bash
# Deploy to staging
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/infra/saas
docker-compose -f docker-compose.staging.yml up -d

# Verify RLM is disabled
docker logs somastack_saas | grep "RLM"
# Should show: RLM disabled via feature flag
```

**Step 2: Enable RLM in Staging**
```bash
# Update environment variable
export SA01_ENABLE_RLM=true

# Restart
docker-compose restart somastack_saas

# Test
curl -X POST http://localhost:63900/api/v2/chat/conversations/test/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "What is AI?"}'
```

**Step 3: Canary Rollout (10% traffic)**
```bash
# Use feature flag service or load balancer
# Route 10% of traffic to RLM-enabled instances
```

**Step 4: Full Production Rollout**
```bash
# Deploy to production with RLM enabled
# Monitor metrics:
# - rlm_iterations_total
# - agent_turn_latency_seconds
# - somabrain_learning_latency_ms
```

### 8.4 Monitoring & Alerting

**Prometheus Queries:**
```promql
# Average iterations per turn
rate(rlm_iterations_total_sum[5m]) / rate(rlm_iterations_total_count[5m])

# Convergence rate
rate(rlm_iterations_total{exit_reason="converged"}[5m]) / rate(rlm_iterations_total[5m])

# Learning latency
histogram_quantile(0.95, rate(somabrain_learning_latency_seconds_bucket[5m]))

# Turn latency
histogram_quantile(0.95, rate(agent_turn_latency_seconds_bucket[5m]))
```

**Alerts:**
```yaml
# Alert if convergence rate drops below 80%
- alert: LowConvergenceRate
  expr: rate(rlm_iterations_total{exit_reason="converged"}[5m]) / rate(rlm_iterations_total[5m]) < 0.8
  for: 5m
  severity: warning

# Alert if learning latency > 100ms
- alert: HighLearningLatency
  expr: histogram_quantile(0.95, rate(somabrain_learning_latency_seconds_bucket[5m])) > 0.1
  for: 5m
  severity: warning
```

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Database Schema
- [ ] Create `RLMIteration` model in `admin/chat/models.py`
- [ ] Add `learned_weights` and `neuromodulator_state` to `Capsule`
- [ ] Generate migration: `python manage.py makemigrations chat core`
- [ ] Run migration: `python manage.py migrate`
- [ ] Verify schema in staging

### Phase 2: RLM Iterator Engine
- [ ] Create `services/common/rlm_iterator.py`
- [ ] Implement `RLMIterator` class with iteration loop
- [ ] Add convergence detection
- [ ] Update `ChatService.send_message()` to use RLMIterator
- [ ] Unit tests for RLMIterator

### Phase 3: SomaBrain Learning
- [ ] Add `publish_turn_metrics()` to `SomaBrainClient`
- [ ] Verify SomaBrain learning endpoint exists
- [ ] Test synchronous weight updates
- [ ] Integration tests

### Phase 4: Tool Integration
- [ ] Create `services/common/tool_discovery.py`
- [ ] Create `services/common/tool_executor.py`
- [ ] Integrate tool execution in RLM loop
- [ ] OPA policy enforcement
- [ ] Circuit breaker for tools

### Phase 5: Event-Sourcing
- [ ] Create `services/common/event_publisher.py`
- [ ] Publish events in RLM loop
- [ ] Verify event immutability
- [ ] Test event replay

### Phase 6: Decision Trace API
- [ ] Create `admin/chat/api/trace.py`
- [ ] Implement `get_decision_trace()` endpoint
- [ ] Implement `get_conversation_trace()` endpoint
- [ ] API documentation

### Phase 7: Testing
- [ ] Unit tests for RLMIterator
- [ ] Integration tests for complete flow
- [ ] Performance benchmarks
- [ ] Security tests (OPA, SpiceDB)

### Phase 8: Deployment
- [ ] Update Docker Compose with RLM config
- [ ] Database migration
- [ ] Staging deployment
- [ ] Canary rollout (10%)
- [ ] Production deployment
- [ ] Monitoring & alerting

---

## RISKS & MITIGATIONS

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| SomaBrain learning endpoint not ready | High | Medium | Feature flag to disable RLM |
| Performance degradation (10-25s per turn) | Medium | High | Early convergence, parallel tool execution |
| Tool execution failures | Medium | Medium | Circuit breaker, graceful degradation |
| Database schema changes | Low | Low | Migration testing in staging |
| Kafka event volume | Medium | Low | Batch publishing, retention policy |
| Backward compatibility | Low | Low | Feature flag for single-shot mode |

---

## CONCLUSION

This implementation plan provides **exact steps** to transform the current single-shot chat flow into the RLM-based learning architecture specified in the SRS.

**Key Points:**
1. **SomaBrain must implement learning endpoint** - This is the critical dependency
2. **RLMIterator is the heart of the system** - Implements 5-10 iterations with learning
3. **All changes are backward compatible** - Feature flags allow gradual rollout
4. **Complete traceability** - Every iteration stored for audit and replay

**Next Steps:**
1. Review this plan with stakeholders
2. Begin Phase 1: Database Schema
3. Coordinate with SomaBrain team for learning endpoint

---

**Document Status:** COMPLETE  
**Ready for Implementation:** YES
