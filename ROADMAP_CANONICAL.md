# SomaAgent01 — Canonical Upgrade Roadmap (Next‑Gen Agent)

Last updated: 2025‑10‑23  
Scope: Full platform upgrade (orchestrator, memory, messaging, policy, tools, observability, security, CI/CD)

This canonical roadmap supersedes the older messaging‑only plan and captures the end‑to‑end program to deliver a durable, policy‑safe, observable, and enterprise‑ready agent. It is repo‑accurate to this codebase (services/*, python/integrations/soma_client.py, conf/*, schemas/*, docs/*).

## Vision and success criteria

| Goal | Success metric |
| --- | --- |
| Durable orchestrator | Checkpointed DAG in Postgres; recovery < 5s; rollback to prior snapshot |
| Role‑based sub‑agents | Roles loaded from conf/roles.yaml; OPA enforces 100% of policy tests |
| Tool framework | Auto‑generated JSON Schemas; schema validation errors < 0.1% in CI |
| Enterprise integration | End‑to‑end latency < 200 ms excl. upstream; zero data loss under outages |
| Security & isolation | Sandbox (gVisor/seccomp) per‑tool option; < 1/day false‑positive Falco alerts |
| Observability | 99% trace coverage; dashboards maintained in external project; SLO=99.9% uptime |
| CI/CD & deployability | Helm install < 10 min; Trivy finds 0 critical; blue/green canary succeeds |

## Target architecture (text)

- Orchestrator (new: services/orchestrator): LangGraph‑style DAG with retry+jitter and Postgres checkpoint store (versioned); emits agent.runs.v1 and agent.steps.v1; optional visualization hooks.
- Memory (SomaBrain‑only): Write‑through remember with Postgres outbox + health‑aware sync worker; Redis recall cache; /link provenance; optional short‑TTL SQLite micro‑cache (feature‑flagged).
- Roles & policy: conf/roles.yaml; conf/policies/*.rego; hot‑reload; uniform policy node before tools; agent.audit.v1 for policy/delegation.
- Tools & sandbox: Auto schema gen from docstrings; streaming delimiters {"delim":"start"|"end"}; optional gVisor/seccomp per‑tool; hard timeouts.
- Messaging & validation: Tenant‑partitioned topics; publish‑time JSON Schema validation; optional Kafka Streams enricher for trace context.
- Observability: OTEL spans propagate SomaBrain request_id; node metrics (success/failure/latency); Prometheus SLO alerts; dashboards maintained externally.
- Deployment/CI/CD: Helm pre‑install (tables/topics); Vault JWT rotation; Trivy scans; benchmark CI job; HPA on custom metrics.

## Mode taxonomy and configuration propagation (aligned)

- Modes: dev_full, dev_prod, prod, prod_ha. One canonical configuration source drives both Docker‑Compose and Helm.
- Global .env: A helper script generates `/root/soma-global.env` with security flags (JWT_ENABLED, OPA_ENABLED, MTLS_ENABLED), feature toggles (ENABLE_REAL_EMBEDDINGS, USE_REAL_INFRA), observability (PROMETHEUS_SCRAPE, OTEL_ENABLED), REPLICA_COUNT and resource hints, Istio/Vault injection flags, and infra ports.
- Docker‑Compose: Services load environment via a unified env_file. In CI/dev_prod, the generated `/root/soma-global.env` is authoritative; in local dev we preserve developer overrides without breaking workflows.
- Helm: Charts consume a global values block `{{ .Values.global.* }}`; overlays `dev-values.yaml`, `prod-values.yaml`, `prod-ha-values.yaml` set mode‑specific values. Service charts map replicas/resources/env/annotations to the global.
- CI: The pipeline selects the overlay based on DEPLOY_MODE and runs validation before success, with canary/rollback logic.

## Folder‑by‑folder scope (highlights)

- services/gateway: write‑through remember (user), streaming delimiters, schema validation on publish, trace & request_id propagation.
- services/conversation_worker: integrate orchestrator; remember assistant; Redis recall; emit runs/steps.
- services/tool_executor: centralized OPA check; delimiters; agent.tools.v1 analytics; sandbox hooks; memory linking.
- services/orchestrator (new): minimal DAG, checkpoint store, retry+jitter, events, visualization hook.
- services/delegation_*: agent.audit.v1 for delegation; optional child runs.
- services/memory_service: deprecate after validation; remove from compose/helm.
- services/common: publisher schema validation; outbox repo; trace utils; idempotency key gen.
- python/integrations/soma_client.py: 1–1.5s /health probe; breaker signals; batch & link helpers.
- conf/: roles.yaml; policies/*.rego; topics.yaml for tenant templates.
- schemas/: add agent.runs.v1.json, agent.steps.v1.json, agent.tools.v1.json, agent.audit.v1.json; extend conversation/tool schemas with tracing.
- docs/: messaging pages for new schemas; monitoring.md health/backoff; data/streams.md partitioning/validation.
- scripts/: somabrain-sync CLI; breaker_open load test with assertions; schema smoke/diff tests in CI.
- infra/: helm pre‑install job; OPA sidecar; Vault injector; HPA; dashboards; alert rules; Falco sidecar.
- webui/: handle streaming delimiters and optional run timeline.

## Contracts (authoritative)

- Idempotency key: `{tenant}/{namespace}/{session_id}/{role}/{timestamp_iso}/{hash16}`; on collision append `~{shortuuid8}`; persist `idem_key_base` and `idem_suffix`; unique `(tenant, namespace, somabrain_key)`; mirror in memory.meta.
- agent.runs.v1: `run_id, tenant, session_id, run_version, run_schema_version, orchestrator_name, orchestrator_build, model_profile, status, started_at, finished_at?, trace_id, request_ids?`.
- agent.steps.v1: `run_id, step_id, node_id, node_type, status, retry_count, started_at, finished_at, latency_ms, span_id, request_id?, inputs_summary, outputs_summary`.
- agent.tools.v1: `run_id, step_id, tool_name, status, tool_execution_ms, tool_error_type?, payload_size?, trace_id`.
- agent.audit.v1: `event_id, category(policy|delegation|sync|security), actor, subject, decision, reason, policy_version?, timestamp, meta`.
- agent.benchmarks.v1: as in `schemas/agent.benchmarks.v1.json`.
- Extend conversation/tool event schemas with `trace_id`, `span_id`, `request_id`.

## Health‑aware outbox policy

- Probe `/health` with 1–1.5s timeout; degraded when `ok=true` but memory_ok=false or high latency, or breaker_open recently observed; down otherwise.
- Degraded: flush concurrency=1, batch<=25, jittered backoff (cap 30s). Down: pause writes; probe only.
- Metrics: `somabrain.health_state{normal|degraded|down}`, `somabrain_outbox.flush_concurrency`, `somabrain.requests.breaker_open.count`.

## Waves and deliverables (6–8 weeks)

### Wave 0 – Contracts & docs (Days 1–3)
- Add schemas: runs/steps/tools/audit; extend conversation/tool with tracing.
- Docs: messaging pages; monitoring/backoff; streams/partitioning; update mkdocs nav; build docs.
- Acceptance: schema smoke PASS; mkdocs build PASS.

### Wave 1 – Memory reliability (Week 1–2)
- Outbox tables + repo; soma_client health/breaker; write‑through remember in gateway & worker; idempotent keys; user↔assistant links.
- Sync worker degraded/down logic; Redis recall cache (5 min); tool output linking; unit/integration + breaker_open load tests.
- Acceptance: bounded queue under breaker; successful drain; zero loss; links present.

### Wave 2 – Orchestrator MVP (Week 2–4)
- services/orchestrator minimal DAG; Postgres checkpoint store (versioned); start/resume/get APIs; emit runs/steps with versioning.
- Policy node; retries with jitter; node.retry_count metric; visualization hook behind flag.
- Acceptance: kill‑and‑resume passes; events + tracing correct; retries bounded.

### Wave 3 – Roles, tools, sandbox (Week 3–5)
- conf/roles.yaml; conf/policies/*.rego; hot‑reload; uniform OPA pre‑tool; agent.audit.v1 for decisions/delegations.
- Auto schema gen (docstrings); agent.tools.v1 analytics; streaming delimiters; UI progressive render; gVisor/seccomp per‑tool; hard timeouts.
- Acceptance: unauthorized calls denied + audited; tools stream; sandbox toggle operational.

### Wave 4 – Messaging, observability, CI/CD (Week 5–6)
- Tenant‑partitioned topics; publish‑time schema validation; optional Kafka Streams enricher; OTEL correlation with request_id; node metrics.
- External dashboards wired to Prometheus; SLO alerts; Helm pre‑install tables/topics; Trivy in CI; benchmark job emits agent.benchmarks.v1.
- Mode plumbing: add `/root/generate-global-env.sh`; adopt unified env_file in Compose; introduce Helm global block + overlays (dev/prod/prod_ha) and wire all service charts to globals (env, replicas, resources, Istio/Vault annotations, observability flags).
- Acceptance: invalid publishes rejected; dashboards live; alerts fire in drills; CI fails on critical CVEs.

### Wave 5 – Security & ops (Week 6–8)
- Vault JWT rotation + config watcher; Falco runtime monitor; OPA testing sandbox CLI.
- somabrain-sync CLI; remove legacy services/memory_service; runbooks & incident playbooks complete.
- Acceptance: rotation seamless; Falco events visible; memory_service removed; runbooks validated.

## Milestones & acceptance criteria

| Milestone | Wave | Description | Acceptance |
| --- | --- | --- | --- |
| M0 | 0 | Contracts + docs | Schemas + docs build PASS |
| M1 | 1 | Outbox + write‑through + recall | Breaker test bounded + drain; zero loss |
| M2 | 2 | Orchestrator MVP | Resume from checkpoint; events/traces OK |
| M3 | 3 | Roles/policy/tools/sandbox | OPA enforced; streaming; analytics live |
| M4 | 4 | Messaging/observability/CI | Validation on publish; dashboards; Trivy PASS |
|     |   | Mode propagation         | Helper script + Compose env alignment + Helm overlays wired |
| M5 | 5 | Security/ops + deprecations | Vault rotation; Falco; memory_service removed |

## Risks & mitigations

- Orchestrator complexity → Minimal DAG + strict checkpoint contract first; expand iteratively.
- OPA latency → Short‑TTL cache; batch evaluations; default‑deny on timeout with audit.
- Sandbox overhead → Per‑tool toggle; profile; isolate only high‑risk tools.
- Kafka Streams complexity → Keep optional; producer‑side enrichment baseline first.
- Token rotation issues → Canary rollout; fallback token cache; alerting.

## Governance and quality gates

- Build/Lint/Typecheck: PASS.
- Tests: unit + integration + breaker_backpressure: PASS.
- Observability: spans + external dashboards + SLO alerts verified in drills: PASS.
- Security: Trivy 0 critical; OPA tests PASS; Vault rotation verified: PASS.
- Docs: mkdocs build PASS; messaging pages up to date.
- Mode validation: CI pipeline selects overlay; all validation checklist items PASS; canary rollout/rollback observable in cluster.

---
Implementation notes for alignment

- The outbox sync worker is deployable via docker-compose and Helm (chart under `infra/helm/outbox-sync`) and must be included in the umbrella release so durable messaging runs in every environment.
- CI’s workflow `.github/workflows/deploy-soma-stack.yml` sets DEPLOY_MODE, generates `/root/soma-global.env`, chooses an overlay, lints charts, scans with Trivy, builds and pushes images, performs Helm upgrade/install with the selected overlay, executes the validation checklist, and optionally applies a canary VirtualService. Failures trigger `helm rollback` and reset traffic to 100% stable.
- For local macOS development, the helper script’s output path is retained for CI parity. Developer ergonomics are preserved by keeping existing `.env` semantics; we will stage Compose updates safely to avoid breaking local setups while ensuring CI uses the canonical file.

---
This document is the single source of truth for SomaAgent01’s upgrade program. Update alongside any scope or acceptance change and keep sprints aligned with `ROADMAP_SPRINTS.md`.
