## Sprint Roadmap — Execution Plan

This sprint roadmap breaks the canonical roadmap into concrete, time-boxed sprints with clear scope, deliverables, and tests. Each sprint completes with PASS/FAIL gates and visible artifacts.

Conventions:
- Definition of Done (DoD): code merged, docs updated, tests passing (unit+integration), CI green, and dashboards updated if applicable.
- Acceptance: explicit checks listed per sprint; failing any check means the sprint goal is not met.

### Sprint 0 — Correctness and Strictness (1 week)
Scope:
- Align SomaBrain base URL to 9696 everywhere; fix docs and compose.
- Enable strict-mode defaults: fail-closed on policy/dependency failures; remove legacy fallbacks.

Deliverables:
- docker-compose.yaml updated to `SOMA_BASE_URL=http://host.docker.internal:9696`.
- Gateway health and UI banner logic for degraded dependencies.
- Canonical roadmap updated (this doc and canonical).

Acceptance tests:
- tests/docs/test_port_alignment.py: asserts 9696 in compose/docs.
- Manual: Gateway /health shows `somabrain_http=up` when SomaBrain at 9696.

Exit criteria:
- All acceptance tests green; feature flags documented; no references to 9999 remain.

### Sprint 1A — Agent Zero Web UI Integration and Real Chat (priority, 1 week)
Scope:
- Integrate Agent Zero Web UI into `webui/` and adapt all network calls to our Gateway `/v1` endpoints.
- Remove any UI polling or filesystem path usage; rely on SSE for streaming and `/v1/uploads` for attachments.
- Remove Gateway inline dialogue fallback; require Conversation Worker and real provider credentials.
- Ensure existing sessions render and new messages stream end-to-end via Kafka and Worker.

Deliverables:
- UI: chat send via POST `/v1/session/message`, SSE wired to `/v1/session/{session_id}/events`, uploads wired to `/v1/uploads` returning `attachment_id`.
- Session list/history/delete/reset routes integrated; delete closes SSE and clears history.
- Gateway: inline dialogue block removed; strict fail-closed errors surface to UI with user-friendly copy.

Acceptance tests:
- tests/playwright/test_ui_chat_stream.py: send → observe `llm.delta` then `llm.complete` over SSE; no polling.
- tests/playwright/test_ui_upload_and_tool.py: upload → message with attachment → tool call and result displayed.
- tests/playwright/test_ui_delete_chat.py: delete chat closes stream and clears messages; new chat works.

Exit criteria:
- Streaming chat works end-to-end with real LLM credentials (OpenAI-compatible provider); no dev fallback paths.
- UI has no references to legacy polling endpoints or filesystem paths.

### Sprint 1 — Attachment Ingestion by ID (1–2 weeks)
Scope:
- Add internal service fetch of attachments by ID; migrate Worker and `document_ingest` tool to `attachment_id` contract.
- Update UI previews/downloads to route only via `/v1/attachments/{id}`.

Deliverables:
- New internal endpoint: GET `/internal/attachments/{id}/binary` (authZ, tenant-scoped, policy enforced) or reuse existing with service auth.
- Worker inline/offload ingestion logic uses attachment_id; document_ingest accepts `{ attachment_id, tenant_id, ... }`.
- UI code no longer references filesystem paths like `/git/agent-zero/tmp/uploads/*`.

Acceptance tests:
- tests/e2e/test_document_ingest_by_id.py: upload → attach → tool offload → assistant uses extracted text; memory WAL contains `attachment_text` record.
- tests/webui/test_attachment_preview_routes.py (Playwright or integration): preview/download via Gateway only.

Exit criteria:
- All acceptance tests green; a 10MB PDF successfully ingests by ID locally; no FS path leakage in UI.

### Sprint 2 — Tool Catalog and Runtime Config (2 weeks)
Scope:
- Implement Tool Catalog (schemas, per-tenant enable, execution profiles, egress allowlists) in Gateway.
- Service-side ETag/TTL config pull; fail closed if missing/stale beyond max-age.
- Centralize provider secrets in Gateway for LLM invocations.

Deliverables:
- Postgres tables: tools, tool_versions, tenant_overrides, execution_profiles, egress_allowlists.
- Admin APIs: `/v1/admin/tools`, `/v1/admin/tools/{name}/tenants/{tenantId}`.
- Runtime APIs: `/v1/tools`, `/v1/runtime-config`, `/internal/tool-catalog` (ETag).

Acceptance tests:
- tests/integration/test_tool_catalog_toggle.py: disable tool → UI/tool list updates → execution denied with audit.
- tests/integration/test_execution_profile_timeout.py: timeout change reflected in Tool Executor within TTL.

Exit criteria:
- UI shows only enabled tools; Tool Executor enforces configured limits; secrets never exposed to services.

### Sprint 3 — Memory Guarantees and Policy (1–2 weeks)
Scope:
- Strengthen outbox/WAL/idempotency; WAL lag surfaced in health and UI banner.
- OPA gates for conversation.send, tool.execute, memory.write with clear user errors and audit entries.

Deliverables:
- Health: WAL/outbox lag metrics and thresholds.
- Policy deny surfaces in Gateway and Worker with error payloads.

Acceptance tests:
- tests/e2e/test_wal_durability_chaos.py: simulate SomaBrain outage; outbox grows and drains; no message loss; timelines consistent.
- tests/integration/test_policy_denies.py: OPA deny returns clear error; audit record captured.

Exit criteria:
- Chaos test reliable on local dev; deny paths user-visible and audited; dashboards include WAL lag.

### Sprint 4 — Large Files and External Storage (2 weeks)
Scope:
- Optional S3/MinIO backing for large attachments; signed URL fetch; AV/quarantine; TTL janitor.

Deliverables:
- Gateway integration to generate signed URLs and store metadata in Postgres; document_ingest fetch via signed GET.

Acceptance tests:
- tests/e2e/test_large_uploads_external_storage.py: 200MB PDF → upload → ingest summarized; policy/AV enforced.

Exit criteria:
- Large-file path stable and documented; default remains Postgres BYTEA for small files.

### Sprint 5 — E2E and CI (1 week)
Scope:
- Playwright suite for core flows; wire smoke to CI; produce artifacts.

Deliverables:
- Playwright specs for: chat send/stream, tool flow, uploads preview, delete chat, policy denies, SSE resilience.
- CI job: run smoke on PR, full suite nightly.

Acceptance tests:
- CI green for smoke; failing specs produce trace/screenshot artifacts.

Exit criteria:
- Contributors see clear, fast feedback on PRs; nightly E2E produces stable artifacts.

---

Tracking and Metrics per Sprint:
- Build: PASS/FAIL on typecheck and unit.
- Lint: PASS with zero new warnings in touched areas.
- Tests: unit+integration must pass; E2E smoke (when applicable).
- Observability: new metrics/spans visible in dev dashboards when relevant.

Review cadence: Demo and checkpoint at the end of each sprint; update this document and the canonical roadmap with any deltas.
