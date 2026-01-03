# AgentIQ Governor Requirements

## Overview

AgentIQ is a Governor-mediated Control Loop that transforms SomaAgent01 into a budgeted transaction system. It provides intelligent context management through lane-based token budgeting, capsule-scoped tool discovery, and adaptive degradation modes.

## Source Documents

- SRS-AGENTIQ-2025-12-18 (Primary specification)
- CANONICAL_REQUIREMENTS.md (RQ-AIQ-050 to RQ-AIQ-059)

## Functional Requirements

### REQ-AIQ-001: Governor Execution Position
The AgentIQ Governor MUST run after OPA policy gates and before model/tool invocation. This ensures all security checks pass before budget computation begins.

**Acceptance Criteria:**
- Governor executes only after `opa_middleware` approves the request
- Governor completes before any LLM call or tool dispatch
- Trace spans show correct ordering: OPA → Governor → LLM/Tool

### REQ-AIQ-002: AIQ Score Computation
The system MUST compute AIQ_pred (predicted intelligence quotient) pre-call and AIQ_obs (observed) post-call.

**Formula:**
```
AIQ_pred = w1*context_quality + w2*tool_relevance + w3*budget_efficiency
AIQ_obs = w1*response_quality + w2*tool_success_rate + w3*token_efficiency
```

**Acceptance Criteria:**
- AIQ scores range 0-100
- Weights configurable via UI Settings
- Both scores persisted in RunReceipt

### REQ-AIQ-003: Lane-Based Prompt Assembly
Prompt assembly MUST use lane plans with the following lanes:

| Lane | Purpose | Min Tokens |
|------|---------|------------|
| System+Policy | System prompt + OPA policies | Variable |
| History | Conversation history | Variable |
| Memory | SomaBrain retrieved context | Variable |
| Tools | Tool definitions | Variable |
| ToolResults | Previous tool outputs | Variable |
| Buffer | Safety margin | ≥200 |

**Acceptance Criteria:**
- Buffer lane MUST have ≥200 tokens reserved
- Each lane has configurable min/max bounds
- Lane overflow triggers degradation

### REQ-AIQ-004: Capsule-Scoped Tool Discovery
Tool discovery MUST be capsule-scoped before Top-K selection.

**Acceptance Criteria:**
- Tools filtered by `CapsuleRecord.allowed_tools` first
- Tools in `CapsuleRecord.prohibited_tools` excluded
- MCP servers filtered by `CapsuleRecord.allowed_mcp_servers`
- Top-K applied AFTER capsule filtering

### REQ-AIQ-005: Digest Faithfulness
Digests (summarized content) MUST retain anchors and carry faithfulness metadata.

**Acceptance Criteria:**
- Original source IDs preserved as anchors
- Faithfulness score (0.0-1.0) computed for each digest
- Digests with faithfulness < 0.5 flagged for review

### REQ-AIQ-006: Degradation Levels
The system MUST support degradation levels L0-L4:

| Level | Name | Behavior |
|-------|------|----------|
| L0 | Normal | Full context, all tools |
| L1 | Reduced | Reduced history, top-3 tools |
| L2 | Minimal | No history, top-1 tool |
| L3 | Emergency | System prompt only, no tools |
| L4 | Safe | Canned response, no LLM call |

**Acceptance Criteria:**
- Degradation level determined by DegradationMonitor state
- Level transitions logged with reason
- Prometheus gauge tracks current level

### REQ-AIQ-007: RunReceipt Emission
Every turn MUST emit a RunReceipt containing:

```python
@dataclass
class RunReceipt:
    turn_id: str
    session_id: str
    tenant_id: str
    capsule_id: str
    aiq_pred: float
    aiq_obs: float
    lane_budgets: Dict[str, int]
    lane_actual: Dict[str, int]
    degradation_level: str
    path_mode: str  # "fast" | "rescue"
    tool_k: int
    latency_ms: float
    timestamp: float
```

**Acceptance Criteria:**
- RunReceipt emitted for every turn
- Persisted to audit store
- Queryable via API

### REQ-AIQ-008: Live-Tunable Configuration
All AIQ weights and thresholds MUST be live-tunable via UI Settings.

**Configurable Parameters:**
- AIQ weight coefficients (w1, w2, w3)
- Lane min/max bounds
- Degradation thresholds
- Tool K values per degradation level

**Acceptance Criteria:**
- Changes take effect without restart
- Configuration cached with TTL
- Invalid configs rejected with error

### REQ-AIQ-009: Fast Path vs Rescue Path
Governor MUST decide between Fast Path and Rescue Path modes:

**Fast Path:**
- Full budget allocation
- All lanes populated
- Normal tool selection

**Rescue Path:**
- Reduced budget
- Critical lanes only (System, Buffer)
- Emergency tool subset or none

**Acceptance Criteria:**
- Path decision based on degradation level and budget availability
- Path mode recorded in RunReceipt
- Rescue Path triggers alert

### REQ-AIQ-010: In-Process Execution
AgentIQ v1 MUST run in-process (not as separate service).

**Acceptance Criteria:**
- No network calls for Governor logic
- Latency overhead ≤5ms for budget computation
- No additional infrastructure dependencies

## Non-Functional Requirements

### REQ-AIQ-NFR-001: Performance
- Budget computation: ≤5ms p95
- Lane allocation: ≤2ms p95
- Total Governor overhead: ≤10ms p95

### REQ-AIQ-NFR-002: Observability
Prometheus metrics required:
- `agentiq_aiq_pred` (histogram)
- `agentiq_aiq_obs` (histogram)
- `agentiq_degradation_level` (gauge)
- `agentiq_path_mode` (counter by mode)
- `agentiq_lane_utilization` (gauge by lane)
- `agentiq_governor_latency_seconds` (histogram)

### REQ-AIQ-NFR-003: Testing
- Regression suite for AIQ invariants
- Chaos suite for degradation transitions
- Property-based tests for budget allocation

### REQ-AIQ-NFR-004: Security
- All configuration changes audit-logged
- RunReceipts contain no PII
- Tool selection respects OPA policies

## Existing Infrastructure (Reuse)

| Component | Location | Status |
|-----------|----------|--------|
| CapsuleStore | `services/common/capsule_store.py` | ✅ Complete |
| CapsuleEnforcer | `services/common/capsule_enforcer.py` | ✅ Complete |
| DegradationMonitor | `services/common/degradation_monitor.py` | ✅ Complete |
| BudgetManager | `services/common/budget_manager.py` | ✅ Complete |
| ContextBuilder | `python/somaagent/context_builder.py` | ⚠️ Needs extension |

## Confidence Score Requirements (Integrated)

### REQ-CONF-001: Logprob Capture
LLM wrappers MUST request token-level logprobs when the provider supports it.

**Acceptance Criteria:**
- OpenAI/Azure: `logprobs=True, top_logprobs=1`
- Anthropic: Use available confidence signals
- Providers without logprobs: Return `confidence=null`

### REQ-CONF-002: Confidence Calculation
The system MUST implement `calculate_confidence()` with configurable modes:

| Mode | Formula |
|------|---------|
| average | `mean(exp(logprobs))` |
| min | `min(exp(logprobs))` |
| percentile_90 | `percentile(exp(logprobs), 10)` |

**Acceptance Criteria:**
- Mode configurable via `SA01_CONFIDENCE_MODE`
- Returns float 0.0-1.0 or null
- Handles empty logprobs gracefully

### REQ-CONF-003: Response Confidence Field
All public API responses MUST include `confidence: float | null` when feature enabled.

**Acceptance Criteria:**
- Field present in SSE `assistant.final` events
- Field present in REST response body
- Null when provider doesn't support logprobs

### REQ-CONF-004: Confidence Persistence
Events and audit stores MUST persist only scalar confidence (no raw token logprobs).

**Acceptance Criteria:**
- RunReceipt includes `confidence` field
- Audit events include `confidence` field
- Raw logprobs NOT persisted (privacy/storage)

### REQ-CONF-005: Confidence Thresholds
Runtime-configurable thresholds for confidence gating:

| Config | Default | Purpose |
|--------|---------|---------|
| `min_acceptance` | 0.3 | Reject below this |
| `on_low` | "warn" | Action: warn/retry/reject |
| `treat_null_as_low` | false | Null = low confidence? |

**Acceptance Criteria:**
- Thresholds configurable via UI Settings
- Low confidence triggers configured action
- Metrics track rejections

### REQ-CONF-006: Confidence Metrics
Prometheus metrics for confidence monitoring:

- `llm_confidence_score` (histogram)
- `llm_confidence_missing_total` (counter)
- `llm_confidence_rejected_total` (counter)
- `llm_confidence_ewma` (gauge)

**Acceptance Criteria:**
- EWMA updated per response
- Histogram buckets: 0.1, 0.3, 0.5, 0.7, 0.9, 1.0
- Labels: provider, model

### REQ-CONF-007: Performance Constraints
Confidence calculation overhead constraints:

- Warm path: ≤5ms
- Cold path: ≤10ms
- Failure MUST NOT abort response

**Acceptance Criteria:**
- Calculation errors logged, not raised
- Response delivered even if confidence fails
- Latency tracked in metrics

### REQ-CONF-008: Feature Flag
Confidence scoring MUST be feature-flagged for rollout.

**Acceptance Criteria:**
- Flag: `SA01_ENABLE_CONFIDENCE_SCORING`
- Default: disabled
- OpenAPI version bump when enabled

## Dependencies

- SomaBrain service (context retrieval)
- Redis (configuration cache)
- PostgreSQL (RunReceipt persistence)
- OPA (policy gates)
- LiteLLM (logprob extraction)
