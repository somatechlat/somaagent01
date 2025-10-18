---
title: Monitoring & Health
---

# Monitoring & Health

## Metrics

- Prometheus collects component metrics.
- Exporters:
  - Gateway: request latency, error count, circuit-breaker stats.
  - Kafka: broker health, partition ISR, consumer lag.
  - Postgres: connection pool, slow queries (pg exporter).
  - Redis: memory usage, hits/misses.

### Key Dashboards

| Dashboard | Metrics |
| --- | --- |
| Gateway Overview | RPS, latency percentiles, error codes |
| Tool Executor | Queue depth, execution duration |
| Infrastructure | CPU/memory per container, disk usage |

## Logging

- Docker stdout/stderr aggregated with `docker logs`.
- For advanced setups, forward to Loki/ELK. Use JSON logs.

## Tracing

- Enable OpenTelemetry via `OTEL_EXPORTER_OTLP_ENDPOINT`.
- Instrument Gateway routes and Tool Executor tasks.

## Alerting

| Alert | Condition | Action |
| --- | --- | --- |
| High Gateway latency | p95 > 3s for 5 min | Investigate provider, Redis |
| Tool queue backlog | `tool.requests` lag > 500 | Scale executors or inspect stuck jobs |
| Kafka ISR shrink | < partitions replicating | Restart broker |

## Synthetic Monitoring

- Schedule periodic `/v1/health` checks.
- Run automated chat scenario periodically to validate end-to-end.

## Incident Response

- Document incidents in `docs/operations/incidents/YYYY-MM-DD.md`.
- Include timeline, root cause, remediation, follow-ups.
