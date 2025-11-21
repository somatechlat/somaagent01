# 📍 Canonical Roadmap — Single Entry SomaAgent01

## 🎯 Vision
Operate SomaAgent01 through **one executable orchestrator** with **one configuration source of truth**, **one health/metrics surface**, and **zero legacy duplicates**, delivering production‑grade lifecycle control, observability, and compliance.

## 🚦 Non‑Negotiables
- **Single point of entry:** `python -m orchestrator.main` (or the orchestrator container) is the only way services start.
- **Single config:** `src/core/config` (and its shim `orchestrator/config.py`) is the only configuration API; ENV precedence is documented and tested.
- **Single health/metrics:** `/v1/health` and `/metrics` exposed once by the orchestrator; services register into it, not vice‑versa.
- **No legacy paths:** Remove `services.common.runtime_config`, duplicate orchestrators, and redundant memory/gateway entry points.
- **Real implementations only:** No fallbacks, stubs, or silent degradation.

## 🧭 Workstreams & Milestones
### 1) Orchestrator Unification (Week 1)
- Merge `ServiceRegistry` into `SomaOrchestrator`; align constructor signature and use registry for startup order/critical flags.
- Keep one health router; delete duplicate monitor/router code after integration.
- Add CI smoke (`python -m orchestrator.main --dry-run` + `/v1/health`).

### 2) Configuration Convergence (Week 2)
- Replace all imports of `services.common.runtime_config` with `orchestrator/config.py` (backed by `src/core/config`).
- Remove obsolete loaders/env helpers; document precedence in `docs/architecture.md`.
- Guardrail test that fails on new `runtime_config` imports.

### 3) Service Lifecycle Standardization (Week 3)
- Register gateway + workers (conversation, tool, memory pipeline) in `ServiceRegistry` with health adapters.
- Choose one launch mode (subprocess or in‑proc) and delete the other; ensure graceful SIGTERM.
- Mount services via the orchestrator FastAPI app; ensure `/v1/health` reflects registry state.

### 4) Gateway Decomposition (Week 4)
- Split `services/gateway/main.py` into routers + middleware per concern (chat, admin, health, tools, memory, sessions, uploads).
- Enforce ≤500 lines per module; add lint to block regressions.

### 5) Memory Path Unification (Week 5)
- Decide “single memory service” model (unified tasks under orchestrator or orchestrated subprocess set).
- Keep `UnifiedMemoryService` as schema/health owner; delete unused memory entry points after migration.

### 6) Observability & Logging (Week 5)
- Central OTLP tracing, shared Prometheus registry, structured JSON logging with request/trace correlation.
- Ensure every service registers metrics via orchestrator bootstrap; expose `/metrics` only once.

### 7) Compose/K8s Cutover (Week 6)
- Simplify `docker-compose.yaml` to **one** app container (`orchestrator`) plus infra (Kafka/Redis/Postgres/OPA); remove per‑service app containers.
- Provide Helm/K8s manifests mirroring the single entry pattern.

### 8) Validation & Release (Week 6)
- E2E smoke + load test (500 RPS target) through orchestrator; verify graceful shutdown.
- Tag `v1.0-single-entry`; publish migration notes and rollback plan.

## ✅ Success Criteria
- `python -m orchestrator.main` starts all required services deterministically; `/v1/health` green; `/metrics` scrapes combined registry.
- No references to `services.common.runtime_config`; static guardrail enforces this.
- Gateway modularized; no file >500 lines; routers/middleware separated.
- Memory services consolidated per chosen model; no duplicate entry points.
- Docker Compose contains only the orchestrator app + infra; CI smoke passes.

## 📌 Immediate Next Actions
1) Patch orchestrator to use `ServiceRegistry` end‑to‑end and remove duplicate health code.
2) Sweep codebase to drop `runtime_config` imports; add lint/test blocker.
3) Draft gateway split structure and begin extraction of health/chat/tool routers.

---

# SomaAgent01 v1.0 — Celery‑Only Architecture & Implementation Guide
**Date:** 2025-11-09 17:37:55  
**Owner:** gpubroker / Adrian Cadena  
**Audience:** Engineering, SRE, Security, Product  

> Supersedes earlier drafts that referenced Temporal/Airflow/APScheduler. Establishes Celery+Redis as the sole async engine while retaining Gateway, OPA, Prometheus, and SomaBrain.

## 0) Executive Summary & Scope
- Keep: FastAPI Gateway, OPA policy, Prometheus metrics, Redis broker/backend, SomaBrain memory.
- Adopt: Celery workers + beat, Canvas patterns (chain/group/chord), Flower for monitoring.
- Remove: Temporal, Airflow, APScheduler.
- Outcome: Deterministic, observable, policy‑guarded async execution on Celery.

## 1) Reference Architecture (Celery‑only)
Redis as broker/backend; Gateway enqueues; Celery workers process queues (`delegation`, `browser`, `code`, `heavy`, `lowprio`); Celery Beat for schedules; Flower for ops; Prometheus for metrics; OPA inline.

## 2) Dependencies (add/ensure)
`celery[redis]>=5.4.0`, `redis>=5.0.0`, `flower>=2.0.1`, `fastapi>=0.115`, `uvicorn>=0.30`, `httpx>=0.27`, `prometheus-client>=0.20`, `python-json-logger`, `structlog`, optional OTEL libs.

## 3) Celery Configuration (single source)
- Centralize broker/backend via `src.core.config` (no runtime_config shim).
- Defaults: JSON serialization, UTC, `task_acks_late`, `task_reject_on_worker_lost`, `task_default_queue=default`, visibility timeout env‑driven.
- Queue routing: map tool classes to dedicated queues; expose via settings/env.
- Tests: `task_always_eager=True` + `task_eager_propagates=True` in test config.

## 4) Scheduling (Beat only)
- Static schedules in `beat_schedule`; dynamic via DB or loader on startup.
- APScheduler removal: export cron → Celery crontab, load into Beat.

## 5) Orchestration Patterns (Canvas)
- Chain for sequences; group+chord for fan‑out/fan‑in; map/starmap for bulk.
- Enforce idempotency with Redis SET NX dedupe keys; validate inputs/outputs.
- Prefer chord for deterministic aggregation.

## 6) Module Implementation Targets
- Gateway: POST actions enqueue Celery Canvas; GET run status via `AsyncResult`.
- Tasks: `delegate` (OPA gated, retries, dedupe), `browser.fetch_page`, `aggregate_summaries`, etc.
- Metrics: counters/histograms per task; worker `/metrics` exporter.
- Observability: JSON logs with request_id/tenant/task_name; Flower for UI.

## 7) Deployment (dev/stage/prod)
- Compose: redis, gateway, `celery-worker`, `celery-beat`, `flower`, opa.
- Orchestrator alignment: either start worker/beat as orchestrated subprocesses or keep infra containers but remove legacy service entries once orchestrator controls lifecycle.

## 8) Reliability & Backpressure
- Queue per class; concurrency caps per queue; rate limits; backoff retries.
- Visibility timeout ≥ worst case runtime; `acks_late` + `time_limit`.
- Dead letters: persist failures, add reprocessor.

## 9) Security & Policy
- OPA deny‑by‑default; allowlisted sub‑agent/tool domains.
- Tenant propagation headers; payload validation; size/time limits.

## 10) Testing & CI
- Unit: eager mode; assert OPA denials, dedupe hits, retries.
- Contract: A2A JSON in/out contracts.
- Load: group/chord at scale; ensure no starvation.
- CI smoke: `celery -A initialize.celery_app inspect ping`; orchestrator dry‑run + `/v1/health`.

## 11) Migration & Rollout (weeks)
1. Deps + heartbeat; prove infra.  
2. Beat migration (all schedules).  
3. Delegation via Celery canary.  
4. Metrics/alerts + Flower.  
5. Flip flag, remove APS/Temporal; tag v1.0‑celery.

## 12) Acceptance / SLOs
- ≥99% task success; p95 delegate latency ≤3s (excl. sub‑agent).
- OPA denials block tasks; metrics exposed; Flower healthy; Beat on time.

---

# Celery Integration Gaps & Actions (2025-11-21 update)
The following consolidates the historical Celery design notes and the latest gap analysis. It is additive to the Celery-only guide above and drives the remaining work.

## Current Gaps
1. Worker package stub only; full worker code and task modules missing.  
2. Core tasks absent (`build_context`, `evaluate_policy`, `store_interaction`, `feedback_loop`, `rebuild_index`, `publish_metrics`, `a2a_chat_task`).  
3. Broker/result config incomplete in compose; Redis service not wired for Celery.  
4. FastAPI routes to dispatch Celery tasks missing/incomplete.  
5. Prometheus task metrics exporter not implemented.  
6. Error-handling patterns (retries/backoff/circuit breaker) not coded.  
7. Deployment artifacts missing (Celery worker Dockerfile, Helm values, CI scripts).  
8. Tests missing (unit/integration/e2e with compose).  
9. Note: if Celery is deprecated later, archive stubs and remove from codebase.

## Required Actions (keep Celery)
- Create Celery app factory in `services/celery_worker/` with broker/backend from `src.core.config`; remove any legacy shims.  
- Implement the core tasks listed above with idempotency, retries, backoff, pybreaker around external calls, and Prometheus counters/histograms.  
- Add `celeryconfig`/settings plus compose services for Redis, Celery worker, beat, Flower; align Helm values and CI.  
- Add FastAPI router (`/api/celery/*`) to enqueue tasks via `apply_async` and expose `GET /v1/runs/{task_id}` using `AsyncResult`.  
- Add dead-letter handling (Redis key/queue) and metrics exporter (port 9510).  
- Write tests: eager mode unit tests for tasks, integration via compose (gateway↔redis↔worker↔prometheus), and CI “celery inspect ping”.  
- Document deprecation path: if Celery is to be removed, delete stubs and update CLEANUP notes instead of leaving dead code.

## If Celery is to be removed
- Remove stubs and compose/Helm entries; reflect in cleanup docs; keep this section as historical context only.
