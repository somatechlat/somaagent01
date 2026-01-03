# Requirements Document

## Introduction

This specification defines the requirements for adding a confidence score (0.0–1.0) to every generated response produced through SomaStack, enabling policy gating, observability, downstream behavior control, and UI transparency.

## Glossary

- **LLM**: Large Language Model provider/model (OpenAI/Anthropic/etc.)
- **logprob**: Natural log of token probability from provider
- **Confidence**: Normalized scalar [0..1] derived from aggregated logprobs
- **Confidence_Calculator**: Module that computes confidence from logprobs
- **OPA**: Open Policy Agent policy engine
- **Event_Store**: Append-only event log used for audit/telemetry

## Requirements

### Requirement 1: Capture Token Log-Probabilities

**User Story:** As a system operator, I want the LLM wrapper to request token-level logprobs, so that confidence can be computed from actual model output.

#### Acceptance Criteria

1. WHEN confidence.enabled is true, THE LLM_Wrapper SHALL request token-level logprobs from the provider
2. WHEN the provider returns logprobs, THE LLM_Wrapper SHALL standardize output into tokens list and token_logprobs list
3. IF the provider does not support logprobs, THEN THE LLM_Wrapper SHALL return null for logprobs without failing the request
4. THE LLM_Wrapper SHALL emit `llm_confidence_missing_total` metric when logprobs are unavailable

### Requirement 2: Compute Normalized Confidence

**User Story:** As a developer, I want a confidence calculator that normalizes logprobs to a 0-1 scalar, so that downstream systems have a consistent confidence metric.

#### Acceptance Criteria

1. THE Confidence_Calculator SHALL implement `calculate_confidence(logprobs: List[float], aggregation: str) -> float | None`
2. WHEN logprobs list is empty or all invalid, THE Confidence_Calculator SHALL return None
3. WHEN aggregation is "average", THE Confidence_Calculator SHALL compute mean of logprobs
4. WHEN aggregation is "min", THE Confidence_Calculator SHALL use minimum logprob
5. WHEN aggregation is "percentile_90", THE Confidence_Calculator SHALL use 10th percentile (lower tail)
6. THE Confidence_Calculator SHALL normalize using `clamp(exp(m), 0.0, 1.0)` where m is aggregated value
7. THE Confidence_Calculator SHALL round to configurable precision (default 3 decimals) for transport

### Requirement 3: Expose Confidence in API Responses

**User Story:** As an API consumer, I want confidence included in all LLM response payloads, so that I can make decisions based on model certainty.

#### Acceptance Criteria

1. WHEN confidence.enabled is true, THE API_Response SHALL include `confidence: float | null` field
2. THE confidence field SHALL appear in `/a2a_chat`, `/delegate`, and tool execution responses
3. FOR streaming responses, THE System SHALL include confidence only in the final summary frame
4. WHEN confidence.enabled is false, THE API_Response SHALL omit the confidence field
5. THE confidence field SHALL be optional for backward compatibility

### Requirement 4: Persist Confidence with Events

**User Story:** As an auditor, I want confidence persisted with events, so that I can trace model certainty over time.

#### Acceptance Criteria

1. WHEN appending events, THE Event_Store SHALL persist `event.payload.confidence` as float or null
2. THE Event_Store SHALL NOT persist raw token_logprobs or token lists
3. THE Event_Store SHALL maintain backward compatibility (unknown fields ignored by old consumers)

### Requirement 5: Configurable Thresholds and Gating

**User Story:** As a policy engineer, I want configurable confidence thresholds, so that I can control system behavior based on certainty levels.

#### Acceptance Criteria

1. THE System SHALL support `confidence.min_acceptance` threshold configuration
2. THE System SHALL support `confidence.on_low` modes: "allow", "flag", "reject"
3. WHEN confidence is null and treat_null_as_low is false, THE System SHALL treat as "allow"
4. WHEN confidence is null and treat_null_as_low is true, THE System SHALL treat as low confidence
5. WHEN on_low is "flag", THE System SHALL attach `metadata.flags += ["LOW_CONFIDENCE"]`
6. WHEN on_low is "reject", THE System SHALL return error code `LOW_CONFIDENCE_REJECTED`

### Requirement 6: Policy Integration (OPA)

**User Story:** As a policy engineer, I want OPA policies to access confidence, so that I can write rules based on model certainty.

#### Acceptance Criteria

1. THE OPA_Input SHALL include `input.confidence` as float or null
2. THE OPA_Input SHALL include `input.confidence_enabled` as boolean
3. THE OPA_Input SHALL include `input.request_id`, `input.tenant_id`, `input.endpoint`
4. OPA policies SHALL be able to deny requests based on confidence threshold

### Requirement 7: Backward Compatibility

**User Story:** As an existing API consumer, I want confidence to be additive only, so that my integrations continue working.

#### Acceptance Criteria

1. THE confidence feature SHALL be additive (no breaking changes)
2. Old clients SHALL continue to work without modification
3. THE API schema change SHALL be a minor version bump only

### Requirement 8: Observability and Logging

**User Story:** As an SRE, I want confidence metrics and logs, so that I can monitor model certainty distributions.

#### Acceptance Criteria

1. THE System SHALL emit `llm_confidence_average` gauge metric with tenant, model, endpoint labels
2. THE System SHALL emit `llm_confidence_histogram` with buckets 0..1
3. THE System SHALL emit `llm_confidence_missing_total` counter
4. THE System SHALL emit `llm_confidence_rejected_total` counter when on_low is "reject"
5. THE System SHALL emit structured logs with request_id, tenant_id, model, endpoint, confidence, confidence_mode, duration_ms
6. THE System SHALL NOT log raw token logprobs

### Requirement 9: Performance Constraints

**User Story:** As a system operator, I want confidence computation to be fast, so that it doesn't impact response latency.

#### Acceptance Criteria

1. THE Confidence_Calculator SHALL add no more than 5ms overhead on warm path
2. THE Confidence_Calculator SHALL add no more than 10ms overhead on cold path
3. THE Confidence_Calculator SHALL be O(n) over token count
4. THE System SHALL sustain existing load targets (≥10k RPS) without new bottlenecks

### Requirement 10: Security and Privacy

**User Story:** As a security officer, I want confidence to not leak model internals, so that sensitive data is protected.

#### Acceptance Criteria

1. THE System SHALL NOT expose or persist raw logprobs or tokens
2. THE System SHALL only store the confidence scalar and algorithm label
3. THE System SHALL validate confidence range [0..1] before emitting to logs
4. Reading confidence metrics SHALL be restricted to admin/operator roles

### Requirement 11: Configuration Management

**User Story:** As an operator, I want confidence behavior configurable without code changes, so that I can tune thresholds in production.

#### Acceptance Criteria

1. THE System SHALL support YAML configuration for confidence settings
2. THE System SHALL support environment variable overrides (CONFIDENCE_ENABLED, CONFIDENCE_AGGREGATION, etc.)
3. THE System SHALL allow enable/disable and threshold changes without code deployment
4. THE System SHALL support optional per-tenant threshold overrides

### Requirement 12: Multi-Tenant Support

**User Story:** As a platform operator, I want confidence isolated per tenant, so that metrics and policies are tenant-scoped.

#### Acceptance Criteria

1. THE confidence metrics and logs SHALL include tenant_id
2. THE confidence thresholds MAY be overridden per tenant
3. THE Event_Store SHALL include tenant_id with confidence data
