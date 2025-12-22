# Requirements Document

## Introduction

This specification defines the requirements for achieving full, lightning-fast integration between SomaAgent01 and SomaBrain cognitive services. The integration enables advanced cognitive capabilities including memory storage/recall, neuromodulation, adaptation learning, sleep cycles, action execution, and planning.

## Glossary

- **SomaAgent01**: The AI agent framework that consumes SomaBrain services
- **SomaBrain**: Cognitive AI service providing memory, neuromodulation, and adaptation APIs (Port 9696)
- **SomaClient**: HTTP client singleton in SomaAgent01 for SomaBrain communication
- **Neuromodulator**: Simulated neurotransmitter levels (dopamine, serotonin, noradrenaline, acetylcholine)
- **Adaptation_Engine**: Learning system that adjusts retrieval and utility weights based on feedback
- **Sleep_Cycle**: Memory consolidation process with NREM and REM phases
- **Circuit_Breaker**: Fault tolerance pattern that opens after consecutive failures

## Requirements

### Requirement 1: Adaptation Reset Integration

**User Story:** As a cognitive agent, I want to reset my adaptation state to defaults, so that I can start fresh for benchmarks or after significant context changes.

#### Acceptance Criteria

1. WHEN an agent requests adaptation reset, THE SomaClient SHALL call POST `/context/adaptation/reset` with tenant_id, base_lr, and reset_history parameters
2. WHEN the reset succeeds, THE System SHALL update the agent's local adaptation_state to reflect defaults
3. IF the reset fails, THEN THE System SHALL raise SomaClientError with the failure detail
4. THE SomaClient method SHALL use existing circuit breaker and retry patterns

### Requirement 2: Action Execution Integration

**User Story:** As a cognitive agent, I want to execute actions through SomaBrain's `/act` endpoint, so that I can leverage salience scoring and focus tracking for cognitive processing.

#### Acceptance Criteria

1. WHEN an agent executes an action, THE SomaClient SHALL call POST `/act` with task, novelty, and universe parameters
2. WHEN the action succeeds, THE System SHALL return results including salience, pred_error, stored flag, and plan
3. THE System SHALL propagate X-Session-ID header for focus state tracking
4. IF the action fails, THEN THE System SHALL raise SomaClientError with the failure detail

### Requirement 3: Sleep State Transitions

**User Story:** As a cognitive agent, I want to transition between sleep states (active, light, deep, freeze), so that I can manage cognitive load and memory consolidation.

#### Acceptance Criteria

1. WHEN an agent requests sleep state transition, THE SomaClient SHALL call POST `/api/brain/sleep_mode` with target_state, ttl_seconds, async_mode, and trace_id
2. THE target_state parameter SHALL accept values: "active", "light", "deep", "freeze"
3. WHEN ttl_seconds is provided, THE System SHALL auto-revert to previous state after expiration
4. IF the transition fails, THEN THE System SHALL raise SomaClientError with the failure detail

### Requirement 4: Utility Sleep Endpoint

**User Story:** As a cognitive agent, I want to use the utility sleep endpoint for tenant-level sleep transitions, so that I have an alternative path for sleep management.

#### Acceptance Criteria

1. WHEN an agent requests utility sleep, THE SomaClient SHALL call POST `/api/util/sleep` with target_state and optional parameters
2. THE System SHALL support the same target_state values as brain_sleep_mode
3. IF the transition fails, THEN THE System SHALL raise SomaClientError with the failure detail

### Requirement 5: Neuromodulator Clamping Compliance

**User Story:** As a cognitive agent, I want neuromodulator updates to respect physiological ranges, so that the cognitive system remains stable.

#### Acceptance Criteria

1. WHEN updating neuromodulators, THE System SHALL clamp dopamine to [0.0, 0.8]
2. WHEN updating neuromodulators, THE System SHALL clamp serotonin to [0.0, 1.0]
3. WHEN updating neuromodulators, THE System SHALL clamp noradrenaline to [0.0, 0.1]
4. WHEN updating neuromodulators, THE System SHALL clamp acetylcholine to [0.0, 0.5]
5. THE somabrain_integration module SHALL apply clamping before sending to SomaBrain

### Requirement 6: Cognitive Integration Wrappers

**User Story:** As a developer, I want high-level wrapper functions in somabrain_integration.py, so that agent code can easily use all SomaBrain capabilities.

#### Acceptance Criteria

1. THE somabrain_integration module SHALL provide `reset_adaptation_state(agent)` wrapper
2. THE somabrain_integration module SHALL provide `execute_action(agent, task, novelty, universe)` wrapper
3. THE somabrain_integration module SHALL provide `transition_sleep_state(agent, target_state, ttl_seconds)` wrapper
4. WHEN any wrapper fails, THE System SHALL log the error and return appropriate fallback (None or False)

### Requirement 7: Sleep Cycle Fix

**User Story:** As a cognitive agent, I want the sleep_cycle call in cognitive.py to use correct SomaBrain API parameters, so that memory consolidation works properly.

#### Acceptance Criteria

1. WHEN consider_sleep_cycle triggers, THE System SHALL call sleep_cycle with nrem=True and rem=True
2. THE System SHALL NOT pass duration_minutes as it is not used by SomaBrain
3. THE System SHALL use tenant_id from agent context

### Requirement 8: Microcircuit Diagnostics (Admin Mode)

**User Story:** As a system administrator, I want to retrieve microcircuit diagnostics, so that I can monitor cognitive system health.

#### Acceptance Criteria

1. WHEN in ADMIN mode, THE SomaClient SHALL provide `micro_diag()` method calling GET `/micro/diag`
2. THE response SHALL include enabled flag, tenant, columns stats, and namespace
3. IF not in ADMIN mode, THE System SHALL return limited diagnostics

### Requirement 9: Sleep Status All Tenants (Admin Mode)

**User Story:** As a system administrator, I want to view sleep status for all tenants, so that I can monitor system-wide consolidation.

#### Acceptance Criteria

1. WHEN in ADMIN mode, THE SomaClient SHALL provide `sleep_status_all()` method calling GET `/sleep/status/all`
2. THE response SHALL include enabled flag, interval_seconds, and per-tenant sleep timestamps
3. IF not in ADMIN mode, THE System SHALL raise appropriate authorization error

### Requirement 10: Metrics and Observability

**User Story:** As a system operator, I want all SomaBrain calls to emit Prometheus metrics, so that I can monitor integration health.

#### Acceptance Criteria

1. THE SomaClient SHALL emit `somabrain_http_requests_total` counter for all new endpoints
2. THE SomaClient SHALL emit `somabrain_request_seconds` histogram for all new endpoints
3. THE SomaClient SHALL propagate OpenTelemetry trace context via inject()
4. THE SomaClient SHALL include X-Request-ID header on all requests

### Requirement 11: Error Handling Consistency

**User Story:** As a developer, I want consistent error handling across all SomaBrain integrations, so that failures are predictable and recoverable.

#### Acceptance Criteria

1. THE SomaClient SHALL raise SomaClientError for all HTTP 4xx and 5xx responses
2. THE SomaClient SHALL include status code and detail in error messages
3. THE SomaClient SHALL increment circuit breaker counter on 5xx errors
4. THE SomaClient SHALL respect Retry-After header on 429 responses

### Requirement 12: Type Safety and Documentation

**User Story:** As a developer, I want all new methods to have complete type hints and docstrings, so that the code is maintainable.

#### Acceptance Criteria

1. THE SomaClient SHALL have complete type hints for all new method parameters and returns
2. THE SomaClient SHALL have docstrings describing purpose, args, and returns for all new methods
3. THE somabrain_integration module SHALL have complete type hints for all new functions
4. THE cognitive module SHALL have complete type hints for all modified functions
