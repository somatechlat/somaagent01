# Confidence Score System

## Overview

The Confidence Score system adds a normalized certainty metric (0.0-1.0) to every LLM-generated response. This enables policy gating, observability, and downstream behavior control based on model certainty.

## Architecture

```
LLM Response
     │
     ▼
┌─────────────────┐
│  LLM Adapter    │ ── Extract logprobs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ConfidenceScorer │ ── Calculate + Evaluate
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌────────┐
│Metrics│ │Response│
└───────┘ └────────┘
```

## Quick Start

### Enable Confidence Scoring

```bash
export CONFIDENCE_ENABLED=true
export CONFIDENCE_AGGREGATION=average
export CONFIDENCE_MIN_ACCEPTANCE=0.40
export CONFIDENCE_ON_LOW=flag
```

### Access in Response

```json
{
  "content": "...",
  "confidence": 0.872,
  "metadata": {
    "flags": []
  }
}
```

## Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONFIDENCE_ENABLED` | bool | `false` | Enable confidence scoring |
| `CONFIDENCE_AGGREGATION` | enum | `average` | `average`, `min`, `percentile_90` |
| `CONFIDENCE_MIN_ACCEPTANCE` | float | `0.40` | Minimum acceptable confidence |
| `CONFIDENCE_ON_LOW` | enum | `flag` | `allow`, `flag`, `reject` |
| `CONFIDENCE_TREAT_NULL_AS_LOW` | bool | `false` | Treat missing logprobs as low |
| `CONFIDENCE_PRECISION_DECIMALS` | int | `3` | Decimal places for rounding |

## Aggregation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `average` | Mean of token logprobs | Balanced view (default) |
| `min` | Minimum logprob | Most conservative |
| `percentile_90` | 10th percentile | Robust to outliers |

## Threshold Actions

| on_low | Behavior |
|--------|----------|
| `allow` | No action, response proceeds |
| `flag` | Adds `LOW_CONFIDENCE` flag to metadata |
| `reject` | Returns `LOW_CONFIDENCE_REJECTED` error |

## API Usage

### Basic Calculation

```python
from python.somaagent.confidence_scorer import ConfidenceScorer

scorer = ConfidenceScorer()
result = scorer.calculate(
    logprobs=[-0.5, -0.3, -0.2],
    provider="openai",
    model="gpt-4"
)
print(result.score)  # 0.716
```

### Threshold Evaluation

```python
is_ok, message = scorer.evaluate_result(result)
if not is_ok:
    print(f"Low confidence: {message}")
```

## Prometheus Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `llm_confidence_histogram` | Histogram | tenant, model, endpoint | Score distribution |
| `llm_confidence_average` | Gauge | tenant, model, endpoint | Current average |
| `llm_confidence_missing_total` | Counter | tenant, model, endpoint | Missing logprobs count |
| `llm_confidence_rejected_total` | Counter | tenant, model, endpoint | Rejection count |
| `llm_confidence_flagged_total` | Counter | tenant, model, endpoint | Flag count |

## OPA Policy Example

```rego
package somaagent.confidence

deny[msg] {
    input.confidence_enabled
    input.confidence != null
    input.confidence < 0.3
    msg := sprintf("Confidence %v below 0.3", [input.confidence])
}
```

## Troubleshooting

### No Confidence in Response

1. Check `CONFIDENCE_ENABLED=true`
2. Verify LLM provider supports logprobs
3. Check `llm_confidence_missing_total` metric

### All Responses Rejected

1. Lower `CONFIDENCE_MIN_ACCEPTANCE`
2. Change `CONFIDENCE_ON_LOW=flag` (warning only)
3. Check actual confidence distribution in histogram

### High Latency

1. Confidence calculation target: ≤5ms
2. Check `llm_confidence_calculation_latency_ms` in logs
3. Report if consistently >10ms

## Security

- Raw logprobs are **never** persisted (only final confidence)
- Confidence metrics require admin/operator role
- All events include `tenant_id` for isolation
