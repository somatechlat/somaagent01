# Eventing & Streaming Standards

## Topics & Naming
- Prefix by domain and bounded context: `somastack.<domain>.<entity>[.<suffix>]`.
  - Examples: `somastack.delegation`, `memory.wal`, `ui.notifications`, `somastack.config.updates`.
- Dead-letter: `<topic>.dlq` with same keying.

## Schemas
- Versioned JSON Schemas stored under `schemas/<domain>/...vN.schema.json`.
- Payload must include:
  - `type`: stable string code (e.g., `ui.notification`).
  - `ts`: producer timestamp ISO-8601 (optional, consumers may add).
  - `trace.trace_id` and `trace.span_id` (redundant to headers).
- Backward compatibility: only additive changes in same version; breaking change ⇒ bump version & topic suffix `.v2` or embed `schema_version`.

## Headers
- Required: `traceparent` (W3C), optional `tracestate`.
- Compatibility: also include `trace_id` and `span_id` for systems without W3C parsing.
- Optional multi-tenancy: `tenant` header when applicable.

## Keys & Ordering
- Use a deterministic key to preserve per-entity ordering:
  - Delegation: `task_id`.
  - Memory WAL: `session_id` or `persona_id`.
  - Notifications: `tenant_id`.

## Consumer Groups
- One group per service role (e.g., `delegation-worker`, `memory-replicator`).
- Scale horizontally by increasing partitions and replicas within same group.

## Backpressure & Retries
- Consumers must handle transient failures with bounded retries and DLQ on exceed.
- Use exponential backoff with jitter for reprocessing.
- Producers should use outbox pattern (already present) for reliability.

## Observability
- Start a PRODUCER span for publish and a CONSUMER span for handle.
- Propagate `traceparent` header; mirror into payload `trace` for logs.
- Metrics:
  - `events_published_total{topic}`
  - `events_consumed_total{topic}`
  - `event_handle_latency_seconds{topic}`
  - `dlq_total{topic}`

## Governance
- PR checklist for new topics:
  1. Schema file added + docs.
  2. Sample payloads provided.
  3. Key selection rationale.
  4. Backward & forward compatibility notes.

## Testing
- Unit: schema validate and header presence.
- Integration: round-trip publish/consume with traced context in a test kafka (or mocked bus).
