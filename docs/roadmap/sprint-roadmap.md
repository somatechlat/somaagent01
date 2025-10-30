## Sprint Roadmap — Execution Plan

This sprint roadmap breaks the canonical roadmap into concrete, time-boxed sprints with clear scope, deliverables, and tests. Each sprint completes with PASS/FAIL gates and visible artifacts.

Conventions:
- Definition of Done (DoD): code merged, docs updated, tests passing (unit+integration), CI green, and dashboards updated if applicable.
- Acceptance: explicit checks listed per sprint; failing any check means the sprint goal is not met.

### Sprint 0 — Priority 0: Live Chat (SSE) E2E (1 week)
Goal:
- Restore end-to-end chatting via the LLM and the full agent infra using the canonical SSE path.

Scope:
- Verify and harden the minimum chat path: POST `/v1/session/message` → Kafka/Worker → SSE `GET /v1/session/{id}/events`.
- Ensure uploads → attachment_id round-trip and chat with attachments works minimally.
- Ensure health surfaces dependency states; UI shows banners but allows sending when overall health is not fully down.

Deliverables:
- Functional SSE chat path observed locally; assistant events visible over SSE.
- UI uses `/v1/session/message`, `/v1/uploads`, and opens SSE for the current session.
- E2E quick script and UI smoke pass in dev; document how to set provider credentials.

Acceptance tests:
- Task: E2E Quick (SSE) — passes and prints an assistant event.
- Task: UI Smoke (Playwright) — loads UI and basic flows without console errors.
- Optional: If provider credentials are present, assistant emits non-error content; else a clear error message appears over SSE (still acceptable for S0).

Exit criteria:
- A send operation produces an assistant SSE event in local dev.
- Basic upload+send works without 5xx.

### Sprint 0.5 — Strictness and No-Legacy Enablement (0.5–1 week)
Scope:
- Disable legacy UI polling (`/v1/ui/poll`) code paths and remove custom CSRF fetch logic in the UI; keep same-origin or header auth.
- Remove duplicate SSE route registrations and inline dialogue fallbacks in Gateway.
- Keep behavior identical for users; add Playwright test to assert no `/poll`/`memory_dashboard` calls; UI must not fetch `/csrf_token`.

Deliverables:
- UI free of polling and bespoke CSRF; SSE-only for streaming.
- Gateway has a single SSE route implementation.

Acceptance tests:
- tests/webui/test_no_legacy_network.spec.ts: asserts no calls to legacy endpoints during chat flows.

Exit criteria:
- All SSE tests green; no legacy network calls observed in Playwright traces.

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
