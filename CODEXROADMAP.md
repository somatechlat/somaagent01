# CODEXROADMAP (Canonical)

Purpose: Production‑grade, centralized roadmap to make this stack behave and look IDENTICAL to the golden agent at http://localhost:7001 while meeting enterprise reliability, security, and operability standards. This is the single source of truth for scope, acceptance, and phased delivery.

## Objectives (Single‑Control‑Plane)
- Centralize behavior in Gateway (APIs, events, settings, credentials).
- Stream everything via SSE; UI renders by role/type; toggles are pure CSS.
- Durable backbone (Kafka + Postgres outbox) and policy (OIDC/OPA/OpenFGA).
- Pixel/behavior parity with golden through tokens + snapshots + Playwright.

## Core Architecture (Real Infra)
- Gateway (FastAPI)
  - Chat enqueue `/v1/session/message`, uploads `/v1/uploads`, attachments, tools `/v1/tools`.
  - UI settings `/v1/ui/settings/*` (JSONB in Postgres) + model profile CRUD; LLM credentials in Redis (Fernet‑encrypted).
  - UI/Utility events `/v1/ui/event` and `/v1/util/event` → Kafka → SSE.
  - SSE `/v1/session/{id}/events` streams conversation.outbound.
  - DurablePublisher with bounded timeouts → Postgres outbox fallback.
  - Security: OIDC/JWT cookies, OPA checks, OpenFGA for tenancy.
- Streams/Stores: Kafka topics (conversation.inbound/outbound, tool.requests/results, memory.wal), Postgres (sessions/ui_settings/attachments/outbox/audit), Redis (session cache + encrypted credentials).
- Workers: Conversation Worker (invokes Gateway LLM), Tool Executor (executes tools), Replicators/Sync (WAL/outbox).

## Event Contract (Uniform)
- Keys: `event_id`, `session_id`, `role` (assistant|user|tool|util|system), `type` (dot names), `message`, `metadata`.
- UI maps role/type → renderer; toggles: `.msg-thoughts`, `.message-util`, `.msg-json` control visibility.

## Reliability & Scale
- Outbox on publish failure; outbox-sync replays. DLQs with requeue.
- SSE connection health; graceful shutdowns; token throttling (~30fps).
- SLOs: p95 enqueue <150ms; SSE reconnect <1s; stable streaming.

## Security & Policy
- OIDC/JWT cookies: Secure, SameSite=None; HTTPS only; CSRF assessed.
- OPA policies for settings/tool‑catalog; OpenFGA tenancy.
- Secrets: Redis via `GATEWAY_ENC_KEY` (Fernet); rotation runbooks.
- Audit: settings.update, tool.request, admin.

## Observability
- OTEL traces across Gateway/Workers; metrics (SSE, publish outcomes, uploads, tools); JSON logs with correlation IDs.
- Dashboards + SLO burn‑alerts; runbooks (Kafka/DB/Redis/SSE).

## Visual & Behavior Parity (Golden 7001)
- Tokens: capture computed styles per selector; store tokens/golden.*.json; compare to local tokens.
- CSS variables: `css/theme.css` with tokens; replace hard‑coded values in `index.css`, `css/messages.css`, `css/settings.css`.
- Snapshots: golden area views (home, sidebar, attachments chip, settings tabs) vs local with small threshold.
- Gate: CI blocks on token or visual diffs > threshold.

## Phase 0 — Golden Baseline & Parity Contract
- Capture golden UI tokens (colors, fonts, spacing, shadows, transitions), screenshots, video of flows.
- Freeze golden Playwright specs as acceptance; define parity checklist by component and behavior.
- Output: design token map, selectors map, baseline snapshots, signed parity checklist.

## Phase 1 — Security & Policy
- OIDC enforced in non‑DEV; JWT cookies `Secure` + `SameSite=None`, CSRF assessment; HTTPS only.
- OPA checks for settings, tool catalog, attachment download; tenant access (OpenFGA) on sensitive ops.
- Secrets via KMS/Vault; `GATEWAY_ENC_KEY` rotated; runbooks for rotation.

## Phase 2 — Schema & Data Stores
- Managed Postgres, Redis, Kafka with HA; migrations idempotent; PITR & restore drill.
- Topic configs (partitions/retention) for conversation/tool/memory WAL.

## Phase 3 — Resilience & Scale
- Horizontal Gateway; SSE connection management; graceful shutdown.
- Worker autoscale vs. lag/CPU; outbox+WAL verified; DLQs.
- SLOs: p95 enqueue <150ms, SSE reconnect <1s, stable streaming.

## Phase 4 — Observability & Runbooks
- OTEL traces through stack; metrics for SSE, uploads, tools, publish outcomes.
- Dashboards and alerts; incident runbooks for Kafka/DB/Redis/SSE.

## Phase 5 — Pixel‑Perfect UI Parity
- Apply golden tokens to CSS; verify micro‑interactions & component states.
- Behavioral parity: streaming semantics, toggles persistence, uploads UX, sidebar/session controls.
- Visual regression and golden Playwright in CI as gates.

## Phase 6 — GUI Features To Activate
- Settings (server‑backed): Agent, Model, API Keys, Uploads, Antivirus, Speech, Scheduler (flagged), plus Tools Manager if present.
- Tools catalog gating; slash commands if golden supports.

## Phase 7 — Tooling & Ingestion Hardening
- Sandbox limits; optional containerized isolation for untrusted code.
- Attachment size gating; OCR/PDF guards; backpressure metrics.

## Phase 8 — CI/CD & Compliance
- SBOM, SAST/DAST, license scan; dev→staging→prod gates; privacy/retention docs.

## Phase 9 — Pilot→GA
- Canary rollout, SLO burn rate; GA after 2–4 weeks green.

---

## Test Strategy (Canonical)

Two tracks run in CI for every PR:
1) Golden acceptance (target http://localhost:7001) — TypeScript Playwright spec suite.
2) Parity acceptance (compare http://localhost:7001 vs. our Gateway UI, default http://localhost:21016/ui) — functional + visual.

Coverage goals:
- Pages: Chat, Settings (all tabs), Tools Manager (if present), Scheduler (shell), Login (if OIDC on).
- Controls: every button, toggle, input, file picker, menu, modal, toast, icon button.
- Behaviors: SSE open/close, streaming, uploads progress, preferences persistence, session lifecycle.
- Visual: snapshot baselines on key states and breakpoints.

Acceptance: All golden specs pass against 7001; parity specs pass against both 7001 and local; visual diffs within tolerance.

Environment variables used by tests:
- `BASELINE_URL` (default `http://localhost:7001/ui`)
- `PARITY_URL`   (default `http://localhost:21016/ui`)

---

## Execution Plan (Initial Milestones)

M1 (This PR):
- Add webui/tests/ui Playwright (TS) suite scaffolding and initial specs matching golden filenames.
- Implement golden smoke, composer, toggles, uploads smoke, parity harness, and utilities.
- Add README with how to run locally; do NOT fetch external repos unless explicitly approved.

M2:
- Expand specs to cover every settings tab field and state transitions; add visual snapshots.
- Add tools manager specs (toggle/execute) if present on golden.

M3:
- Wire tests into CI; add load/soak; finalize SLO dashboards.

---

Notes:
- No external downloads performed automatically. The golden repo (agent-zero) may be consulted only with explicit approval.
- All UI parity patches will be validated by tests; no unverified visual changes land on main.

---

## Current Status (Live)
- Gateway emits `/v1/ui/event` and `/v1/util/event` → Kafka → SSE; UI renders `role=util` bubbles (toggle‑controlled).
- Settings save toasts (progress→success/error) in UI; Gateway emits `ui.settings.saved` event post‑save.
- Model profile default base URL (e.g., Groq) set server‑side if left blank.
- Tests: golden/local/parity Playwright suites (containers) cover chat, toggles, uploads, tools, settings persistence, utilities, long‑stream stability.
- Golden snapshots saved (home/settings); parity project prepared.

## Sprint 01 Backlog (Do NOW)
1) Token Capture & Parity
   - Add Playwright token capture utilities and area snapshot specs (home, sidebar open, composer, attachments chip, settings: uploads/AV).
   - Generate golden tokens/snapshots; run local capture; produce token/visual diffs.
   - Create `css/theme.css`; replace hard‑coded values in header/sidebar/composer; re‑run parity and commit minimal deltas.
2) Behavior Closeouts
   - Thoughts/Utilities tests (assert greeting & SSE util bubble logic once per chat).
   - Chat flows: new/reset/delete polished; ensure SSE reconnect stability.
   - Settings fields: verify validations and field masks align with golden.
3) CI Gates
   - Add containerized golden/local/parity jobs; upload traces/snapshots/diffs; block merges on red.
4) Observability
   - Add SSE connect/error metrics; outbox depth; settings.save timing; dashboards + alerts.

## Sprint 02 Backlog
1) Messages & Attachments Visuals (tokens → theme.css) — wrap up parity on message bubble spacing, code blocks, shadows.
2) Settings tabs visuals (Agent/Model/Keys, Uploads/AV, Speech) — finalize tokens and snapshots.
3) Tooling hardening (resource limits, containerized untrusted exec optional) + catalog gating in UI (read‑only view for non‑admins).
4) CI polish: flaky detection, retries, visual diff tuning; load/soak smoke per PR.

## Acceptance Criteria
- Visual parity: zero token diffs on selected selectors; visual diffs ≤ 0.5% pixels across captured views.
- Behavior parity: all button/input flows green in golden & local; toggles behave identically; settings persist centrally and emit `ui.settings.saved`; SSE availability ≥ 99.9%.

