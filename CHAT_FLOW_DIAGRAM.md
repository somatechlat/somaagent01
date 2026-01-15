# COMPLETE CHAT MESSAGE FLOW DIAGRAM

**User Message → LLM → Back to User**

Based on real codebase: `services/common/chat_service.py`

---

## 🔄 MERMAID DIAGRAM

```mermaid
sequenceDiagram
    participant User as User
    participant ChatAPI as ChatAPI
    participant Database as PostgreSQL
    participant Governor as Gov
    participant Context as CB
    participant Health as Health
    participant Capsule as Caps
    participant ModelRouter as MR
    participant LLM as LLM
    participant SomaBrain as Brain
    participant Memory as MemStore
    participant Metrics as Prometheus

    autonumber

    User->>ChatAPI: HTTP POST /chat/conversations/{id}/messages
    Note over User: +Message content

    rect # STAGE 1: Store User Message (Line 243-261)
    ChatAPI->>PostgreSQL: INSERT Message (role="user", content, token_count)
    PostgreSQL-->>ChatAPI: Message stored with ID
    Note over PostgreSQL: +Trace Registry updated
    ChatAPI-->>Prometheus: CHAT_REQUESTS.inc("send_message", start)

    rect # STAGE 2: Load Conversation & History (Line 263-278)
    ChatAPI->>PostgreSQL: SELECT Conversation
    PostgreSQL-->>ChatAPI: Conversation + tenant_id
    ChatAPI->>PostgreSQL: SELECT Messages (ORDER BY created_at DESC LIMIT 20)
    PostgreSQL-->>ChatAPI: Raw history (max 20 messages, reversed)
    Note over ChatAPI: +tenant_id + raw_history loaded

    rect # STAGE 3: Load Capsule (Line 294-306)
    ChatAPI->>PostgreSQL: SELECT Capsule WHERE id=agent_id
    PostgreSQL-->>ChatAPI: Capsule record
    Note over ChatAPI: +system_prompt (The Soul) + config
    Note over ChatAPI: NO HARDCODING default system_prompt

    rect # STAGE 4: Detect Required Capabilities (Line 308-327)
    ChatAPI->>MR: detect_required_capabilities(content)
    Note over MR: +Analyze content for: attachments, images, code, etc.
    MR-->>ChatAPI: required_caps list
    Note over MR: NO hardcoded fallback values

    rect # STAGE 5: Select Model via Router (Line 329-363)
    ChatAPI->>PostgreSQL: SELECT LLMModelConfig (capability-based routing)
    Note over ChatAPI: SINGLE SOURCE OF TRUTH
    ChatAPI->>MR: select_model(required_caps, capsule_body)
    MR-->>ChatAPI: SelectedModel (provider, name, priority)
    Note over MR: No hardcoded model selection

    rect # STAGE 6: Get Health Status (Line 365-375)
    ChatAPI->>Health: get_overall_health()
    Note over Health: Check service status (SomaBrain, Database, LLM)
    Health-->>ChatAPI: OverallHealth (degraded: bool, critical: bool)
    Note over ChatAPI: is_degraded flag

    rect # STAGE 7: Allocate Budget via Governor (Line 377-395)
    ChatAPI->>Gov: allocate_budget(max_tokens, is_degraded)
    Note over Gov: FIXED production ratios (Normal vs Degraded)
    Gov-->>ChatAPI: GovernorDecision (lane_budget, health_status, mode)
    Note over Gov:
    - NORMAL: system=15%, history=25%, memory=25%, tools=20%, buffer=5%
    - DEGRADED: system=40%, history=10%, memory=15%, tools=0%, buffer=35%

    rect # STAGE 8: Initialize SomaBrain Client (Line 397-423)
    alt Disconnected
    ChatAPI->>Brain: SomaBrainClient.get_async()
    Note over SomaBrain: HTTP connection established
    Note over ChatAPI: SAAS mode = HTTP client, STANDALONE = embedded modules
    Brain-->>ChatAPI: SomaBrainClient instance (or None)
    Note over ChatAPI: None if unavailable (graceful degradation)

    rect # STAGE 9: Build Context (Line 425-490)
    alt Connected
    ChatAPI->>CB: create_context_builder(somabrain, token_counter)
    ChatAPI->>CB: builder.build_for_turn(turn, lane_budget, is_degraded)
    Note over CB:
    - Retrieve context from SomaBrain (vector search, salience ranking)
    - Apply lane budget constraints
    - Build prompt with system + history + memory snippets

    rect STAGE 9: Fallback Minimal Context
    alt Fallback (SomaBrain unavailable)
    ChatAPI-->>ChatAPI: BuiltContext(minimal)
    Note over ChatAPI: No memory retrieval, only Capsule system_prompt

    CB-->>ChatAPI: BuiltContext(system_prompt, messages, token_counts, lane_actual)
    Note over ChatAPI: Ready messages for LLM (system + user + history + memory)

    rect # STAGE 10: Record Metrics (Line 492-494)
    ChatAPI-->>Prometheus: record_turn_phase(turn_id, CONTEXT_BUILT)
    Note over Prometheus: Timing measurement

    rect # STAGE 11: Prepare LLM Messages (Line 496-510)
    ChatAPI->>LLM: Prepare LangChain messages (System, Human, Assistant roles)
    Note over LLM: SystemMessage(prompt) + HumanMessage(user_msg)
    Note over LLM: AIMessage(empty) for streaming output

    rect # STAGE 12: Invoke LLM & Stream (Line 512-535)
    ChatAPI->>LLM: llm._astream(messages)
    Note over LLM: Provider-specific (OpenAI, Anthropic, etc.)
    Note over LLM: SAAS mode timeout = 60s, STANDALONE = 30s
    Note over LLM: Graceful timeout handling

    loop Stream Response
    LLM-->>ChatAPI: AsyncGenerator yielding chunks
    Note over ChatAPI: Each chunk contains token/string
    Note over LLM: Error handling (TimeoutError, generic Exception)
    Note over LLM: Prometheus metrics on each phase (LLM_INVOKED, COMPLETED)

    rect # STAGE 13: Collect Full Response (Line 537-538)
    ChatAPI->>ChatAPI: full_response = "".join(response_content)
    ChatAPI->>ChatAPI: token_count_out = len(full_response.split())
    Note over ChatAPI: Total tokens generated by LLM

    rect # STAGE 14: Store Assistant Message (Line 540-557)
    ChatAPI->>PostgreSQL: INSERT Message (role="assistant", content, latency_ms, model)
    PostgreSQL-->>ChatAPI: Message stored
    Note over PostgreSQL: Trace Registry updated automatically
    ChatAPI->>PostgreSQL: UPDATE Conversation SET message_count = total
    Note over ChatAPI: Conversation metadata updated

    rect # STAGE 15: Non-blocking Memory Store (Line 560-572)
    ChatAPI->>MemStore: store_interaction(...)
    Note over MemStore: Background task (fire-and-forget, NO BLOCKING)
    Note over MemStore: Stores to SomaBrain + PostgreSQL Outbox if degraded

    rect # STAGE 16: Signal Follow-Up (Line 574-594)
    alt History has >= 2 messages
    Note over ChatAPI: Last message was assistant, now user responding
    ChatAPI->>MemStore: signal_follow_up(conversation_id)
    Note over ChatAPI: Implicit RL signal for GMD training

    rect # STAGE 17: Signal Long Response (Line 596-607)
    alt User message > 200 characters
    ChatAPI->>MemStore: signal_long_response(conversation_id)
    Note over MemStore: Indicates engaged user

    rect # STAGE 18: Final Metrics (Line 609-618)
    ChatAPI-->>Prometheus: record_turn_complete(tokens_in, tokens_out, model, provider)
    Note over Prometheus: Full turn metrics (latency, token counts, result)

    rect # STAGE 19: Request Success Metrics (Line 620-622)
    ChatAPI-->>Prometheus: CHAT_TOKENS.inc(input & output)
    ChatAPI-->>Prometheus: CHAT_LATENCY.observe(total_time)
    ChatAPI-->>Prometheus: CHAT_REQUESTS.inc(success)

    ChatAPI-->>User: Stream response tokens (SSE or HTTP streaming)
    Note over User: +Full LLM response token by token

    ChatAPI-->>Prometheus: METRICS RECORDED
    Note over Prometheus: Observability complete
```

---

## 📊 FLOW COMPONENTS & WHO IS CONNECTED

### 1. **User** (External)
- **Connected:** YES
- **Entry Point:** HTTP POST `/chat/conversations/{id}/messages`
- **Role:** Initiator of chat interaction

### 2. **ChatAPI** (`services/common/chat_service.py`)
- **Connected:** YES
- **Type:** Django service with async/await
- **Role:** Orchestrator of entire flow

### 3. **PostgreSQL** (`admin.chat.models`)
- **Connected:** YES (via Django ORM)
- **Role:**
  - Stores messages (Trace Registry)
  - Stores conversations
  - Stores agent settings (Capsule)
  - Stores LLM model config

**Models:**
- `Message` (role: "user" | "assistant", content, token_count, latency_ms, model)
- `Conversation` (tenant_id, user_id, agent_id, status, message_count, title)
- `Capsule` (system_prompt, config, neuromodulator_baseline)
- `LLMModelConfig` (provider, name, capabilities)

### 4. **Governor** (`services/common/simple_governor.py`)
- **Connected:** YES
- **Role:**
  - Token budget allocation
  - Production-grade (Fixed ratios, NO guesses)
  - Binary healthy/degraded decisions

**Budget Ratios (FIXED - Production Proven):**

| Lane | Normal Mode | Degraded Mode |
|-------|-------------|----------------|
| system_policy | 15% | 40% (prioritized) |
| history | 25% | 10% (minimal) |
| memory | 25% | 15% (limited) |
| tools | 20% | 0% (disabled) |
| tool_results | 10% | 0% (disabled) |
| buffer | 5% | 35% (safety margin) |

### 5. **Health Monitor** (`services/common/health_monitor.py`)
- **Connected:** YES
- **Role:** Checks service health status
- **Services Checked:**
  - SomaBrain (reachable?)
  - PostgreSQL (responsive?)
  - LLM (available?)

**Health Model:** Binary (Healthy | Degraded)
- NO multi-level degradation (simplified from AgentIQ)

### 6. **Context Builder** (`services/common/simple_context_builder.py`)
- **Connected:** YES (when SomaBrain available)
- **Role:**
  - Retrieve context from SomaBrain (vector search)
  - Apply lane budget constraints
  - Assemble prompt (system + history + memory)
  - Redact PII from memory
  - Optimize snippet selection (knapsack algorithm)

### 7. **Capsule** (via PostgreSQL `admin.core.models.Capsule`)
- **Connected:** YES
- **Role:**
  - Provides `system_prompt` (The Soul)
  - Model constraints (allowed_models via config)
  - Neuromodulator baselines

**NO HARDCODING:** No fallback system_prompt - uses Capsule or empty

### 8. **Model Router** (`services/common/model_router.py`)
- **Connected:** YES
- **Role:**
  - Capability-based model selection (SINGLE SOURCE OF TRUTH)
  - Routes to appropriate LLM provider (OpenAI, Anthropic, etc.)
  - Priority-based routing

**Config Source:** `LLMModelConfig.from_orm()`
- **Selection Criteria:** `required_capabilities` (attachments, images, code, etc.)

### 9. **LLM** (`admin.llm.services.litellm_client.py` or other providers)
- **Connected:** YES (via Model Router)
- **Role:** Generate assistant response
- **Providers:** OpenAI, Anthropic, etc. (provider-selected)
- **Mode:** Streaming (Async Generator)

**Streaming Protocol:**
- SAAS mode: 60s timeout (network calls)
- STANDALONE mode: 30s timeout (local/embedded)
- Graceful degradation on SomaBrain unavailable

### 10. **SomaBrain** (`admin.core.somabrain_client.py`)
- **Connected:** YES (SAAS mode) or DISCONNECTED (graceful degradation)
- **Role:** Vector search & memory storage
- **Operations:**
  - `recall_context()` - Vector search with salience ranking
  - `store_interaction()` - Store conversations + embeddings
  - Health check `/health` endpoint

**Degradation Handling:**
- Client fails → Uses minimal context (no memory retrieval)
- No blocking - background task continues

### 11. **Memory Store** (`services/common/chat_memory.py`)
- **Connected:** YES
- **Role:**
  - Interface to SomaBrain (SAAS) or local (STANDALONE)
  - Outbox queue for zero-data-loss

**Outbox Mechanism:**
- If SomaBrain down → Queue to `OutboxMessage` table
- Replay on recovery → background worker processes
- **Crucial:** NO DATA LOSS during outages

### 12. **Prometheus/Metrics** (`services/common/unified_metrics.py`)
- **Connected:** YES (observes all stages)
- **Role:**
  - Record turn phases (AUTH_VALIDATED → CONTEXT_BUILT → LLM_INVOKED → COMPLETED)
  - Token counts (input/output)
  - Latency (histogram buckets)
  - Request counters (success/error per method)

**Metrics Recorded:**
```
PHASE METRICS:
- chat_service_duration_seconds (histogram)
- turn_start, turn_complete

TOKEN METRICS:
- chat_tokens_total (counter) [direction: input|output]

REQUEST METRICS:
- chat_service_requests_total (counter) [method, result]
```

---

## 🎯 DEPLOYMENT MODES & INFRASTRUCTURE CONNECTIONS

### SAAS Mode (`SA01_DEPLOYMENT_MODE = "SAAS"`)

| Component | Connected? | How |
|-----------|-------------|------|
| PostgreSQL | **YES** | Django ORM connection via `DJANGO_DATABASES` |
| SomaBrain | **YES** | HTTP client (`SomaBrainClient.get_async()`) |
| LLM Router | **YES** | Reads from `LLMModelConfig` (PostgreSQL) |
| LLM Provider | **YES** | HTTP calls to OpenAI/Anthropic API |
| Prometheus | **YES** | Metrics via `PrometheusClient` |
| Redis | **YES** | Session store, caching (via Django channels settings) |
| Kafka | **YES** | Async events (background memory store) |

**Timeouts:**
- LLM: 60s (SAAS) / 30s (STANDALONE)
- Context building: Default 30s
- SomaBrain HTTP: Default 30s

### Degradation Scenario: SomaBrain Disconnected

| Stage | Behavior | Who Handles |
|--------|-----------|--------------|
| Load Capsule | Normal | ChatAPI → PostgreSQL (always works) |
| Detect Capabilities | Normal | Model Router (doesn't need Brain) |
| Select Model | Normal | Model Router (doesn't need Brain) |
| Get Health | Works | Health Monitor detects Brain down |
| Allocate Budget | Works | Governor uses degraded flag |
| Initialize SomaBrain | **DISCONNECTED** | Returns None gracefully |
| Build Context | **FALLBACK** | Uses minimal context (no memory) |
| Invoke LLM | **WORKS** | Uses fallback context +Capsule prompt |
| Store Memory | **QUEUED** | Outbox → Will replay when Brain up |
| Stream Response | **WORKS** | LLM generates response |
| Return to User | **WORKS** | Tokens stream normally |

**Result:** Chat works even when SomaBrain is down (graceful degradation)

---

## 📋 DATA FLOW SUMMARY

### Message Flow (User → Database → LLM → Database → Back to User)

1. **User Message** → ChatAPI HTTP endpoint
2. **ChatAPI** → PostgreSQL (store as "user" message)
3. **ChatAPI** → PostgreSQL (load conversation + history)
4. **ChatAPI** → PostgreSQL (load Capsule for constraints + system_prompt)
5. **ChatAPI** → Model Router (select LLM based on capabilities)
6. **ChatAPI** → Health Monitor (check degraded flag)
7. **ChatAPI** → Governor (allocate token budget based on health)
8. **ChatAPI** → SomaBrain (connect or handle None gracefully)
9. **ChatAPI** → Context Builder (assemble prompt from memory + history)
10. **ChatAPI** → LLM Provider (stream generation)
11. **ChatAPI** → PostgreSQL (store as "assistant" message)
12. **ChatAPI** → Memory Store (background, non-blocking)
13. **ChatAPI** → User (stream tokens via HTTP/SSE)

### Key Design Decisions

**SINGLE SOURCE OF TRUTH:**
- Model selection from `LLMModelConfig` ORM table (no hardcoded models)
- Settings from `Capsule` (no hardcoded prompts)

**NO HARDING FALLBACKS:**
- System prompt from Capsule or empty (NOT "Assistant ready")
- Degradation uses minimal context (not blocking)

**REAL INFRASTRUCTURE ONLY:**
- PostgreSQL for persistence
- SomaBrain for vector search
- LLM providers via HTTP
- Prometheus for observability
- Kafka for async events
- Redis for caching

**PRODUCTION GRADE:**
- Fixed Governor ratios (field-tested)
- Graceful SomaBrain degradation (no errors, fallback context)
- Non-blocking memory store (fire-and-forget)
- Comprehensive metrics at every phase
