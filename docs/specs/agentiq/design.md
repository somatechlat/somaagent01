# AgentIQ Governor + Confidence Score - Design Document

## 1. Executive Summary

This design implements the AgentIQ Governor and Confidence Score system for SomaAgent01, enabling lane-based token budgeting, AIQ scoring, adaptive degradation, and LLM confidence tracking. The system is designed for **millions of transactions** with sub-10ms overhead.

## 2. Transport Architecture Analysis

### 2.1 Current State Assessment

| Component | Status | Location |
|-----------|--------|----------|
| HTTP Transport | ✅ Implemented | `somabrain/somabrain/memory/transport.py` |
| gRPC Proto | ⚠️ Defined only | `somabrain/somabrain/proto/memory.proto` |
| WebSocket | ❌ Not in SomaBrain | Only in AgentVoiceBox |
| Temporal | ✅ Implemented | `somaAgent01/services/*/temporal_worker.py` |

### 2.2 Transport Options for Millions of Transactions

| Transport | Latency | Throughput | Implementation Effort | Recommendation |
|-----------|---------|------------|----------------------|----------------|
| HTTP/2 + Connection Pool | 2-5ms | ~10K TPS | Low (enhance existing) | ✅ Phase 1 |
| gRPC Streaming | 1-3ms | ~50K TPS | Medium (implement proto) | ⚠️ Phase 2 |
| WebSocket | <1ms | ~100K TPS | High (new in SomaBrain) | ❌ Not recommended |
| Temporal Workflows | N/A | Durable | Already implemented | ✅ Use for durability |

### 2.3 Recommended Architecture

**Phase 1 (This Spec):** Optimize HTTP/2 with aggressive connection pooling
- Leverage existing `MemoryHTTPTransport` with enhanced pooling
- Use Temporal for durable workflow orchestration (already in place)
- Target: 10K TPS with <10ms p95 latency

**Phase 2 (Future):** gRPC streaming for high-frequency operations
- Implement `MemoryService` from existing proto
- Bidirectional streaming for recall/remember batches
- Target: 50K+ TPS with <3ms p95 latency

**NOT Recommended:** WebSocket for SomaBrain
- Would require significant SomaBrain changes
- HTTP/2 + gRPC provides better semantics for request/response patterns
- WebSocket better suited for real-time voice (already in AgentVoiceBox)

## 3. System Architecture

### 3.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Gateway Service                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ OPA Gate    │→ │ AgentIQ     │→ │ LLM Router  │→ │ Confidence Scorer   │ │
│  │ (existing)  │  │ Governor    │  │ (existing)  │  │ (new)               │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │               │                │                    │             │
│         │               ▼                │                    │             │
│         │        ┌─────────────┐         │                    │             │
│         │        │ Lane        │         │                    │             │
│         │        │ Allocator   │         │                    │             │
│         │        └─────────────┘         │                    │             │
└─────────│───────────────│────────────────│────────────────────│─────────────┘
          │               │                │                    │
          ▼               ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Shared Infrastructure                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Capsule     │  │ Degradation │  │ Budget      │  │ RunReceipt Store    │ │
│  │ Store       │  │ Monitor     │  │ Manager     │  │ (PostgreSQL)        │ │
│  │ (existing)  │  │ (existing)  │  │ (existing)  │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
          │                                │
          ▼                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SomaBrain Service                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ /context/   │  │ /memory/    │  │ /neuro-     │  │ /sleep/run          │ │
│  │ evaluate    │  │ recall      │  │ modulators  │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Execution Flow

```
Request → OPA Gate → AgentIQ Governor → LLM Call → Confidence Score → Response
              │              │                │              │
              │              ├─ Lane Plan     │              ├─ Logprob Extract
              │              ├─ AIQ_pred      │              ├─ Confidence Calc
              │              ├─ Degradation   │              └─ Threshold Check
              │              │   Check        │
              │              └─ Capsule       │
              │                 Filter        │
              │                               │
              └───────────────────────────────┴─→ RunReceipt Emit
```

## 4. Detailed Component Design

### 4.1 AgentIQ Governor

**Location:** `somaAgent01/python/somaagent/agentiq_governor.py` (new file)

```python
@dataclass
class LanePlan:
    """Token budget allocation across lanes."""
    system_policy: int      # System prompt + OPA policies
    history: int            # Conversation history
    memory: int             # SomaBrain retrieved context
    tools: int              # Tool definitions
    tool_results: int       # Previous tool outputs
    buffer: int             # Safety margin (≥200)
    
    def total(self) -> int:
        return sum([self.system_policy, self.history, self.memory, 
                    self.tools, self.tool_results, self.buffer])

@dataclass
class AIQScore:
    """Intelligence quotient scores."""
    predicted: float        # Pre-call prediction (0-100)
    observed: float         # Post-call observation (0-100)
    components: Dict[str, float]  # Breakdown by factor

class AgentIQGovernor:
    """Governor-mediated control loop for budgeted transactions."""
    
    def __init__(
        self,
        capsule_store: CapsuleStore,
        degradation_monitor: DegradationMonitor,
        budget_manager: BudgetManager,
        config: AgentIQConfig,
    ) -> None: ...
    
    async def govern(
        self,
        turn: TurnContext,
        max_tokens: int,
    ) -> GovernorDecision: ...
```

### 4.2 Lane Allocator

**Location:** `somaAgent01/python/somaagent/lane_allocator.py` (new file)

```python
class LaneAllocator:
    """Allocates token budget across lanes with degradation awareness."""
    
    DEFAULT_RATIOS = {
        "system_policy": 0.15,
        "history": 0.25,
        "memory": 0.25,
        "tools": 0.20,
        "tool_results": 0.10,
        "buffer": 0.05,  # Minimum 200 tokens
    }
    
    DEGRADED_RATIOS = {
        DegradationLevel.MINOR: {"history": 0.15, "tools": 0.10},
        DegradationLevel.MODERATE: {"history": 0.10, "tools": 0.05, "memory": 0.15},
        DegradationLevel.SEVERE: {"history": 0.0, "tools": 0.0, "memory": 0.10},
        DegradationLevel.CRITICAL: {"history": 0.0, "tools": 0.0, "memory": 0.0},
    }
    
    def allocate(
        self,
        total_budget: int,
        degradation_level: DegradationLevel,
        capsule: CapsuleRecord,
    ) -> LanePlan: ...
```

### 4.3 Confidence Scorer

**Location:** `somaAgent01/python/somaagent/confidence_scorer.py` (new file)

```python
class ConfidenceMode(str, Enum):
    AVERAGE = "average"
    MIN = "min"
    PERCENTILE_90 = "percentile_90"

@dataclass
class ConfidenceResult:
    """Result of confidence calculation."""
    score: Optional[float]  # 0.0-1.0 or None if unavailable
    mode: ConfidenceMode
    token_count: int
    provider: str
    model: str

class ConfidenceScorer:
    """Calculates confidence scores from LLM logprobs."""
    
    def __init__(
        self,
        mode: ConfidenceMode = ConfidenceMode.AVERAGE,
        min_acceptance: float = 0.3,
        on_low: str = "warn",  # "warn" | "retry" | "reject"
        treat_null_as_low: bool = False,
    ) -> None: ...
    
    def calculate(
        self,
        logprobs: Optional[List[float]],
        provider: str,
        model: str,
    ) -> ConfidenceResult: ...
```

### 4.4 RunReceipt

**Location:** `somaAgent01/python/somaagent/run_receipt.py` (new file)

```python
@dataclass
class RunReceipt:
    """Immutable record of a governed turn execution."""
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
    path_mode: str  # "fast" | "rescue"
    tool_k: int
    latency_ms: float
    timestamp: float
    
    def to_audit_event(self) -> Dict[str, Any]: ...
```

## 5. Integration Points

### 5.1 Existing Components to Extend

| Component | File | Changes Required |
|-----------|------|------------------|
| ContextBuilder | `python/somaagent/context_builder.py` | Add lane-aware budget allocation |
| DegradationMonitor | `services/common/degradation_monitor.py` | Expose level for Governor |
| CapsuleStore | `services/common/capsule_store.py` | No changes (use as-is) |
| BudgetManager | `services/common/budget_manager.py` | No changes (use as-is) |

### 5.2 SomaBrain Integration

The existing `SomaClient` already supports all required endpoints:
- `context_evaluate()` - Memory retrieval for lanes
- `get_neuromodulators()` - Cognitive state
- `get_adaptation_state()` - Learning weights
- `sleep_cycle()` - Memory consolidation

### 5.3 LiteLLM Integration for Logprobs

```python
# In LLM wrapper (services/gateway/llm_router.py)
async def invoke_with_logprobs(
    messages: List[Dict],
    model: str,
    **kwargs,
) -> Tuple[str, Optional[List[float]]]:
    """Invoke LLM and extract logprobs if available."""
    # OpenAI/Azure: logprobs=True, top_logprobs=1
    # Anthropic: Use available confidence signals
    # Others: Return None for logprobs
```

## 6. Configuration Schema

### 6.1 AgentIQ Configuration

```yaml
# config/agentiq.yaml (loaded via Settings)
agentiq:
  enabled: true
  
  # AIQ weights (must sum to 1.0)
  weights:
    context_quality: 0.4
    tool_relevance: 0.3
    budget_efficiency: 0.3
  
  # Lane bounds (min/max tokens)
  lanes:
    system_policy:
      min: 100
      max: 2000
    history:
      min: 0
      max: 4000
    memory:
      min: 0
      max: 2000
    tools:
      min: 0
      max: 1500
    tool_results:
      min: 0
      max: 1000
    buffer:
      min: 200
      max: 500
  
  # Degradation thresholds
  degradation:
    l1_threshold: 0.7  # AIQ_pred below this → L1
    l2_threshold: 0.5
    l3_threshold: 0.3
    l4_threshold: 0.1
  
  # Tool selection
  tool_k:
    normal: 5
    l1: 3
    l2: 1
    l3: 0
    l4: 0
```

### 6.2 Confidence Configuration

```yaml
# config/confidence.yaml
confidence:
  enabled: false  # Feature flag
  mode: "average"  # average | min | percentile_90
  min_acceptance: 0.3
  on_low: "warn"  # warn | retry | reject
  treat_null_as_low: false
  
  # Provider-specific settings
  providers:
    openai:
      logprobs: true
      top_logprobs: 1
    azure:
      logprobs: true
      top_logprobs: 1
    anthropic:
      # Anthropic doesn't expose logprobs; use null
      logprobs: false
```

## 7. Prometheus Metrics

### 7.1 AgentIQ Metrics

```python
# Histograms
AGENTIQ_AIQ_PRED = Histogram(
    "agentiq_aiq_pred",
    "Predicted AIQ score distribution",
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)
AGENTIQ_AIQ_OBS = Histogram(
    "agentiq_aiq_obs", 
    "Observed AIQ score distribution",
    buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)
AGENTIQ_GOVERNOR_LATENCY = Histogram(
    "agentiq_governor_latency_seconds",
    "Governor computation latency",
    buckets=[0.001, 0.002, 0.005, 0.01, 0.02, 0.05],
)

# Gauges
AGENTIQ_DEGRADATION_LEVEL = Gauge(
    "agentiq_degradation_level",
    "Current degradation level (0-4)",
    labelnames=("tenant_id",),
)
AGENTIQ_LANE_UTILIZATION = Gauge(
    "agentiq_lane_utilization",
    "Lane token utilization ratio",
    labelnames=("lane",),
)

# Counters
AGENTIQ_PATH_MODE = Counter(
    "agentiq_path_mode_total",
    "Path mode selections",
    labelnames=("mode",),  # fast | rescue
)
```

### 7.2 Confidence Metrics

```python
LLM_CONFIDENCE_SCORE = Histogram(
    "llm_confidence_score",
    "LLM response confidence scores",
    labelnames=("provider", "model"),
    buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
)
LLM_CONFIDENCE_MISSING = Counter(
    "llm_confidence_missing_total",
    "Count of responses without confidence",
    labelnames=("provider", "model"),
)
LLM_CONFIDENCE_REJECTED = Counter(
    "llm_confidence_rejected_total",
    "Count of responses rejected for low confidence",
    labelnames=("provider", "model"),
)
LLM_CONFIDENCE_EWMA = Gauge(
    "llm_confidence_ewma",
    "Exponentially weighted moving average of confidence",
    labelnames=("provider", "model"),
)
```

## 8. Database Schema

### 8.1 RunReceipt Table

```sql
-- migrations/versions/xxx_add_run_receipts.py
CREATE TABLE run_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    turn_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    capsule_id VARCHAR(64),
    aiq_pred FLOAT NOT NULL,
    aiq_obs FLOAT NOT NULL,
    confidence FLOAT,
    lane_budgets JSONB NOT NULL,
    lane_actual JSONB NOT NULL,
    degradation_level VARCHAR(16) NOT NULL,
    path_mode VARCHAR(16) NOT NULL,
    tool_k INTEGER NOT NULL,
    latency_ms FLOAT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes for common queries
    INDEX idx_run_receipts_session (session_id),
    INDEX idx_run_receipts_tenant (tenant_id),
    INDEX idx_run_receipts_created (created_at DESC)
);

-- Partition by month for scale
CREATE TABLE run_receipts_y2025m12 PARTITION OF run_receipts
    FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');
```

## 9. Error Handling

### 9.1 Governor Failures

```python
class GovernorError(Exception):
    """Base exception for Governor failures."""

class BudgetExhaustedError(GovernorError):
    """Raised when no valid lane plan can be computed."""

class CapsuleNotFoundError(GovernorError):
    """Raised when capsule lookup fails."""

# Recovery strategy: Fall back to Rescue Path
async def govern_with_fallback(turn: TurnContext) -> GovernorDecision:
    try:
        return await governor.govern(turn, max_tokens)
    except GovernorError as e:
        logger.warning("Governor failed, using rescue path", error=str(e))
        return GovernorDecision.rescue_path(turn)
```

### 9.2 Confidence Failures

```python
# Confidence calculation MUST NOT abort response
def calculate_confidence_safe(logprobs: Optional[List[float]]) -> Optional[float]:
    try:
        return scorer.calculate(logprobs)
    except Exception as e:
        logger.warning("Confidence calculation failed", error=str(e))
        LLM_CONFIDENCE_MISSING.labels(provider, model).inc()
        return None
```

## 10. Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Governor overhead | ≤10ms p95 | `agentiq_governor_latency_seconds` |
| Lane allocation | ≤2ms p95 | Internal timing |
| AIQ computation | ≤5ms p95 | Internal timing |
| Confidence calculation | ≤5ms p95 | Internal timing |
| RunReceipt persistence | Async (non-blocking) | Background task |

## 11. Security Considerations

1. **RunReceipts contain no PII** - Only IDs and metrics
2. **Configuration changes audit-logged** - Via existing audit system
3. **Tool selection respects OPA** - Governor runs AFTER OPA gate
4. **Capsule filtering enforced** - Tools filtered by capsule before Top-K

## 12. Testing Strategy

### 12.1 Unit Tests
- Lane allocation with various degradation levels
- AIQ score computation with edge cases
- Confidence calculation modes

### 12.2 Integration Tests
- Full Governor flow with real SomaBrain
- RunReceipt persistence and retrieval
- Degradation level transitions

### 12.3 Property-Based Tests
- Lane budgets always sum to total
- AIQ scores always in [0, 100]
- Confidence scores always in [0, 1] or None

### 12.4 Chaos Tests
- SomaBrain unavailable → Rescue path
- Database unavailable → RunReceipt queued
- High load → Degradation escalation

## 13. Rollout Plan

### Phase 1: Foundation (This Spec)
- [ ] AgentIQ Governor core
- [ ] Lane Allocator
- [ ] Confidence Scorer
- [ ] RunReceipt model and persistence
- [ ] Prometheus metrics
- [ ] Feature flags

### Phase 2: Integration
- [ ] ContextBuilder lane awareness
- [ ] LLM wrapper logprob extraction
- [ ] Gateway middleware integration
- [ ] UI Settings for configuration

### Phase 3: Optimization
- [ ] HTTP/2 connection pool tuning
- [ ] RunReceipt batch persistence
- [ ] Confidence EWMA alerting

### Phase 4 (Future): gRPC Transport
- [ ] Implement `MemoryService` from proto
- [ ] Bidirectional streaming for batches
- [ ] Migration path from HTTP

## 14. Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| httpx | ≥0.24 | HTTP/2 transport |
| prometheus-client | ≥0.17 | Metrics |
| sqlalchemy | ≥2.0 | RunReceipt persistence |
| pydantic | ≥2.0 | Configuration validation |
| temporalio | ≥1.0 | Durable workflows (existing) |

## 15. Open Questions

1. **Q:** Should RunReceipts be stored in PostgreSQL or a time-series DB?
   **A:** PostgreSQL with monthly partitioning for simplicity; migrate to TimescaleDB if needed.

2. **Q:** How to handle confidence for streaming responses?
   **A:** Aggregate logprobs across chunks; emit final confidence in `assistant.final`.

3. **Q:** Should degradation level be per-tenant or global?
   **A:** Per-tenant for isolation; global fallback for infrastructure failures.
