# SomaAgent01 Integration Roadmap

This roadmap breaks the Agent Zero → SomaAgent01/SomaBrain convergence work into a foundation sprint followed by parallel tracks that can progress simultaneously. Each track advertises explicit entry/exit criteria so coordination across teams stays lightweight.

## Sprint 0 – Baseline Readiness (Week 1)
- **Goals**
  - Confirm repository cleanliness and align local/dev/prod container profiles.
  - Instrument health probes for SomaBrain, Kafka, Redis, Postgres, and OpenFGA from the Agent Zero runtime.
  - Document the canonical compose workflow, noting that Grafana is deferred until the custom visualization layer lands.
- **Key Deliverables**
  - Updated `infra/docker-compose.somaagent01.yaml` with `dev`/`prod` profiles and Prometheus-only observability.
  - Health-check utility invoked during agent bootstrap (fails fast with actionable errors).
  - Runbook excerpt covering environment variables, required ports, and dependency checks.
- **Acceptance Criteria**
  - `docker compose up` (core) succeeds on a fresh workstation using the documented steps.
  - SomaBrain connectivity issues are surfaced within 30 seconds of agent start.
  - Status summary logged into operator console and stored in telemetry topic.

## Parallel Sprint Grid (Weeks 2–5)
Once Sprint 0 closes, three capability tracks kick off together. Shared milestones ensure messaging, memory, and observability advance in lock-step while policy/tooling work begins as soon as Kafka transport is stable.

| Track | Focus | Duration | Dependencies |
| --- | --- | --- | --- |
| A | Messaging Convergence | 2 weeks | Sprint 0 |
| B | Memory & State Unification | 2 weeks | Sprint 0 |
| C | Observability & Metrics | 2 weeks | Sprint 0 |
| D | Tooling Offload & Policy | 3 weeks | Track A completion, Track C telemetry schemas |
| E | Production Hardening & Launch | 2 weeks | Tracks A–D exit criteria |

### Track A – Messaging Convergence (Sprint A1, 2 weeks)
- **Goals**
  - Drive conversations via Kafka transport instead of the local CLI loop.
  - Normalize session metadata (tenant, persona, budget) across gateway and Agent Zero context.
  - Provide a compatibility shim so legacy CLI flows still work in dev mode.
- **Key Deliverables**
  - Kafka client adapter in core agent (`python/helpers`) mirroring `KafkaEventBus` semantics.
  - Session bootstrapper that hydrates `AgentContext` from gateway-created records (Postgres + Redis).
  - Feature flag to select between CLI and Kafka ingestion paths.
- **Acceptance Criteria**
  - End-to-end conversation initiated from SomaAgent gateway reaches the Agent Zero reasoning loop and streams responses back over Kafka/WebSocket.
  - Session metadata remains consistent after reconnects and quick actions.
  - Legacy CLI remains functional when `SOMA_AGENT_MODE=LOCAL`.

### Track B – Memory & State Unification (Sprint B1, 2 weeks)
- **Goals**
  - Mandate SomaBrain as the authoritative long-term memory store outside of troubleshooting mode.
  - Align metadata schemas (coordinates, universes, persona IDs) and eviction policies.
  - Provide migration tooling for historical FAISS snapshots.
- **Key Deliverables**
  - `SomaMemory` refresh hooks tied to conversation resets and persona switches.
  - `SOMA_ENABLED` defaulted to true with explicit opt-out for dev.
  - CLI script to ingest/export FAISS archives via `SomaClient.migrate_import`.
- **Current Progress**
  - Canonical session envelope schema captured in `docs/SomaAgent01_Session_State.md`, covering Redis/Postgres alignment and migration entry criteria.
  - Pending: implement `session_backfill.py` script and tighten repository tests before enabling the new table in production.
- **Acceptance Criteria**
  - Memory writes in either runtime surface everywhere within 5 seconds.
  - Regression tests covering similarity search, delete-by-query, and WM cache limits.
  - Documentation update outlining fallback procedure and support boundaries.

### Track C – Observability & Metrics (Sprint C1, 2 weeks)
- **Goals**
  - Deliver Prometheus-only monitoring while every service exposes a `/metrics` endpoint or Prometheus scrape target.
  - Standardize metrics names/labels across gateway, workers, tool executor, and policy services.
  - Capture requirements for the upcoming custom visualization stack that will replace Grafana.
- **Key Deliverables**
  - Prometheus scrape configuration covering Kafka, Redis, Postgres, OpenFGA, OPA, gateway, conversation worker, tool executor, and delegation services.
  - Code instrumentation or exporters added where gaps exist (track TODOs inline with services).
  - Design brief defining the future visualization layer and migration plan from Grafana.
- **Acceptance Criteria**
  - Prometheus targets show green for all core services under the `dev` profile.
  - Critical SLO/SLA metrics (latency, queue depth, tool durations, policy decisions) are queryable via PromQL.
  - Visualization requirements logged with owners and scheduled follow-up.

### Track D – Tooling Offload & Policy Enforcement (Sprint D1, 3 weeks)
- **Goals**
  - Replace in-process tool execution with remote execution via Kafka (`tool.requests`/`tool.results`).
  - Enforce OPA/OpenFGA decisions consistently before tool execution and memory mutation.
  - Emit structured telemetry for tool runs, budgets, and delegation workflows, aligning with Track C schemas.
- **Key Deliverables**
  - Async tool invocation pipeline awaiting remote responses with timeout/retry strategy.
  - Policy enforcement middleware shared between services and core runtime.
  - Metrics/trace emitters aligned with Prometheus + ClickHouse schemas.
- **Acceptance Criteria**
  - 95th-percentile tool turnaround ≤ 8 seconds in staging environment.
  - Unauthorized tool attempts are blocked with auditable policy decisions.
  - Telemetry dashboards (temporary PromQL notebooks) reflect tool usage and budget consumption in near real-time.

### Track E – Production Hardening & Launch (Sprint E1, 2 weeks)
- **Goals**
  - Harden deployment pipeline, secrets management, and failover scenarios.
  - Finalize documentation, runbooks, and on-call procedures.
  - Execute dress rehearsal load test and failure-injection drills.
- **Key Deliverables**
  - GitHub Actions (or preferred CI) workflow building and publishing dev/prod images.
  - Vault-backed secret injection for prod profile, with fallbacks for dev.
  - Load-test report covering Kafka throughput, worker scaling, and recovery playbooks.
- **Acceptance Criteria**
  - Successful canary release serving real tenants with monitored SLOs.
  - Rollback procedure tested end-to-end.
  - All critical documentation hosted alongside existing SomaAgent manuals.

---

**Coordination Notes**
- Hold a cross-track stand-up thrice weekly to unblock shared dependencies (schema changes, topic contracts, Prometheus labels).
- Use the shared metrics backlog to track any service that cannot yet expose Prometheus data—owning teams must either instrument or raise a blocker.
- Grafana remain out of rotation until the custom visualization stack clears design review; capture that decision in Track C’s design brief.

### Current Implementation Snapshot
- Track A kicked off with Kafka topic contract validation; gateway now emits metrics that will back the transport soak tests.
- Track C delivered Prometheus endpoints for the FastAPI gateway (`/metrics`) and conversation worker (port `9301`), plus new scrape jobs in `observability/prometheus.yml`.
- Upcoming during this sprint: extend exporters to tool executor and enrich Prometheus labels before wiring custom visualization in place of Grafana.

**Next Steps**
1. Close Sprint 0 and confirm Prometheus-only observability in the compose stack.
2. Kick off Tracks A, B, and C concurrently with shared milestone reviews at the end of week 3.
3. Green-light Track D once Kafka messaging passes soak tests; pre-stage production readiness tasks for Track E.
