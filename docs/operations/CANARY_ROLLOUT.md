# Canary Rollout Plan (Gateway Parity Features)

## Phases
- Enable in dev with flags (masking, classifier, sequence, token metrics)
- Run golden trace compare for fixed prompts; update snapshots when intentional changes occur
- Soak test via k6 to baseline latency/throughput
- Canary enable in staging (5-10% of sessions) by environment flags
- Monitor dashboards and alerts for 24-48h; rollback flags on regressions

## Flags
- `SA01_ENABLE_CONTENT_MASKING` (default: false)
- `SA01_ENABLE_ERROR_CLASSIFIER` (default: false)
- `SA01_ENABLE_SEQUENCE` (default: true)
- `SA01_ENABLE_TOKEN_METRICS` (default: true)
- `SA01_ENABLE_REASONING_STREAM` (reserved)
- `SA01_ENABLE_TOOL_EVENTS` (reserved)

## KPIs
- First token latency p95 (`assistant_first_token_seconds`)
- SSE disconnects/connection count
- Rate limited requests/minute and ratio
- Error classification mix (timeout vs upstream vs internal)

## Rollback
- Flip flags to previous values
- Clear Redis sequence keys (`session:*:seq`) if needed (harmless otherwise)
- Re-run golden trace to confirm restoration

## Notes
- Masking rules should be versioned; test against known secret patterns before enabling
- Keep metrics server disabled during unit tests; enable in staging/prod for alerting
