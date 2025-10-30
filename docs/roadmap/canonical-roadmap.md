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
- SomaBrain reachable at `http://host.docker.internal:9696` via `SOMA_BASE_URL` (Compose).

Centralized configuration and tools:
- Gateway hosts a central Tool Catalog and runtime config. It provides:
	- A single registry of tools, schemas, and per-tenant enable flags and execution profiles (timeouts, concurrency, resource limits).
	- A UI-safe runtime config projection (`/v1/runtime-config`) and a public tool list (`/v1/tools`) without secrets.
	- Distribution to services via ETag/TTL-cached internal endpoints. Services fail closed if the catalog is unavailable (strict mode).
	- Provider secrets centralized in Gateway; services invoke providers through Gateway, not with raw keys.

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

Attachment ingestion contract:
- All ingestion paths use `attachment_id` (no filesystem paths). A service-only fetch streams content from Gateway (policy-enforced; tenant-scoped).
- The `document_ingest` tool accepts `{ attachment_id, tenant_id, content_type?, size_bytes? }` and returns `{ text, metadata }` with extraction details.
- Large files use external object storage via signed URLs (optional), with metadata retained in Postgres.

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

Strict-mode defaults:
- Fail-closed policies in dev and prod: when a dependency or authorization check fails, the system surfaces a clear error to the UI and audit log; no silent fallbacks.
- Dev mirrors prod posture (no mocks); warnings and health banners appear in UI when components degrade.

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

## Web UI Integration (Agent Zero behavior)

Goal: adopt Agent Zero’s proven Web UI interaction model while preserving our architecture and contracts. No mocks, no inline fallbacks; UI must operate against real services via Gateway only.

What to copy/adapt from Agent Zero UI:
- Chat transport: strictly SSE for streaming via `/v1/session/{session_id}/events` with event types `llm.delta`, `llm.complete`, `tool.call`, `tool.result`, `error`, `heartbeat`.
- Message send: POST `/v1/session/message` with `{ message, session_id?, persona_id?, attachments? }`; UI must not poll legacy endpoints; it awaits SSE for responses.
- Attachments: uploads via POST `/v1/uploads` returning descriptors `{ id, sha256, content_type, size_bytes, url }`; messages reference `attachments: [{ id }]` (no filesystem paths).
- Session management: list/history/delete/reset through Gateway routes; delete chat removes session history and closes streams.
- Tools: request via POST `/v1/tool/request`; UI shows tool call and result events inline, matching the SSE contract.
- Profiles and runtime config: UI fetches `/v1/tools` and `/v1/runtime-config` for model profiles, allowed tools, limits, and flags; secrets never exposed.

What we will not keep:
- Any legacy UI polling or proxy fallbacks.
- Any inline dialogue fallback in Gateway; replies must originate from Conversation Worker and real LLM providers.

Acceptance criteria for UI integration:
- Sending a message from the UI produces streamed assistant deltas over SSE within p50 < 1s under local dev.
- Uploading a file yields an attachment_id; subsequent message referencing it triggers tool ingestion and assistant usage of extracted text.
- Deleting a chat closes the current SSE stream and removes history; a new chat starts clean.
- UI reflects Tool Catalog enable/disable and execution profile limits within configured TTL.

## Rollout Plan and Milestones

Phase 0 — Correctness and Strictness
- Align SomaBrain port to 9696 across code/docs/compose; health checks green when SomaBrain is up.
- Enable strict-mode defaults (fail-closed on policy/dependency failures) and surface banners in UI; remove legacy fallbacks.

Phase 0.5 — Agent Zero Web UI Integration and Real Chat (priority)
- Integrate Agent Zero UI into `webui/` with adapters to our `/v1` endpoints.
- Remove any UI-side polling or file path usage; wire SSE, uploads, and session controls.
- Remove Gateway inline dialogue fallback; require Conversation Worker running and real provider credentials.
- Playwright parity smoke: chat send/stream, upload+tool, delete chat.

Phase 1 — Attachment Ingestion by ID
- Add internal service fetch endpoint for attachments by ID and migrate Worker and `document_ingest` to `attachment_id` contracts.
- Update UI previews/downloads to route via Gateway `/v1/attachments/{id}` and eliminate filesystem path references.

Phase 2 — Central Tool Catalog and Runtime Config
- Implement Tool Catalog in Gateway (schemas, execution profiles, per-tenant flags, egress allowlists) with ETag/TTL distribution to services.
- Centralize provider secrets at Gateway; Workers invoke providers via Gateway.

Phase 3 — Memory Guarantees and Policy
- Strengthen outbox/WAL/idempotency; expose WAL/outbox lag in health; chaos-test recovery.
- OPA gates for conversation.send, tool.execute, memory.write; precise user-visible denies and audit.

Phase 4 — Large Files and External Storage
- Add S3/MinIO storage for large attachments with signed URL fetch; Gateway AV/quarantine and TTL janitor.

Phase 5 — E2E and CI
- Playwright suite for chat streaming, uploads, tool flows, delete chat, policy denies; wire to CI.
- Add docs/versioned schemas; publish acceptance checks per sprint.

## Concrete Next Steps (Backlog)

1) Update docker-compose and docs to `SOMA_BASE_URL=http://host.docker.internal:9696`; add a test to enforce alignment.
2) Implement internal attachment fetch-by-ID and migrate Worker and `document_ingest` to use it; adjust UI previews.
3) Add Tool Catalog tables/APIs in Gateway and service-side ETag/TTL fetch with fail-closed behavior.
4) Enforce OPA gates across conversation/tool/memory flows with clear deny errors and audits; expose WAL lag in health.
5) Add Playwright smoke covering uploads/streaming/tool-call and delete chat; wire to CI.
6) Add structured logging and schema validation (JSONSchema in `schemas/`) on key envelopes.
7) Integrate Agent Zero UI and adapters; remove Gateway inline dialogue fallback; ensure SSE-only streaming path; document required env vars for real LLM.
8) Verify conversation history continuity: existing sessions render in UI; SSE resumes on refresh; delete/reset behave correctly.

## References (in-repo)

- Services: `services/gateway/main.py`, `services/conversation_worker/main.py`, `services/tool_executor/main.py`, `services/memory_*/*`, `services/ui*/main.py`.
- Client: `python/integrations/soma_client.py`.
- Docs: `docs/technical-manual/architecture.md`, `docs/technical-manual/tools-messages-memories.md`.

This roadmap is canonical. Proposed changes should be added here first, then implemented with tests and observability.
