---
title: SomaBrain Memory Plane
slug: memory-plane
version: 1.0.0
last-reviewed: 2025-10-24
audience: platform-engineers, SREs
---

# SomaBrain Memory Plane

A single, authoritative memory backend backed by SomaBrain HTTP. Legacy SKM and the gRPC memory service are removed. All memory writes flow via SomaBrain with a durable write-ahead log (WAL) and replication to Postgres for query/ops.

## Data flow

- Producers: conversation_worker, tool_executor, and optionally gateway write-through.
- Policy: OPA "memory.write" pre-check in workers; gateway enforces OPA only when auth required.
- Primary write: SomaBrainClient HTTP remember/remember_batch with:
  - idempotency_key
  - metadata including tenant, agent_profile_id, universe_id, persona_id
  - attachments[]
- WAL: gateway/workers emit a memory.wal event with payload and write result metadata.
- Replication: memory_replicator consumes memory.wal and persists to Postgres replica table; idempotent on event_id.
- DLQ: replication errors publish to Kafka DLQ and persist to Postgres dlq_messages; gateway offers admin list/purge/reprocess.

## Headers and metadata

Ingress headers applied by gateway:
- X-Agent-Profile -> metadata.agent_profile_id
- X-Universe-Id -> metadata.universe_id (fallback SOMA_NAMESPACE)
- X-Persona-Id -> overrides persona_id when body omits it

The gateway also merges auth-derived metadata (tenant, subject, issuer, scope) when JWT auth is enabled.

## Idempotency

Idempotency key format: stable hash over id, type, role, session_id, persona_id, content, attachments, and metadata timestamps. The Postgres replica enforces ON CONFLICT(event_id) DO NOTHING with a unique index to ensure idempotent inserts.

## Feature flags (env)

- GATEWAY_WRITE_THROUGH=true|false
- GATEWAY_WRITE_THROUGH_ASYNC=true|false (default false in tests; true recommended in prod)
- SOMA_BASE_URL=http(s)://…
- SOMA_TLS_CA, SOMA_TLS_CERT, SOMA_TLS_KEY (optional mTLS)
- MEMORY_WAL_TOPIC=memory.wal

## Services

- gateway: thin ingress/router, optional write-through, DLQ admin, health aggregation.
- conversation_worker: persists user/assistant events via SomaBrain; emits WAL.
- tool_executor: persists tool outputs via SomaBrain; emits WAL.
- memory_replicator: consumes WAL, writes Postgres replica, DLQ on error.
- outbox_sync: durable publisher; health-aware batch/interval via SomaBrain /health probe.

## Health and observability

- Gateway /v1/health and /healthz aggregate: Postgres, Redis, Kafka, somabrain_http, memory_replicator lag, memory_dlq depth.
- Metrics (Prometheus):
  - gateway_write_through_attempts_total, gateway_write_through_results_total, gateway_write_through_wal_results_total
  - memory_replicator_events_total, memory_replicator_replication_seconds, memory_replicator_lag_seconds
  - outbox_sync_publish_total, somabrain_health_state, outbox_sync_effective_batch_size
  - client-side: SomaBrain client request metrics (HTTP status/latency)
- Tracing: OpenTelemetry with OTLP exporter; disable in tests with OTEL_EXPORTER_OTLP_DISABLED=true

## Alerts (suggested thresholds)

See Reference > Observability & Alerts for full rule examples. Highlights:
- Replication lag > 60s for 5m -> warn; > 300s -> critical
- DLQ depth > 0 sustained 10m -> warn; > 100 -> critical
- Gateway write-through errors rate > 5% over 10m -> warn; > 20% -> critical
- Outbox publish retries increasing with failures -> investigate Kafka

## Deployment notes

docker-compose.yaml includes memory_replicator and outbox_sync. Set SOMA_BASE_URL to your SomaBrain endpoint. In prod, enable GATEWAY_REQUIRE_AUTH and configure JWT/OPA as appropriate. For high throughput, enable GATEWAY_WRITE_THROUGH_ASYNC.
