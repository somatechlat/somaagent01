# AgentIQ Governor

Lane-based token budgeting and AIQ scoring for SomaAgent01.

## Overview

AgentIQ is a Governor-mediated control loop that transforms SomaAgent01 into a budgeted transaction system. It provides:

- **Lane-based token budgeting** - 6 lanes for context assembly
- **Capsule-scoped tool discovery** - Filter tools by capsule permissions
- **Adaptive degradation** - L0-L4 levels for graceful degradation
- **AIQ scoring** - Intelligence quotient for quality tracking
- **RunReceipt emission** - Audit records for every turn

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Request Flow                            │
├─────────────────────────────────────────────────────────────┤
│  OPA Gate → AgentIQ Governor → ContextBuilder → LLM Call    │
└─────────────────────────────────────────────────────────────┘
```

### Execution Position

AgentIQ Governor runs:
- **After** OPA policy gates approve the request
- **Before** LLM invocation or tool dispatch
- **In-process** (no network calls for Governor logic)

Target latency: ≤10ms p95

## Lane System

Token budget is allocated across 6 lanes:

| Lane | Purpose | Default Ratio |
|------|---------|---------------|
| `system_policy` | System prompt + OPA policies | 15% |
| `history` | Conversation history | 25% |
| `memory` | SomaBrain retrieved context | 25% |
| `tools` | Tool definitions | 20% |
| `tool_results` | Previous tool outputs | 10% |
| `buffer` | Safety margin (minimum 200) | 5% |

### Lane Allocation by Degradation Level

| Level | History | Memory | Tools | Buffer |
|-------|---------|--------|-------|--------|
| L0 (Normal) | 25% | 25% | 20% | 5% |
| L1 (Minor) | 15% | 30% | 10% | 10% |
| L2 (Moderate) | 10% | 15% | 5% | 15% |
| L3 (Severe) | 0% | 10% | 0% | 20% |
| L4 (Critical) | 0% | 0% | 0% | 30% |

## Configuration

### Environment Variables

```bash
# Feature flag (default: disabled)
SA01_ENABLE_AGENTIQ_GOVERNOR=true

# Confidence scoring (default: disabled)
SA01_ENABLE_CONFIDENCE_SCORING=true
SA01_CONFIDENCE_MODE=average  # average, min, percentile_90
```

### Configuration File

`conf/agentiq.yaml`:

```yaml
agentiq:
  enabled: true
  weights:
    context_quality: 0.4
    tool_relevance: 0.3
    budget_efficiency: 0.3
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
    buffer:
      min: 200
      max: 500
  degradation:
    l1_threshold: 0.7
    l2_threshold: 0.5
    l3_threshold: 0.3
    l4_threshold: 0.1
  tool_k:
    normal: 5
    l1: 3
    l2: 1
    l3: 0
    l4: 0
```

## API Reference

### GovernorDecision

Result of `Governor.govern()` call:

```python
@dataclass(frozen=True)
class GovernorDecision:
    lane_plan: LanePlan       # Token allocation per lane
    aiq_score: AIQScore       # Predicted/observed scores
    degradation_level: DegradationLevel
    path_mode: PathMode       # "fast" or "rescue"
    tool_k: int               # Max tools to use
    capsule_id: Optional[str]
    allowed_tools: List[str]
    latency_ms: float
```

### RunReceipt

Audit record emitted per turn:

```python
@dataclass(frozen=True)
class RunReceipt:
    turn_id: str
    session_id: str
    tenant_id: str
    capsule_id: Optional[str]
    aiq_pred: float           # 0-100
    aiq_obs: float            # 0-100
    confidence: Optional[float]  # 0-1
    lane_budgets: Dict[str, int]
    lane_actual: Dict[str, int]
    degradation_level: str
    path_mode: str
    tool_k: int
    latency_ms: float
    timestamp: float
```

## Metrics

### Prometheus Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `agentiq_aiq_pred` | histogram | Predicted AIQ scores |
| `agentiq_aiq_obs` | histogram | Observed AIQ scores |
| `agentiq_degradation_level` | gauge | Current degradation level |
| `agentiq_path_mode` | counter | Fast vs rescue path usage |
| `agentiq_lane_utilization` | gauge | Token usage per lane |
| `agentiq_governor_latency_seconds` | histogram | Governor execution time |
| `llm_confidence_score` | histogram | LLM response confidence |
| `llm_confidence_missing_total` | counter | Responses without logprobs |
| `llm_confidence_rejected_total` | counter | Low confidence rejections |

## Usage

### Basic Usage

```python
from python.somaagent.agentiq_governor import (
    AgentIQGovernor,
    TurnContext,
)
from services.common.capsule_store import CapsuleStore
from services.common.degradation_monitor import DegradationMonitor
from services.common.budget_manager import BudgetManager

# Initialize
governor = AgentIQGovernor(
    capsule_store=CapsuleStore(db),
    degradation_monitor=DegradationMonitor(),
    budget_manager=BudgetManager(),
)

# Create turn context
turn = TurnContext(
    turn_id="turn-123",
    session_id="session-456",
    tenant_id="tenant-789",
    user_message="Hello!",
    available_tools=["echo", "search"],
)

# Get decision
decision = await governor.govern_with_fallback(turn, max_tokens=8000)

# Use lane plan in ContextBuilder
context = await context_builder.build_for_turn(
    turn=turn_dict,
    max_prompt_tokens=8000,
    lane_plan=decision.lane_plan,
)
```

### With Confidence Scoring

```python
from python.somaagent.confidence_scorer import ConfidenceScorer

scorer = ConfidenceScorer()

# After LLM call, extract logprobs
logprobs = response.choices[0].logprobs.content

# Calculate confidence
result = scorer.calculate(
    logprobs=[t.logprob for t in logprobs],
    provider="openai",
    model="gpt-4",
)

# Evaluate against threshold
is_ok, message = scorer.evaluate_result(result)
if not is_ok:
    # Handle low confidence
    pass
```

## Troubleshooting

### Governor Latency > 10ms

1. Check capsule store DB connection
2. Verify degradation monitor cache is working
3. Profile with `agentiq_governor_latency_seconds` histogram

### Low AIQ Scores

1. Check memory snippet quality (SomaBrain health)
2. Verify tool availability matches user intent
3. Review degradation level - may be in degraded state

### Rescue Path Triggered Unexpectedly

1. Check `agentiq_degradation_level` gauge
2. Review recent failures in degradation monitor
3. Verify capsule constraints aren't too restrictive

## Database Schema

Table: `run_receipts`

```sql
CREATE TABLE run_receipts (
    id UUID PRIMARY KEY,
    turn_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    capsule_id TEXT,
    aiq_pred REAL NOT NULL,
    aiq_obs REAL NOT NULL,
    confidence REAL,
    lane_budgets JSONB NOT NULL,
    lane_actual JSONB NOT NULL,
    degradation_level TEXT NOT NULL,
    path_mode TEXT NOT NULL,
    tool_k INTEGER NOT NULL,
    latency_ms REAL NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
```

Indexes: `session_id`, `tenant_id`, `created_at`, `degradation_level`
