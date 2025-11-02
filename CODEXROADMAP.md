# CODEXROADMAP (Canonical)

Purpose: Production-grade roadmap and parity plan to make this stack behave and look IDENTICAL to the golden agent at http://localhost:7001, while meeting enterprise reliability, security, and operability standards. This is the single source of truth for scope, acceptance, and phased delivery.

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

