# Implementation Tasks

## Task 1: Add adaptation_reset() method to SomaClient

**Requirements:** REQ-1

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Add `adaptation_reset()` async method after `adaptation_state()` method
- [x] Accept parameters: tenant_id, base_lr, reset_history, retrieval_defaults, utility_defaults, gains, constraints
- [x] Build request body with non-None values only
- [x] Call `POST /context/adaptation/reset`
- [x] Return response mapping
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Method calls correct endpoint with correct payload structure
- Uses existing `_request()` infrastructure for metrics/retry/circuit breaker
- Raises `SomaClientError` on failure

**STATUS: COMPLETE**

---

## Task 2: Add act() method to SomaClient

**Requirements:** REQ-2

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Add `act()` async method in cognitive endpoints section
- [x] Accept parameters: task (required), top_k, universe, session_id
- [x] Build request body with task, top_k, universe
- [x] Add `X-Session-ID` header if session_id provided
- [x] Call `POST /act`
- [x] Return ActResponse mapping
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Method calls correct endpoint with correct payload structure
- Propagates X-Session-ID header for focus state tracking
- Uses existing `_request()` infrastructure

**STATUS: COMPLETE**

---

## Task 3: Add brain_sleep_mode() method to SomaClient

**Requirements:** REQ-3

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Add `brain_sleep_mode()` async method in sleep endpoints section
- [x] Accept parameters: target_state (required), ttl_seconds, async_mode, trace_id
- [x] Validate target_state is one of: "active", "light", "deep", "freeze"
- [x] Build SleepRequest body
- [x] Call `POST /api/brain/sleep_mode`
- [x] Return response mapping
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Method validates target_state before sending
- Raises ValueError for invalid target_state
- Uses existing `_request()` infrastructure

**STATUS: COMPLETE**

---

## Task 4: Add util_sleep() method to SomaClient

**Requirements:** REQ-4

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Add `util_sleep()` async method in sleep endpoints section
- [x] Accept parameters: target_state (required), ttl_seconds, async_mode, trace_id
- [x] Validate target_state is one of: "active", "light", "deep", "freeze"
- [x] Build SleepRequest body
- [x] Call `POST /api/util/sleep`
- [x] Return response mapping
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Method validates target_state before sending
- Raises ValueError for invalid target_state
- Uses existing `_request()` infrastructure

**STATUS: COMPLETE**

---

## Task 5: Add micro_diag() method to SomaClient

**Requirements:** REQ-8

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Add `micro_diag()` async method in cognitive endpoints section
- [x] No parameters required
- [x] Call `GET /micro/diag`
- [x] Return diagnostic mapping
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Method calls correct endpoint
- Uses existing `_request()` infrastructure
- Returns diagnostic info or raises SomaClientError

**STATUS: COMPLETE**

---

## Task 6: Add sleep_status_all() method to SomaClient

**Requirements:** REQ-9

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Add `sleep_status_all()` async method in sleep endpoints section
- [x] No parameters required
- [x] Call `GET /sleep/status/all`
- [x] Return status mapping with tenants dict
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Method calls correct endpoint
- Uses existing `_request()` infrastructure
- Returns all-tenant status or raises SomaClientError

**STATUS: COMPLETE**

---

## Task 7: Add neuromodulator clamping to somabrain_integration.py

**Requirements:** REQ-5

**File:** `somaAgent01/python/somaagent/somabrain_integration.py`

**Changes:**
- [x] Add `NEUROMOD_CLAMP_RANGES` constant dict at module level
- [x] Add `clamp_neuromodulator(name: str, value: float) -> float` function
- [x] Update `update_neuromodulators()` to use clamping before sending to SomaBrain
- [x] Update clamping ranges: dopamine [0.0, 0.8], serotonin [0.0, 1.0], noradrenaline [0.0, 0.1], acetylcholine [0.0, 0.5]

**Acceptance Criteria:**
- All neuromodulator values are clamped before API call
- Clamping function is idempotent
- Existing tests continue to pass

**STATUS: COMPLETE**

---

## Task 8: Add reset_adaptation_state() wrapper to somabrain_integration.py

**Requirements:** REQ-6

**File:** `somaAgent01/python/somaagent/somabrain_integration.py`

**Changes:**
- [x] Add `reset_adaptation_state(agent, base_lr, reset_history) -> bool` async function
- [x] Call `agent.soma_client.adaptation_reset()`
- [x] Handle SomaClientError and log warning
- [x] Return True on success, False on failure
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Wrapper handles errors gracefully
- Returns boolean success indicator
- Logs failures with PrintStyle

**STATUS: COMPLETE**

---

## Task 9: Add execute_action() wrapper to somabrain_integration.py

**Requirements:** REQ-6

**File:** `somaAgent01/python/somaagent/somabrain_integration.py`

**Changes:**
- [x] Add `execute_action(agent, task, universe) -> Optional[Dict]` async function
- [x] Call `agent.soma_client.act()` with session_id from agent
- [x] Handle SomaClientError and log warning
- [x] Return ActResponse dict on success, None on failure
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Wrapper handles errors gracefully
- Propagates session_id for focus tracking
- Returns response dict or None

**STATUS: COMPLETE**

---

## Task 10: Add transition_sleep_state() wrapper to somabrain_integration.py

**Requirements:** REQ-6

**File:** `somaAgent01/python/somaagent/somabrain_integration.py`

**Changes:**
- [x] Add `transition_sleep_state(agent, target_state, ttl_seconds) -> bool` async function
- [x] Call `agent.soma_client.brain_sleep_mode()`
- [x] Handle SomaClientError and ValueError, log warning
- [x] Return True on success, False on failure
- [x] Add complete type hints and docstring

**Acceptance Criteria:**
- Wrapper handles errors gracefully
- Returns boolean success indicator
- Logs failures with PrintStyle

**STATUS: COMPLETE**

---

## Task 11: Fix sleep_cycle call in cognitive.py

**Requirements:** REQ-7

**File:** `somaAgent01/python/somaagent/cognitive.py`

**Changes:**
- [x] Locate `consider_sleep_cycle()` function
- [x] Change `duration_minutes=5` to `nrem=True, rem=True`
- [x] Remove unused `duration_minutes` parameter

**Before:**
```python
sleep_result = await agent.soma_client.sleep_cycle(
    tenant_id=agent.tenant_id,
    persona_id=agent.persona_id,
    duration_minutes=5,
)
```

**After:**
```python
sleep_result = await agent.soma_client.sleep_cycle(
    tenant_id=agent.tenant_id,
    persona_id=agent.persona_id,
    nrem=True,
    rem=True,
)
```

**Acceptance Criteria:**
- sleep_cycle called with correct SomaBrain API parameters
- No duration_minutes parameter used
- Memory consolidation triggers correctly

**STATUS: COMPLETE**

---

## Task 12: Update __all__ export in soma_client.py

**Requirements:** REQ-12

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Verify `__all__` list includes all public exports
- [x] No changes needed if already correct (SomaClient, SomaClientError, SomaMemoryRecord)

**Acceptance Criteria:**
- Module exports are complete and correct

**STATUS: COMPLETE (no changes needed)**

---

## Task 13: Add integration tests for new endpoints

**Requirements:** REQ-10, REQ-11

**File:** `somaAgent01/tests/integrations/test_soma_client_integration.py`

**Changes:**
- [x] Add test for `adaptation_reset()` with real SomaBrain
- [x] Add test for `act()` with real SomaBrain (xfail - SomaBrain bug)
- [x] Add test for `brain_sleep_mode()` with real SomaBrain (xfail - SomaBrain bug)
- [x] Add test for `util_sleep()` with real SomaBrain (xfail - SomaBrain bug)
- [x] Add test for `micro_diag()` with real SomaBrain
- [x] Add test for `sleep_status_all()` with real SomaBrain
- [x] Add test for neuromodulator clamping (moved to separate file due to import deps)
- [x] Skip tests if infrastructure unavailable

**Acceptance Criteria:**
- Tests use real infrastructure (no mocks per VIBE rules)
- Tests skip gracefully when SomaBrain unavailable
- All new methods have test coverage

**Known SomaBrain Bugs (xfail):**
- `/act` endpoint: Cognitive processing error
- `/api/brain/sleep_mode` and `/api/util/sleep`: TenantSleepState model missing `updated_at` default

**STATUS: COMPLETE**

---

## Task 14: Verify metrics emission for new endpoints

**Requirements:** REQ-10

**File:** `somaAgent01/python/integrations/soma_client.py`

**Changes:**
- [x] Verify all new methods use `_request()` which emits metrics
- [x] No additional changes needed if using `_request()` infrastructure

**Acceptance Criteria:**
- `somabrain_http_requests_total` counter incremented for new endpoints
- `somabrain_request_seconds` histogram recorded for new endpoints
- OpenTelemetry trace context propagated

**STATUS: COMPLETE (all new methods use _request())**

---

## Summary

| Task | File | Priority | Complexity |
|------|------|----------|------------|
| 1 | soma_client.py | HIGH | LOW |
| 2 | soma_client.py | HIGH | LOW |
| 3 | soma_client.py | HIGH | LOW |
| 4 | soma_client.py | MEDIUM | LOW |
| 5 | soma_client.py | MEDIUM | LOW |
| 6 | soma_client.py | MEDIUM | LOW |
| 7 | somabrain_integration.py | HIGH | LOW |
| 8 | somabrain_integration.py | MEDIUM | LOW |
| 9 | somabrain_integration.py | HIGH | LOW |
| 10 | somabrain_integration.py | MEDIUM | LOW |
| 11 | cognitive.py | CRITICAL | LOW |
| 12 | soma_client.py | LOW | LOW |
| 13 | tests/ | HIGH | MEDIUM |
| 14 | soma_client.py | LOW | LOW |

**Recommended Order:**
1. Task 11 (Critical bug fix)
2. Tasks 1-6 (SomaClient methods)
3. Task 7 (Neuromodulator clamping)
4. Tasks 8-10 (Wrapper functions)
5. Tasks 12-14 (Cleanup and tests)
