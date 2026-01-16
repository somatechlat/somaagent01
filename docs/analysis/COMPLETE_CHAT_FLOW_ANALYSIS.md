# COMPLETE CHAT FLOW ANALYSIS & IMPLEMENTATION PLAN

**Document ID:** ANALYSIS-CHAT-FLOW-2026-01-15  
**Version:** 1.0.0  
**Status:** ANALYSIS COMPLETE - READY FOR IMPLEMENTATION  
**Date:** January 15, 2026  
**Authors:** All VIBE Personas (PhD Developer, Analyst, QA, ISO Documenter, Security, Performance, UX, Django Architect, Django Infra Expert, Django Evangelist)

---

## EXECUTIVE SUMMARY

After comprehensive analysis of the existing codebase and the SRS-COMPLETE-PERFECT-CHAT-FLOW-SOMABRAIN-LEARNING-ISO.md specification, I have identified **critical gaps** between the current implementation and the RLM-based learning architecture specified in the SRS.

### Current State (What Exists)
- ✅ **Basic Chat Flow**: Single-shot LLM calls via `ChatService.send_message()`
- ✅ **SomaBrain Integration**: HTTP client for memory recall/store (via `SomaBrainClient`)
- ✅ **Capsule System**: Django ORM models for agent identity (`Capsule`, `Capability`)
- ✅ **Tool Registry**: Basic tool discovery via `Capability` M2M relationships
- ✅ **Model Router**: Capability-based model selection from `LLMModelConfig`
- ✅ **Governor**: Token budget allocation (normal/degraded modes)
- ✅ **Health Monitor**: Binary health checking
- ✅ **Metrics**: Unified Prometheus metrics
- ✅ **SaaS Deployment**: Docker Compose with all infrastructure

### Target State (What SRS Specifies)
- ❌ **RLM Iteration Loop**: 5-10 iterations per turn with convergence detection
- ❌ **Synchronous Learning**: `SomaBrain.publish_turn_metrics()` called after EVERY iteration
- ❌ **Weight Updates**: α, β, γ, τ, λ, μ, ν parameters updated per iteration
- ❌ **Neuromodulator System**: Dopamine-gated learning rates
- ❌ **Tool Execution in Loop**: Tools executed within RLM iterations
- ❌ **Convergence Assessment**: Early exit on confidence >= 0.9
- ❌ **RLMIteration Model**: Store complete iteration data (weights_before, weights_after, etc.)
- ❌ **Event-Sourcing**: Kafka event log for replayability
- ❌ **Decision Trace**: Complete trace accessible per turn

### Critical Gap: No Direct SomaFractalMemory Access
**IMPORTANT:** The SRS explicitly states: "somaAgent01 has ZERO direct access to SomaFractalMemory" (ARCH-001). All memory operations must go through SomaBrain. The current implementation correctly uses `SomaBrainClient` for all memory operations, which is compliant.

---

## 1. ARCHITECTURE ANALYSIS

### 1.1 Current Architecture (Production-Ready)

```
User → ChatAPI → PostgreSQL (Message/Conversation) → Model Router → LLM → Response
                              ↓
                        SomaBrainClient (HTTP)
                              ↓
                        SomaBrain (Memory)
                              ↓
                        PostgreSQL (Outbox)
                              ↓
                        Kafka (WAL)
                              ↓
                        SomaFractalMemory (Async)
```

**Key Characteristics:**
- **Single-shot flow**: One LLM call per user message
- **No iteration**: No RLM loop, no convergence detection
- **No learning**: No weight updates, no neuromodulator integration
- **Async memory**: Memory storage is fire-and-forget (non-blocking)
- **Graceful degradation**: Works when SomaBrain is unavailable

### 1.2 Target Architecture (SRS Specification)

```
User → ChatAPI → PostgreSQL → Capsule → Model Router → RLM Iterator (5-10 loops)
                              ↓                              ↓
                        SomaBrainClient ←→ SomaBrain.publish_turn_metrics()
                              ↓                              ↓
                        PostgreSQL (RLMIteration) ←→ Weight Updates (α,β,γ,τ,λ,μ,ν)
                              ↓
                        Kafka (Event Log - Replayable)
                              ↓
                        SomaFractalMemory (Async)
```

**Key Characteristics:**
- **RLM Loop**: 5-10 iterations per turn with convergence detection
- **Synchronous Learning**: Learning happens IN-PROCESS after every iteration
- **Weight Updates**: 7 parameters updated per iteration via SomaBrain
- **Neuromodulators**: Dopamine, serotonin, noradrenaline, acetylcholine
- **Event-Sourcing**: All decisions logged to Kafka for replay
- **Traceability**: Complete decision trace per turn

---

## 2. CRITICAL IMPLEMENTATION GAPS

### 2.1 Missing: RLMIteration Django Model

**Current:** No model to store iteration data  
**Required:** Model with fields:
- `turn_id`, `iteration_number`
- `weights_before`, `weights_after`, `weight_deltas`
- `neuromodulators_before`, `neuromodulators_after`
- `tool_calls`, `tool_results`
- `confidence`, `latency_ms`
- `convergence_score`

### 2.2 Missing: RLM Iterator Engine

**Current:** `ChatService.send_message()` makes single LLM call  
**Required:** Loop with 5-10 iterations:
1. Build context with current weights
2. Call LLM (deterministic with seed)
3. Parse tool calls from response
4. Execute tools (with OPA policy check)
5. **CRITICAL:** Call `SomaBrain.publish_turn_metrics()` ← LEARNING HAPPENS HERE
6. Receive updated weights from SomaBrain
7. Store iteration in PostgreSQL
8. Assess convergence (confidence >= 0.9)
9. Loop or exit

### 2.3 Missing: Synchronous Learning Integration

**Current:** `SomaBrainClient` only provides HTTP API for memory operations  
**Required:** `SomaBrain.publish_turn_metrics()` method that:
- Accepts iteration data (tools_used, confidence, latency, etc.)
- Computes salience: `salience = w_novelty * novelty + w_error * error`
- Updates neuromodulators (dopamine, serotonin, noradrenaline, acetylcholine)
- Updates weights: `p_new = clamp(p_old + lr_eff * gain_p * signal, p_min, p_max)`
- Returns updated weights to chat flow
- **Must be SYNCHRONOUS** (not async task)

### 2.4 Missing: Tool Execution in RLM Loop

**Current:** Tools are not executed in the chat flow  
**Required:** Tools executed within RLM iterations:
- Parse tool calls from LLM response
- Check OPA policy before execution
- Execute tools with circuit breaker
- Store results for next iteration
- Send tool success/failure signals to SomaBrain

### 2.5 Missing: Convergence Detection

**Current:** No convergence logic  
**Required:** Assess after each iteration:
- `convergence_score = confidence × success_factor × tool_utility`
- Exit if `convergence_score >= threshold` (default 0.9)
- Exit if `iteration_number == max_iterations - 1`
- Exit if LLM stop_reason == "end_turn"

### 2.6 Missing: Event-Sourcing & Replayability

**Current:** No Kafka event logging for chat flow  
**Required:** Publish immutable events:
- `chat.turn_started`
- `chat.iteration_completed`
- `chat.turn_complete`
- Event contains: turn_id, weights_before/after, tools_executed, etc.

### 2.7 Missing: Decision Trace API

**Current:** No API to retrieve complete decision trace  
**Required:** API endpoint to query:
- All RLMIterations for a turn
- Weight evolution across iterations
- Tool execution results
- Convergence decision

---

## 3. IMPLEMENTATION PLAN

### 3.1 Phase 1: Database Schema (Week 1)

**Task 1.1: Create RLMIteration Model**

```python
# admin/chat/models.py (add after Message model)

class RLMIteration(models.Model):
    """RLM iteration record - stores complete iteration data for replayability."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turn_id = models.UUIDField(db_index=True)
    conversation_id = models.UUIDField(db_index=True)
    
    iteration_number = models.IntegerField()
    
    # Weights (α, β, γ, τ, λ, μ, ν)
    weights_before = models.JSONField(default=dict)
    weights_after = models.JSONField(default=dict)
    weight_deltas = models.JSONField(default=dict)
    
    # Neuromodulators
    neuromodulators_before = models.JSONField(default=dict)
    neuromodulators_after = models.JSONField(default=dict)
    
    # LLM call
    model = models.CharField(max_length=100)
    confidence = models.FloatField()
    latency_ms = models.IntegerField()
    
    # Tools
    tool_calls = models.JSONField(default=list)
    tool_results = models.JSONField(default=list)
    
    # Context
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    
    # Convergence
    convergence_score = models.FloatField()
    exit_reason = models.CharField(max_length=50, null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "rlm_iterations"
        ordering = ["turn_id", "iteration_number"]
        indexes = [
            models.Index(fields=["turn_id", "iteration_number"]),
            models.Index(fields=["conversation_id", "created_at"]),
        ]
    
    def __str__(self):
        return f"RLMIteration({self.turn_id}:{self.iteration_number})"
```

**Task 1.2: Add Weights to Capsule**

```python
# admin/core/models.py (Capsule model - add fields)

class Capsule(models.Model):
    # ... existing fields ...
    
    # Learned weights (updated by SomaBrain)
    learned_weights = models.JSONField(
        default=dict,
        help_text="Current learned weights: α, β, γ, τ, λ, μ, ν"
    )
    
    # Neuromodulator state
    neuromodulator_state = models.JSONField(
        default=dict,
        help_text="Current neuromodulator levels"
    )
```

**Task 1.3: Create Migration**

```bash
cd admin
python manage.py makemigrations chat core
python manage.py migrate
```

### 3.2 Phase 2: RLM Iterator Engine (Week 2-3)

**Task 2.1: Create RLMIterator Class**

```python
# services/common/rlm_iterator.py

from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator, Optional
from uuid import uuid4

from admin.core.models import Capsule
from admin.llm.models import LLMModelConfig
from admin.chat.models import RLMIteration
from services.common.model_router import select_model
from services.common.simple_governor import get_governor
from services.common.simple_context_builder import create_context_builder
from services.common.unified_metrics import get_metrics, TurnPhase
from admin.core.somabrain_client import SomaBrainClient

logger = logging.getLogger(__name__)


class RLMIterator:
    """Recursive Language Model Iterator - The Heart of Learning."""
    
    def __init__(
        self,
        conversation_id: str,
        agent_id: str,
        user_id: str,
        tenant_id: str,
        user_message: str,
        raw_history: list[dict],
    ):
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.user_message = user_message
        self.raw_history = raw_history
        self.turn_id = str(uuid4())
        
        # Load capsule
        self.capsule = None
        self.system_prompt = ""
        self.learning_config = {}
        
        # Weights (start with capsule defaults or zeros)
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
        self.iteration_results = []
        self.max_iterations = 10
        self.convergence_threshold = 0.9
        
    async def initialize(self) -> None:
        """Load capsule and initialize state."""
        from asgiref.sync import sync_to_async
        
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
        
        logger.info(f"RLMIterator initialized for turn {self.turn_id[:8]}")
    
    async def iterate(self) -> AsyncIterator[dict]:
        """Execute RLM iterations and yield results."""
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
        from admin.llm.services.litellm_client import get_chat_model
        
        # Initialize metrics
        metrics = get_metrics()
        turn_metrics = metrics.record_turn_start(
            turn_id=self.turn_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            agent_id=self.agent_id,
        )
        
        # Load capsule and models
        await self.initialize()
        
        # Get health status
        from services.common.health_monitor import get_health_monitor
        health_monitor = get_health_monitor()
        overall_health = health_monitor.get_overall_health()
        is_degraded = overall_health.degraded
        
        # Allocate budget
        governor = get_governor()
        from django.conf import settings
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
        capsule_body = {"allowed_models": self.capsule.config.get("allowed_models", []) if self.capsule else []}
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
            
            # Deterministic seed
            seed = int(self.turn_id, 16) % (2**32)
            
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
            if learning_result and isinstance(learning_result, dict):
                updated_weights = learning_result.get("weights", {})
                updated_neuromodulators = learning_result.get("neuromodulators", {})
                
                # Compute deltas
                weight_deltas = {}
                for key in self.weights:
                    if key in updated_weights:
                        weight_deltas[key] = updated_weights[key] - self.weights[key]
                
                # Update local state
                self.weights.update(updated_weights)
                self.neuromodulators.update(updated_neuromodulators)
            
            # 7. Store RLMIteration
            iteration = RLMIteration(
                turn_id=self.turn_id,
                conversation_id=self.conversation_id,
                iteration_number=iteration_num,
                weights_before=self.weights,  # Before update
                weights_after=updated_weights if learning_result else self.weights,
                weight_deltas=weight_deltas if learning_result else {},
                neuromodulators_before=self.neuromodulators,
                neuromodulators_after=updated_neuromodulators if learning_result else self.neuromodulators,
                model=f"{selected_model.provider}/{selected_model.name}",
                confidence=confidence,
                latency_ms=iteration_latency,
                tool_calls=tool_calls,
                tool_results=tool_results,
                prompt_tokens=len(built.messages),
                completion_tokens=len(full_response.split()),
                convergence_score=confidence,  # Simplified
                exit_reason=None,
            )
            
            @sync_to_async
            def save_iteration():
                iteration.save()
            
            await save_iteration()
            
            # 8. Assess convergence
            convergence_score = confidence  # Simplified
            
            # Yield result
            yield {
                "iteration_number": iteration_num,
                "response": full_response,
                "confidence": confidence,
                "convergence_score": convergence_score,
                "weights": self.weights.copy(),
                "neuromodulators": self.neuromodulators.copy(),
            }
            
            # 9. Check exit conditions
            if convergence_score >= self.convergence_threshold:
                logger.info(f"Converged at iteration {iteration_num} (score={convergence_score:.2f})")
                # Update iteration with exit reason
                iteration.exit_reason = "converged"
                await save_iteration()
                break
            
            if iteration_num == self.max_iterations - 1:
                logger.info(f"Max iterations reached at {iteration_num}")
                iteration.exit_reason = "max_iterations"
                await save_iteration()
                break
        
        # Update capsule with learned weights
        await self._update_capsule_weights()
        
        # Record completion metrics
        metrics.record_turn_complete(
            turn_id=self.turn_id,
            tokens_in=turn_metrics.tokens_in,
            tokens_out=sum(len(r["response"].split()) for r in self.iteration_results),
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
    
    async def _update_capsule_weights(self) -> None:
        """Update capsule with learned weights."""
        from asgiref.sync import sync_to_async
        
        @sync_to_async
        def update():
            if self.capsule:
                self.capsule.learned_weights = self.weights
                self.capsule.neuromodulator_state = self.neuromodulators
                self.capsule.save(update_fields=["learned_weights", "neuromodulator_state"])
        
        await update()
    
    async def _store_final_message(self, response: str, latency_ms: int) -> None:
        """Store final assistant message."""
        from asgiref.sync import sync_to_async
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

**Task 2.2: Update ChatService to Use RLMIterator**

```python
# services/common/chat_service.py (modify send_message method)

async def send_message(
    self, conversation_id: str, agent_id: str, content: str, user_id: str
) -> AsyncIterator[str]:
    """Send message with RLM iteration loop."""
    from services.common.rlm_iterator import RLMIterator
    
    # Load conversation and history
    # ... existing code ...
    
    # Create RLM iterator
    iterator = RLMIterator(
        conversation_id=conversation_id,
        agent_id=agent_id,
        user_id=user_id,
        tenant_id=tenant_id,
        user_message=content,
        raw_history=raw_history,
    )
    
    # Execute RLM iterations
    async for iteration_result in iterator.iterate():
        # Stream response to user
        yield iteration_result["response"]
        
        # Check if converged
        if iteration_result.get("convergence_score", 0) >= 0.9:
            break
```

### 3.3 Phase 3: SomaBrain Learning Integration (Week 3-4)

**Task 3.1: Add publish_turn_metrics to SomaBrainClient**

```python
# admin/core/somabrain_client.py (add method)

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

**Task 3.2: Update SRS to Clarify Learning Flow**

The SRS specifies learning happens at `SomaBrain.publish_turn_metrics()`. This method must:
1. Accept iteration data
2. Compute salience
3. Update neuromodulators
4. Update weights
5. Return updated weights

This is a **SomaBrain-side implementation**, not somaAgent01.

### 3.4 Phase 4: Tool Integration (Week 4-5)

**Task 4.1: Implement Tool Discovery from Capsule**

```python
# services/common/tool_discovery.py

async def discover_tools_from_capsule(agent_id: str) -> dict[str, dict]:
    """Discover tools from Capsule capabilities.
    
    Returns: {tool_name: tool_config}
    """
    from asgiref.sync import sync_to_async
    from admin.core.models import Capsule, Capability
    
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
    
    return await get_capsule_tools()
```

**Task 4.2: Implement Tool Execution in RLM Loop**

```python
# services/common/tool_executor.py

async def execute_tool(
    tool_name: str,
    tool_args: dict,
    agent_id: str,
    tenant_id: str,
) -> dict[str, Any]:
    """Execute a tool with OPA policy check."""
    from admin.core.somabrain_client import SomaBrainClient
    
    # Check OPA policy
    # ... OPA evaluation ...
    
    # Execute tool
    # ... tool execution ...
    
    # Send signal to SomaBrain
    somabrain = await SomaBrainClient.get_async()
    await somabrain.publish_reward(
        session_id=agent_id,
        signal="tool_execution",
        value=1.0 if success else -0.2,
        meta={"tool": tool_name, "success": success},
    )
    
    return result
```

### 3.5 Phase 5: Event-Sourcing (Week 5-6)

**Task 5.1: Create Kafka Event Publishing**

```python
# services/common/event_publisher.py

async def publish_chat_event(
    event_type: str,
    turn_id: str,
    payload: dict,
    tenant_id: str,
) -> None:
    """Publish immutable event to Kafka."""
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
```

**Task 5.2: Publish Events in RLM Loop**

```python
# In RLMIterator.iterate()

# After each iteration
await publish_chat_event(
    event_type="chat.iteration_completed",
    turn_id=self.turn_id,
    payload={
        "iteration_number": iteration_num,
        "confidence": confidence,
        "weights_before": self.weights,
        "weights_after": updated_weights,
        "tools_used": [t["name"] for t in tool_calls],
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
    },
    tenant_id=self.tenant_id,
)
```

### 3.6 Phase 6: Decision Trace API (Week 6-7)

**Task 6.1: Create Decision Trace Endpoint**

```python
# admin/chat/api/trace.py

from django_ninja import Router
from admin.chat.models import RLMIteration, Message

router = Router()

@router.get("/{turn_id}")
async def get_decision_trace(request, turn_id: str):
    """Get complete decision trace for a turn."""
    iterations = await RLMIteration.objects.filter(turn_id=turn_id).order_by("iteration_number").all()
    messages = await Message.objects.filter(conversation_id=iterations[0].conversation_id).all()
    
    return {
        "turn_id": turn_id,
        "iterations": [
            {
                "iteration_number": it.iteration_number,
                "weights_before": it.weights_before,
                "weights_after": it.weights_after,
                "weight_deltas": it.weight_deltas,
                "confidence": it.confidence,
                "convergence_score": it.convergence_score,
                "exit_reason": it.exit_reason,
            }
            for it in iterations
        ],
        "messages": [
            {
                "role": m.role,
                "content": m.content[:200],  # Truncate for display
                "created_at": m.created_at,
            }
            for m in messages
        ],
    }
```

### 3.7 Phase 7: Testing & Validation (Week 7-8)

**Task 7.1: Unit Tests for RLMIterator**

```python
# tests/test_rlm_iterator.py

import pytest
from services.common.rlm_iterator import RLMIterator

@pytest.mark.asyncio
async def test_rlm_iterator_convergence():
    """Test that RLM iterator converges within max iterations."""
    iterator = RLMIterator(
        conversation_id="test-conv",
        agent_id="test-agent",
        user_id="test-user",
        tenant_id="test-tenant",
        user_message="What is machine learning?",
        raw_history=[],
    )
    
    results = []
    async for result in iterator.iterate():
        results.append(result)
    
    assert len(results) <= 10
    assert any(r["convergence_score"] >= 0.9 for r in results)

@pytest.mark.asyncio
async def test_weight_updates():
    """Test that weights are updated after each iteration."""
    # ... test implementation ...
```

**Task 7.2: Integration Tests**

```python
# tests/test_chat_flow.py

@pytest.mark.asyncio
async def test_complete_chat_flow_with_learning():
    """Test end-to-end chat flow with RLM and learning."""
    # ... test implementation ...
```

**Task 7.3: Performance Tests**

```bash
# Benchmark RLM iterations
pytest tests/benchmark/test_rlm_performance.py --benchmark-only
```

### 3.8 Phase 8: Production Deployment (Week 8-9)

**Task 8.1: Update Docker Compose**

```yaml
# infra/saas/docker-compose.yml (add SomaBrain learning service)

somastack_saas:
  environment:
    - SA01_ENABLE_RLM=true
    - SA01_RLM_MAX_ITERATIONS=10
    - SA01_RLM_CONVERGENCE_THRESHOLD=0.9
```

**Task 8.2: Database Migration**

```bash
cd admin
python manage.py makemigrations chat core
python manage.py migrate
```

**Task 8.3: Rollout Strategy**

1. **Staging**: Deploy with RLM disabled (feature flag)
2. **Canary**: Enable RLM for 10% of traffic
3. **Full Rollout**: Enable for all tenants

---

## 4. CRITICAL CONSIDERATIONS

### 4.1 Performance Impact

**Current:** ~2-5 seconds per turn (single LLM call)  
**Target:** ~10-25 seconds per turn (5-10 iterations)

**Mitigation:**
- Early convergence (confidence >= 0.9) reduces average iterations
- Parallel tool execution where possible
- Optimized context building (caching)

### 4.2 SomaBrain Integration

**Critical:** The SRS specifies `SomaBrain.publish_turn_metrics()` must be **synchronous** and return updated weights immediately.

**Current:** `SomaBrainClient` only provides HTTP API  
**Required:** SomaBrain must implement learning endpoint that:
- Accepts iteration data
- Computes salience and updates weights
- Returns updated weights in response
- **Must be fast** (< 50ms) to avoid adding latency

### 4.3 Tool Execution Complexity

**Current:** No tool execution in chat flow  
**Required:** Tools executed within RLM iterations with:
- OPA policy enforcement
- Circuit breaker protection
- Timeout handling
- Result storage for next iteration

### 4.4 Memory Operations

**Current:** Memory operations are async (fire-and-forget)  
**Required:** Memory operations remain async, but learning signals must be synchronous

**Clarification:** The SRS states "All learning happens synchronously through SomaBrain". This refers to `publish_turn_metrics()`, not memory storage.

### 4.5 Backward Compatibility

**Current:** Single-shot flow works  
**Required:** RLM flow must be feature-flagged:
- `SA01_ENABLE_RLM=true` to enable RLM iterations
- `SA01_ENABLE_RLM=false` to use single-shot (current behavior)

---

## 5. IMPLEMENTATION CHECKLIST

### Phase 1: Database Schema
- [ ] Create `RLMIteration` model
- [ ] Add `learned_weights` and `neuromodulator_state` to `Capsule`
- [ ] Generate and run migrations
- [ ] Verify schema in staging

### Phase 2: RLM Iterator Engine
- [ ] Create `RLMIterator` class
- [ ] Implement iteration loop (0-10)
- [ ] Add convergence detection
- [ ] Integrate with `ChatService.send_message()`
- [ ] Unit tests for iterator

### Phase 3: SomaBrain Learning
- [ ] Add `publish_turn_metrics()` to `SomaBrainClient`
- [ ] Verify SomaBrain learning endpoint exists
- [ ] Test synchronous weight updates
- [ ] Integration tests

### Phase 4: Tool Integration
- [ ] Implement tool discovery from Capsule
- [ ] Add tool execution in RLM loop
- [ ] OPA policy enforcement
- [ ] Circuit breaker for tools

### Phase 5: Event-Sourcing
- [ ] Create Kafka event publishing
- [ ] Publish events in RLM loop
- [ ] Verify event immutability
- [ ] Test event replay

### Phase 6: Decision Trace API
- [ ] Create trace endpoint
- [ ] Query RLMIteration and Message tables
- [ ] Format response
- [ ] API documentation

### Phase 7: Testing
- [ ] Unit tests for RLMIterator
- [ ] Integration tests for complete flow
- [ ] Performance benchmarks
- [ ] Security tests (OPA, SpiceDB)

### Phase 8: Deployment
- [ ] Update Docker Compose
- [ ] Database migration
- [ ] Staging deployment
- [ ] Canary rollout
- [ ] Production deployment

---

## 6. RISKS & MITIGATIONS

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| SomaBrain learning endpoint not ready | High | Medium | Feature flag to disable RLM |
| Performance degradation | Medium | High | Early convergence, parallel execution |
| Tool execution failures | Medium | Medium | Circuit breaker, graceful degradation |
| Database schema changes | Low | Low | Migration testing in staging |
| Kafka event volume | Medium | Low | Batch publishing, retention policy |

---

## 7. CONCLUSION

The current implementation provides a **production-ready single-shot chat flow** with SomaBrain integration. The SRS specifies a **complete RLM-based learning architecture** that requires significant additional implementation.

**Key Takeaways:**
1. **SomaBrain must implement learning endpoint** (`publish_turn_metrics()`)
2. **RLMIterator must be added** to somaAgent01
3. **RLMIteration model must be created** for traceability
4. **Tool execution must be integrated** into RLM loop
5. **Event-sourcing must be implemented** for replayability
6. **All changes must be feature-flagged** for backward compatibility

**Recommendation:** Implement in phases, starting with database schema and RLMIterator, then integrate SomaBrain learning, then add tools and event-sourcing.

---

**Document Status:** COMPLETE  
**Next Steps:** Begin Phase 1 implementation
