# Observability Playbook

## Metrics

- **Prometheus** collects component metrics. Access via `http://localhost:<PROMETHEUS_PORT>`.
- Exporters:
  - Gateway: request latency, error count, circuit-breaker stats.
  - Kafka: broker health, partition ISR, consumer lag.
  - Postgres: connection pool, slow queries (enable pg exporter).
  - Redis: memory usage, hits/misses.

### Key Dashboards

| Dashboard | Metrics |
| --- | --- |
| Gateway Overview | RPS, latency percentiles, error codes |
| Realtime Speech | Session success rate, negotiation latency |
| Tool Executor | Queue depth, execution duration |
| Infrastructure | CPU/memory per container, disk usage |

## Logging

- Docker stdout/stderr aggregated with `docker logs`.
- For advanced setups, forward to Loki or ELK. Structure logs as JSON for easier parsing.
- Retain logs for at least 30 days in production.

## Tracing

- Enable OpenTelemetry by setting `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Instrument Gateway routes and Tool Executor tasks.

## Alerting

| Alert | Condition | Action |
| --- | --- | --- |
| High Gateway latency | p95 > 3s for 5 min | Investigate LLM provider, Redis | 
| Tool queue backlog | `somastack.tools` lag > 500 | Scale executors or inspect stuck jobs |
| Realtime session failures | Error rate > 10% | Check API key, network |
| Kafka ISR shrink | < partitions replicating | Restart broker |

## Log Triage

1. `docker logs -f somaAgent01_gateway`
2. Filter by correlation ID (from UI debug panel).
3. For tool issues, inspect executor logs.

## Synthetic Monitoring

- Schedule periodic `/healthz` checks.
- Run automated chat scenario (via CI agent) two times per hour to validate end-to-end.

## Incident Response

- Document incidents in `docs/operations/incidents/YYYY-MM-DD.md`.
- Include timeline, root cause, remediation, follow-up tasks.

## Capacity Planning

- Track CPU/memory for Gateway and Tool Executor under load tests.
- Scale Kafka partitions when throughput > 10k messages/minute.

## Instrumentation TODOs

- Add Prometheus metrics for `/realtime_session` success/failure counts.
- Implement structured logging in Tool Executor with correlation IDs.
- Wire tracing for memory fetch/save operations.
