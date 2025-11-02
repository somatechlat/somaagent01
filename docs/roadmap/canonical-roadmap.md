<!-- Canonical roadmap for somaAgent01 — generated/updated 2025-10-30 by GitHub Copilot -->
# SomaAgent01 Canonical Roadmap (Canonical)

Last updated: 2025-10-30

This document is the canonical roadmap for the somaAgent01 project. It consolidates the project's vision, the implemented components, the gaps vs the canonical vision, and the prioritized tasks to reach parity with the Agent Zero UI and the canonical streaming transport.

Summary
- Vision: a developer-first, production-ready multi-service agent platform exposing a single, predictable Gateway surface for UI and integrators. The Gateway provides secure same-origin UI serving, cookie/session or header-token auth, SSE streaming for real-time message updates, uploads, tool invocation endpoints, and credential management. Workers (Conversation Worker, Tool Executor) are event-driven and consume/publish to the message backbone.
- Canonical transport: Server-Sent Events (SSE) via GET /v1/session/{id}/events from the Gateway. Polling is deprecated and only supported for legacy clients via an adapter layer. Websockets are optional as a later enhancement.

Core Components (current state)
- Gateway (edge API)
  - Responsibilities: HTTP surface for clients, session creation, message ingress, SSE streaming endpoint (/v1/session/{id}/events), upload endpoint, tool request endpoint, and credential endpoints.
  - State: Implemented. Health endpoint validated (local probe returned 200 during analysis).

- Conversation Worker
  - Responsibilities: consume conversation.inbound, orchestrate LLM calls, detect tools, emit tool.requests, write memory WALs to SomaBrain or memory store, publish session events.
  - State: Implemented and present.

- Tool Executor
  - Responsibilities: consume tool.requests, run tools in a sandbox, enforce policy (OPA), publish tool.results, and emit structured outputs for memory capture.
  - State: Implemented and present.

- Session Repository
  - Responsibilities: durable session event store (Postgres-backed), migration SQL present.
  - State: Implemented.

- LLM Credentials Store
  - Responsibilities: store LLM provider credentials (Redis + Fernet encryption) and supply them to Gateway/Workers.
  - State: Implemented; GATEWAY_ENC_KEY required by deployments.

- Web UI
  - `webui/` in-repo: modernized SSE-first UI that maps to the Gateway SSE contract.
  - `tmp/webui/` (Agent Zero copy): provided by user; used as UX reference. It contains some legacy polling code and vendor bundles.

Canonical Decisions
- Use Gateway SSE (/v1/session/{id}/events) as the single production transport.
- Serve the Web UI from the Gateway (same-origin) to preserve cookie/session semantics—do not run a standalone `run_ui.py` server in production.
- Provide small adapter endpoints for legacy/polling UI copies while migrating clients to SSE.
- Tool catalog lives in Postgres and is exposed via Gateway endpoints; tool invocation uses POST /v1/tool/request and emits results via SSE events tied to sessions.

Gaps vs Roadmap (prioritized)
1. Acceptance testing and API contract tests (HIGH)
   - Missing: automated Playwright smoke tests and API contract probes for: SSE subscribe & receive, message send (POST /v1/session/{id}/message), file upload round-trip, tool request -> tool result flow, and credential flows.
   - Action: add Playwright smoke tests, pytest API contract tests, and CI workflows to run them.

2. Optimized deploy manifest (HIGH)
   - Missing: `docker-compose.optimized.yaml` referenced by `deploy-optimized.sh` is absent.
   - Action: produce an optimized compose file (lean 7-container stack) or update the deploy script to use existing `docker-compose.yaml` with tuned profiles and resource limits.

3. Documentation references and stale scripts (MEDIUM)
   - Issues: `run_ui.py` is deprecated but referenced in Makefile, docs, .vscode/launch.json, and tests. `deploy-optimized.sh` references a missing compose manifest. `tmp/webui` is a redundant copy of the Agent Zero UI.
   - Action: archive or remove deprecated files and update references; update docs to point to Gateway serving for the UI.

4. UI parity tasks (MEDIUM)
   - Items: port progressive token rendering, tool-panel UX, upload-progress UI, reconnect/backoff for SSE, and UX polish from Agent Zero (error handling and offline UX).
   - Action: migrate selective components from `tmp/webui` into `webui/` and add Playwright tests for UX behaviors.

5. Adapter endpoints for legacy clients (LOW)
   - Action: small Gateway adapter layer to accept legacy poll shapes and transform them to canonical flows; mark deprecated and remove after clients migrate.

Acceptance Criteria (per feature)
- SSE streaming: UI subscribes to `GET /v1/session/{id}/events` and receives event types: session.open, message.chunk, message.complete, tool.requested, tool.result, memory.write, and session.close. SSE reconnects must resume from last event id where supported.
- Message send: `POST /v1/session/{id}/message` returns 202 with the session/event envelope; message appears via SSE within acceptable latency (configurable threshold, default 5s in dev).
- Tool invocation: `POST /v1/tool/request` accepts structured tool payloads, publishes to Kafka, Tool Executor consumes and emits `tool.result` events visible to the subscribing client via SSE.
- Uploads: client uploads to `POST /v1/uploads` which returns a resource URL; uploaded content must be available to workers for tool processing and memory ingestion.

Roadmap: Next 3 sprints (high level)
- Sprint 1 (2 weeks): API contract tests + CI; create `docker-compose.optimized.yaml` (or fix deploy script); archive deprecated files (`run_ui.py`, `tmp/webui`) and update docs; add basic Playwright smoke test for UI SSE subscribe health.
- Sprint 2 (2 weeks): Migrate key UX from `tmp/webui` into `webui/`: streaming token rendering, tool panel, upload progress. Add Playwright tests for UX flows. Implement small Gateway adapter for legacy poll endpoints (backwards compatibility) — mark deprecated.
- Sprint 3 (2 weeks): Harden deployments (resource tuning), add OPA policy verification in CI, end-to-end tests for tool executor and memory WAL capture, finalize removal of legacy adapters post migration.

Appendix: Quick API contract samples
- SSE subscribe
  - GET /v1/session/{id}/events
  - Events: id:<event-id>\n event:message.chunk\n data: {"session_id":"...","chunk":"...","cursor":42}\n
- Send message
  - POST /v1/session/{id}/message
  - Body: {"role":"user","content":"Hello"}
  - Response: 202 Accepted {"envelope_id":"...","status":"queued"}

- Tool request
  - POST /v1/tool/request
  - Body: {"session_id":"...","tool_id":"calculator","inputs":{...}}

Verification & Quality gates
- Build: ensure `docker-compose.yaml` and `Dockerfile` build locally. If an optimized compose is added, validate composition via `docker compose -f docker-compose.optimized.yaml ps`.
- Lint/Typecheck: run project linters and Python type checks if configured (e.g., mypy, flake8); add minimal pre-commit hooks if absent.
- Tests: run newly added Playwright smoke and pytest API contract tests in CI; pass locally in dev before merging.

Notes and assumptions
- Assumed that Gateway SSE contract is the single canonical streaming transport; websockets may be added later for higher-throughput clients.
- Assumed Postgres, Kafka, Redis are available in dev (docker compose). The deploy script references ports different from dev defaults; confirm during deploy manifest creation.
- All destructive repo edits should be performed on a backup branch; archival is preferred to immediate deletion.

If you accept this canonical roadmap I will also create the sprinted roadmap file with sprint-level tickets and specific test tasks.

---

Delta update — 2025-10-31

Scope: finalize Agent Zero Web UI parity using SSE-only transport, wire any remaining legacy UI actions to canonical /v1 endpoints, add import/export and nudge routes (done), and stop accidental “auto new chat” creation.

What changed today
- UI: SSE-only path enforced; unified renderer used for history and live events; session history loads before SSE to avoid races; default selection stabilized; restart UX corrected.
- UI actions wired to canonical endpoints: nudge (/v1/session/action), sessions import/export (POST /v1/sessions/import, POST /v1/sessions/export).
- Error surfacing: red toasts and offline/memory-degraded banners added; subpath (/ui) import-map fixed.
- Pending items converted into explicit tasks for the next sprint (see sprinted roadmap):
  - Stop auto new chat creation by making default selection idempotent and not creating provisional chats on empty list.
  - Add history/context-window endpoints under /v1 and rewire the UI modal buttons.
  - Add /v1/workdir/* endpoints and rewire the Files modal.
  - Expand Playwright parity tests (thinking/tool lifecycle, uploads progress, history/context/files) and stabilize timeouts.

Acceptance gates targeted
- Build: PASS
- Lint/Typecheck: PASS
- Tests: Gateway health, E2E tool flow, and UI smoke PASS; new Playwright parity specs to be added next.

Notes
- “No legacy” principle reaffirmed: any non-/v1 calls in the UI are considered regressions and must be migrated or disabled.


========================
Centralize Gateway / UI URLs (Immediate action)
========================

Decision (explicit)
- Canonical Gateway host port: 21016 (the UI must be reachable at http://localhost:21016/ui/index.html).
- Canonical environment variables (reuse existing names):
  - `GATEWAY_PORT` (numeric, default 21016)
  - `GATEWAY_BASE_URL` (full URL, e.g. http://localhost:21016)
  - `WEB_UI_BASE_URL` (UI entry, e.g. http://localhost:21016/ui)

Rationale
- Many tests, scripts and docs contained hard-coded values (21016, 20016, 8010, and literal http://127.0.0.1 URLs). This causes runtime confusion. The project already uses `GATEWAY_PORT` and `GATEWAY_BASE_URL` in places; we will standardize on them and prefer `WEB_UI_BASE_URL` for UI consumers.

Immediate plan (no new systems, minimal edits)
1. Ensure `.env` / `.env.example` contains the canonical variables (set `GATEWAY_PORT=21016`, `GATEWAY_BASE_URL=http://localhost:21016`, `WEB_UI_BASE_URL=http://localhost:21016/ui`).
2. Replace hard-coded URL fallbacks in tests, scripts, and webui test configs to prefer `WEB_UI_BASE_URL` → `GATEWAY_BASE_URL` → derived `http://localhost:${GATEWAY_PORT}`. Exact files to update include (representative):
   - `tests/e2e/*.py`, `tests/playwright/*.py`, `tests/ui/*`
   - `webui/playwright.config.ts` and `webui/tests/*.spec.ts`
   - `scripts/e2e_quick.py`, `scripts/ui-smoke.sh`, `scripts/check_stack.sh`
   - `python/api/*` modules that fallback to `http://localhost:20016` or `http://127.0.0.1:21016`
   - `.vscode/tasks.json` and Makefile examples
   - docs under `docs/*` and generated `site/*` that embed http://localhost:21016 or other literal ports
3. Archive (do not permanently delete without record) clearly broken / redundant artifacts that confuse developers:
   - `run_ui.py` (deprecated stub)
   - `tmp/webui/` (redundant Agent Zero UI copy)
   - `deploy-optimized.sh` (references missing compose file)
   Archive location: `archive/` at repo root, with timestamped names (e.g. `archive/run_ui-20251030.py`, `archive/tmp-webui-20251030.tar.gz`, `archive/deploy-optimized-20251030.sh`).
4. Verify by running the dev stack and smoke tests (see "Verification" below).

Safety & VIBE constraints
- No new configuration systems or helper files will be introduced. Edits reuse existing env variables and the repo's helpers.
- Files will be archived before removal so the operation is reversible.
- Changes will be committed directly to the working branch per your instruction (no extra branches), with a single clear commit and changelog.

Verification
- Bring up the dev stack (with `GATEWAY_PORT=21016`) and confirm:
  - The UI is reachable at `http://localhost:21016/ui/index.html`.
  - `curl -s http://localhost:21016/v1/health` returns 200 and expected JSON status.
  - Run `pytest -q tests/e2e/test_api_contract_smoke.py` — passes or at least successfully performs the POST and opens SSE.
  - Run the Playwright UI smoke `./scripts/ui-smoke.sh ${WEB_UI_BASE_URL}` to validate UI load and network behavior.

Post-conditions
- All literal host:port occurrences for Gateway/UI should be removed except in docs examples that explicitly show how to set the env variables (those will show variables not raw URLs).
- `archive/` will contain the moved/archived files for safe undo.

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
- `ui`: SPA served directly by Gateway; SSE streaming for chat updates.
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

- AuthN: session cookies or OIDC; browser calls use same-origin cookies or header/bearer tokens. No custom CSRF endpoint.
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
- Security tests: CORS, authZ policies, redaction; secrets not present in logs.
- CI gates: build, lint/typecheck, unit, integration, E2E (smoke) required; full E2E nightly.

## Web UI Integration (Canonical behavior)

Goal: ship a clean, SSE-only Web UI against canonical Gateway contracts. No mocks, no inline fallbacks; UI must operate against real services via Gateway only.

Canonical UI behaviors:
- Chat transport: strictly SSE for streaming via `/v1/session/{session_id}/events` with event types `llm.delta`, `llm.complete`, `tool.call`, `tool.result`, `error`, `heartbeat`.
- Message send: POST `/v1/session/message` with `{ message, session_id?, persona_id?, attachments? }`; UI must not poll legacy endpoints; it awaits SSE for responses.
- Attachments: uploads via POST `/v1/uploads` returning descriptors `{ id, sha256, content_type, size_bytes, url }`; messages reference `attachments: [{ id }]` (no filesystem paths).
- Session management: list/history/delete/reset through Gateway routes; delete chat removes session history and closes streams.
- Tools: request via POST `/v1/tool/request`; UI shows tool call and result events inline, matching the SSE contract.
- Profiles and runtime config: UI fetches `/v1/tools` and `/v1/runtime-config` for model profiles, allowed tools, limits, and flags; secrets never exposed.

Canonical endpoints and flows (summary)
- Chat send: POST `/v1/session/message` with `{ session_id, message, attachments? }`.
- File uploads: POST `/v1/uploads`, then reference returned `attachment_id` in the message.
- Streaming updates: subscribe to SSE `GET /v1/session/{session_id}/events`; render `llm.delta`, `llm.complete`, `tool.*`.
- Auth: same-origin cookies or header/bearer tokens (no CSRF endpoint).

Memory views
- Prefer read-only, SomaBrain-backed endpoints (list/search/delete under policy). Avoid UI polling; use manual refresh or SSE invalidations when available.

Knowledge import
- POST `/v1/uploads` then trigger a `document_ingest` tool call referencing `attachment_id`; show tool events in-stream.

Session controls
- `/v1/sessions/{id}/reset`, `/v1/sessions/{id}` DELETE, `/v1/sessions/import`, `/v1/sessions/export`, `/v1/sessions/{id}/pause`, `/v1/health`.

UI behavior requirements (copy exactly from A0, implemented via canonical endpoints)
- Progressive streaming token render with smooth autoscroll and speech synthesis hooks
- Attachments UX: drag/drop, multi-file upload, progress bar, preview; map to upload→attachment_id flow
- Session list and tasks switching preserved; selection persisted in localStorage; delete closes SSE and clears view
- Notifications and error handling: frontend toasts on fetch failures; backend disconnected banner; strict error copies
- Settings modal: memory dashboard, scheduler/tasks, tool visibility driven by `/v1/tools` and `/v1/runtime-config`

Enforcement
- SSE-only; no UI proxy or polling.
- No inline dialogue fallback in Gateway; replies originate from Conversation Worker and real providers.

Acceptance criteria for UI integration:
- Sending a message from the UI produces streamed assistant deltas over SSE within p50 < 1s under local dev.
- Uploading a file yields an attachment_id; subsequent message referencing it triggers tool ingestion and assistant usage of extracted text.
- Deleting a chat closes the current SSE stream and removes history; a new chat starts clean.
- UI reflects Tool Catalog enable/disable and execution profile limits within configured TTL.

NO LEGACY enforcement (applies to both UI and Gateway)
SSE-only and no-CSRF (ongoing checks)
- No UI polling; SSE subscribe + reconnect/backoff.
- No CSRF fetch endpoint; rely on same-origin cookies or header token.
- Single canonical SSE path in Gateway.
- No dashboard polling; prefer read-only backed endpoints and explicit refresh.

Test plan additions (Playwright + pytest)
- test_ui_chat_stream_sse: open SSE, send message, assert llm.delta then llm.complete; no polling
- test_ui_upload_ingest_tool: upload file(s), send message referencing attachments, assert `tool.call` and `tool.result` events and assistant utilization of extracted text
- test_ui_memory_dashboard_readonly: load subdirs, search memories, view detail, no polling; optional delete guarded by policy flag
- test_api_session_controls: reset/delete/export/import/nudge/pause endpoints round-trip without legacy routes
- test_no_legacy_network: assert no network calls to disallowed legacy endpoints.

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


## Centralize LLM model/profile management (priority)

Goal
- Make the Gateway the single source of truth for all model profiles, provider credentials, base_url normalization, and runtime model resolution. All services must invoke LLMs through the Gateway endpoints (`/v1/llm/invoke` and `/v1/llm/invoke/stream`) and must not propagate raw `base_url` values between services.

Why this is needed
- During audits we found model/profile information and base_url normalization logic duplicated across services (workers, Gateway, local config files). This causes validation errors (eg. "invalid model/base_url after normalization"), runtime surprises, and operational friction. Centralization reduces surface area for mistakes, makes credential management secure, and simplifies rollout of provider changes.

Design decisions (summary)
- Gateway owns: ModelProfileStore reads/writes, `_normalize_llm_base_url` rules, provider detection, and credential lookup. It exposes a CRUD API for profiles and a secure credentials endpoint. Workers send only role + messages + limited overrides (model name, temperature, kwargs) — they do not send `base_url`.
- Gateway exposes `/v1/model-profiles` (CRUD), `/v1/llm/credentials/{provider}` (internal credential access), and an admin `/v1/llm/test` to validate profile connectivity.
- Compatibility modes: `GATEWAY_MODEL_LOCK` config with values `off|warn|enforce` to aid migration: warn when workers send `base_url`, then block when enforce is set.

Acceptance criteria
- Worker->Gateway->Provider flow succeeds end-to-end: POST to Gateway invoke returns stream or non-stream content and the UI receives assistant events via SSE.
- No service outside Gateway performs normalization logic that changes `base_url` semantics.
- Gateway audit logs record provider and normalized base_url for every LLM invoke.

Migration strategy (high level)
1. Audit all usages of model/profile and `base_url` (scripts, conf, services). Document and back up existing profiles.
2. Implement Gateway CRUD/API and `GATEWAY_MODEL_LOCK=warn` to detect incoming `base_url` overrides and log warnings.
3. Update workers to stop sending `base_url` and to rely on Gateway resolution of model->provider->base_url.
4. Flip `GATEWAY_MODEL_LOCK=enforce` after canary testing and complete removal of duplicated config.

Risks & mitigations
- Risk: Missing credentials after migration. Mitigation: use `/v1/llm/test` and a migration script to copy secrets into Gateway store, validate, and only then enforce lock.
- Risk: Legacy clients sending `base_url`. Mitigation: `warn` mode that logs and surfaces in UI and builds a one-click migration map.

---

## 2025-10-31 Update — Real Endpoints Roadmap (Merged)

This addendum locks our single-surface Gateway API and the UI’s SSE-only behavior. It merges decisions we’ve implemented with the remaining work to reach full parity with the original Agent Zero Web UI while retaining the somaAgent01 architecture.

Feature → Endpoint map (authoritative)
- Chat ingress: `POST /v1/session/message`
- Session stream (SSE): `GET /v1/session/{session_id}/events`
- Recent timeline: `GET /v1/sessions/{session_id}/events`
- Uploads: `POST /v1/uploads`
- Attachments download: `GET /v1/attachments/{id}`
- Tools catalog/list: `GET /v1/tools`, `GET /v1/tool-catalog`, `PUT /v1/tool-catalog/{name}`
- Tool request enqueue: `POST /v1/tool/request`
- UI settings (sections): `GET|POST /v1/ui/settings/sections`
- Runtime config (UI boot hints): `GET /v1/runtime-config`, `GET /ui/config.json`
- Session helpers: `POST /v1/sessions/{id}/reset`, `POST /v1/sessions/{id}/pause`, `GET /v1/sessions/{id}/history`, `GET /v1/sessions/{id}/context-window`, `POST /v1/sessions/import`, `POST /v1/sessions/export`, `DELETE /v1/sessions/{id}`
- Workdir (developer UX): `GET /v1/workdir/list`, `POST /v1/workdir/upload`, `POST /v1/workdir/delete`, `GET /v1/workdir/download`
- Antivirus check: `GET /v1/av/test`

Transport and events (canonical)
- SSE-only. Event envelope matches “Outbound SSE Event Contract (sa01-v1)”.
- Event types: `assistant.thinking`, `assistant.stream`, `assistant.final`, `tool.start`, `tool.result`, `uploads.progress`.

Phased delivery (done vs remaining)
- Done: single Gateway surface; UI served under `/ui`; session durability; outbox + memory write outbox; settings sections + audit logging.
- Remaining (high→medium):
  - UI tool lifecycle de-duplication when `tool.start` lacks `request_id` but `tool.result` includes it
  - Uploads progress single-block per file and render “Uploaded:” when only a final “done” event arrives
  - Settings modal Alpine init race under automation; ensure modal opens reliably on first click
  - Provider credential presence hints to enable SSE assistant tests

Acceptance for this addendum
- No legacy UI calls appear (`/v1/ui/poll`, `/v1/csrf`)
- Uploading small files shows “Uploaded:” even without intermediate progress
- Tool start→result yields a single “Tool: <name>” block with result body
- Settings modal renders sections on first open in CI/local

---

## 2025-11-01 Update — Long-message stability, Thought-bubble parity, and Canonical Memory APIs

Scope
- Fix UI collapse/flip during very long assistant streams by adopting a streaming-safe renderer and CSS containment.
- Achieve visual/behavioral parity for thought bubbles (ephemeral thinking hint + final thoughts rows) with the 7001 demo.
- Canonicalize Memory Dashboard endpoints under `/v1/memories/*` and rewire the UI to them (remove reliance on legacy `/memory_dashboard`).

What changed (code)
- Web UI streaming safety:
  - During streaming, render assistant deltas without markdown/KaTeX (`response_stream` message type) and throttle DOM updates to ~30fps.
  - On final event, perform a single markdown+KaTeX render to replace the streaming content.
  - CSS containment and transition disabling applied to streaming message containers to prevent layout thrash.
- Thought bubble parity:
  - Ephemeral thinking bubble lifecycle tightened (show on thinking, clear on final/error/reset); visuals aligned to golden where possible.
  - “Show thoughts” toggle instantly affects `.msg-thoughts`; persistence remains under `/v1/ui/preferences`.
- Memory Dashboard APIs:
  - New canonical routes:
    - `GET /v1/memories/current-subdir`
    - `GET /v1/memories/subdirs`
    - `GET /v1/memories?memory_subdir=&q=&area=&limit=`
    - `DELETE /v1/memories/{id}`
    - `POST /v1/memories/bulk-delete` with `{ ids: number[] }`
    - `PATCH /v1/memories/{id}` with `{ edited: { content?, metadata? } }`
  - UI store (`memory-dashboard-store.js`) rewired to these endpoints.
  - Legacy `/memory_dashboard` kept as a compatibility shim; slated for removal post cutover.

Tests added
- Playwright: `thought.bubbles.and.toggles.spec.ts`
  - Sends a message, waits for assistant to finish (progress empty), clicks all `.kvps-row.msg-thoughts .kvps-val` rows if present, then flips Show thoughts/JSON/utils and performs best‑effort DOM visibility checks.

Acceptance criteria
- Long streaming replies do not cause UI collapse or flipping; progress bar remains coherent; no errors logged.
- Thought bubbles (ephemeral + final thoughts) match the golden UI’s look and timing; toggles flip visibility instantly and persist via preferences.
- Memory Dashboard uses `/v1/memories/*` endpoints in the UI; basic flows (list/search/delete/update) function; no UI polling.

Next sprints (focused)
- Sprint A (stability):
  - Finalize streaming renderer (metrics: frame times under load), add throttling guardrails and optional raf-based coalescing.
  - Extend Playwright with a “long message torture test” (markdown + code + LaTeX + images) and record video/trace.
- Sprint B (parity polish):
  - Copy exact bubble CSS from golden assets and unify styles; add structural assertions for bubble elements.
  - Expand toggles test to verify persistence across reload and themes.
- Sprint C (memory UX):
  - Add pagination/filter UX assertions; integrate optional delete policy checks; consider SSE-invalidations for live updates.

