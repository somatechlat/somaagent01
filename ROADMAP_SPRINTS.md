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
- Acceptance: invalid publishes rejected; dashboards live; alerts tested.

### Sprint 8 (W4‑S8) – Helm & CI Hardening
Goal: Smooth installs and secure builds.
- Helm pre‑install job for DB tables + topics; HPA on tool latency.
- CI: Trivy scan (fail on critical), benchmark job emitting agent.benchmarks.v1; docs build.
- Acceptance: helm install < 10 min; CI green with Trivy 0 critical.

### Sprint 9 (W5‑S9) – Vault Rotation & OPA Sandbox
Goal: Secrets and policy ergonomics.
- Vault‑based SURFSENSE_JWT rotation + config watcher; OPA testing sandbox CLI.
- Acceptance: rotation seamless; policy sandbox usable by developers.

### Sprint 10 (W5‑S10) – Ops Tools & Deprecations
Goal: Final polish and cleanup.
- scripts/somabrain-sync CLI (manual flush + audit); remove services/memory_service from compose/helm and code paths; runbooks & incident playbooks.
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
1. Create Sprint 0 tickets and assign owners.
2. Add schema/docs tasks to CI and verify mkdocs build.
3. Start Sprints 1–2 focusing on outbox + write‑through + sync worker + load test.
