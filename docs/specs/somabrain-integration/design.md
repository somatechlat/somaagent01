# Design Document

## Introduction

This document specifies the technical design for achieving full SomaBrain integration in SomaAgent01. The design covers new SomaClient methods, wrapper functions in somabrain_integration.py, bug fixes in cognitive.py, and neuromodulator clamping compliance.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SomaAgent01                                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    Agent (agent.py)                              │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │    │
│  │  │ cognitive.py    │  │ somabrain_      │  │ soma_client.py  │  │    │
│  │  │ (high-level)    │──│ integration.py  │──│ (HTTP client)   │  │    │
│  │  │                 │  │ (wrappers)      │  │                 │  │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SomaBrain (Port 9696)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐          │
│  │ /act            │  │ /context/       │  │ /sleep/run      │          │
│  │ /plan/suggest   │  │ adaptation/     │  │ /sleep/status   │          │
│  │ /micro/diag     │  │ reset           │  │ /api/brain/     │          │
│  │                 │  │ /state          │  │ sleep_mode      │          │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Design Details

### Component 1: SomaClient New Methods

**Relevant Requirements:** REQ-1, REQ-2, REQ-3, REQ-4, REQ-8, REQ-9

#### 1.1 adaptation_reset() Method

```python
async def adaptation_reset(
    self,
    *,
    tenant_id: Optional[str] = None,
    base_lr: Optional[float] = None,
    reset_history: bool = True,
    retrieval_defaults: Optional[Mapping[str, float]] = None,
    utility_defaults: Optional[Mapping[str, float]] = None,
    gains: Optional[Mapping[str, float]] = None,
    constraints: Optional[Mapping[str, float]] = None,
) -> Mapping[str, Any]:
    """Reset adaptation engine to defaults for clean benchmarks.

    Args:
        tenant_id: Tenant identifier for per-tenant reset
        base_lr: Optional base learning rate override
        reset_history: Whether to clear feedback history (default True)
        retrieval_defaults: Optional retrieval weight defaults {alpha, beta, gamma, tau}
        utility_defaults: Optional utility weight defaults {lambda_, mu, nu}
        gains: Optional adaptation gains {alpha, gamma, lambda_, mu, nu}
        constraints: Optional adaptation constraints {*_min, *_max}

    Returns:
        {"ok": True, "tenant_id": str}

    Raises:
        SomaClientError: On HTTP 4xx/5xx or network failure
    """
```

**Endpoint:** `POST /context/adaptation/reset`

**Request Body:**
```json
{
  "tenant_id": "string|null",
  "base_lr": 0.01,
  "reset_history": true,
  "retrieval_defaults": {"alpha": 0.5, "beta": 0.5, "gamma": 0.5, "tau": 0.5},
  "utility_defaults": {"lambda_": 0.5, "mu": 0.5, "nu": 0.5},
  "gains": {"alpha": 0.1, "gamma": 0.1, "lambda_": 0.1, "mu": 0.1, "nu": 0.1},
  "constraints": {"alpha_min": 0.0, "alpha_max": 1.0, ...}
}
```

#### 1.2 act() Method

```python
async def act(
    self,
    task: str,
    *,
    top_k: int = 3,
    universe: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Mapping[str, Any]:
    """Execute a cognitive action step with salience scoring.

    Args:
        task: The task/action description to execute
        top_k: Number of memory hits to consider (default 3)
        universe: Optional universe scope for memory operations
        session_id: Optional session ID for focus state tracking

    Returns:
        ActResponse with task, results (list of ActStepResult), plan, plan_universe

    Raises:
        SomaClientError: On HTTP 4xx/5xx or network failure
    """
```

**Endpoint:** `POST /act`

**Request Body:**
```json
{
  "task": "string",
  "top_k": 3,
  "universe": "string|null"
}
```

**Response:**
```json
{
  "task": "string",
  "results": [
    {
      "step": "string",
      "novelty": 0.5,
      "pred_error": 0.5,
      "salience": 0.7,
      "stored": true,
      "wm_hits": 2,
      "memory_hits": 5,
      "policy": null
    }
  ],
  "plan": ["step1", "step2"],
  "plan_universe": "string|null"
}
```

#### 1.3 brain_sleep_mode() Method

```python
async def brain_sleep_mode(
    self,
    target_state: str,
    *,
    ttl_seconds: Optional[int] = None,
    async_mode: bool = False,
    trace_id: Optional[str] = None,
) -> Mapping[str, Any]:
    """Transition tenant sleep state via cognitive endpoint.

    Args:
        target_state: One of "active", "light", "deep", "freeze"
        ttl_seconds: Optional TTL after which state auto-reverts to active
        async_mode: If True, return immediately (non-blocking)
        trace_id: Optional trace identifier for observability

    Returns:
        Sleep transition response

    Raises:
        SomaClientError: On HTTP 4xx/5xx or network failure
        ValueError: If target_state is invalid
    """
```

**Endpoint:** `POST /api/brain/sleep_mode`

#### 1.4 util_sleep() Method

```python
async def util_sleep(
    self,
    target_state: str,
    *,
    ttl_seconds: Optional[int] = None,
    async_mode: bool = False,
    trace_id: Optional[str] = None,
) -> Mapping[str, Any]:
    """Transition tenant sleep state via utility endpoint.

    Args:
        target_state: One of "active", "light", "deep", "freeze"
        ttl_seconds: Optional TTL after which state auto-reverts to active
        async_mode: If True, return immediately (non-blocking)
        trace_id: Optional trace identifier for observability

    Returns:
        Sleep transition response

    Raises:
        SomaClientError: On HTTP 4xx/5xx or network failure
        ValueError: If target_state is invalid
    """
```

**Endpoint:** `POST /api/util/sleep`

#### 1.5 micro_diag() Method

```python
async def micro_diag(self) -> Mapping[str, Any]:
    """Get microcircuit diagnostics (admin mode).

    Returns:
        Diagnostic info with enabled, tenant, columns, namespace

    Raises:
        SomaClientError: On HTTP 4xx/5xx or network failure
    """
```

**Endpoint:** `GET /micro/diag`

#### 1.6 sleep_status_all() Method

```python
async def sleep_status_all(self) -> Mapping[str, Any]:
    """Get sleep status for all tenants (admin mode).

    Returns:
        {"enabled": bool, "interval_seconds": int, "tenants": {tid: {nrem, rem}}}

    Raises:
        SomaClientError: On HTTP 4xx/5xx or network failure
    """
```

**Endpoint:** `GET /sleep/status/all`

---

### Component 2: Neuromodulator Clamping

**Relevant Requirements:** REQ-5

The SomaBrain neuromod.py router enforces these physiological ranges:

| Neuromodulator | Min | Max |
|----------------|-----|-----|
| dopamine       | 0.0 | 0.8 |
| serotonin      | 0.0 | 1.0 |
| noradrenaline  | 0.0 | 0.1 |
| acetylcholine  | 0.0 | 0.5 |

**Implementation in somabrain_integration.py:**

```python
# Neuromodulator clamping ranges (from SomaBrain neuromod.py)
NEUROMOD_CLAMP_RANGES = {
    "dopamine": (0.0, 0.8),
    "serotonin": (0.0, 1.0),
    "noradrenaline": (0.0, 0.1),
    "acetylcholine": (0.0, 0.5),
}

def clamp_neuromodulator(name: str, value: float) -> float:
    """Clamp neuromodulator value to physiological range."""
    min_val, max_val = NEUROMOD_CLAMP_RANGES.get(name, (0.0, 1.0))
    return max(min_val, min(max_val, value))
```

---

### Component 3: Wrapper Functions in somabrain_integration.py

**Relevant Requirements:** REQ-6

#### 3.1 reset_adaptation_state()

```python
async def reset_adaptation_state(
    agent: "Agent",
    base_lr: Optional[float] = None,
    reset_history: bool = True,
) -> bool:
    """Reset adaptation state to defaults for clean benchmarks.

    Args:
        agent: The agent instance
        base_lr: Optional base learning rate override
        reset_history: Whether to clear feedback history

    Returns:
        True if reset succeeded, False otherwise
    """
```

#### 3.2 execute_action()

```python
async def execute_action(
    agent: "Agent",
    task: str,
    *,
    universe: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Execute a cognitive action through SomaBrain.

    Args:
        agent: The agent instance
        task: The task/action description
        universe: Optional universe scope

    Returns:
        ActResponse dict or None on failure
    """
```

#### 3.3 transition_sleep_state()

```python
async def transition_sleep_state(
    agent: "Agent",
    target_state: str,
    *,
    ttl_seconds: Optional[int] = None,
) -> bool:
    """Transition agent to specified sleep state.

    Args:
        agent: The agent instance
        target_state: One of "active", "light", "deep", "freeze"
        ttl_seconds: Optional TTL for auto-revert

    Returns:
        True if transition succeeded, False otherwise
    """
```

---

### Component 4: Bug Fix in cognitive.py

**Relevant Requirements:** REQ-7

**Current (Buggy) Code:**
```python
sleep_result = await agent.soma_client.sleep_cycle(
    tenant_id=agent.tenant_id,
    persona_id=agent.persona_id,
    duration_minutes=5,  # BUG: SomaBrain doesn't use duration_minutes
)
```

**Fixed Code:**
```python
sleep_result = await agent.soma_client.sleep_cycle(
    tenant_id=agent.tenant_id,
    persona_id=agent.persona_id,
    nrem=True,
    rem=True,
)
```

---

### Component 5: Metrics and Observability

**Relevant Requirements:** REQ-10

All new SomaClient methods will:
1. Emit `somabrain_http_requests_total` counter with labels (method, path, status)
2. Emit `somabrain_request_seconds` histogram with labels (method, path, status)
3. Propagate OpenTelemetry trace context via `inject()`
4. Include `X-Request-ID` header on all requests

This is already handled by the existing `_request()` method infrastructure.

---

### Component 6: Error Handling

**Relevant Requirements:** REQ-11

All new methods will:
1. Raise `SomaClientError` for HTTP 4xx/5xx responses
2. Include status code and detail in error messages
3. Increment circuit breaker counter on 5xx errors
4. Respect `Retry-After` header on 429 responses

This is already handled by the existing `_request()` method infrastructure.

---

## Correctness Properties (for Property-Based Testing)

### Property 1: Neuromodulator Clamping Idempotence
```
∀ name ∈ {dopamine, serotonin, noradrenaline, acetylcholine},
∀ value ∈ ℝ:
  clamp(name, clamp(name, value)) == clamp(name, value)
```

### Property 2: Neuromodulator Range Compliance
```
∀ name ∈ {dopamine, serotonin, noradrenaline, acetylcholine},
∀ value ∈ ℝ:
  min_range[name] ≤ clamp(name, value) ≤ max_range[name]
```

### Property 3: Sleep State Validity
```
∀ state ∈ {"active", "light", "deep", "freeze"}:
  brain_sleep_mode(state) succeeds OR raises SomaClientError
```

### Property 4: Circuit Breaker Monotonicity
```
After N consecutive 5xx errors where N ≥ CB_THRESHOLD:
  circuit_breaker_open == True
```

### Property 5: Retry-After Compliance
```
∀ response with status 429 and Retry-After header:
  actual_delay ≥ min(Retry-After_seconds, 120)
```

---

## Data Flow Diagrams

### Sleep Cycle Flow (Fixed)

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
│ cognitive.py│     │ somabrain_          │     │ soma_client │
│             │     │ integration.py      │     │             │
└──────┬──────┘     └──────────┬──────────┘     └──────┬──────┘
       │                       │                       │
       │ consider_sleep_cycle()│                       │
       │──────────────────────>│                       │
       │                       │                       │
       │                       │ sleep_cycle(nrem=T,  │
       │                       │ rem=T)               │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │                       │ POST /sleep/run
       │                       │                       │ {nrem:true,rem:true}
       │                       │                       │──────────────────>
       │                       │                       │
       │                       │<──────────────────────│
       │                       │ SleepRunResponse      │
       │<──────────────────────│                       │
       │ sleep_result          │                       │
       │                       │                       │
       │ optimize_cognitive_   │                       │
       │ parameters()          │                       │
       │                       │                       │
```

### Action Execution Flow

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────┐
│ Agent Code  │     │ somabrain_          │     │ soma_client │
│             │     │ integration.py      │     │             │
└──────┬──────┘     └──────────┬──────────┘     └──────┬──────┘
       │                       │                       │
       │ execute_action(task)  │                       │
       │──────────────────────>│                       │
       │                       │                       │
       │                       │ act(task, session_id) │
       │                       │──────────────────────>│
       │                       │                       │
       │                       │                       │ POST /act
       │                       │                       │ X-Session-ID: ...
       │                       │                       │──────────────────>
       │                       │                       │
       │                       │<──────────────────────│
       │                       │ ActResponse           │
       │<──────────────────────│                       │
       │ {salience, pred_error,│                       │
       │  stored, plan}        │                       │
```

---

## Security Considerations

1. **Admin Endpoints**: `micro_diag()` and `sleep_status_all()` require admin authentication in SomaBrain. The client will propagate auth headers but not enforce admin mode locally.

2. **Adaptation Reset**: Only allowed in dev mode per SomaBrain implementation. The client will receive HTTP 403 if called in prod.

3. **Tenant Isolation**: All methods propagate `X-Tenant-ID` header for proper tenant scoping.

---

## Testing Strategy

1. **Integration Tests**: Real SomaBrain instance (port 9696) to verify all endpoint flows
2. **Property Tests**: Hypothesis-based tests for clamping and state machine properties with real infrastructure
3. **Load Tests**: Verify circuit breaker behavior under real failure conditions
4. **Skip Pattern**: Tests skip gracefully when SomaBrain infrastructure unavailable

**NO MOCKS** - All tests use real SomaBrain service per VIBE Coding Rules.

---

## Dependencies

- `httpx`: Async HTTP client (existing)
- `opentelemetry`: Trace propagation (existing)
- `prometheus_client`: Metrics (existing via observability.metrics)

No new dependencies required.
