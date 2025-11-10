# Dev–Prod Parity Roadmap (High Priority)

Purpose: run the entire platform locally with production behavior (security, data flows, observability) while right‑sizing resources for a single machine. No test bypasses, no hidden relaxations, no legacy fallbacks. Everything on; only smaller.

## Principles
- Production posture: auth required, policy enforced, durable write paths, auditability, SSE‑only, no polling.
- Single source of truth: settings via facade + registry; avoid scattered `os.getenv` reads.
- Deterministic & observable: health‑gated startup, structured logs, metrics, and traces across all hops.
- Minimal footprint: reduce partitions/concurrency/pools; retain correctness and failure modes.

## Current Snapshot (as observed)
- Gateway up; chat POST ok; SSE enabled. Policy selective gates active → 401/403 on unauthenticated UI calls (expected).
- Conversation Worker / Tool Executor / Memory Replicator running; need end‑to‑end validation for memory write/recall and tool lifecycle.
- OPA container running; real denies observed; no bypass in dev compose.
- Somabrain integration available (weights/context); recall/flags not yet exercised in smoke.
- Env centralization incomplete; many direct `os.getenv` calls.

## Acceptance Criteria (Dev–Prod Mode)
- All services healthy with single `make dev-up` + health gate. `/v1/health` reflects policy/DB/Kafka/OPA/Somabrain readiness.
- Auth + policy enforced for conversation.send, tool.execute, memory.write, scheduler CRUD, OperationsAdministration.
- UI authenticated; chat streams via SSE; uploads return attachment ids; scheduler CRUD works; no polling/legacy endpoints.
- Durable memory: local Postgres + WAL/outbox; replicator healthy; DLQ lag visible.
- Somabrain calls in the loop: weights, context build, reward updates, flags, recall; failures degrade clearly with metrics & audit.
- Observability: metrics counters/histograms present; distributed traces span Gateway→Worker→Somabrain→back; no secrets in logs.

## Resource Scaling (Local Defaults)
- Kafka: topics 1 partition, RF=1; acks=all; small linger.
- Postgres: pool 5–10; statement timeout 10–30s.
- Redis: modest max clients; short TTL for transient keys.
- Celery: workers 1–2; prefetch=1; visibility timeout moderate.
- Circuit breakers: fail_max=3, reset_timeout=30s.
- Processes: single uvicorn/worker process; small thread pools.
- Tracing: small batch exporters; Prometheus on localhost.

## Required Env Overlay (illustrative)
- Gateway/UI: `GATEWAY_PORT=21016`, `GATEWAY_BASE_URL=http://localhost:21016`, `WEB_UI_BASE_URL=http://localhost:21016/ui`
- Infra: `POSTGRES_DSN=...`, `REDIS_URL=...`, `KAFKA_BOOTSTRAP_SERVERS=localhost:9092`
- Security: `REQUIRE_AUTH=true`, `OPA_URL=http://opa:8181`
- Somabrain: `SOMA_BASE_URL=http://host.docker.internal:9696`
- Observability: `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`, metrics host/port
- Celery: `CELERY_BROKER_URL=redis://redis:6379/0`, `CELERY_RESULT_BACKEND=redis://redis:6379/0`, `CELERY_WORKER_CONCURRENCY=1`

## Sprints (Parallel Where Safe)

### DP0 — Foundation & Health Gating (1–2d)
- Tasks: single compose profile; health‑wait gating; topic/schema init; startup summary logging (active features, scaled caps).
- Acceptance: `make dev-up && make health-wait` → Gateway `/v1/health` reports ready including policy and Somabrain; startup summary printed.

### DP1 — Auth & Policy in UI (1d)
- Tasks: dev API key issuance; UI fetch layer sends bearer/cookie; verify policy allow/deny with structured logs and metrics.
- Acceptance: scheduler/settings/file ops return 2xx (authorized); `auth_decisions_total` shows allow/deny as expected.

### DP2 — Somabrain Full Loop (2–3d)
- Tasks: wire recall in conversation path (feature‑flagged), ensure weights/context build, reward updates, tenant flags merge; add metrics: `somabrain_requests_total`, latency histograms.
- Acceptance: chat invokes Somabrain endpoints; failures degrade explicitly; metrics/trace attributes show endpoints and status.

### DP3 — Observability Expansion (1d)
- Tasks: enrich spans (request_id, session_id, tenant); add gauges for WAL/outbox lag, DLQ depth, consumer lag; dashboards baseline.
- Acceptance: traces link across services; Prometheus shows lag and decision metrics; no PII/secrets in logs.

### DP4 — Config Centralization (2–3d, rolling)
- Tasks: migrate high‑impact env reads (db/kafka/redis/auth flags/uploads/speech) to facade; add linter/test to forbid stray `os.getenv`.
- Acceptance: grep outside allowed modules → zero; `/v1/runtime-config` sourced from facade only.

### DP5 — Scheduler Canonicalization (1d)
- Tasks: add canonical `/v1/ui/scheduler/*` (list/create/update/run/delete/history); deprecate legacy paths; audit log entries.
- Acceptance: UI uses `/v1/ui/scheduler/*`; audit entries present; policy enforced.

### DP6 — Memory Durability Validation (1d)
- Tasks: chaos test SomaBrain outage → verify WAL/outbox retries and replica sync; expose lag/health in `/v1/health`.
- Acceptance: messages persist and reconcile; health reflects degraded/ok; alerts (metrics) increment.

### DP7 — CI Parity Jobs (1d)
- Tasks: add matrix: dev‑prod stack smoke (API + UI), metrics scrape, trace presence; golden UI mode retained.
- Acceptance: CI green on parity checks; artifacts (screenshots/traces) optional.

## Parallelization Guidance
- Run DP0 → DP1 sequentially (foundation + auth). DP2/DP3/DP5 can proceed in parallel by different owners. DP4 runs as rolling refactor. DP6 after core loops pass; DP7 last.

## Runbook (Operator‑Facing)
- Start: `make dev-up && make health-wait`
- Verify:
  - `curl -s http://localhost:21016/v1/health | jq`
  - `curl -s http://localhost:21016/metrics | head`
  - `curl -s "$SOMA_BASE_URL/healthz"`
- UI: ensure dev token present; load `WEB_UI_BASE_URL`; send chat; test uploads, scheduler CRUD.

## Metrics & Alerts (minimum set)
- Auth/Policy: `auth_decisions_total{action,result}`, `auth_duration_seconds`
- Somabrain: `somabrain_requests_total{endpoint,status}`, latency
- Memory: WAL/outbox attempts/results, replica lag, DLQ depth
- Streaming: time‑to‑first token, assistant tokens total
- Kafka: consumer lag, publish failures

## Risks & Mitigations
- UI auth gaps → seed dev token or enable local login; never disable policy.
- Policy latency → short TTL cache + breaker; fail‑closed with clear errors.
- External dependency outages → degrade explicitly; surface in metrics and health.
- Env drift → facade + linter; audit config diffs.

## Definition of Done
- One‑command local stack with production behavior; all protected flows authorized and audited; SSE chat + tools + scheduler working; Somabrain in the loop; metrics/traces comprehensive; config centralized for critical paths; CI parity job green.

## Ownership & Governance
- Changes that alter posture or routes must update this roadmap first. Every sprint closes with acceptance checks and a brief ops note.
