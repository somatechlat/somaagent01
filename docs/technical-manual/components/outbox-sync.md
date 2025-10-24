# Outbox Sync Worker

Resilient, health-aware publishing from Postgres to Kafka using a transactional outbox.

## Overview

- Write-path enqueues JSON payloads into `message_outbox` when Kafka is degraded or to guarantee durability.
- A background worker (`services/outbox_sync/main.py`) continuously claims pending rows, publishes to Kafka, and marks them `sent`.
- Retries use capped exponential backoff with deduplication via an optional `dedupe_key`.

## Table schema

- `topic TEXT` – Kafka topic to publish to
- `payload JSONB` – full JSON event; trace context is injected at publish-time
- `headers JSONB` – reserved for future use
- `status TEXT` – `pending | sending | sent | failed`
- `retry_count INT`, `next_attempt_at TIMESTAMPTZ`
- `dedupe_key TEXT` – unique when not null
- `session_id TEXT`, `tenant TEXT` – provenance hints

The schema and trigger are created automatically by `ensure_schema()`.

## Worker behavior

- Batch claim using `FOR UPDATE SKIP LOCKED`
- Publish via `KafkaEventBus.publish(topic, payload)`
- On success: `sent`
- On failure: `pending` with `retry_count += 1` and `next_attempt_at = now + backoff`
- After `OUTBOX_SYNC_MAX_RETRIES`, mark `failed`

## Configuration

- `OUTBOX_SYNC_BATCH_SIZE` (default 100)
- `OUTBOX_SYNC_INTERVAL_SECONDS` (default 0.5)
- `OUTBOX_SYNC_MAX_RETRIES` (default 8)
- `OUTBOX_SYNC_BACKOFF_BASE_SECONDS` (default 1.0)
- `OUTBOX_SYNC_BACKOFF_MAX_SECONDS` (default 60.0)
- Metrics: Prometheus on `OUTBOX_SYNC_METRICS_PORT` (default 9469)

## Integration notes

- Use `OutboxStore.enqueue()` in write paths as a fallback when `KafkaEventBus.healthcheck()` fails or as a standard durable write.
- For idempotency, set a stable `dedupe_key` (e.g., event ID); enqueues with the same key are no-ops.
- The worker is safe to run with multiple replicas.