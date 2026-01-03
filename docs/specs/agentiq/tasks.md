# AgentIQ Governor + Confidence Score - Implementation Tasks

## Task Overview

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| T1 | Create AgentIQ Governor core | P0 | 4h | None | ✅ DONE |
| T2 | Create Lane Allocator | P0 | 3h | T1 | ✅ DONE (in T1) |
| T3 | Create Confidence Scorer | P0 | 3h | None | ✅ DONE |
| T4 | Create RunReceipt model | P0 | 2h | None | ✅ DONE |
| T5 | Add Prometheus metrics | P0 | 2h | T1, T3, T4 | ✅ DONE |
| T6 | Create database migration | P1 | 1h | T4 | ⏳ PENDING |
| T7 | Integrate with ContextBuilder | P1 | 3h | T1, T2 | ⏳ PENDING |
| T8 | Add LLM logprob extraction | P1 | 3h | T3 | ⏳ PENDING |
| T9 | Add configuration schema | P1 | 2h | T1, T3 | ✅ DONE |
| T10 | Add feature flags | P1 | 1h | T9 | ✅ DONE |
| T11 | Unit tests | P1 | 4h | T1-T4 | ⏳ PENDING |
| T12 | Integration tests | P2 | 4h | T1-T10 | ⏳ PENDING |
| T13 | Documentation | P2 | 2h | All | ⏳ PENDING |

---

## Task 1: Create AgentIQ Governor Core ✅ COMPLETE

**File:** `somaAgent01/python/somaagent/agentiq_governor.py`

**Requirements:** REQ-AIQ-001, REQ-AIQ-002, REQ-AIQ-009, REQ-AIQ-010

### Acceptance Criteria
- [x] Governor executes after OPA gate, before LLM call
- [x] Computes AIQ_pred pre-call
- [x] Decides Fast Path vs Rescue Path
- [x] Latency overhead ≤10ms p95
- [x] In-process execution (no network calls for Governor logic)

### Implementation Notes
```python
# Key classes to implement:
# - AgentIQConfig: Pydantic model for configuration
# - AIQScore: Dataclass for predicted/observed scores
# - GovernorDecision: Result of govern() call
# - AgentIQGovernor: Main governor class

# Must integrate with existing:
# - CapsuleStore (services/common/capsule_store.py)
# - DegradationMonitor (services/common/degradation_monitor.py)
# - BudgetManager (services/common/budget_manager.py)
```

---

## Task 2: Create Lane Allocator ✅ COMPLETE (included in T1)

**File:** `somaAgent01/python/somaagent/agentiq_governor.py` (LaneAllocator class)

**Requirements:** REQ-AIQ-003, REQ-AIQ-006

### Acceptance Criteria
- [x] Allocates tokens across 6 lanes: system_policy, history, memory, tools, tool_results, buffer
- [x] Buffer lane always ≥200 tokens
- [x] Respects degradation level (L0-L4)
- [x] Respects capsule constraints
- [x] Lane overflow triggers degradation escalation

### Implementation Notes
```python
# Lane ratios by degradation level:
# L0 (Normal): Full allocation
# L1 (Minor): Reduced history (15%), reduced tools (10%)
# L2 (Moderate): Minimal history (10%), minimal tools (5%)
# L3 (Severe): No history, no tools
# L4 (Critical): System prompt only, no tools, no memory
```

---

## Task 3: Create Confidence Scorer ✅ COMPLETE

**File:** `somaAgent01/python/somaagent/confidence_scorer.py`

**Requirements:** REQ-CONF-001, REQ-CONF-002, REQ-CONF-005, REQ-CONF-007

### Acceptance Criteria
- [x] Implements calculate_confidence() with 3 modes: average, min, percentile_90
- [x] Returns float 0.0-1.0 or None
- [x] Handles empty/missing logprobs gracefully
- [x] Calculation overhead ≤5ms
- [x] Failure does NOT abort response

### Implementation Notes
```python
# Confidence modes:
# - average: mean(exp(logprobs))
# - min: min(exp(logprobs))
# - percentile_90: percentile(exp(logprobs), 10)

# Threshold actions:
# - warn: Log warning, continue
# - retry: Retry LLM call once
# - reject: Return error to user
```

---

## Task 4: Create RunReceipt Model ✅ COMPLETE

**File:** `somaAgent01/python/somaagent/run_receipt.py`

**Requirements:** REQ-AIQ-007, REQ-CONF-004

### Acceptance Criteria
- [x] Immutable dataclass with all required fields
- [x] Includes confidence field (nullable)
- [x] to_audit_event() method for persistence
- [x] No PII in receipt

### Implementation Notes
```python
@dataclass(frozen=True)
class RunReceipt:
    turn_id: str
    session_id: str
    tenant_id: str
    capsule_id: str
    aiq_pred: float
    aiq_obs: float
    confidence: Optional[float]
    lane_budgets: Dict[str, int]
    lane_actual: Dict[str, int]
    degradation_level: str
    path_mode: str
    tool_k: int
    latency_ms: float
    timestamp: float
```

---

## Task 5: Add Prometheus Metrics ✅ COMPLETE

**File:** `somaAgent01/python/somaagent/agentiq_metrics.py`

**Requirements:** REQ-AIQ-NFR-002, REQ-CONF-006

### Acceptance Criteria
- [x] agentiq_aiq_pred histogram
- [x] agentiq_aiq_obs histogram
- [x] agentiq_degradation_level gauge
- [x] agentiq_path_mode counter
- [x] agentiq_lane_utilization gauge
- [x] agentiq_governor_latency_seconds histogram
- [x] llm_confidence_score histogram
- [x] llm_confidence_missing_total counter
- [x] llm_confidence_rejected_total counter
- [x] llm_confidence_ewma gauge

### Implementation Notes
```python
# Use existing observability/metrics.py wrappers
# Labels: tenant_id, provider, model, lane, mode
# Buckets aligned with requirements
```

---

## Task 6: Create Database Migration

**File:** `somaAgent01/migrations/versions/xxx_add_run_receipts.py`

**Requirements:** REQ-AIQ-007

### Acceptance Criteria
- [ ] Creates run_receipts table with all fields
- [ ] Adds indexes for session_id, tenant_id, created_at
- [ ] Sets up monthly partitioning
- [ ] Reversible migration

### Implementation Notes
```sql
-- Use Alembic for migration
-- Partition by month for scale
-- JSONB for lane_budgets and lane_actual
```

---

## Task 7: Integrate with ContextBuilder

**File:** `somaAgent01/python/somaagent/context_builder.py` (modify existing)

**Requirements:** REQ-AIQ-003, REQ-AIQ-004

### Acceptance Criteria
- [ ] ContextBuilder accepts LanePlan from Governor
- [ ] Respects lane token limits
- [ ] Capsule-scoped tool filtering before Top-K
- [ ] Reports actual lane usage back to Governor

### Implementation Notes
```python
# Extend BuiltContext to include lane_actual
# Add lane_plan parameter to build_for_turn()
# Filter tools by capsule.allowed_tools before ranking
```

---

## Task 8: Add LLM Logprob Extraction

**File:** `somaAgent01/services/gateway/llm_router.py` (modify existing)

**Requirements:** REQ-CONF-001, REQ-CONF-003

### Acceptance Criteria
- [ ] OpenAI/Azure: Request logprobs=True, top_logprobs=1
- [ ] Extract logprobs from response
- [ ] Pass to ConfidenceScorer
- [ ] Include confidence in assistant.final event
- [ ] Handle providers without logprob support

### Implementation Notes
```python
# LiteLLM completion params:
# - logprobs=True (OpenAI, Azure)
# - top_logprobs=1

# Response extraction:
# response.choices[0].logprobs.content[i].logprob
```

---

## Task 9: Add Configuration Schema ✅ COMPLETE

**Files:**
- `somaAgent01/python/somaagent/agentiq_config.py`
- `somaAgent01/conf/agentiq.yaml`

**Requirements:** REQ-AIQ-008, REQ-CONF-005

### Acceptance Criteria
- [x] Pydantic models for AgentIQ and Confidence config
- [x] YAML configuration file
- [x] Validation of weights (sum to 1.0)
- [x] Validation of lane bounds
- [x] Live-tunable via Settings (reload_config())

### Implementation Notes
```python
# Use Pydantic v2 for validation
# Integrate with existing src/core/config.py
# Support hot-reload via Settings cache
```

---

## Task 10: Add Feature Flags ✅ COMPLETE

**Files:**
- `somaAgent01/python/somaagent/agentiq_governor.py` (is_agentiq_enabled())
- `somaAgent01/python/somaagent/confidence_scorer.py` (is_confidence_enabled())

**Requirements:** REQ-CONF-008

### Acceptance Criteria
- [x] SA01_ENABLE_AGENTIQ_GOVERNOR flag
- [x] SA01_ENABLE_CONFIDENCE_SCORING flag
- [x] Default: disabled
- [x] OpenAPI version bump when enabled (N/A - no API changes yet)

### Implementation Notes
```python
# Add to cfg.flag() system
# Check flags in Governor and Scorer entry points
# Log when features are enabled/disabled
```

---

## Task 11: Unit Tests

**Files:**
- `somaAgent01/tests/unit/test_agentiq_governor.py`
- `somaAgent01/tests/unit/test_lane_allocator.py`
- `somaAgent01/tests/unit/test_confidence_scorer.py`
- `somaAgent01/tests/unit/test_run_receipt.py`

**Requirements:** REQ-AIQ-NFR-003

### Acceptance Criteria
- [ ] Governor decision logic tests
- [ ] Lane allocation with all degradation levels
- [ ] Confidence calculation modes
- [ ] RunReceipt serialization
- [ ] Edge cases: empty inputs, invalid configs
- [ ] Property-based tests for invariants

### Test Cases
```python
# Governor tests:
# - test_governor_executes_after_opa
# - test_governor_computes_aiq_pred
# - test_governor_selects_fast_path
# - test_governor_selects_rescue_path
# - test_governor_latency_under_10ms

# Lane tests:
# - test_lane_allocation_normal
# - test_lane_allocation_degraded_l1_l4
# - test_buffer_always_200_minimum
# - test_lane_overflow_triggers_degradation

# Confidence tests:
# - test_confidence_average_mode
# - test_confidence_min_mode
# - test_confidence_percentile_mode
# - test_confidence_handles_empty_logprobs
# - test_confidence_failure_does_not_abort
```

---

## Task 12: Integration Tests

**Files:**
- `somaAgent01/tests/integration/test_agentiq_flow.py`
- `somaAgent01/tests/integration/test_confidence_flow.py`

**Requirements:** REQ-AIQ-NFR-003

### Acceptance Criteria
- [ ] Full Governor flow with real SomaBrain
- [ ] RunReceipt persistence and retrieval
- [ ] Degradation level transitions
- [ ] Confidence in SSE events
- [ ] Chaos tests for service failures

### Prerequisites
- Real infrastructure (PostgreSQL, Redis, SomaBrain)
- `docker compose --profile core up -d`

---

## Task 13: Documentation

**Files:**
- `somaAgent01/docs/agentiq.md`
- `somaAgent01/docs/confidence.md`

**Requirements:** All

### Acceptance Criteria
- [ ] Architecture overview
- [ ] Configuration reference
- [ ] API reference for RunReceipt
- [ ] Metrics reference
- [ ] Troubleshooting guide

---

## Implementation Order

```
Week 1:
├── T4: RunReceipt model (foundation)
├── T3: Confidence Scorer (independent)
├── T1: AgentIQ Governor core
└── T2: Lane Allocator

Week 2:
├── T5: Prometheus metrics
├── T9: Configuration schema
├── T10: Feature flags
└── T6: Database migration

Week 3:
├── T7: ContextBuilder integration
├── T8: LLM logprob extraction
└── T11: Unit tests

Week 4:
├── T12: Integration tests
└── T13: Documentation
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests passing (≥80% coverage)
- [ ] Integration tests passing
- [ ] No VIBE violations (no mocks, no placeholders, no TODOs)
- [ ] Prometheus metrics exposed
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Feature flags working
