# Design Document

## Introduction

This document specifies the technical design for implementing the Confidence Score Extension in SomaStack. The design covers the confidence calculator, LLM wrapper modifications, API response serialization, event persistence, OPA integration, and observability.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SomaAgent01                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Request Flow                                 │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │    │
│  │  │ API Gateway     │  │ LLM Wrapper     │  │ Confidence          │  │    │
│  │  │ (serializer)    │──│ (logprobs req)  │──│ Calculator          │  │    │
│  │  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘  │    │
│  │           │                    │                      │              │    │
│  │           ▼                    ▼                      ▼              │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │    │
│  │  │ OPA Policy      │  │ Event Store     │  │ Metrics/Logs        │  │    │
│  │  │ (input.conf)    │  │ (persist conf)  │  │ (histograms)        │  │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM Provider                                    │
│                    (OpenAI/Anthropic/LiteLLM)                               │
│                    Returns: text + token_logprobs                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Design Details

### Component 1: Confidence Calculator Module

**Relevant Requirements:** REQ-2, REQ-9

**File:** `somaAgent01/python/helpers/confidence.py`

```python
from __future__ import annotations

import math
from typing import List, Optional

from src.core.config import cfg


def calculate_confidence(
    logprobs: Optional[List[float]],
    aggregation: str = "average",
    precision: int = 3,
) -> Optional[float]:
    """Calculate normalized confidence score from token logprobs.

    Args:
        logprobs: List of token log-probabilities (natural log)
        aggregation: Aggregation mode - "average", "min", or "percentile_90"
        precision: Decimal precision for rounding (default 3)

    Returns:
        Confidence score in [0.0, 1.0] or None if logprobs unavailable
    """
    if not logprobs:
        return None

    # Filter invalid entries (NaN, None)
    valid = [lp for lp in logprobs if lp is not None and not math.isnan(lp)]
    if not valid:
        return None

    # Aggregate based on mode
    if aggregation == "min":
        m = min(valid)
    elif aggregation == "percentile_90":
        # 10th percentile (lower tail, more conservative)
        sorted_lp = sorted(valid)
        idx = max(0, int(len(sorted_lp) * 0.1))
        m = sorted_lp[idx]
    else:  # default: average
        m = sum(valid) / len(valid)

    # Normalize: exp(m) clamped to [0, 1]
    confidence = max(0.0, min(1.0, math.exp(m)))

    # Round for transport
    return round(confidence, precision)
```

### Component 2: Confidence Configuration

**Relevant Requirements:** REQ-5, REQ-11

**File:** `somaAgent01/src/core/config/confidence_config.py`

```python
from dataclasses import dataclass
from typing import Literal, Optional

from src.core.config import cfg


@dataclass
class ConfidenceConfig:
    """Configuration for confidence score feature."""

    enabled: bool = False
    aggregation: Literal["average", "min", "percentile_90"] = "average"
    min_acceptance: float = 0.40
    on_low: Literal["allow", "flag", "reject"] = "flag"
    treat_null_as_low: bool = False
    precision_decimals: int = 3

    @classmethod
    def from_env(cls) -> "ConfidenceConfig":
        """Load configuration from environment variables."""
        return cls(
            enabled=cfg.flag("CONFIDENCE_ENABLED", False),
            aggregation=cfg.env("CONFIDENCE_AGGREGATION", "average") or "average",
            min_acceptance=float(cfg.env("CONFIDENCE_MIN_ACCEPTANCE", "0.40") or "0.40"),
            on_low=cfg.env("CONFIDENCE_ON_LOW", "flag") or "flag",
            treat_null_as_low=cfg.flag("CONFIDENCE_TREAT_NULL_AS_LOW", False),
            precision_decimals=int(cfg.env("CONFIDENCE_PRECISION_DECIMALS", "3") or "3"),
        )


# Singleton instance
_config: Optional[ConfidenceConfig] = None


def get_confidence_config() -> ConfidenceConfig:
    """Get confidence configuration singleton."""
    global _config
    if _config is None:
        _config = ConfidenceConfig.from_env()
    return _config
```

### Component 3: LLM Wrapper Modifications

**Relevant Requirements:** REQ-1, REQ-8

**File:** Modify existing LLM wrapper (e.g., `python/helpers/llm.py` or LiteLLM integration)

The LLM wrapper must:
1. Check `confidence.enabled` before requesting logprobs
2. Pass `logprobs=True` (or provider-specific parameter) to the LLM call
3. Extract and standardize logprobs from response
4. Emit `llm_confidence_missing_total` metric when unavailable

```python
async def generate_with_confidence(
    prompt: str,
    model: str,
    **kwargs,
) -> tuple[str, Optional[List[float]]]:
    """Generate text with optional logprobs for confidence calculation.

    Returns:
        Tuple of (generated_text, token_logprobs or None)
    """
    config = get_confidence_config()

    # Request logprobs if confidence enabled
    if config.enabled:
        kwargs["logprobs"] = True

    response = await llm_call(prompt, model, **kwargs)

    # Extract logprobs from response (provider-specific)
    logprobs = None
    if config.enabled:
        logprobs = extract_logprobs(response)
        if logprobs is None:
            LLM_CONFIDENCE_MISSING.labels(
                tenant=kwargs.get("tenant_id", "default"),
                model=model,
                endpoint=kwargs.get("endpoint", "unknown"),
            ).inc()

    return response.text, logprobs
```

### Component 4: Response Serialization

**Relevant Requirements:** REQ-3, REQ-7

**API Response Schema (Non-Streaming):**

```json
{
  "response": "...",
  "confidence": 0.87,
  "metadata": {
    "request_id": "...",
    "tenant_id": "...",
    "model": "...",
    "flags": []
  }
}
```

**Error Response (Reject Mode):**

```json
{
  "error": {
    "code": "LOW_CONFIDENCE_REJECTED",
    "message": "Response rejected due to low confidence.",
    "details": {
      "confidence": 0.31,
      "min_acceptance": 0.40
    }
  },
  "metadata": {
    "request_id": "...",
    "tenant_id": "..."
  }
}
```

### Component 5: Threshold Enforcement

**Relevant Requirements:** REQ-5

```python
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class ConfidenceResult:
    """Result of confidence evaluation."""

    confidence: Optional[float]
    action: str  # "allow", "flag", "reject"
    flags: List[str]


def evaluate_confidence(
    confidence: Optional[float],
    config: ConfidenceConfig,
) -> ConfidenceResult:
    """Evaluate confidence against thresholds.

    Args:
        confidence: Computed confidence score or None
        config: Confidence configuration

    Returns:
        ConfidenceResult with action and flags
    """
    flags: List[str] = []

    # Handle null confidence
    if confidence is None:
        if config.treat_null_as_low:
            return ConfidenceResult(
                confidence=None,
                action=config.on_low,
                flags=["LOW_CONFIDENCE"] if config.on_low == "flag" else [],
            )
        return ConfidenceResult(confidence=None, action="allow", flags=[])

    # Check threshold
    if confidence < config.min_acceptance:
        if config.on_low == "flag":
            flags.append("LOW_CONFIDENCE")
        return ConfidenceResult(
            confidence=confidence,
            action=config.on_low,
            flags=flags,
        )

    return ConfidenceResult(confidence=confidence, action="allow", flags=[])
```

### Component 6: OPA Integration

**Relevant Requirements:** REQ-6

OPA input structure:

```json
{
  "confidence": 0.87,
  "confidence_enabled": true,
  "request_id": "uuid",
  "tenant_id": "tenant-123",
  "endpoint": "/a2a_chat",
  "model": "gpt-4",
  "user": "..."
}
```

Example OPA policy:

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

### Component 7: Event Persistence

**Relevant Requirements:** REQ-4, REQ-10

Event payload structure:

```json
{
  "event_type": "LLM_RESPONSE",
  "timestamp": "2025-12-16T12:00:00Z",
  "tenant_id": "tenant-123",
  "request_id": "uuid",
  "model": "gpt-4",
  "payload": {
    "response": "...",
    "confidence": 0.87
  }
}
```

**Prohibited fields:** `token_logprobs`, `tokens`, per-token probabilities.

### Component 8: Observability

**Relevant Requirements:** REQ-8

**Prometheus Metrics:**

```python
from observability.metrics import Counter, Histogram, Gauge

LLM_CONFIDENCE_HISTOGRAM = Histogram(
    "llm_confidence_histogram",
    "Distribution of LLM confidence scores",
    labelnames=("tenant", "model", "endpoint"),
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

LLM_CONFIDENCE_AVERAGE = Gauge(
    "llm_confidence_average",
    "Rolling average of LLM confidence scores",
    labelnames=("tenant", "model", "endpoint"),
)

LLM_CONFIDENCE_MISSING = Counter(
    "llm_confidence_missing_total",
    "Count of requests where logprobs were unavailable",
    labelnames=("tenant", "model", "endpoint"),
)

LLM_CONFIDENCE_REJECTED = Counter(
    "llm_confidence_rejected_total",
    "Count of requests rejected due to low confidence",
    labelnames=("tenant", "model", "endpoint"),
)
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system.*

### Property 1: Confidence Range Compliance

*For any* computed confidence value, the result SHALL be in the range [0.0, 1.0] or None.

**Validates: Requirements 2.6**

### Property 2: Confidence Calculation Idempotence

*For any* list of logprobs and aggregation mode, calling `calculate_confidence` twice with the same inputs SHALL produce identical results.

**Validates: Requirements 2.1**

### Property 3: Empty Input Returns None

*For any* empty or all-invalid logprobs list, `calculate_confidence` SHALL return None.

**Validates: Requirements 2.2**

### Property 4: Aggregation Mode Ordering

*For any* list of logprobs with variance, `min` aggregation SHALL produce a result ≤ `average` aggregation.

**Validates: Requirements 2.3, 2.4**

### Property 5: Threshold Enforcement Consistency

*For any* confidence value below `min_acceptance`, the system SHALL apply the configured `on_low` action consistently.

**Validates: Requirements 5.5, 5.6**

### Property 6: No Logprob Leakage

*For any* event persisted or log emitted, raw token logprobs SHALL NOT be present.

**Validates: Requirements 4.2, 10.1**

---

## Data Flow Diagrams

### Confidence Calculation Flow

```
┌─────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ LLM Wrapper │     │ Confidence          │     │ Response        │
│             │     │ Calculator          │     │ Serializer      │
└──────┬──────┘     └──────────┬──────────┘     └────────┬────────┘
       │                       │                         │
       │ generate(logprobs=T)  │                         │
       │──────────────────────>│                         │
       │                       │                         │
       │ text + logprobs       │                         │
       │<──────────────────────│                         │
       │                       │                         │
       │                       │ calculate_confidence()  │
       │                       │──────────────────────>  │
       │                       │                         │
       │                       │ confidence: 0.87        │
       │                       │<──────────────────────  │
       │                       │                         │
       │                       │ evaluate_confidence()   │
       │                       │──────────────────────>  │
       │                       │                         │
       │                       │ action: allow/flag/rej  │
       │                       │<──────────────────────  │
       │                       │                         │
       │                       │ serialize_response()    │
       │                       │──────────────────────>  │
       │                       │                         │
       │                       │ {response, confidence}  │
       │                       │<──────────────────────  │
```

---

## Security Considerations

1. **No Raw Logprob Storage**: Only the scalar confidence is persisted; raw logprobs are discarded after calculation.

2. **Logging Sanitization**: Confidence is validated to [0..1] before logging; no string interpolation.

3. **RBAC**: Confidence metrics access restricted to admin/operator roles.

4. **Input Validation**: Logprobs are validated for NaN/None before processing.

---

## Testing Strategy

1. **Unit Tests**: Test `calculate_confidence` with various inputs, edge cases, aggregation modes
2. **Property Tests**: Hypothesis-based tests for range compliance, idempotence, ordering
3. **Integration Tests**: End-to-end tests with real LLM calls (when available)
4. **Contract Tests**: Validate API response schema includes confidence field
5. **Load Tests**: Verify overhead ≤5ms at 10k RPS

**NO MOCKS** - All tests use real infrastructure per VIBE Coding Rules.

---

## Dependencies

- `math`: Standard library for exp/log calculations
- `prometheus_client`: Metrics (existing via observability.metrics)
- `structlog`: Structured logging (existing)

No new dependencies required.
