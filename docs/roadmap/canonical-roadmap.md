## Canonical Roadmap — Auditability, Observability, and Perfect Memory

This is the living, canonical roadmap for building SomaAgent01 into an auditable, observable, and traceable agentic platform with perfect message persistence and recall via SomaBrain. It is grounded in the current infrastructure and codebase.

### Vision and Non‑Negotiables

- Every interaction is auditable: we can answer who/what/when/why/how for any message, tool call, or LLM response.
- End-to-end traceability: a single trace follows a request across UI → Gateway → Workers → Providers → SomaBrain.
- Perfect memory: all user and assistant messages are durably persisted and available for high-quality recall in SomaBrain.
- Security by default: least privilege, encrypted by default, policy enforced (OPA/OpenFGA), and no plaintext secrets in logs.
- Production-grade reliability: idempotent processing, backpressure, retries with budgets, and SLOs with actionable alerts.

## System Overview (as-built)

Core services (verified under `services/`):
- `gateway`: FastAPI edge API handling UI, settings, uploads, LLM invoke (/v1/llm/invoke[/stream]), SSE/WS, and write-through to SomaBrain.
- `conversation_worker`: Consumes inbound chat events, orchestrates tools, streams responses via Gateway invoke, and writes memories.
- `tool_executor`: Executes registered tools deterministically; reports tool_call events.
- `ui` and `ui_proxy`: SPA hosting and proxying for local/dev; SSE streaming for chat updates.
- `memory_service`, `memory_replicator`, `memory_sync`, `outbox_sync`: Durable memory pipeline (WAL/outbox) and replica sync.
- `delegation_gateway`, `delegation_worker`: Delegated agent flows (if enabled).

Foundational infra:
- Kafka (event backbone), Redis (state/cache), Postgres (durable store), Vault/Env (secrets), OpenFGA (authz), OPA (policy), OpenTelemetry (traces/metrics/logs), Prometheus (metrics), Grafana/Tempo/Loki (observability).
- SomaBrain reachable at `http://host.docker.internal:9999` via `SOMA_BASE_URL` (Compose).

## Data and Event Contracts (canonical)

Identifiers and correlation:
- `request_id`: client-generated or edge-assigned; returned to client.
- `trace_id`/`span_id`: W3C Trace Context propagated via `traceparent` header and Kafka headers.
- `session_id`, `message_id`, `tool_call_id`, `memory_id`: UUIDv4; unique across services.
- `idempotency_key`: for POSTs that may be retried (e.g., message send), also carried in Kafka headers.

Canonical message envelope (Kafka and internal HTTP JSON):
- `meta`: { request_id, trace_id, idempotency_key, tenant_id, user_id, session_id, created_at }
- `payload`: one of `message.user`, `message.assistant`, `tool.call`, `tool.result`, `llm.request`, `llm.delta`, `llm.complete`, `memory.write`, `memory.recall`, `error`.
- `version`: schema version, starting at `v1`.

Persistence contract:
- All `message.user` and `message.assistant` events must be persisted in Postgres and written through to SomaBrain; outbox/WAL ensures durability and at-least-once delivery; consumers implement idempotency.
- Attachments are referenced by stable URIs: `/v1/attachments/{id}`; metadata saved with content hash and MIME.

SSE/WS streaming contract:
- Streamed events carry `event` and `data` fields; `data` includes `meta` fields above.
- Event types: `llm.delta`, `llm.complete`, `tool.call`, `tool.result`, `error`, `heartbeat`.

## Traceability and Observability

OpenTelemetry propagation and spans:
- Ingress: generate/accept `request_id` and `traceparent`; start `gateway.receive` span.
- Gateway → Worker: include `traceparent`, `request_id`, `idempotency_key` in Kafka headers.
- Worker → Gateway Invoke → Provider: propagate `traceparent`; spans: `worker.handle_message`, `gateway.llm.invoke`, `provider.api.call`.
- Memory write-through: `memory.write` span encloses Postgres insert, WAL publish, SomaBrain HTTP call.

Metrics (Prometheus):
- QPS/latency/error for: `/v1/session/message`, `/v1/llm/invoke`, tool executions, memory writes and recalls.
- Budgets: retry counts, DLQ depth, outbox lag, replica lag.
- Cost: token usage by provider/model; per-tenant caps.

Logs:
- Structured JSON with `level`, `timestamp`, `message`, `request_id`, `trace_id`, `session_id`, `user_id`, `tenant_id`.
- No secrets, no PII beyond stable IDs; redact payloads as needed (configurable).

## Security Model

- AuthN: session cookies or OIDC; CSRF enforced for browser calls.
- AuthZ: OpenFGA for resource relations; OPA for policy gates (e.g., tool allowlist, PII egress checks).
- Secrets: provider API keys stored centrally; never logged; access via internal credentials endpoint with internal token.
- Transport: HTTPS/TLS; internal mTLS optional; WAF headers and strict CORS for UI.
- Data protection: PII minimization, column-level encryption for sensitive fields, backup/restore tested.

## SomaBrain Integration (Perfect Memory and Recall)

- Write-through path: Worker persists messages locally and calls SomaBrain over `SOMA_BASE_URL` with retries and idempotency.
- Outbox/WAL: if SomaBrain temporarily unavailable, retry with exponential backoff; replicas reconcile via `memory_replicator`.
- Recall: Provide `recall(query|ids|context_window)` call surfaces in Gateway; Worker may fetch recall context pre-LLM invoke.
- Feedback: Store user feedback signals (helpful/not helpful/tag) and send to SomaBrain for learning.

Acceptance criteria:
- 100% of messages are persisted locally and visible in SomaBrain within SLA (p50 1s, p95 5s) under normal conditions.
- Recall returns deterministic slices tied to `session_id` or semantic query with stable relevance signals.
- End-to-end traces for any message include spans across all hops and appear in Tempo/Jaeger.

## Auditing and Compliance

- Immutable audit log: append-only audit events (`who`, `what`, `when`, `why`, `how`) stored in Postgres and replicated to cold storage.
- Change management: settings POST creates audit entries; diffs recorded (with secret masking).
- Export: admin endpoint to export audit traces for a `request_id`/`session_id`.

## Testing and CI/CD

- Unit: schema validation for envelopes; idempotency tests; provider credential fetch tests.
- Integration: write-through tests (Gateway ↔ Worker ↔ SomaBrain); tool orchestration; SSE stream integrity.
- E2E/Playwright: console/network-clean smoke; chat send/stream; tool flow; memory proof (health-gated for replica lag).
- Security tests: CSRF, CORS, authZ policies, redaction; secrets not present in logs.
- CI gates: build, lint/typecheck, unit, integration, E2E (smoke) required; full E2E nightly.

## Rollout Plan and Milestones

Phase 0 — Hardening (now)
- Enforce provider credential validation on settings POST; single-model semantics; normalize base URLs.
- Centralize LLM invocations in Gateway with internal token; Worker shim for legacy tests.
- Standardize uploads and SSE/WS streaming; fix SPA routing/assets.

Phase 1 — Traceability and Audit
- Propagate `traceparent` across HTTP and Kafka; include `request_id`, `idempotency_key` headers; add span naming across services.
- Implement audit event sink and admin export; mask secrets in settings diffs.

Phase 2 — Memory Guarantees
- Strengthen outbox idempotency keys and dedupe; DLQ with replay tooling; replica lag health gates.
- Add recall surfaces and pre-invoke enrichment flow; feedback capture pipeline.

Phase 3 — Security and Policy
- Wire OpenFGA checks around sessions/tools; OPA policies for PII/tool egress; add mTLS option.
- Column-level encryption for sensitive fields; backup/restore drills.

Phase 4 — SLOs and Cost
- Define SLOs: availability, latency, memory write p95, recall p95; alerts and on-call runbooks.
- Token/cost budgets per tenant; rate limits and backpressure.

## Concrete Next Steps (Backlog)

1) Add/verify W3C trace context propagation in Gateway, Workers, and HTTP clients; include Kafka header propagation.
2) Introduce `audit_event` table and producer; add audit on settings changes, tool execution, and message send.
3) Extend `python/integrations/soma_client.py` with explicit idempotency header and improved retries; expose recall endpoint in Gateway.
4) Implement `recall` pre-invoke enrichment step in `conversation_worker` controlled by feature flag.
5) Add Playwright strict network/console checks to CI; E2E memory proof with health gating.
6) Add structured logging fields everywhere; ensure secrets redaction.
7) Define and publish message envelope JSONSchema under `schemas/` with versioning and validation.

## References (in-repo)

- Services: `services/gateway/main.py`, `services/conversation_worker/main.py`, `services/tool_executor/main.py`, `services/memory_*/*`, `services/ui*/main.py`.
- Client: `python/integrations/soma_client.py`.
- Docs: `docs/technical-manual/architecture.md`, `docs/technical-manual/tools-messages-memories.md`.

This roadmap is canonical. Proposed changes should be added here first, then implemented with tests and observability.
