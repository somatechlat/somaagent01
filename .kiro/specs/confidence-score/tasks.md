# Confidence Score - Implementation Tasks

## Document Control

| Field | Value |
|-------|-------|
| **Document ID** | SA01-CONF-TASKS-2025-12 |
| **Version** | 1.0 |
| **Date** | 2025-12-21 |
| **Status** | CANONICAL |
| **Implements** | SA01-CONF-DESIGN-2025-12 |

---

## Task Overview

| ID | Task | Priority | Effort | Dependencies | Status |
|----|------|----------|--------|--------------|--------|
| T1 | Create Confidence Calculator | P0 | 2h | None | ⏳ PENDING |
| T2 | Create Confidence Configuration | P0 | 1h | None | ⏳ PENDING |
| T3 | Add LLM Logprob Extraction | P0 | 3h | T1, T2 | ⏳ PENDING |
| T4 | Implement Threshold Enforcement | P0 | 2h | T1, T2 | ⏳ PENDING |
| T5 | Add Prometheus Metrics | P0 | 2h | T1 | ⏳ PENDING |
| T6 | Update API Response Serialization | P1 | 2h | T1, T4 | ⏳ PENDING |
| T7 | Add OPA Integration | P1 | 2h | T1 | ⏳ PENDING |
| T8 | Update Event Persistence | P1 | 1h | T1 | ⏳ PENDING |
| T9 | Unit Tests | P1 | 3h | T1-T4 | ⏳ PENDING |
| T10 | Property Tests | P1 | 2h | T1-T4 | ⏳ PENDING |
| T11 | Integration Tests | P2 | 3h | T1-T8 | ⏳ PENDING |
| T12 | Documentation | P2 | 1h | All | ⏳ PENDING |

---

## Task 1: Create Confidence Calculator

**File:** `somaAgent01/python/somaagent/confidence_scorer.py`

**Requirements:** REQ-CONF-001, REQ-CONF-002, REQ-CONF-009

### Acceptance Criteria
- [ ] Implements `calculate_confidence(logprobs, aggregation, precision)` function
- [ ] Supports 3 aggregation modes: average, min, percentile_90
- [ ] Returns float 0.0-1.0 or None
- [ ] Handles empty/missing logprobs gracefully (returns None)
- [ ] Filters NaN and None values before calculation
- [ ] Calculation overhead ≤5ms
- [ ] Uses `math.exp()` for normalization with clamping to [0, 1]

### Implementation Notes
```python
# Key function signature:
def calculate_confidence(
    logprobs: Optional[List[float]],
    aggregation: str = "average",
    precision: int = 3,
) -> Optional[float]:
    """Calculate normalized confidence score from token logprobs."""
```

---

## Task 2: Create Confidence Configuration

**File:** `somaAgent01/python/somaagent/confidence_config.py`

**Requirements:** REQ-CONF-005, REQ-CONF-011

### Acceptance Criteria
- [ ] Creates `ConfidenceConfig` dataclass with all settings
- [ ] Implements `from_env()` class method for environment loading
- [ ] Supports CONFIDENCE_ENABLED, CONFIDENCE_AGGREGATION env vars
- [ ] Supports CONFIDENCE_MIN_ACCEPTANCE, CONFIDENCE_ON_LOW env vars
- [ ] Supports CONFIDENCE_TREAT_NULL_AS_LOW, CONFIDENCE_PRECISION_DECIMALS
- [ ] Implements singleton pattern via `get_confidence_config()`
- [ ] Integrates with existing `src.core.config.cfg` system

### Implementation Notes
```python
@dataclass
class ConfidenceConfig:
    enabled: bool = False
    aggregation: Literal["average", "min", "percentile_90"] = "average"
    min_acceptance: float = 0.40
    on_low: Literal["allow", "flag", "reject"] = "flag"
    treat_null_as_low: bool = False
    precision_decimals: int = 3
```

---

## Task 3: Add LLM Logprob Extraction

**File:** `somaAgent01/services/gateway/llm_router.py` (modify existing)

**Requirements:** REQ-CONF-001, REQ-CONF-003

### Acceptance Criteria
- [ ] When confidence.enabled, request logprobs=True from LLM provider
- [ ] Extract logprobs from OpenAI/Azure response format
- [ ] Standardize output into List[float] format
- [ ] Handle providers without logprob support (return None)
- [ ] Emit `llm_confidence_missing_total` metric when unavailable
- [ ] Pass logprobs to ConfidenceScorer for calculation
- [ ] Include confidence in assistant.final SSE event

### Implementation Notes
```python
# LiteLLM completion params:
# - logprobs=True (OpenAI, Azure)
# - top_logprobs=1

# Response extraction:
# response.choices[0].logprobs.content[i].logprob
```

---

## Task 4: Implement Threshold Enforcement

**File:** `somaAgent01/python/somaagent/confidence_scorer.py`

**Requirements:** REQ-CONF-005

### Acceptance Criteria
- [ ] Creates `ConfidenceResult` dataclass with confidence, action, flags
- [ ] Implements `evaluate_confidence(confidence, config)` function
- [ ] Handles null confidence based on treat_null_as_low setting
- [ ] Returns action: "allow", "flag", or "reject"
- [ ] Adds "LOW_CONFIDENCE" flag when on_low is "flag"
- [ ] Returns error code LOW_CONFIDENCE_REJECTED when on_low is "reject"

### Implementation Notes
```python
@dataclass
class ConfidenceResult:
    confidence: Optional[float]
    action: str  # "allow", "flag", "reject"
    flags: List[str]
```

---

## Task 5: Add Prometheus Metrics

**File:** `somaAgent01/python/somaagent/confidence_metrics.py`

**Requirements:** REQ-CONF-008

### Acceptance Criteria
- [ ] Creates `llm_confidence_histogram` with buckets 0.1-1.0
- [ ] Creates `llm_confidence_average` gauge
- [ ] Creates `llm_confidence_missing_total` counter
- [ ] Creates `llm_confidence_rejected_total` counter
- [ ] All metrics have labels: tenant, model, endpoint
- [ ] Integrates with existing observability/metrics.py

### Implementation Notes
```python
LLM_CONFIDENCE_HISTOGRAM = Histogram(
    "llm_confidence_histogram",
    "Distribution of LLM confidence scores",
    labelnames=("tenant", "model", "endpoint"),
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)
```

---

## Task 6: Update API Response Serialization

**File:** `somaAgent01/services/gateway/schemas.py` (modify existing)

**Requirements:** REQ-CONF-003, REQ-CONF-007

### Acceptance Criteria
- [ ] Adds optional `confidence: float | None` field to response schemas
- [ ] Includes confidence in `/a2a_chat`, `/delegate` responses
- [ ] For streaming, includes confidence only in final summary frame
- [ ] Omits confidence field when confidence.enabled is false
- [ ] Maintains backward compatibility (field is optional)
- [ ] Adds `flags` list to metadata for LOW_CONFIDENCE flag

---

## Task 7: Add OPA Integration

**File:** `somaAgent01/policy/confidence.rego`

**Requirements:** REQ-CONF-006

### Acceptance Criteria
- [ ] OPA input includes `input.confidence` as float or null
- [ ] OPA input includes `input.confidence_enabled` as boolean
- [ ] Creates example policy for confidence-based denial
- [ ] Updates OPA input builder to include confidence fields

### Implementation Notes
```rego
package somaagent.confidence

default allow = true

deny[msg] {
    input.confidence_enabled
    input.confidence != null
    input.confidence < 0.3
    msg := sprintf("Confidence %v below minimum threshold 0.3", [input.confidence])
}
```

---

## Task 8: Update Event Persistence

**File:** `somaAgent01/services/common/event_store.py` (modify existing)

**Requirements:** REQ-CONF-004, REQ-CONF-010

### Acceptance Criteria
- [ ] Event payload includes `confidence` field (float or null)
- [ ] Does NOT persist raw token_logprobs or token lists
- [ ] Maintains backward compatibility (unknown fields ignored)
- [ ] Validates confidence range [0..1] before persisting

---

## Task 9: Unit Tests

**Files:**
- `somaAgent01/tests/unit/test_confidence_scorer.py`
- `somaAgent01/tests/unit/test_confidence_config.py`

**Requirements:** REQ-CONF-009

### Acceptance Criteria
- [ ] Tests calculate_confidence with valid logprobs
- [ ] Tests calculate_confidence with empty list (returns None)
- [ ] Tests calculate_confidence with all NaN values (returns None)
- [ ] Tests all 3 aggregation modes: average, min, percentile_90
- [ ] Tests evaluate_confidence threshold enforcement
- [ ] Tests ConfidenceConfig.from_env() loading
- [ ] Tests edge cases: single value, negative logprobs

### Test Cases
```python
# test_confidence_scorer.py
def test_calculate_confidence_average_mode():
    logprobs = [-0.5, -0.3, -0.2]
    result = calculate_confidence(logprobs, "average")
    assert 0.0 <= result <= 1.0

def test_calculate_confidence_empty_returns_none():
    assert calculate_confidence([]) is None
    assert calculate_confidence(None) is None

def test_calculate_confidence_min_mode():
    logprobs = [-0.5, -0.3, -0.2]
    result = calculate_confidence(logprobs, "min")
    # min should be <= average
    avg = calculate_confidence(logprobs, "average")
    assert result <= avg
```

---

## Task 10: Property Tests

**File:** `somaAgent01/tests/property/test_confidence_properties.py`

**Requirements:** REQ-CONF-002

### Acceptance Criteria
- [ ]* **Property 1: Confidence Range Compliance**
  - *For any* computed confidence value, result is in [0.0, 1.0] or None
  - **Validates: Requirement 2.6**

- [ ]* **Property 2: Confidence Calculation Idempotence**
  - *For any* logprobs list and aggregation mode, calling twice produces identical results
  - **Validates: Requirement 2.1**

- [ ]* **Property 3: Empty Input Returns None**
  - *For any* empty or all-invalid logprobs list, returns None
  - **Validates: Requirement 2.2**

- [ ]* **Property 4: Aggregation Mode Ordering**
  - *For any* logprobs with variance, min ≤ average
  - **Validates: Requirements 2.3, 2.4**

### Implementation Notes
```python
from hypothesis import given, strategies as st

@given(st.lists(st.floats(min_value=-10, max_value=0, allow_nan=False)))
def test_confidence_range_compliance(logprobs):
    result = calculate_confidence(logprobs)
    if result is not None:
        assert 0.0 <= result <= 1.0
```

---

## Task 11: Integration Tests

**File:** `somaAgent01/tests/integration/test_confidence_flow.py`

**Requirements:** REQ-CONF-003, REQ-CONF-004

### Acceptance Criteria
- [ ] Tests full flow: LLM call → logprob extraction → confidence calculation
- [ ] Tests confidence in SSE events
- [ ] Tests confidence in event persistence
- [ ] Tests OPA policy with confidence input
- [ ] Tests threshold enforcement with real config

### Prerequisites
- Real infrastructure (PostgreSQL, Redis, LLM provider)
- `docker compose --profile core up -d`

---

## Task 12: Documentation

**File:** `somaAgent01/docs/confidence.md`

**Requirements:** All

### Acceptance Criteria
- [ ] Architecture overview with diagram
- [ ] Configuration reference (all env vars)
- [ ] API response examples
- [ ] OPA policy examples
- [ ] Metrics reference
- [ ] Troubleshooting guide

---

## Implementation Order

```
Week 1:
├── T1: Confidence Calculator (foundation)
├── T2: Confidence Configuration
├── T4: Threshold Enforcement
└── T5: Prometheus Metrics

Week 2:
├── T3: LLM Logprob Extraction
├── T6: API Response Serialization
├── T7: OPA Integration
└── T8: Event Persistence

Week 3:
├── T9: Unit Tests
├── T10: Property Tests
├── T11: Integration Tests
└── T12: Documentation
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Unit tests passing (≥80% coverage)
- [ ] Property tests passing
- [ ] Integration tests passing
- [ ] No VIBE violations (no mocks, no placeholders, no TODOs)
- [ ] Prometheus metrics exposed
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Feature flag working (CONFIDENCE_ENABLED)

---

## Notes

- Tasks marked with `*` are property-based tests
- All tests use real infrastructure per VIBE Coding Rules
- Confidence feature is additive only (no breaking changes)
- Default: disabled (opt-in via CONFIDENCE_ENABLED=true)

