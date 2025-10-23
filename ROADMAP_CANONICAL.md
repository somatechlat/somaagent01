# Agent Zero — Messaging Architecture Canonical Roadmap

Last updated: 2025-03-28  
Branch: messaging_architecture

This roadmap captures the end-to-end plan for restoring the full conversational pipeline, consolidating on the modern FastAPI gateway, and delivering a production-ready messaging backbone that runs locally with real services and scales to staging.

## Vision

Provide a single, policy-aware messaging architecture that:

- Runs the entire agent stack locally with all required dependencies (Kafka, Redis, Postgres, OPA, tool executor, UI) and zero mocks.
- Persists LLM credentials captured in the UI into runtime configuration securely and immediately.
- Uses the official single-node KRaft Kafka image across all environments.
- Streams conversations and tool results end-to-end via Kafka topics with deterministic ordering and backpressure handling.
- Exposes one modern FastAPI gateway for every ingress (HTTP, WebSocket, SSE) while decommissioning legacy Flask paths.
- Ships with an executable roadmap and sprint plan (waves) so the team can deliver incrementally.

## Constraints

- No mocked dependencies: compose stack must bring up the real services used in production parity.
- Gateway-first: All ingress traffic goes through `services/gateway/main.py`; legacy Flask endpoints are removed, not muted.
- Kafka official image (`confluentinc/cp-kafka`) with single-node KRaft mode; topic configs managed via automation, not manual CLI.
- Secrets and credentials flow from UI ➜ backend ➜ persisted env/secret store without manual edits.
- Every behavioral change requires Playwright/E2E regression coverage for chat happy-path and tool execution.
- Documentation updates ship with the code change that alters behavior.

## Waves & Deliverables

### Wave 0 – Baseline Integrity
- Document and verify the current docker-compose stack on branch `messaging_architecture`.
- Capture existing configs (.env, compose overrides) and codify smoke checks (Kafka health, gateway `/health`, worker consumer lag).
- Acceptance: `docker compose up` brings all services healthy; minimal smoke script passes; roadmap + sprint docs merged.

### Wave 1 – Gateway Consolidation
- Remove legacy Flask/`agent.py` messaging routes; migrate UI to call FastAPI gateway endpoints exclusively.
- Implement unified request validation, JWT/OPA hooks, and consistent response schema across REST/WebSocket/SSE.
- Acceptance: UI chat works only through gateway; legacy modules deleted; lint/tests green.

### Wave 2 – Messaging Backbone Restoration
- Rebuild Kafka topic provisioning and consumer wiring for `conversation.inbound`, `conversation.outbound`, `tool.requests`, `tool.results` with aiokafka.
- Ensure tool results bridge back to conversations, including error propagation and retry semantics.
- Acceptance: Automated integration test publishes a message and receives a streamed answer including tool output; Kafka consumer lag < 5s under load test.

### Wave 3 – Credential Flow & Persistence
- Implement UI form to store LLM credentials via settings API; persist to encrypted env store (filesystem secret vault or database table).
- Ensure runtime services reload or fetch credentials without restart; add validation and redaction in logs.
- Acceptance: Playwright test enters key, refreshes page, key still present (masked) and gateway uses it to call upstream LLM.

### Wave 4 – End-to-End Hardening
- Expand Playwright suite to cover multi-turn conversations, tool invocation, and cancellation paths.
- Add observability: OpenTelemetry spans across gateway ➜ worker ➜ tool executor; Grafana dashboard for messaging KPIs.
- Acceptance: Playwright suite green in CI; trace correlation visible; dashboard panel shows live throughput/error rate.

### Wave 5 – Performance & Release
- Load test (500 concurrent sessions) with controlled degradation strategy; implement autoscaling hooks or worker concurrency controls.
- Produce release runbook, rollback plan, and migration notes for removing legacy stack.
- Acceptance: Load test stays within SLA (<2s average response, 0 data loss), runbook approved, release candidate tagged.

## Milestones & Acceptance Criteria

| Milestone | Wave | Description | Acceptance |
| --- | --- | --- | --- |
| M0 | Wave 0 | Baseline compose stack + documentation committed | `docker compose ps` healthy, smoke script logs success |
| M1 | Wave 1 | Gateway-only ingress with legacy removal | UI chat works via gateway; 100% tests pass |
| M2 | Wave 2 | Kafka messaging pipeline restored | Automated test validates inbound/outbound/tool roundtrip |
| M3 | Wave 3 | Credentials persisted & hot-loaded | Playwright credential scenario green; secrets encrypted |
| M4 | Wave 4 | Observability & E2E coverage | Playwright suite + telemetry dashboards operational |
| M5 | Wave 5 | Performance sign-off & release artifacts | Load test report approved; runbook + rollback published |

## Dependencies & Environment Contract

- `.env` files remain source of truth; credential secrets stored using `services/gateway/settings.py` helpers with encryption key from `conf/env/`.
- Compose files: `docker-compose.yaml` (core stack), optional profiles for optimized builds. Official Kafka image referenced in all variants.
- Topics and ACLs codified in `infra/kafka/` manifests (to be added/updated during Wave 2).
- Playwright tests live under `tests/e2e/`; smoke tests under `scripts/`.
- Documentation updates go into `docs/` (`docs/roadmap_sa01.md` or new `docs/messaging/` folder).

## Risks & Mitigations

- **Credential leakage**: enforce redaction in logs, use secrets manager abstraction, add automated tests for redaction.
- **Kafka instability**: monitor broker metrics, include restart scripts, keep local data volumes isolated per build.
- **UI regressions**: rely on Playwright suite per PR and manual smoke as backup.
- **Legacy removal fallout**: phased branch `messaging_architecture` with feature flags; maintain fallback compose profile until Wave 2 completes.

## How to Maintain

- Update this roadmap whenever scope or acceptance criteria shift.
- Keep waves aligned with sprint plans in `ROADMAP_SPRINTS.md`.
- Ensure every merge request references wave/milestone IDs and links to tests and documentation updates.

---
Canonical roadmap for the messaging architecture overhaul established on branch `messaging_architecture`.
