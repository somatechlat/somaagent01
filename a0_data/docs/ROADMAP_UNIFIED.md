# SomaAgent01 Unified Roadmap

**Generated:** October 8, 2025  
**Maintainers:** Platform Integration Squad

This document merges the current sprint roadmap and production gap analysis into a single reference. It supersedes the standalone `ROADMAP_SPRINTS.md` and complements `ROADMAP_GAP_ANALYSIS.md` by embedding its critical findings. Treat this file as the canonical planning artifact going forward.

---

## 🔗 Integration Anchor Points

- **SomaAgentHub integration endpoint:** `http://localhost:60010/` (local orchestration target for Agent ↔ SomaAgentHub integration).
- **Primary web UI:** `http://localhost:7002/` (Agent UI container). Post restart validation MUST include UI health checks.
- **Telemetry ingress:** `otel-collector:4317` (default OTLP endpoint for dev profile).

---

<!-- Realtime API compatibility checklist removed per user request. -->

---

## 📅 Sprint Roadmap (Current & Upcoming)

| Sprint | Duration | Goal | Deliverable |
|-------|----------|------|-------------|
| **Sprint 1** | 1 week | **Prune & Refactor Compose** – remove Whisper, merge services, delete one-off init containers, add API hook for voice. | Updated `docker-compose.somaagent01.yaml` (13 → 9 containers) + environment variable `VOICE_API_URL`. |
| **Sprint 2** | 1 week | **Add Monitoring & Health-Checks** – ensure Prometheus scrapes all services, add Grafana dashboard (optional). | Prometheus config updated, health-endpoints verified. |
| **Sprint 3** | 1 week | **Test End-to-End Flow** – UI → Delegation → Worker → SLM → Memory, with voice API stub. | Automated smoke-test script, updated runbook. |
| **Sprint 4** | 0.5 week | **Documentation & CI** – lock down the new stack, add CI job that builds the reduced compose file and runs the smoke test. | Updated docs, GitHub Actions workflow. |
| **Sprint 5** (optional) | 0.5 week | **Future-Proofing** – add optional compose profiles and a “full-stack” integration profile. | Profile-aware compose file, README examples. |
| **Sprint 6** | TBD | **(Reserved)** – placeholder retained; detailed realtime compatibility content removed per request. | TBD. |

### Sprint Execution Notes
- Sprint 6 tasks align with the checklist above; ensure backlog items reference `RT-###` issue IDs for tracking.
- Each sprint should deliver updated documentation (roadmap summaries, runbook changes) to keep this file and the knowledge base in sync.

---

## 🧭 Production Gap Analysis (Integrated Summary)

Derived from `ROADMAP_GAP_ANALYSIS.md` – refer there for historical log, but the essential blockers are catalogued here.

### 1. Infrastructure & Deployment
- Lacking Kubernetes/Helm manifests, GitOps automation, Terraform modules, and CI/CD pipelines.
- No Compose smoke tests in CI; add in Sprint 4 deliverables.

### 2. Testing & Quality
- No automated pytest suite, integration tests, or schema compatibility checks.
- Smoke tests and chaos experiments absent.

### 3. Observability
- Missing Prometheus dashboards, OpenTelemetry tracing, and alerting rules.
- Metrics endpoints require verification; integrate into Sprint 2 & Sprint 6.

### 4. Security & Governance
- Rate limiting absent at gateway; multi-tenant isolation incomplete (Kafka ACLs, Postgres RLS).
- Policy enforcement gaps remain in conversation worker; secret rotation automation missing.

### 5. Operator Tooling
- No session inspector UI, model profile dashboard, or requeue management console.
- CLI tooling for session replay must coincide with realtime replay harness (Sprint 6 dependency).

### 6. Feature Gap Highlights
- Domain models, advanced SLM pipeline, router enhancements, Canvas real-time updates, privileged mode framework, and enterprise governance remain outstanding.

### 7. Scale & Resilience
- Chaos tests (Kafka outage, Redis latency), latency SLO enforcement, load testing to +20% headroom, and incident drill procedures are required before production signoff.

---

## ✅ Immediate Next Steps (2025-10-08)
1. Finalize Sprint 6 work package in Jira/Linear with tasks covering:
   - Session schema documentation and persistence.
   - Audio buffer limit enforcement & error alignment.
   - Tool-to-response sequencing adjustments.
   - Conformance recorder/replayer harness (pointed at `http://localhost:60010/`).
2. Update `docs/SomaAgent01_Runbook.md` with Realtime health check instructions and new endpoint validations.
3. Align CI roadmap: add Compose smoke test job (Sprints 4 & 6) and conformance diff stage.
4. Restart SomaAgent01 dev cluster, validate Agent UI (`http://localhost:7002/`) and Realtime endpoint readiness following config changes.

---

## 📘 Cross-References
- `docs/ROADMAP_SPRINTS.md` – retained for changelog history; defer to this unified document for current planning.
- `docs/ROADMAP_GAP_ANALYSIS.md` – holds full narrative gap assessment; summaries imported here.
- `SOMAGENT_TOOL_SERVICE_DESIGN.md` – tool execution schema, to be updated alongside Sprint 6 tooling tasks.

> **Reminder:** After each sprint review, sync this unified roadmap with the latest outcomes and backlog reprioritization.
