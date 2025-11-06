# Operational Alerts (Draft)

Recommended Prometheus alert rules to support new parity features.

## SSE & Streaming
- alert: HighSSEDisconnectRate
  expr: rate(gateway_sse_connections[5m]) < 0 and (gateway_sse_connections offset 5m) > 0
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "All SSE connections dropped to zero"
    description: "Previously active SSE connections have dropped to zero. Investigate gateway health or network issues."

- alert: SlowFirstToken
  expr: histogram_quantile(0.95, sum(rate(assistant_first_token_seconds_bucket[5m])) by (le)) > 5
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "First token latency >5s p95"
    description: "Increased model or network latency impacting UX."

- alert: ReasoningEventMissingFinal
  expr: sum(increase(gateway_reasoning_events_total{phase="started"}[15m])) > 0 and sum(increase(gateway_reasoning_events_total{phase="final"}[15m])) == 0
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Reasoning started without final markers"
    description: "Thinking start events observed but no matching final – possible aborted stream or provider stall."

- alert: ToolEventStartedWithoutFinal
  expr: sum(increase(gateway_tool_events_total{type="started"}[10m])) > 0 and sum(increase(gateway_tool_events_total{type="final"}[10m])) == 0
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Tool events started without completion"
    description: "Tool call initiation observed but no final marker – investigate tool execution subsystem."

## Errors & Classifier
- alert: StreamingErrorSpike
  expr: increase(gateway_llm_invoke_results_total{result="error"}[10m]) > 10
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Streaming errors spiking"
    description: "More than 10 streaming errors in 10 minutes. Check provider status."

## Rate Limiting
- alert: RateLimitBlockedSurge
  expr: increase(gateway_rate_limit_results_total{result="blocked"}[5m]) > 100
  for: 5m
  labels:
    severity: info
  annotations:
    summary: "Many requests are rate limited"
    description: "Validate client behavior or adjust limits."

## Masking
- alert: MaskRuleHitSpike
  expr: increase(mask_events_total[15m]) > 200
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High volume of masking events"
    description: "Potential credential leakage attempts or misconfigured clients."

> NOTE: `mask_events_total` needs to be added if masking metrics are promoted beyond current minimal implementation.
