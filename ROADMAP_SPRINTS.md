# 🗺️ Canonical Sprint Roadmap – SomaAgent01 Next‑Gen Upgrade

This sprint plan operationalizes the canonical roadmap across 6–8 weeks. Sprints map to waves and reference real repo paths (services/*, python/integrations/*, conf/*, schemas/*, docs/*, infra/*, webui/*).

## 📆 Sprint structure
Two‑week sprints with explicit Goals, Deliverables, and Acceptance. Use IDs (e.g., W2‑S3) in PR titles.

### Sprint 0 (W0‑S0) – Contracts & Docs
Goal: Lock contracts and docs so implementation starts cleanly.
- Add schemas: `schemas/agent.runs.v1.json`, `schemas/agent.steps.v1.json`, `schemas/agent.tools.v1.json`, `schemas/agent.audit.v1.json`; extend conversation/tool schemas with tracing fields.
- Docs: `docs/messaging/agent-*.md` pages; update `mkdocs.yml`; build docs.
- Scripts: ensure `scripts/schema_smoke_test.py` covers new schemas.
- Acceptance: schema smoke PASS; mkdocs build PASS.

### Sprint 1 (W1‑S1) – Memory Reliability I
Goal: Durable writes via outbox and write‑through integration.
- services/common: outbox repo + idempotency key generator + publisher validation.
- python/integrations/soma_client.py: `/health` probe (1–1.5s), breaker signals, batch & link helpers.
- services/gateway + services/conversation_worker: write‑through remember (user/assistant) with idempotent keys; create user↔assistant links.
- services/memory (SomaBrain): implement streaming SearchMemory RPC and client helper.
- Acceptance: unit tests PASS; write‑through persists to outbox when degraded/down.

### Sprint 2 (W1‑S2) – Memory Reliability II
Goal: Health‑aware sync worker, recall cache, and back‑pressure test.
- New sync worker: degraded/down modes, jittered backoff, concurrency=1, batch<=25; metrics.
- Redis recall cache (5 min TTL); link tool outputs.
- Load test: force `breaker_open` and verify bounded queue + drain.
- Acceptance: load test PASS; zero loss; metrics show throttling.

### Sprint 3 (W2‑S3) – Orchestrator MVP
Goal: Minimal DAG + checkpoints + events.
- services/orchestrator: DAG runner; checkpoint store (versioned); start/resume/get; emit runs/steps with versioning and tracing.
- conversation_worker integration: delegate flow to orchestrator.
- Acceptance: kill‑and‑resume PASS; events visible and valid.

### Sprint 4 (W2‑S4) – Policy Node & Visualization Hook
Goal: Enforcement + introspection.
- Central policy node calling OPA before tools; deny‑by‑default on timeout with audit.
- Optional visualization export hook (flagged) to external consumer.
- Acceptance: policy tests PASS; audit events present; retries bounded.

### Sprint 5 (W3‑S5) – Roles, Tool Schemas, Streaming
Goal: Safer tools with better UX.
- conf/roles.yaml + conf/policies/*.rego + hot‑reload.
- Auto schema gen from docstrings; agent.tools.v1 analytics.
- tool_executor: streaming delimiters; webui: progressive render support.
- Acceptance: unauthorized calls denied + audited; UI streams progressively.

### Sprint 6 (W3‑S6) – Sandbox & Timeouts
Goal: Isolation for high‑risk tools.
- Sandbox runner using gVisor/seccomp; per‑tool toggle; minimal FS; hard timeouts.
- Falco rules and dashboards.
- Acceptance: sandbox tools run; Falco events observable; performance impact documented.

### Sprint 7 (W4‑S7) – Messaging Validation & Observability
Goal: Safer bus and deeper visibility.
- Tenant‑partitioned topics and publish‑time JSON Schema validation.
- OTEL propagation of SomaBrain request_id; node metrics exported.
- Grafana dashboards and SLO alerts for latency/error/outbox backlog.
- Aggregated `/healthz` endpoint in gateway (fan‑out checks to core dependencies and sub‑services).
- Acceptance: invalid publishes rejected; dashboards live; alerts tested.

### Sprint 8 (W4‑S8) – Helm & CI Hardening
Goal: Smooth installs and secure builds.
- Helm pre‑install job for DB tables + topics; HPA on tool latency.
- CI: Trivy scan (fail on critical), benchmark job emitting agent.benchmarks.v1; docs build.
- CI: OPA policy unit tests integrated; baseline performance thresholds enforced from benchmark job.
- Acceptance: helm install < 10 min; CI green with Trivy 0 critical.

### Sprint 9 (W5‑S9) – Vault Rotation & OPA Sandbox
Goal: Secrets and policy ergonomics.
- Vault‑based SURFSENSE_JWT rotation + config watcher; OPA testing sandbox CLI.
- Acceptance: rotation seamless; policy sandbox usable by developers.

### Sprint 10 (W5‑S10) – Ops Tools & Deprecations
Goal: Final polish and cleanup.
- scripts/somabrain-sync CLI (manual flush + audit); services/memory_service removed from compose/helm and code paths; runbooks & incident playbooks.
- webui: minimal Dead‑Letter UI to inspect Kafka DLQ, filter, and retry/ack.
- Acceptance: manual flush audited; memory_service fully removed; runbooks validated.

## 🌊 Wave alignment

| Wave | Scope | Sprints |
| --- | --- | --- |
| 0 | Contracts & docs | 0 |
| 1 | Memory reliability | 1–2 |
| 2 | Orchestrator MVP | 3–4 |
| 3 | Roles, tools, sandbox | 5–6 |
| 4 | Messaging/observability/CI | 7–8 |
| 5 | Security & ops | 9–10 |

## 📦 Canonical files & owners
- `ROADMAP_CANONICAL.md` – Platform roadmap (Architecture)
- `ROADMAP_SPRINTS.md` – Sprint schedule (Delivery)
- `docs/messaging/` – Event contracts and runbooks (Tech Writing)
- `schemas/` – JSON Schemas (Platform)
- `services/*` – Services (Backend)
- `python/integrations/` – Clients (Platform)
- `infra/` – Helm/K8s/observability (DevOps)
- `webui/` – UI streaming + run timelines (Frontend)
- `scripts/` – Load tests, CLI, automation (Platform)

## ✅ Next steps
1. Create feature branch: `feature/full-somabrain-memory`.
2. Execute Memory Plane M1 tasks first (env and CI guard; remove legacy artifacts); then proceed with M2 (SomaBrainClient hardening and OPA pre‑write checks).
3. Coordinate /v1/agents/profiles contract with frontend, then deliver replication/DLQ (M3) and health aggregator (M5) in subsequent sprints.

---

## Focused Memory Plane Sprint Plan (Appendix)

Sprint A (1 week) – M1 Foundations
- Lock envs: SOMA_BASE_URL and SOMA_NAMESPACE across dev/staging/prod.
- Add CI guard: fail if legacy memory_service or memory_client exists.
- Remove remaining memory_service code and Helm charts.
- Acceptance: CI guard green; repo free of legacy artifacts; mkdocs build PASS.

Sprint B (2 weeks) – M2 Harden SomaBrainClient
- Rename SomaClient → SomaBrainClient with a short-lived alias.
- Add OTEL spans, retry with jitter, X‑Request‑Id propagation.
- Implement embed_then_remember and remember_batch; emit memory_write_* metrics.
- Insert OPA memory.write pre-checks in conversation_worker and tool_executor.
- Acceptance: unit tests PASS; metrics visible; OPA enforced (fail-open in dev toggleable).

Sprint C (2 weeks) – M3 Replicator + DLQ
- Publish to memory.wal after successful writes.
- New services/memory_replicator consuming WAL to write to replica; send irrecoverable to memory.dlq.
- Gateway admin endpoints for DLQ list/inspect/replay; Helm topics/envs.
- Acceptance: e2e test PASS (primary+replica); DLQ replay works; Grafana shows replication metrics.

Sprint D (1 week) – M4/M5 Profiles + Health
- Middleware to propagate universe_id/persona_id and agent_profile_id.
- Gateway /v1/agents/profiles; UI wiring; memory_health_aggregator with /v1/health/memory.
- Acceptance: headers propagate; health shows lag; alerts configured.
