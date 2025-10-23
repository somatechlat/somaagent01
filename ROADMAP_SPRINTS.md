# 🗺️ Canonical Sprint Roadmap – Messaging Architecture Overhaul

## Vision
Deliver a resilient end-to-end messaging pipeline that powers Agent Zero’s conversational experience through the modern FastAPI gateway, official KRaft Kafka, and automated UI credential flows.

---

## 📆 Sprint Structure
We operate in **3-week sprints** aligned with roadmap waves. Each sprint lists **Goals**, **Key Deliverables**, **Owners**, and **Acceptance Criteria**.

### Sprint 0 – Baseline & Roadmap Commit (Wave 0)
**Goal**: Capture the current state, codify smoke checks, and merge the canonical roadmap + sprint plan.
- Document compose services, env contracts, and smoke scripts in `docs/messaging/baseline.md`.
- Add automated health probe script `scripts/check_stack.py` (gateway, Kafka, worker).
- Merge updated `ROADMAP_CANONICAL.md` and this sprint file into `messaging_architecture` branch.
- **Acceptance**: Smoke script exits 0 on fresh `docker compose up`; documentation PR approved.

### Sprint 1 – Gateway Consolidation (Wave 1)
**Goal**: Route all ingress through FastAPI and delete legacy Flask pathways.
- Refactor UI (`webui/`) to call FastAPI endpoints exclusively; remove references to legacy routes.
- Delete `agent.py` legacy handlers and associated Flask blueprints/tests.
- Implement unified error contract (`services/gateway/errors.py`) and ensure SSE/WebSocket parity.
- Expand API tests under `tests/integration/gateway/` for chat start, stream, cancel.
- **Acceptance**: UI chat works end-to-end via gateway; integration tests green; lint passes; no Flask code remains.

### Sprint 2 – Kafka Messaging Backbone (Wave 2)
**Goal**: Restore Kafka topics, consumers, and tool result routing.
- Codify topic creation in `infra/kafka/topics.yaml` and bootstrap script.
- Update conversation worker to handle retries, DLQ, and tool result fan-in; ensure idempotent offsets.
- Add contract tests ensuring `tool.results` messages bubble to UI stream.
- Provide load-test harness (`scripts/loadtest_kafka.py`) hitting 50 concurrent sessions.
- **Acceptance**: Automated test publishes message and receives response with tool data; no dropped events under load test; metrics confirm consumer lag < 5s.

### Sprint 3 – Credential Persistence & E2E Tests (Wave 3)
**Goal**: Make UI credential settings durable and verifiable via Playwright.
- Extend settings API to encrypt/store LLM keys, backed by new secrets table or file vault.
- Implement hot-reload for credentials in gateway/conversation worker with caching + invalidation.
- Add Playwright tests for credential entry, persistence, and masked display; wire into CI.
- Harden logging with redaction filters and add security regression tests.
- **Acceptance**: Playwright workflow green; manual log review confirms no secret leakage; gateway uses stored key to call LLM stub successfully.

### Sprint 4 – Observability & Release Prep (Waves 4-5)
**Goal**: Harden system with observability, performance, and release artifacts.
- Instrument OpenTelemetry traces across gateway ➜ worker ➜ tool executor; publish Grafana dashboard JSON.
- Expand Playwright coverage for multi-turn, tool errors, cancellation, and network blips.
- Run 500-session load test, capture metrics, and document fallback strategy.
- Publish release runbook (`docs/messaging/release.md`) including rollback, smoke tests, and migration notes.
- **Acceptance**: CI Playwright suite stable; load test meets SLA (<2s p95); dashboard deployed; runbook approved by stakeholders.

### Backlog / Stretch Items
- Multi-tenant credential vault integration.
- Kafka schema registry adoption with Avro/Protobuf contracts.
- Automated chaos tests for broker restarts.

---

## 🌊 Wave Alignment

| Wave | Scope | Covered Sprint |
| --- | --- | --- |
| Wave 0 | Baseline integrity & documentation | Sprint 0 |
| Wave 1 | Gateway consolidation | Sprint 1 |
| Wave 2 | Kafka messaging restoration | Sprint 2 |
| Wave 3 | Credential persistence | Sprint 3 |
| Wave 4 | E2E hardening | Sprint 4 |
| Wave 5 | Performance & release | Sprint 4 (second half) |

---

## 📦 Canonical Files & Owners
- `ROADMAP_CANONICAL.md` – Messaging roadmap (owner: Architecture).
- `ROADMAP_SPRINTS.md` – Sprint schedule (owner: Delivery).
- `docs/messaging/` – Living documentation, smoke scripts, runbooks (owner: Technical Writing).
- `scripts/` – Automation, load tests, smoke checks (owner: Platform).
- `tests/e2e/` – Playwright automation (owner: QA).

---

## ✅ Next Steps
1. Finalize Sprint 0 tickets in the project board and assign owners.
2. Wire smoke script into CI (pre-merge) once Sprint 0 closes.
3. Use wave/sprint IDs (e.g., `W1-S1`) in commit messages and PR titles for traceability.
