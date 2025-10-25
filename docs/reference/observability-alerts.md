---
title: Observability & Alerts
slug: observability-alerts
version: 1.0.0
last-reviewed: 2025-10-24
---

# Observability & Alerts

Below are sample Prometheus alert rules to monitor the memory plane and related services. Tune thresholds for your SLOs.

## Memory Replicator

```yaml
groups:
- name: memory-plane
  rules:
  - alert: MemoryReplicationLagHigh
    expr: memory_replicator_lag_seconds > 60
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Memory replication lag high"
      description: "Lag is {{ $value }}s (>60s) for 5m. Investigate memory_replicator and Kafka backlog."

  - alert: MemoryReplicationLagCritical
    expr: memory_replicator_lag_seconds > 300
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Memory replication lag critical"
      description: "Lag is {{ $value }}s (>300s) for 5m. WAL not applying."

  - alert: MemoryDLQNotEmpty
    expr: gateway_dlq_depth > 0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Memory DLQ accumulating"
      description: "DLQ depth increasing for 10m. Check DLQ admin endpoints."
```

## Gateway write-through

```yaml
- name: gateway
  rules:
  - alert: GatewayWriteThroughErrors
    expr: rate(gateway_write_through_results_total{result=~"exception|server_error|client_error"}[10m])
          /
          rate(gateway_write_through_attempts_total[10m]) > 0.05
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Gateway write-through error rate >5%"
      description: "High error rate on SomaBrain write-through."
```

## Outbox sync

```yaml
- name: outbox
  rules:
  - alert: OutboxPublishFailures
    expr: rate(outbox_sync_publish_total{result=~"failed|retry"}[10m]) > 0
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Outbox publish failures"
      description: "Outbox experiencing retries/failures. Check Kafka connectivity."

  - alert: SomaBrainDown
    expr: somabrain_health_state{state="down"} == 1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "SomaBrain health DOWN"
      description: "SomaBrain /health probe failing from outbox_sync."
```

## Notes

- Expose metrics ports (gateway, replicator, outbox_sync) to your Prometheus.
- Adjust label selectors to your environment (namespace/job).
- Consider adding SLO-based alerts for latency and throughput per tenant.
