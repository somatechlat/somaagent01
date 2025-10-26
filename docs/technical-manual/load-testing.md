# Load & Soak Testing (Wave C)

This document describes how to run a lightweight load/soak test against the Gateway using the repository's built-in harness.

- Harness script: `scripts/load/soak_gateway.py`
- Dependencies: uses `httpx` only (already in `requirements.txt`). No Locust needed.
- Purpose: exercise the `/v1/session/message` write path under load, while observing metrics:
  - gateway_write_through_* counters (if GATEWAY_WRITE_THROUGH=true)
  - memory_replicator_* metrics (if WAL + replicator are running)
  - gateway_dlq_depth gauge stays near zero (steady state)

## Quick start

1. Ensure the Gateway is running locally (e.g., `make stack-up` or your compose profile) and reachable at `http://127.0.0.1:8010`.
2. Run a smoke test:

```bash
make load-smoke
```

It will send ~5 requests/second for 15 seconds, printing a JSON summary (count, ok/err, p50/p95/p99).

## Configurable soak

Use `make load-soak` and override environment variables to control parameters:

- TARGET_URL: base URL for gateway (default `http://127.0.0.1:8010`)
- PATH: request path (default `/v1/session/message`)
- RPS: target requests per second (float; default `5`)
- DURATION: test duration seconds (default `30`)
- CONCURRENCY: max in-flight requests (default `20`)
- JWT: optional bearer token (for `GATEWAY_REQUIRE_AUTH=true`)
- TENANT: optional tenant string to include in metadata
- PERSONA_ID: optional persona id to include
- MESSAGE: request message (default `"ping"`)

Example:

```bash
TARGET_URL=http://127.0.0.1:8010 RPS=25 DURATION=120 CONCURRENCY=50 make load-soak
```

## Observability checklist

While the load is running, confirm:

- Gateway metrics endpoint exposes counters/gauges incrementing as expected (Prometheus scrape).
- If write-through is enabled:
  - `gateway_write_through_attempts_total{path="/v1/session/message"}` increases.
  - `gateway_write_through_results_total{result="ok"}` dominates; error labels stay low.
  - `gateway_write_through_wal_results_total{result="ok"}` increments; errors stay near zero.
- Replicator metrics show bounded lag (if WAL is enabled and replicator is running).
- DLQ remains empty (depth near zero) in steady state.

## SLO targets (baseline)

These are starting points; tune based on environment scale:

- Error rate: < 0.5% during sustained load.
- p95 latency for `/v1/session/message`: < 300ms in dev/local; < 150ms in staging for baseline throughput.
- WAL→replica lag: ≤ 2s steady state under baseline load; temporary spikes acceptable during bursts but must recover.

## Tips

- To test the full write path, set `GATEWAY_WRITE_THROUGH=true` and start Kafka/Postgres/Replicator.
- To isolate Gateway overhead, leave write-through disabled; the harness still exercises validation and enqueue with Outbox fallback.
- Increase `CONCURRENCY` when the client becomes a bottleneck (HTTP-level backpressure).

## Next steps

- Integrate these metrics with your external dashboards (Voyant) and define recording rules for latency quantiles, error rates, and lag maxima.
- Extend the harness to cover export and admin endpoints if needed.
