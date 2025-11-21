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
