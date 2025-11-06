# Sprint Roadmap

## Sprint 1 — Settings Centralization + Make The Agent Talk
- Goals:
	- Single-save Settings (`/v1/ui/settings/sections`) for every field, including External → API Keys.
	- Secrets masked on GET; encrypted at rest; no seeders or secondary POSTs.
	- Hot-apply overlays and service toggles; publish `config_updates`; workers reload.
	- Expand provider dropdowns (chat/util/browser) to show all providers with Groq default.
	- Agent can “talk” end-to-end: save → test → stream a reply.
- Tasks:
	- Accept all `api_key_*` in Gateway sections; persist encrypted; mask on GET.
	- Expand `conf/model_providers.yaml` chat providers (OpenAI, Groq, Azure, Mistral, DeepSeek, xAI, HuggingFace, LM Studio, Ollama, Other).
	- Ensure `settings.js` posts only sections; remove secondary credential POSTs; keep placeholders.
	- Hot-apply updated fields for chat/util/embed/browser, LiteLLM, uploads, AV, speech.
	- Add `/v1/llm/status` details into Settings “Status” panel (follow-up UI wiring).
- Acceptance:
	- Saving any field updates runtime without restart; secrets masked.
	- `/v1/llm/test` passes with valid key; UI chat streams assistant replies.

## Sprint 2 — Diagnostics, Aliases, and Provider Polish
- Goals:
	- Model alias registry (e.g., UI label “GPT‑OSS‑120B” → exact provider model).
	- Provider normalization guardrails (no OpenRouter special cases, sensible defaults).
	- Settings banners for missing keys/unreachable providers.
- Tasks:
	- Alias resolver in Gateway; pass-through by default.
	- Expand `/v1/llm/status` reachability and coercion flags.
	- UI: Add Status view and lightweight banners.
- Acceptance:
	- Aliases resolve in invoke/test; diagnostics show clear state/banners.

## Sprint 3 — Memory + Constitution
- Goals:
	- SomaBrain memory parity across conversation stages.
	- Constitution and Decisions tabs fully editable and hot-applied.
- Tasks:
	- Ensure memory recall toggles/thresholds are read dynamically by workers.
	- Wire Constitution endpoints and hot-apply.
- Acceptance:
	- Memory button shows relevant content; constitution edits reflected immediately.

## Sprint 4 — Observability & Tests
- Goals:
	- Robust metrics and admin probes; end-to-end tests.
- Tasks:
	- Metrics for `/v1/llm/test` by provider; SSE stability checks.
	- Playwright: Settings save → LLM test → stream → visual assertions.
- Acceptance:
	- CI passes; telemetry surfaces failures quickly; no secrets in logs.
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

### Sprint 0.5 — Strictness and No-Legacy Enablement (completed)
Scope:
- Enforced SSE-only; removed UI proxy/poll and bespoke CSRF paths. Added tests to assert no `/v1/ui/poll` or `/v1/csrf` calls.

Deliverables:
- UI free of polling and bespoke CSRF; SSE-only for streaming.
- Gateway exposes a single SSE route implementation.

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
- UI code no longer references filesystem paths like `/git/agent-zero/tmp/uploads/*`.

Acceptance tests:
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

---

## 2025-10-31 Sprint Addendum — Immediate Focus

Sprint A — UI Parity Polish (now)
- Fix tool lifecycle de-duplication: single “Tool: <name>” block even when `request_id` appears only on `tool.result`.
- Uploads progress: exactly one upload block per filename; show “Uploaded:” when only a final event is observed.
- Settings modal: ensure Alpine initialization so modal opens on first click in automation.
- Tests: extend Playwright specs to assert the above behaviors.

Sprint B — API Contract Tests + Docs
- Add pytest probes for: `/v1/session/message`, `/v1/session/{id}/events` (SSE), `/v1/uploads`, `/v1/tools`, `/v1/ui/settings/sections`.
- Document request/response examples in technical manual for each UI-used endpoint.

Sprint C — Credential UX + Model Test
- Settings: add provider key masking hints and a light-weight “Test model” (optional `/v1/llm/test`) wiring.
- Update runtime-config to surface provider availability for boot-time UX hints.

Sprint D — Memory + Observability
- Health: surface WAL/outbox lag with thresholds and banners; collect Prometheus metrics.
- Tests: chaos test to assert outbox/WAL resilience; Playwright checks for health banners without blocking chat.
