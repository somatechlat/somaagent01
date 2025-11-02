<!-- Sprinted roadmap derived from canonical roadmap — generated 2025-10-30 -->
# SomaAgent01 Roadmap (Sprinted)

Last updated: 2025-10-31
Branch: INTEGRATION-ZERO

Overview
This file breaks the canonical roadmap into sprint-sized deliverables, with acceptance tests, owners (placeholder), and estimated effort.

## Priority: Centralize LLM model/profile management (1-2 sprints)

Why priority
- Recent diagnostics found the UI/worker flow failing due to inconsistent model/profile values and base_url normalization (`invalid model/base_url after normalization`). This blocks end-to-end assistant replies. Centralizing profiles in the Gateway is required to unblock E2E functionality and make the system operable and secure.

Goals
- Make Gateway the single source of truth for model profiles, provider credentials, and base_url normalization.
- Remove raw `base_url` propagation from workers and other services; workers must send only role + messages + limited overrides (model name, temperature, kwargs).
- Provide compatibility flags and a migration path with `warn` → `enforce` modes.

Sprint A (1 week) — Audit & Gateway API
- Tasks
  1. Complete a full audit of code and env usage of `model`, `base_url`, and model profile reads/writes. Produce an audit doc with file-by-file findings and backups of current profiles (todo #1).
  2. Design Gateway API contract for model/profile CRUD, credential management, and a `/v1/llm/test` endpoint (todo #2).
  3. Add `GATEWAY_MODEL_LOCK` env flag and implement `warn` logging behavior (no enforcement yet).
- Acceptance
  - Audit doc delivered. Gateway API spec reviewed. `GATEWAY_MODEL_LOCK=warn` logs incoming `base_url` overrides but does not block invokes.

Sprint B (1–2 weeks) — Gateway authority & worker migration
- Tasks
  1. Implement Gateway CRUD for `/v1/model-profiles` and internal credentials endpoints (todo #3).
  2. Harden `_normalize_llm_base_url` and provider detection; add unit tests (todo #7).
  3. Update workers to stop sending `base_url` in overrides and to call Gateway only (todo #4).
  4. Deprecate per-service profile envs and add startup warnings (todo #5).
- Acceptance
  - Worker->Gateway->Provider flow works end-to-end in dev; Playwright smoke shows assistant reply. `GATEWAY_MODEL_LOCK=enforce` can be enabled in a canary without breaking processing.

Notes
- These centralization sprints take precedence over other UI migration work until assistant reply flow is stable.


## Sprint — UI Parity & No‑Legacy Completion (2025‑10‑31 → +1 week)

Goals
- Make the Web UI identical in behavior to Agent Zero while fully wired to our backend.
- Eliminate the “auto new chat” symptom and ensure default selection is idempotent.
- Replace remaining legacy UI actions (history, context, files) with canonical /v1 routes.

Tasks
1) Stop auto new chat creation
  - Add a one-time init guard for default selection.
  - Do not auto-create a session when no sessions exist; show empty state and wait for explicit action.
  - Consolidate duplicate DOMContentLoaded handlers that cause re-inits; add a dev-only counter for newContext calls.

2) History/context endpoints and UI wiring
  - Backend: GET `/v1/sessions/{id}/history` → { history, tokens }.
  - Backend: GET `/v1/sessions/{id}/context-window` → { content, tokens }.
  - UI: `webui/js/history.js` calls these routes; SSE-only, no polling.

3) Files modal to /v1
  - Backend: `/v1/workdir/list|upload|delete|download` minimal FS adapter under a sandboxed base dir.
  - UI: `webui/js/file_browser.js` to use `/v1/workdir/*` with current response mapping.

4) Playwright parity tests
  - Startup default selection without auto-create; thinking placeholder + tool.start lifecycle; uploads progress; history/context display; files modal list/upload/delete/download.

Acceptance
- No phantom sessions created over 10+ minutes idle.
- History/Context and Files actions work via /v1; no legacy calls observed in network logs.
- UI smoke and tool e2e pass; new Playwright parity specs added and green locally.


Sprint 1 — Foundation & Tests (2 weeks)
- Goals
  - Create API contract tests and Playwright smoke test harness.
  - Add or generate `docker-compose.optimized.yaml` or update `deploy-optimized.sh` to point to `docker-compose.yaml` with tuned profiles.
  - Archive deprecated files (`run_ui.py`, `tmp/webui`) and update docs/Makefile/launch configs.

- Tasks
  1. Add pytest API contract tests (smoke):
     - Test SSE subscribe: open SSE stream to `/v1/session/{test-session}` and assert event types for a synthetic message flow.
     - Test POST /v1/session/{id}/message returns 202 and appears in SSE.
     - Test POST /v1/uploads returns a usable resource URL.
  2. Add a Playwright smoke test that opens the Gateway-served UI, subscribes to SSE, sends a message via the UI, and checks for progressive token rendering.
  3. Create `docker-compose.optimized.yaml` (subset of `docker-compose.yaml`) and update `deploy-optimized.sh`.
  4. Archive `run_ui.py` into `archive/` and tarball `tmp/webui` into `archive/tmp-webui-<date>.tar.gz`.

- Acceptance
  - All new tests pass locally in the dev environment.
  - `deploy-optimized.sh` runs successfully in a local laptop dev environment (simulated) and brings up core infra.

Sprint 0 — Urgent: Centralize URLs & Cleanup (immediate, half-day)

- Goal
  - Make the UI canonical at http://localhost:21016/ui and remove non-working hard-coded references across tests, scripts, and docs. Archive deprecated artifacts that cause confusion.

- Tasks
  1. Hard-coded discovery: grep and list all occurrences of `localhost:21016`, `127.0.0.1:21016`, `20016`, and `8010` usage in tests/scripts/docs (already performed).
  2. Set canonical env defaults in `.env` / `.env.example`:
     - GATEWAY_PORT=21016
     - GATEWAY_BASE_URL=http://localhost:21016
     - WEB_UI_BASE_URL=http://localhost:21016/ui
  3. Replace literal fallbacks in the following files with env lookups:
     - `tests/e2e/*`, `tests/playwright/*`, `tests/ui/*`
     - `webui/playwright.config.ts`, `webui/tests/*.spec.ts`
     - `scripts/e2e_quick.py`, `scripts/ui-smoke.sh`, `scripts/check_stack.sh`
     - `python/api/*` modules with fallback strings
     - `.vscode/tasks.json`
  4. Archive the confusing artifacts to `archive/` (timestamped): `run_ui.py`, `tmp/webui/`, `deploy-optimized.sh`.
  5. Run quick verification: `make dev-up` then `pytest -q tests/e2e/test_api_contract_smoke.py` and `./scripts/ui-smoke.sh`.

- Acceptance
  - UI loads at http://localhost:21016/ui/index.html in a browser.
  - Smoke tests issue POST /v1/session/message and open SSE streams successfully.
  - A repo grep for `localhost:21016` / `127.0.0.1:21016` shows only documented examples that reference the env variables (not raw literals used at runtime).

- Notes
  - This sprint (Sprint 0) is tactical and must be completed before Sprint 1 tests are relied upon in CI.
  - Per your direction: no new config systems or helper files will be added; we will reuse existing env mechanisms and helpers. Files will be archived before removal.

Sprint 2 — UI Migration & Compatibility (2 weeks)
- Goals
  - Migrate key UX components from `tmp/webui` into `webui/` (streaming rendering, tool panel, upload progress).
  - Implement Gateway adapter endpoints for legacy poll flows (marked deprecated).

- Tasks
  1. Identify and extract UI components from `tmp/webui` (list source file names and functions). Port them to `webui/` with minimal refactors to fit project build.
  2. Add Playwright tests for tool invocation: open tool panel, call a sample tool (mocked), and assert `tool.result` appears in UI.
  3. Implement a Gateway adapter route that accepts legacy poll payloads and transforms them into the canonical message/event workflow.

- Acceptance
  - Playwright UX tests pass in CI.
  - Legacy adapter logs show correct transformations; the adapter is flagged as deprecated in docs.

Sprint 3 — Harden & Remove Legacy (2 weeks)
- Goals
  - Harden resource settings and deployment, add OPA checks, run end-to-end tool execution tests and memory WAL verification.
  - Remove legacy adapter after clients are migrated.

- Tasks
  1. Add OPA policy verification into CI for tool execution flows.
  2. Run end-to-end tests that: send a message, cause a tool invocation, ensure Tool Executor publishes `tool.result`, and confirm memory WAL ingestion to SomaBrain.
  3. Finalize deploy resource tuning in `docker-compose.optimized.yaml` and update docs.

- Acceptance
  - E2E tests pass in CI and local dev.
  - Legacy adapter fully removed and all references cleaned.

Backlog / Nice-to-have
- Websocket support for high-throughput UIs (research + benchmark).
- Autoscaling blueprint for cloud deployment (k8s helm charts + metrics rules).
- Rich Playwright scenarios for error paths and long-lived sessions.

Owners and notes
- Owners: TBD. Suggest assigning one engineer (backend) for Sprint 1 and one frontend engineer for Sprint 2.
- Notes: All changes should be done on feature branches and validated with the provided tests before merge to `main`.
