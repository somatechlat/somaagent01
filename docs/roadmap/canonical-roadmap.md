# Central Configuration Architecture (Planned Consolidation)

Objective: Eliminate scattered environment variable access and ad‑hoc flag checks by introducing a single, layered configuration access surface consumed everywhere (gateway, workers, UI support code). No direct `os.getenv` calls remain in business logic after migration – only within the configuration loader.

Layers & Precedence (highest wins):
1. Dynamic Overrides: Runtime config documents delivered via Kafka (or future Somabrain config endpoint) and applied through `ConfigRegistry.apply_update()`.
2. Environment Variables: 12‑factor compliance; provide non-secret overrides at container start.
3. Defaults: Versioned static defaults derived from `SA01Settings.environment_defaults()` and seed config documents.

Core Components:
- `SA01Settings` (static/base): Environment‑aware service connection defaults (Postgres/Kafka/Redis/OPA/metrics). Provides stable base and environment mapping.
- `ConfigRegistry` (dynamic): Validates and stores a JSONSchema-backed snapshot (`registry.v1.schema.json`), notifies subscribers, and exposes consistent shape for application consumption.
- `FeatureRegistry`: Pure in‑memory projection of feature descriptors + profile; will be driven by dynamic overrides (e.g., profile change, forced enable/disable list) once merged with `ConfigRegistry`.
- `RuntimeConfigFacade` (new planned module): Single import point (`from services.common.runtime_config import cfg`) exposing read‑only helper methods: `cfg.db()`, `cfg.kafka()`, `cfg.redis()`, `cfg.feature('token_metrics')`, `cfg.flag('embeddings_ingest')`, `cfg.policy()`, `cfg.somabrain()`, `cfg.profile()`. Internally composes SA01Settings + registry snapshot + computed feature states.
- Metrics Layer: Prometheus gauges/counters updated from a single periodic refresher (`cfg.refresh_metrics()`), replacing per‑module self‑updates.

Design Principles:
- Fail‑Closed for Sensitive Domains: If dynamic override layer is unavailable, security‑critical values (policy fail‑open, masking enablement) revert to conservative defaults explicitly defined in SA01Settings.
- Immutable Read Surface: Callers cannot mutate configuration dictionaries; updates only occur via validated registry documents.
- Deterministic Hashing: Each effective merged snapshot publishes a `config_effective_checksum` metric for change detection and alerting.
- Single Path for Flags: All feature/flag queries route through `cfg.flag()` which first resolves remote tenant override cache → registry descriptor → fallback default.
- Zero Direct Env Access: A linter rule (planned) prohibits `os.getenv(` outside configuration and bootstrap modules.

Access Flow:
```
Incoming Kafka config event → deserialize → ConfigRegistry.apply_update() → recompute merged snapshot (defaults + env + dynamic) → update FeatureRegistry overlay → emit metrics + trigger subscribers → RuntimeConfigFacade exposes new view.
```

Planned Migration Steps:
1. Inventory all `os.getenv` usages (gateway, session_repository, embeddings, features, tool executor).
2. Introduce `runtime_config.py` with facade & merge logic (no behavior change yet; shadow reads).
3. Replace direct env reads with facade methods (batch by domain: database, kafka, redis, feature flags, masking, policy, embeddings).
4. Integrate dynamic overrides (config update listener) and publish `config_effective_checksum` metric.
5. Enforce linter rule + add unit test `test_no_direct_getenv.py` blocking straggler `os.getenv` references.
6. Update `/v1/runtime-config` endpoint to source exclusively from facade (deprecate internal recomputation).

Metrics To Add:
- `config_effective_checksum` (Gauge – last applied checksum)
- `config_layer_source_total{layer}` (Counter – counts of accesses hitting dynamic|env|default)
- `feature_flag_resolution_total{source}` (Counter – local|remote|cache_miss|cache_hit)
- `config_update_latency_seconds` (Histogram – time from receipt to facade publication)

Risk & Mitigations:
- Stale Overrides: Use checksum comparison + optional monotonic `version` to reject regressions.
- Partial Documents: JSONSchema requires explicit fields; missing keys fall back to defaults predictably.
- Tenant Explosion (flag cache size): Introduce size‑bounded LRU for per‑tenant overrides with eviction metric.
- Deployment Drift: Print merged snapshot summary at startup and include checksum in `/health/summary` for observability.

Acceptance Criteria (Centralization Complete):
- Grep for `os.getenv(` outside allowed modules returns zero.
- `/v1/feature-flags` effective states match facade outputs for sampled features (golden test).
- Dynamic config update triggers metric change and subscriber callback without error.
- Single import `cfg` used in all new code paths for settings/flags.

Next Sprint Integration: This architecture underpins L2 (Learning & Context) by enabling remote toggles for experimental learning weight adjustments and context build heuristics without re-deploy.

# 📍 Canonical Roadmap – somaAgent01
*Merged with Agent-Zero architectural insights – 2025-11-08*

---

## 0️⃣ Executive Summary
This is the **single source of truth** for the post-merge, centralised architecture of **somaAgent01** after integrating the best patterns from *Agent-Zero*.  
We now have **zero import-time side-effects**, **deterministic middleware**, **test-friendly singletons**, and a **clear separation of concerns**.

---

## 1️⃣ Vision & Success Criteria
| Goal | Description | Success Metric |
|------|-------------|----------------|
| **Single source of truth** | All external services (Somabrain, OPA, Kafka, Postgres, etc.) are accessed through **registry singletons** that live in a dedicated `integrations/` package. | Every module imports `from integrations.service> import singleton>`; no direct `httpx`, `kafka-python`, `psycopg2` usage outside the registry. |
| **Zero import-time side-effects** | Background workers, DB pools, Kafka producers, and Prometheus metrics are **lazy-initialised** in FastAPI startup hooks or explicit `init()` calls. | Test suite runs with `settings.testing=True` without “event loop already running” or connection errors. |
| **Deterministic middleware stack** | OPA, auth, request-id, and observability middleware are registered **once** and configured from the central `settings` object. | No `NameError` for stale factories; auth tests receive the expected `HTTPException`. |
| **Observability-first** | All request/response paths emit structured logs, request-id correlation, and Prometheus metrics defined in a single `observability/metrics.py`. | Prometheus endpoint `/metrics` contains `somabrain_requests_total`, `gateway_http_requests_total`, etc. |
| **Test-friendly & extensible** | The architecture supports unit- and integration-testing with simple monkey-patching of the singleton objects. | All existing tests (≈ 300) pass after the refactor. |
| **Clear documentation & diagram** | A single markdown file (`docs/roadmap/canonical-roadmap.md`) describes the whole system, the layers, and the data-flow. | New contributors can read the file and understand where to add a feature in 5 minutes. |

---

## 2️⃣ Target State – Layered Architecture
```
src/
├─ config/
│   ├─ __init__.py               # expose `settings`
│   └─ settings.py               # Pydantic BaseSettings – immutable singleton
├─ integrations/
│   ├─ __init__.py               # expose public singletons
│   ├─ somabrain/
│   │   ├─ __init__.py           # `client = SomabrainClient()`
│   │   └─ client.py             # async httpx wrapper
│   ├─ opa/
│   │   ├─ __init__.py           # `policy = EnforcePolicy(...)`
│   │   └─ middleware.py         # class EnforcePolicy
│   ├─ kafka/
│   │   └─ producer.py           # lazy-init KafkaProducer singleton
│   └─ postgres/
│       └─ pool.py               # asyncpg pool singleton
├─ observability/
│   ├─ __init__.py
│   ├─ metrics.py                # factories + all metric objects
│   └─ logging.py                # structured logger with request-id
├─ services/
│   └─ gateway/
│       ├─ __init__.py
│       ├─ app.py                # FastAPI instance, routes, startup/shutdown
│       └─ dependencies.py       # FastAPI Depends helpers
├─ main.py                       # uvicorn services.gateway.app:app
└─ docs/
    └─ roadmap/
        └─ canonical-roadmap.md  # ← this file
```

---

## 3️⃣ Key Patterns & Communication
| Pattern | Where used | Description |
|---------|------------|-------------|
| **Configuration singleton** | `config/settings.py` | `settings = Settings()` loaded once; all env vars typed & validated. |
| **Integration registry** | `integrations/__init__.py` | Exposes `somabrain_client`, `opa_policy`, `kafka_producer`, `pg_pool`. |
| **Lazy startup hooks** | `services/gateway/app.py` | Background services start only when `settings.testing=False`. |
| **Deterministic middleware** | `app.add_middleware(opa_policy.__class__, fail_open=settings.policy_fail_open)` | Registered **once**, no duplicate factories. |
| **Observability layer** | `observability/metrics.py` | Centralised Prometheus metrics; `request-id` propagated in logs. |
| **Test isolation** | `pytest.ini` sets `TESTING=1` | Background services skipped; singletons can be monkey-patched. |
| **Event bus** | `services/common/event_bus.py` (existing) | Decoupled domain events between workers. |

---

## 4️⃣ Detailed Implementation Roadmap
| Milestone | Description | Owner | Duration | Acceptance Criteria |
|-----------|-------------|-------|----------|---------------------|
| **M0 – Baseline** | Freeze current `main` branch, ensure CI passes. | – | 0 d | CI green on `prune/auto-cleanup` (expected failures noted). |
| **M1 – Config Layer** | Create `config/settings.py`, replace all `os.getenv` with `settings`. | Senior Backend | 1 d | No `os.getenv` left; `settings` imported everywhere. |
| **M2 – Integration Registry** | Move Somabrain client, OPA middleware, Kafka producer, Postgres pool into `integrations/` singletons. | Senior Backend | 2 d | Every module imports from `integrations.service>`; tests can `monkeypatch` singleton. |
| **M3 – Observability Core** | Create `observability/metrics.py` with factories first, then metric objects. | Observability Engineer | 1 d | Importing any module no longer raises `NameError`. |
| **M4 – FastAPI Refactor** | Rewrite `services/gateway/app.py` to use singletons, clean middleware, add startup/shutdown. | Senior Backend | 2 d | `uvicorn services.gateway.app:app` starts; `/docs` & `/metrics` work. |
| **M5 – Test-Mode Guard** | Add `settings.testing` flag; guard background service startup. | QA Engineer | 1 d | `pytest -q` runs without external services; no “event loop” errors. |
| **M6 – Auth & OPA Alignment** | Adjust `EnforcePolicy` to respect `settings.require_auth` and `settings.policy_fail_open`. | Security Engineer | 1 d | `tests/unit/test_gateway_authorization.py` passes with expected `HTTPException`. |
| **M7 – Documentation Overhaul** | Populate this file with diagram, layer description, and step-by-step guide. | Technical Writer | 1 d | New contributors can locate `integrations.somabrain.client` in 5 min. |
| **M7.5 – Pixel-Perfect UI Parity** | Copy golden CSS, fonts, spacing, icons; map canonical SSE events to golden DOM structure; dual-mode Playwright suite. | Frontend + QA | 3 d | Playwright `parity.spec.ts` passes both `GATEWAY_BASE_URL` and `http://localhost:7001` modes with 1px diffs. |
| **M8 – Full Test Run & Fixes** | Run entire suite, fix residual import errors, update mocks. | QA Engineer | 2 d | **0 failures** (unit + integration tests). |
| **M9 – CI/CD Integration** | Add lint (`ruff`), type-check (`mypy`), and startup verification. | DevOps Engineer | 1 d | GitHub Actions passes on every PR. |
| **M10 – Release** | Tag `v0.1.0-centralised`; push to `master`. | Release Manager | 0.5 d | Release notes include “centralised integration registry”. |

**Total estimated effort:** ~ 12 person-days.

---

## 5️⃣ Communication & Data Flow
```
┌────────────┐     ┌──────────────────────┐
│   Client   │────▶│  FastAPI Gateway     │
└────────────┘     │   (app.py)           │
                   │  – middleware        │
                   │  – routes            │
                   └──────────┬───────────┘
                              │
              ┌───────────────┴───────────────┐
              │  integrations singletons      │
              │  - somabrain_client           │
              │  - opa_policy                 │
              │  - kafka_producer             │
              │  - pg_pool                    │
              └───────────────┬───────────────┘
                              │
                   ┌──────────┴───────────┐
                   │ External Services    │
                   │ - Somabrain Brain    │
                   │ - OPA Service        │
                   │ - Kafka Cluster      │
                   │ - Postgres           │
                   └──────────────────────┘
```

---

## 6️⃣ Post-Merge Checklist (tick when done)
- [ ] `config/settings.py` created and all env reads migrated.  
- [ ] `integrations/` folder created; all singletons exposed via `__init__.py`.  
- [ ] `observability/metrics.py` centralises all metric creation.  
- [ ] `services/gateway/app.py` uses only public singletons; no import-time side-effects.  
- [ ] CI passes (`pytest -q`, `ruff`, `mypy`, Docker build).  
- [ ] Documentation (this file) reflects final state and is peer-reviewed.

---

## 7️⃣ Next Steps
1. Create the new folder structure (`config/`, `integrations/`, `observability/`).  
2. Move the first integration (`somabrain`) and run the test suite.  
3. Iterate per milestone until M10 is complete.  
4. Tag release `v0.1.0-centralised` and merge to `master`.

---

*This canonical roadmap supersedes any prior partial roadmaps and should be the only living document describing the overall architecture.*

## 📚 Integration of Celery into somaagent01 (Canonical)

Version: 1.0 – 2025‑11‑08
Audience: Developers, DevOps engineers, and security auditors working on the somaagent01 code‑base.

Table of Contents
Why Celery?
High‑Level Architecture
Prerequisites & Dependencies
Code Layout & Core Components
FastAPI Scheduler API
LLM Tool – schedule_task_celery
Security – JWT Middleware & Scope Enforcement
Observability – Prometheus Metrics
Docker‑Compose Deployment
Feature‑Flag Switching (APScheduler ↔ Celery)
Migration from APScheduler to Celery
Testing Strategy
Roll‑out Checklist
Appendix – Example Payloads & cURL snippets

1️⃣ Why Celery?
Reason	Benefit for somaagent01
Distributed workers	Heavy or long‑running tasks (model inference, large downloads) run in separate processes, keeping the LLM‑agent responsive.
Reliable delivery & retries	Guarantees at‑least‑once execution, automatic exponential back‑off, dead‑letter queues – essential for production automation.
Cron / periodic jobs	Celery Beat provides a robust, persistent scheduler that survives container restarts.
Task chaining & workflows	Canvas primitives (chains, groups, chords) enable multi‑step pipelines (e.g., fetch → process → store).
Horizontal scalability	Adding more workers is just a new container – linear scaling.
Existing stack compatibility	The project already uses Redis for other services; Celery works natively with Redis as broker + backend.

When to adopt?

When you have long‑running or CPU‑heavy jobs.
When you need retries, dead‑letter handling, or task chaining.
When you anticipate scaling the system horizontally.
For simple low‑frequency cron jobs you can keep using APScheduler (lighter).

2️⃣ High‑Level Architecture
+-------------------+      +-------------------+      +-------------------+
|   FastAPI (agent)   | → |   Celery Beat      | → |   Celery Workers   |
+-------------------+      +-------------------+      +-------------------+
        ^                         ^                         ^
        |                         |                         |
        |   Redis broker (queues)  |   Redis result store    |
        +-----------------------------------------------------+

FastAPI (the existing agent server) exposes a /api/celery/* REST API for job CRUD.
Celery Beat enqueues periodic jobs; Celery Workers execute tasks and post results.
Redis acts as broker and optional result backend.

3️⃣ Prerequisites & Dependencies
- Redis available for broker + result backend
- Celery 5.x, celery[redis]
- FastAPI and Pydantic (already present)
- Prometheus client for metrics

4️⃣ Code Layout & Core Components
- celery_app/: Celery application factory and tasks registration
- scheduler/: API adapters for APScheduler and Celery modes
- extensions/: `schedule_task_celery` tool wrapper for LLM-triggered tasks
- services/gateway/main.py: feature-flag wiring, runtime-config surface, API router include

5️⃣ FastAPI Scheduler API (Unified)
- GET /v1/ui/scheduler/jobs – list
- POST /v1/ui/scheduler/jobs – create
- PUT /v1/ui/scheduler/jobs/{id} – update
- POST /v1/ui/scheduler/jobs/{id}/run – run now
- DELETE /v1/ui/scheduler/jobs/{id} – delete
- GET /v1/ui/scheduler/runs?job_id=&cursor= – history

6️⃣ LLM Tool – schedule_task_celery
- Thin wrapper selecting APScheduler or Celery implementation based on feature flag
- Validates payload, enqueues job, returns job id and trace

7️⃣ Security – JWT Middleware & Scope Enforcement
- Scopes: scheduler:read, scheduler:write, scheduler:run
- Optional OPA tenant policies
- Audit log for CRUD and run-now actions

8️⃣ Observability – Prometheus Metrics
- scheduler_jobs_total
- scheduler_runs_started_total / success_total / failure_total
- scheduler_run_duration_seconds (histogram)
- Celery queue depth gauge (broker)

9️⃣ Docker‑Compose Deployment
- Add celery_worker and celery_beat services
- Configure USE_CELERY/SCHEDULER_USE_CELERY, Redis URL, concurrency

🔟 Feature‑Flag Switching (APScheduler ↔ Celery)
- Env/config flag `SCHEDULER_USE_CELERY`
- Runtime-config projects `scheduler.enabled` and `scheduler.use_celery` to UI

1️⃣1️⃣ Migration from APScheduler to Celery
- Export current jobs → JSON, transform → Celery Beat entries
- Validate counts, enable flag, rollback path documented

1️⃣2️⃣ Testing Strategy
- Unit (validators, wrapper), Integration (API + Celery), E2E (compose), Load, Security

1️⃣3️⃣ Roll‑out Checklist
- Code review, CI, staging with flag off → on, smoke tests, security audit, observability check, migration run, rollback tested, production deploy, post‑deploy review

📎 Appendix – Example Payloads & cURL snippets
- Job creation payload, cURL for create/list/run

📌 Final notes
- Feature‑flag enables gradual rollout; code is modular to swap Celery if needed later.

End of documentation.


========================
Centralize Gateway / UI URLs (Immediate action)
========================

Decision (explicit)
- Canonical Gateway host port: 21016 (the UI must be reachable at http://localhost:21016/ui/index.html).
- Canonical environment variables (reuse existing names):
  - `GATEWAY_PORT` (numeric, default 21016)
  - `GATEWAY_BASE_URL` (full URL, e.g. http://localhost:21016)
  - `WEB_UI_BASE_URL` (UI entry, e.g. http://localhost:21016/ui)

Rationale
- Many tests, scripts and docs contained hard-coded values (21016, 20016, 8010, and literal http://127.0.0.1 URLs). This causes runtime confusion. The project already uses `GATEWAY_PORT` and `GATEWAY_BASE_URL` in places; we will standardize on them and prefer `WEB_UI_BASE_URL` for UI consumers.

Immediate plan (no new systems, minimal edits)
1. Ensure `.env` / `.env.example` contains the canonical variables (set `GATEWAY_PORT=21016`, `GATEWAY_BASE_URL=http://localhost:21016`, `WEB_UI_BASE_URL=http://localhost:21016/ui`).
2. Replace hard-coded URL fallbacks in tests, scripts, and webui test configs to prefer `WEB_UI_BASE_URL` → `GATEWAY_BASE_URL` → derived `http://localhost:${GATEWAY_PORT}`. Exact files to update include (representative):
   - `tests/e2e/*.py`, `tests/playwright/*.py`, `tests/ui/*`
   - `webui/playwright.config.ts` and `webui/tests/*.spec.ts`
   - `scripts/e2e_quick.py`, `scripts/ui-smoke.sh`, `scripts/check_stack.sh`
   - `python/api/*` modules that fallback to `http://localhost:20016` or `http://127.0.0.1:21016`
   - `.vscode/tasks.json` and Makefile examples
   - docs under `docs/*` and generated `site/*` that embed http://localhost:21016 or other literal ports
3. Remove clearly broken / redundant artifacts that confuse developers and standardize on the single compose manifest.
4. Verify by running the dev stack and smoke tests (see "Verification" below).

Safety & VIBE constraints
- No new configuration systems or helper files will be introduced. Edits reuse existing env variables and the repo's helpers.
- Files will be archived before removal so the operation is reversible.
- Changes will be committed directly to the working branch per your instruction (no extra branches), with a single clear commit and changelog.

Verification
- Bring up the dev stack (with `GATEWAY_PORT=21016`) and confirm:
  - The UI is reachable at `http://localhost:21016/ui/index.html`.
  - `curl -s http://localhost:21016/v1/health` returns 200 and expected JSON status.
  - Run `pytest -q tests/e2e/test_api_contract_smoke.py` — passes or at least successfully performs the POST and opens SSE.
  - Run the Playwright UI smoke `./scripts/ui-smoke.sh ${WEB_UI_BASE_URL}` to validate UI load and network behavior.

Post-conditions
- All literal host:port occurrences for Gateway/UI should be removed except in docs examples that explicitly show how to set the env variables (those will show variables not raw URLs).
- `archive/` will contain the moved/archived files for safe undo.

## Canonical Roadmap — Auditability, Observability, and Perfect Memory

This is the living, canonical roadmap for building SomaAgent01 into an auditable, observable, and traceable agentic platform with perfect message persistence and recall via SomaBrain. It is grounded in the current infrastructure and codebase.

### Vision and Non‑Negotiables

- Every interaction is auditable: we can answer who/what/when/why/how for any message, tool call, or LLM response.
- End-to-end traceability: a single trace follows a request across UI → Gateway → Workers → Providers → SomaBrain.
- Perfect memory: all user and assistant messages are durably persisted and available for high-quality recall in SomaBrain.
- Security by default: least privilege, encrypted by default, policy enforced (OPA/OpenFGA), and no plaintext secrets in logs.
- Production-grade reliability: idempotent processing, backpressure, retries with budgets, and SLOs with actionable alerts.

## System Overview (as-built)

Core services (verified under `services/`):
- `gateway`: FastAPI edge API handling UI, settings, uploads, LLM invoke (/v1/llm/invoke[/stream]), SSE/WS, and write-through to SomaBrain.
- `conversation_worker`: Consumes inbound chat events, orchestrates tools, streams responses via Gateway invoke, and writes memories.
- `tool_executor`: Executes registered tools deterministically; reports tool_call events.
- `ui`: SPA served directly by Gateway; SSE streaming for chat updates.
- `memory_service`, `memory_replicator`, `memory_sync`, `outbox_sync`: Durable memory pipeline (WAL/outbox) and replica sync.
- `delegation_gateway`, `delegation_worker`: Delegated agent flows (if enabled).

Foundational infra:
- Kafka (event backbone), Redis (state/cache), Postgres (durable store), Vault/Env (secrets), OpenFGA (authz), OPA (policy), OpenTelemetry (traces/metrics/logs), Prometheus (metrics), Grafana/Tempo/Loki (observability).
- SomaBrain reachable at `http://host.docker.internal:9696` via `SOMA_BASE_URL` (Compose).

Centralized configuration and tools:
- Gateway hosts a central Tool Catalog and runtime config. It provides:
	- A single registry of tools, schemas, and per-tenant enable flags and execution profiles (timeouts, concurrency, resource limits).
	- A UI-safe runtime config projection (`/v1/runtime-config`) and a public tool list (`/v1/tools`) without secrets.
	- Distribution to services via ETag/TTL-cached internal endpoints. Services fail closed if the catalog is unavailable (strict mode).
	- Provider secrets centralized in Gateway; services invoke providers through Gateway, not with raw keys.

## Data and Event Contracts (canonical)

Identifiers and correlation:
- `request_id`: client-generated or edge-assigned; returned to client.
- `trace_id`/`span_id`: W3C Trace Context propagated via `traceparent` header and Kafka headers.
- `session_id`, `message_id`, `tool_call_id`, `memory_id`: UUIDv4; unique across services.
- `idempotency_key`: for POSTs that may be retried (e.g., message send), also carried in Kafka headers.

Canonical message envelope (Kafka and internal HTTP JSON):
- `meta`: { request_id, trace_id, idempotency_key, tenant_id, user_id, session_id, created_at }
- `payload`: one of `message.user`, `message.assistant`, `tool.call`, `tool.result`, `llm.request`, `llm.delta`, `llm.complete`, `memory.write`, `memory.recall`, `error`.
- `version`: schema version, starting at `v1`.

Persistence contract:
- All `message.user` and `message.assistant` events must be persisted in Postgres and written through to SomaBrain; outbox/WAL ensures durability and at-least-once delivery; consumers implement idempotency.
- Attachments are referenced by stable URIs: `/v1/attachments/{id}`; metadata saved with content hash and MIME.

Attachment ingestion contract:
- All ingestion paths use `attachment_id` (no filesystem paths). A service-only fetch streams content from Gateway (policy-enforced; tenant-scoped).
- The `document_ingest` tool accepts `{ attachment_id, tenant_id, content_type?, size_bytes? }` and returns `{ text, metadata }` with extraction details.
 

SSE/WS streaming contract:
- Streamed events carry `event` and `data` fields; `data` includes `meta` fields above.
- Event types: `llm.delta`, `llm.complete`, `tool.call`, `tool.result`, `error`, `heartbeat`.

## Traceability and Observability

OpenTelemetry propagation and spans:
- Ingress: generate/accept `request_id` and `traceparent`; start `gateway.receive` span.
- Gateway → Worker: include `traceparent`, `request_id`, `idempotency_key` in Kafka headers.
- Worker → Gateway Invoke → Provider: propagate `traceparent`; spans: `worker.handle_message`, `gateway.llm.invoke`, `provider.api.call`.
- Memory write-through: `memory.write` span encloses Postgres insert, WAL publish, SomaBrain HTTP call.

Metrics (Prometheus):
- QPS/latency/error for: `/v1/session/message`, `/v1/llm/invoke`, tool executions, memory writes and recalls.
- Budgets: retry counts, DLQ depth, outbox lag, replica lag.
- Cost: token usage by provider/model; per-tenant caps.

Logs:
- Structured JSON with `level`, `timestamp`, `message`, `request_id`, `trace_id`, `session_id`, `user_id`, `tenant_id`.
- No secrets, no PII beyond stable IDs; redact payloads as needed (configurable).

## Security Model

- AuthN: session cookies or OIDC; browser calls use same-origin cookies or header/bearer tokens. No custom CSRF endpoint.
- AuthZ: OpenFGA for resource relations; OPA for policy gates (e.g., tool allowlist, PII egress checks).
- Secrets: provider API keys stored centrally; never logged; access via internal credentials endpoint with internal token.
- Transport: HTTPS/TLS; internal mTLS optional; WAF headers and strict CORS for UI.
- Data protection: PII minimization, column-level encryption for sensitive fields, backup/restore tested.

## SomaBrain Integration (Perfect Memory and Recall)

- Write-through path: Worker persists messages locally and calls SomaBrain over `SOMA_BASE_URL` with retries and idempotency.
- Outbox/WAL: if SomaBrain temporarily unavailable, retry with exponential backoff; replicas reconcile via `memory_replicator`.
- Recall: Provide `recall(query|ids|context_window)` call surfaces in Gateway; Worker may fetch recall context pre-LLM invoke.
- Feedback: Store user feedback signals (helpful/not helpful/tag) and send to SomaBrain for learning.

Acceptance criteria:
- 100% of messages are persisted locally and visible in SomaBrain within SLA (p50 1s, p95 5s) under normal conditions.
- Recall returns deterministic slices tied to `session_id` or semantic query with stable relevance signals.
- End-to-end traces for any message include spans across all hops and appear in Tempo/Jaeger.

Strict-mode defaults:
- Fail-closed policies in dev and prod: when a dependency or authorization check fails, the system surfaces a clear error to the UI and audit log; no silent fallbacks.
- Dev mirrors prod posture (no mocks); warnings and health banners appear in UI when components degrade.

## Auditing and Compliance

- Immutable audit log: append-only audit events (`who`, `what`, `when`, `why`, `how`) stored in Postgres and replicated to cold storage.
- Change management: settings POST creates audit entries; diffs recorded (with secret masking).
- Export: admin endpoint to export audit traces for a `request_id`/`session_id`.

## Testing and CI/CD

- Unit: schema validation for envelopes; idempotency tests; provider credential fetch tests.
- Integration: write-through tests (Gateway ↔ Worker ↔ SomaBrain); tool orchestration; SSE stream integrity.
- E2E/Playwright: console/network-clean smoke; chat send/stream; tool flow; memory proof (health-gated for replica lag).
- Security tests: CORS, authZ policies, redaction; secrets not present in logs.
- CI gates: build, lint/typecheck, unit, integration, E2E (smoke) required; full E2E nightly.

## Web UI Integration (Canonical behavior)

Goal: ship a clean, SSE-only Web UI against canonical Gateway contracts. No mocks, no inline fallbacks; UI must operate against real services via Gateway only.

Canonical UI behaviors:
- Chat transport: strictly SSE for streaming via `/v1/session/{session_id}/events` with event types `llm.delta`, `llm.complete`, `tool.call`, `tool.result`, `error`, `heartbeat`.
- Message send: POST `/v1/session/message` with `{ message, session_id?, persona_id?, attachments? }`; UI must not poll legacy endpoints; it awaits SSE for responses.
- Attachments: uploads via POST `/v1/uploads` returning descriptors `{ id, sha256, content_type, size_bytes, url }`; messages reference `attachments: [{ id }]` (no filesystem paths).
- Session management: list/history/delete/reset through Gateway routes; delete chat removes session history and closes streams.
- Tools: request via POST `/v1/tool/request`; UI shows tool call and result events inline, matching the SSE contract.
- Profiles and runtime config: UI fetches `/v1/tools` and `/v1/runtime-config` for model profiles, allowed tools, limits, and flags; secrets never exposed.

Canonical endpoints and flows (summary)
- Chat send: POST `/v1/session/message` with `{ session_id, message, attachments? }`.
- File uploads: POST `/v1/uploads`, then reference returned `attachment_id` in the message.
- Streaming updates: subscribe to SSE `GET /v1/session/{session_id}/events`; render `llm.delta`, `llm.complete`, `tool.*`.
- Auth: same-origin cookies or header/bearer tokens (no CSRF endpoint).

Memory views
- Prefer read-only, SomaBrain-backed endpoints (list/search/delete under policy). Avoid UI polling; use manual refresh or SSE invalidations when available.

Knowledge import
- POST `/v1/uploads` then trigger a `document_ingest` tool call referencing `attachment_id`; show tool events in-stream.

Session controls
- `/v1/sessions/{id}/reset`, `/v1/sessions/{id}` DELETE, `/v1/sessions/import`, `/v1/sessions/export`, `/v1/sessions/{id}/pause`, `/v1/health`.

UI behavior requirements (copy exactly from A0, implemented via canonical endpoints)
- Progressive streaming token render with smooth autoscroll and speech synthesis hooks
- Attachments UX: drag/drop, multi-file upload, progress bar, preview; map to upload→attachment_id flow
- Session list and tasks switching preserved; selection persisted in localStorage; delete closes SSE and clears view
- Notifications and error handling: frontend toasts on fetch failures; backend disconnected banner; strict error copies
- Settings modal: memory dashboard, scheduler/tasks, tool visibility driven by `/v1/tools` and `/v1/runtime-config`

Enforcement
- SSE-only; no UI proxy or polling.
- No inline dialogue fallback in Gateway; replies originate from Conversation Worker and real providers.

Acceptance criteria for UI integration:
- Sending a message from the UI produces streamed assistant deltas over SSE within p50 < 1s under local dev.
- Uploading a file yields an attachment_id; subsequent message referencing it triggers tool ingestion and assistant usage of extracted text.
- Deleting a chat closes the current SSE stream and removes history; a new chat starts clean.
- UI reflects Tool Catalog enable/disable and execution profile limits within configured TTL.

NO LEGACY enforcement (applies to both UI and Gateway)
SSE-only and no-CSRF (ongoing checks)
- No UI polling; SSE subscribe + reconnect/backoff.
- No CSRF fetch endpoint; rely on same-origin cookies or header token.
- Single canonical SSE path in Gateway.
- No dashboard polling; prefer read-only backed endpoints and explicit refresh.

Test plan additions (Playwright + pytest)
- test_ui_chat_stream_sse: open SSE, send message, assert llm.delta then llm.complete; no polling
- test_ui_upload_ingest_tool: upload file(s), send message referencing attachments, assert `tool.call` and `tool.result` events and assistant utilization of extracted text
- test_ui_memory_dashboard_readonly: load subdirs, search memories, view detail, no polling; optional delete guarded by policy flag
- test_api_session_controls: reset/delete/export/import/nudge/pause endpoints round-trip without legacy routes
- test_no_legacy_network: assert no network calls to disallowed legacy endpoints.

## Rollout Plan and Milestones

Phase 0 — Correctness and Strictness
- Align SomaBrain port to 9696 across code/docs/compose; health checks green when SomaBrain is up.
- Enable strict-mode defaults (fail-closed on policy/dependency failures) and surface banners in UI; remove legacy fallbacks.

Phase 0.5 — Agent Zero Web UI Integration and Real Chat (priority)
- Integrate Agent Zero UI into `webui/` with adapters to our `/v1` endpoints.
- Remove any UI-side polling or file path usage; wire SSE, uploads, and session controls.
- Remove Gateway inline dialogue fallback; require Conversation Worker running and real provider credentials.
- Playwright parity smoke: chat send/stream, upload+tool, delete chat.

Phase 1 — Attachment Ingestion by ID
- Add internal service fetch endpoint for attachments by ID and migrate Worker and `document_ingest` to `attachment_id` contracts.
- Update UI previews/downloads to route via Gateway `/v1/attachments/{id}` and eliminate filesystem path references.

Phase 2 — Central Tool Catalog and Runtime Config
- Implement Tool Catalog in Gateway (schemas, execution profiles, per-tenant flags, egress allowlists) with ETag/TTL distribution to services.
- Centralize provider secrets at Gateway; Workers invoke providers via Gateway.

Phase 3 — Memory Guarantees and Policy
- Strengthen outbox/WAL/idempotency; expose WAL/outbox lag in health; chaos-test recovery.
- OPA gates for conversation.send, tool.execute, memory.write; precise user-visible denies and audit.

 

Phase 5 — E2E and CI
- Playwright suite for chat streaming, uploads, tool flows, delete chat, policy denies; wire to CI.
- Add docs/versioned schemas; publish acceptance checks per sprint.

## Concrete Next Steps (Backlog)

1) Update docker-compose and docs to `SOMA_BASE_URL=http://host.docker.internal:9696`; add a test to enforce alignment.
2) Implement internal attachment fetch-by-ID and migrate Worker and `document_ingest` to use it; adjust UI previews.
3) Add Tool Catalog tables/APIs in Gateway and service-side ETag/TTL fetch with fail-closed behavior.
4) Enforce OPA gates across conversation/tool/memory flows with clear deny errors and audits; expose WAL lag in health.
5) Add Playwright smoke covering uploads/streaming/tool-call and delete chat; wire to CI.
6) Add structured logging and schema validation (JSONSchema in `schemas/`) on key envelopes.
7) Integrate Agent Zero UI and adapters; remove Gateway inline dialogue fallback; ensure SSE-only streaming path; document required env vars for real LLM.
8) Verify conversation history continuity: existing sessions render in UI; SSE resumes on refresh; delete/reset behave correctly.

## References (in-repo)

- Services: `services/gateway/main.py`, `services/conversation_worker/main.py`, `services/tool_executor/main.py`, `services/memory_*/*`, `services/ui*/main.py`.
- Client: `python/integrations/soma_client.py`.
- Docs: `docs/technical-manual/architecture.md`, `docs/technical-manual/tools-messages-memories.md`.

This roadmap is canonical. Proposed changes should be added here first, then implemented with tests and observability.


## Centralize LLM model/profile management (priority)

Goal
- Make the Gateway the single source of truth for all model profiles, provider credentials, base_url normalization, and runtime model resolution. All services must invoke LLMs through the Gateway endpoints (`/v1/llm/invoke` and `/v1/llm/invoke/stream`) and must not propagate raw `base_url` values between services.

Why this is needed
- During audits we found model/profile information and base_url normalization logic duplicated across services (workers, Gateway, local config files). This causes validation errors (eg. "invalid model/base_url after normalization"), runtime surprises, and operational friction. Centralization reduces surface area for mistakes, makes credential management secure, and simplifies rollout of provider changes.

Design decisions (summary)
- Gateway owns: ModelProfileStore reads/writes, `_normalize_llm_base_url` rules, provider detection, and credential lookup. Workers send only role + messages + limited overrides (model name, temperature, kwargs) — they do not send `base_url`.
- Centralized Settings: UI saves all agent/model settings and provider secrets via `/v1/ui/settings/sections` (single writer path). Provider secrets are encrypted (mandatory `GATEWAY_ENC_KEY`) and surfaced only as presence + `updated_at` via `/v1/ui/settings/credentials`.
- Gateway exposes `/v1/model-profiles` (CRUD), `/v1/ui/settings/*` (settings reads/writes), and `/v1/llm/test` for profile connectivity validation.
- Legacy credentials endpoints (`/v1/llm/credentials`, `/v1/llm/credentials/{provider}`) removed; callers must use Settings sections save flow.
- Callers cannot override `base_url`; the Gateway always uses the profile’s value.

Acceptance criteria
- Worker->Gateway->Provider flow succeeds end-to-end: POST to Gateway invoke returns stream or non-stream content and the UI receives assistant events via SSE.
- No service outside Gateway performs normalization logic that changes `base_url` semantics.
- Gateway audit logs record provider and normalized base_url for every LLM invoke.

Migration strategy (high level)
1. Audit all usages of model/profile and `base_url` (scripts, conf, services). Document and back up existing profiles.
2. Implement Gateway CRUD/API and ensure any incoming `overrides.base_url` is ignored.
3. Update workers to stop sending `base_url` and to rely on Gateway resolution of model->provider->base_url.
4. Complete removal of duplicated config; no lock flag required.

Risks & mitigations
- Risk: Missing credentials after migration. Mitigation: use `/v1/llm/test` and a migration script to copy secrets into Gateway store, validate, and only then enforce lock.
- Risk: Legacy clients sending `base_url`. Mitigation: `warn` mode that logs and surfaces in UI and builds a one-click migration map.

---

## 2025-10-31 Update — Real Endpoints Roadmap (Merged)

This addendum locks our single-surface Gateway API and the UI’s SSE-only behavior. It merges decisions we’ve implemented with the remaining work to reach full parity with the original Agent Zero Web UI while retaining the somaAgent01 architecture.

Feature → Endpoint map (authoritative)
- Chat ingress: `POST /v1/session/message`
- Session stream (SSE): `GET /v1/session/{session_id}/events`
- Recent timeline: `GET /v1/sessions/{session_id}/events`
- Uploads: `POST /v1/uploads`
- Attachments download: `GET /v1/attachments/{id}`
- Tools catalog/list: `GET /v1/tools`, `GET /v1/tool-catalog`, `PUT /v1/tool-catalog/{name}`
- Tool request enqueue: `POST /v1/tool/request`
- UI settings (sections): `GET|POST /v1/ui/settings/sections`
- Runtime config (UI boot hints): `GET /v1/runtime-config`, `GET /ui/config.json`
- Session helpers: `POST /v1/sessions/{id}/reset`, `POST /v1/sessions/{id}/pause`, `GET /v1/sessions/{id}/history`, `GET /v1/sessions/{id}/context-window`, `POST /v1/sessions/import`, `POST /v1/sessions/export`, `DELETE /v1/sessions/{id}`
- Workdir (developer UX): `GET /v1/workdir/list`, `POST /v1/workdir/upload`, `POST /v1/workdir/delete`, `GET /v1/workdir/download`
- Antivirus check: `GET /v1/av/test`

Transport and events (canonical)
- SSE-only. Event envelope matches “Outbound SSE Event Contract (sa01-v1)”.
- Event types: `assistant.thinking`, `assistant.stream`, `assistant.final`, `tool.start`, `tool.result`, `uploads.progress`.

Phased delivery (done vs remaining)
- Done: single Gateway surface; UI served under `/ui`; session durability; outbox + memory write outbox; settings sections + audit logging.
- Remaining (high→medium):
  - UI tool lifecycle de-duplication when `tool.start` lacks `request_id` but `tool.result` includes it
  - Uploads progress single-block per file and render “Uploaded:” when only a final “done” event arrives
  - Settings modal Alpine init race under automation; ensure modal opens reliably on first click
  - Provider credential presence hints to enable SSE assistant tests

Acceptance for this addendum
- No legacy UI calls appear (`/v1/ui/poll`, `/v1/csrf`)
- Uploading small files shows “Uploaded:” even without intermediate progress
- Tool start→result yields a single “Tool: <name>” block with result body
- Settings modal renders sections on first open in CI/local

---

## 2025-11-01 Update — Long-message stability, Thought-bubble parity, and Canonical Memory APIs

Scope
- Fix UI collapse/flip during very long assistant streams by adopting a streaming-safe renderer and CSS containment.
- Achieve visual/behavioral parity for thought bubbles (ephemeral thinking hint + final thoughts rows) with the 7001 demo.
- Canonicalize Memory Dashboard endpoints under `/v1/memories/*` and rewire the UI to them (remove reliance on legacy `/memory_dashboard`).

What changed (code)
- Web UI streaming safety:
  - During streaming, render assistant deltas without markdown/KaTeX (`response_stream` message type) and throttle DOM updates to ~30fps.
  - On final event, perform a single markdown+KaTeX render to replace the streaming content.
  - CSS containment and transition disabling applied to streaming message containers to prevent layout thrash.
- Thought bubble parity:
  - Ephemeral thinking bubble lifecycle tightened (show on thinking, clear on final/error/reset); visuals aligned to golden where possible.
  - “Show thoughts” toggle instantly affects `.msg-thoughts`; persistence remains under `/v1/ui/preferences`.
- Memory Dashboard APIs:
  - New canonical routes:
    - `GET /v1/memories/current-subdir`
    - `GET /v1/memories/subdirs`
    - `GET /v1/memories?memory_subdir=&q=&area=&limit=`
    - `DELETE /v1/memories/{id}`
    - `POST /v1/memories/bulk-delete` with `{ ids: number[] }`
    - `PATCH /v1/memories/{id}` with `{ edited: { content?, metadata? } }`
  - UI store (`memory-dashboard-store.js`) rewired to these endpoints.
  - Legacy `/memory_dashboard` kept as a compatibility shim; slated for removal post cutover.

Tests added
- Playwright: `thought.bubbles.and.toggles.spec.ts`
  - Sends a message, waits for assistant to finish (progress empty), clicks all `.kvps-row.msg-thoughts .kvps-val` rows if present, then flips Show thoughts/JSON/utils and performs best‑effort DOM visibility checks.

Acceptance criteria
- Long streaming replies do not cause UI collapse or flipping; progress bar remains coherent; no errors logged.
- Thought bubbles (ephemeral + final thoughts) match the golden UI’s look and timing; toggles flip visibility instantly and persist via preferences.
- Memory Dashboard uses `/v1/memories/*` endpoints in the UI; basic flows (list/search/delete/update) function; no UI polling.

Next sprints (focused)
- Sprint A (stability):
  - Finalize streaming renderer (metrics: frame times under load), add throttling guardrails and optional raf-based coalescing.
  - Extend Playwright with a “long message torture test” (markdown + code + LaTeX + images) and record video/trace.
- Sprint B (parity polish):
  - Copy exact bubble CSS from golden assets and unify styles; add structural assertions for bubble elements.
  - Expand toggles test to verify persistence across reload and themes.
- Sprint C (memory UX):
  - Add pagination/filter UX assertions; integrate optional delete policy checks; consider SSE-invalidations for live updates.

---

## 2025-11-02 Update — Dual‑mode Parity (Golden 7001 vs Local /v1) and Test Matrix

Scope
- Establish a two-mode UI test strategy to compare our local canonical UI (served by Gateway at :21016 under /ui and backed by /v1 APIs) against the golden reference running on port 7001 (which uses legacy routes and serves UI at the root).
- Ensure our local Web UI achieves UX/CSS/behavioral parity with the golden demo while retaining strict SSE-only and /v1-only contracts locally.

What changed (tests and harness)
- Playwright config already honors WEB_UI_BASE_URL; we added a GOLDEN_MODE flag. When GOLDEN_MODE=1 or WEB_UI_BASE_URL contains :7001, tests relax network assertions and switch to more permissive selectors.
- Updated tests:
  - `network.no-legacy.spec.ts`: now skipped in GOLDEN_MODE (golden legitimately makes legacy calls).
  - `parity.spec.ts`: detects GOLDEN_MODE and (a) does not assert `/v1/session/message` POST, (b) uses robust input selectors, (c) gates sidebar session controls to local-only.
  - `long.stream.torture.spec.ts`: made completion checks robust (handles cases where progress bar text may not clear even though streaming completes) and avoids strict locator ambiguity.
  - `chat.reset.single-reply.spec.ts` and `controls.sidebar.sessions.spec.ts`: hardened selectors and timeouts.
  - New: `golden.smoke.spec.ts` — a lenient smoke for golden: loads the page, types into the first text input/textarea, sends via Enter/click and asserts a visible DOM change; no /v1 assumptions.

How to run
- Local (canonical /v1):
  - `WEB_UI_BASE_URL=http://127.0.0.1:21016/ui npx playwright test`
- Golden (port 7001):
  - `WEB_UI_BASE_URL=http://127.0.0.1:7001 GOLDEN_MODE=1 npx playwright test specs/golden.smoke.spec.ts specs/parity.spec.ts`

Acceptance gates for parity
- Visual/behavioral parity: thought bubble timing, streaming smoothness, toggle interactions, session controls UX, and general layout should match golden 7001.
- Local strictness retained: no polling or CSRF endpoints; only `/v1/*` routes are allowed; SSE-only stream path.

Status (as of 2025-11-02)
- Local UI suite: PASS (all critical specs green; env-dependent scheduler/tools smokes are skipped). Long-stream torture stabilized (no transient shrink), multi-turn chats stable, no duplicate replies after reset. Memory Dashboard rewired to `/v1/memories/*`.
- Golden checks: PASS for `golden.smoke` and adapted `parity.spec` against `http://127.0.0.1:7001`.
- Python E2E tool flow: PASS (1 test, 1 warning about custom mark; to be registered later).
- Known pending items:
  - Expand golden run to include long-stream and thought-bubbles with selector adapters (some selectors differ at 7001 root).
  - CSS pixel parity for thought-bubble icons/spacing; add optional screenshot assertions.

Next steps
1) Extend GOLDEN_MODE adapter helpers (shared util) and apply to the remaining specs so the entire smoke set can run against 7001.
2) Produce a short “parity delta” report (selectors/CSS/behavior) from a side-by-side run and implement the CSS polish locally.
3) Add CI jobs for both matrices: local canonical (/v1-only) and golden-compat (selector-only, network relaxed).

Quality gates snapshot
- Build: PASS (dev stack up).
- Lint/Typecheck: PASS (no new issues introduced by spec edits).
- Tests: Local UI suite PASS; Golden subset PASS; E2E tool flow: FAIL (to be triaged).


---

## 2025-11-08 Update — Streaming Centralization (Event Bus) & SSE Hardening

Scope
- Consolidate all UI real-time updates behind a single client stream and event bus; eliminate residual polling (scheduler, memory dashboard) and ship production-grade reconnection, heartbeats, and backpressure.

What changed (current state)
- Chat: migrated from legacy polling to SSE in `webui/index.js`. CSRF fetch removed from `webui/js/api.js`. Confirmed no `/poll` references in chat code.
- Gap: other panels (scheduler, memory dashboard) still use polling; no shared client event bus; reconnect/backoff minimal; no heartbeat stall detection.

Design decisions
- Single stream client: `webui/js/stream.js` wraps `EventSource` with jittered backoff, Last-Event-ID, heartbeat tracking, and stall detection → emits standardized UI events onto a bus.
- Central event bus: `webui/js/event-bus.js` is a minimal pub/sub with topic strings; domain stores subscribe and update state.
- Canonical UI event schema (additive on top of existing assistant/tool events):
  - `ui.status.progress` — progress updates for long-running work (payload: { id, label?, pct?, stage?, details? }).
  - `ui.status.paused` — conversation/session paused/resumed state (payload: { session_id, paused, reason? }).
  - `ui.notification` — transient notifications/toasts (payload: { level: info|warn|error, message, code?, href? }).
  - `session.list.update` — session/task list invalidations or diffs (payload: { added?, removed?, changed? }).
  - `task.list.update` — task/scheduler invalidations or diffs (payload mirrors above).
- Domain stores: `messagesStore`, `notificationsStore`, `progressStore`, `sessionsStore`, `tasksStore` consume bus events; views bind to stores. Messages continue to handle `assistant.delta/complete`, `tool.start/result`.

Server updates (Gateway)
- Extend SSE publisher to include the canonical UI events above where applicable (progress/paused/notifications and list invalidations). Continue emitting `heartbeat` at a fixed cadence.
- Support `Last-Event-ID` to help reconnect resume. Expose `X-Accel-Buffering: no` and appropriate cache headers.
 - Emit lightweight invalidation hints alongside normal payloads:
   - `task.list.update` when task-related events occur (e.g., `task.*`, or `tool.result`/`assistant.final` with `metadata.task_id`).
   - `memory.list.update` for `memory.*` events.
   These hints allow SSE-driven UI list refreshes without polling.

Reliability
- Reconnect/backoff: full jitter exponential backoff with max cap; fast-path on immediate user action (send message) to force a quick reconnect attempt.
- Heartbeat stall detection: UI banner after N missed heartbeats; auto-retry in background; allow manual retry button.
- Backpressure: coalesce frequent progress updates (throttle to ~10–20Hz) and only re-render at animation frames.

Testing
- Playwright: `stream.reconnect.and.banner.spec.ts` (disconnect → banner → auto-recover), `no-poll.anywhere.spec.ts` (assert no network calls to legacy/poll endpoints), `scheduler.memory.bus.spec.ts` (live updates via SSE, no polling), long-stream remains green.
- Pytest API: contract tests for new UI event types (`ui.status.progress`, `ui.notification`) and `Last-Event-ID` resume.
 - Pytest API: assert presence of `task.list.update`/`memory.list.update` hint events during representative flows.

Acceptance criteria
- No polling in any UI module (chat, scheduler, memory dashboard, settings), verified via Playwright network assertions.
- Stream client reconnects with jittered backoff; heartbeat stall triggers an offline banner and recovers automatically.
- Session/task/memory views update via SSE invalidations or diffs; manual refresh still available but not required.
- Large histories remain responsive: either virtualization or message trimming is enabled without breaking grouping.

Status / Next steps
- Done: chat SSE, CSRF removal. In progress: planning and roadmap consolidation for central event bus.
- Next: implement `event-bus.js` and `stream.js`, refactor `index.js` to use the bus, extend Gateway to emit canonical UI events, migrate scheduler and memory dashboard stores, add tests.

---

## 2025-11-09 Addition — Unified Configuration / Security / Secrets Hardening Roadmap (M0–M12)

This section merges prior architectural, security, and settings analyses into a single phased plan. It focuses on eliminating schema ambiguity, centralizing provider credentials, enforcing policy gates, and delivering auditable, deterministic configuration flows.

### Guiding Principles
- Single authoritative write path for UI + runtime settings (no scattered direct table writes).
- Provider credentials encrypted at rest; rotation possible without code changes.
- All settings changes produce masked audit diffs and Kafka `config_updates` events.
- Read paths are cached, versioned, and fail closed when invariants break.
- Strict separation of concerns: registry (metadata), store (persistence), resolver (runtime projection), policy (OPA/OpenFGA), secrets backend (encryption / rotation).

### Milestone Overview
| Milestone | Focus | Key Artifacts | Primary Risks | Acceptance Snapshot |
|-----------|-------|---------------|---------------|---------------------|
| M0 | Instrument & Inventory | Route catalog, metrics, audit diff schema | Blind spots may hide unsafe flows | All settings endpoints mapped & emitting metrics; audit diff schema validated |
| M1 | Read-only Registry | `SettingsRegistry` (in-memory typed view) | Drift between registry & DB snapshot | Registry stable across test runs; no write methods |
| M2 | Typed Schemas & Validation | Pydantic models per domain (`ui`, `llm`, `tooling`, `auth`, `limits`) | Legacy untyped writes break | All incoming writes validated; invalid payload → 422 with field map |
| M3 | Transactional Write Path | Single POST `/v1/ui/settings/sections` → domain split + audit diff | Race conditions, partial writes | Atomic commit; audit diff includes masked secrets; event published |
| M4 | Secrets Backend & Rotation | `SecretsBackend` with key version, Fernet or AES-GCM envelope | Lost key = unusable creds | Key version recorded; rotation script passes canary test |
| M5 | Auth Hardening | Enforce `REQUIRE_AUTH`, internal token depreciation, JWT scopes | Lock-out on misconfig | All protected endpoints reject unauthenticated calls in strict mode |
| M6 | Provider Normalization Service | `_normalize_llm_base_url` extracted & consolidated | Hidden divergence in workers | Workers no longer attempt normalization; 0 base_url overrides |
| M7 | Drift Detection & Health | Compare registry vs DB vs cache, expose `/v1/config/drift` | False positives cause noise | p95 drift check < 50ms; health gating accurate |
| M8 | Observability Expansion | Structured logs, span attributes for config writes | PII leakage risk | No secrets in logs; span shows domain + diff hash |
| M9 | Key Rotation Automation | Cron/CI pipeline rotates + re-encrypts stale versions | Rotation failure mid-cycle | Dry-run validation; rollback key retained until success |
| M10 | Multi-Tenant Partitioning | Tenant-specific overrides with fallback precedence | Cross-tenant bleed | Override precedence documented; tests prove isolation |
| M11 | Policy-Driven Dynamic Limits | Per-tenant rate/tool limits enforced via OPA / FGA | Policy latency | Cache TTL ensures p95 policy check < 10ms |
| M12 | Externalized Config Packages | Export minimal config bundle for air-gapped analysis | Incomplete masking | Bundle excludes raw secrets; diffs stored with masked placeholders |

### Critical Path (Why This Order)
1. M0–M2 build visibility & strong typing before altering write mechanics.
2. M3 introduces atomic writes; must land before secrets centralization (M4) so secrecy is applied once.
3. M4–M5 secure sensitive data & enforce auth; prevents later expansions from amplifying risk.
4. M6 removes normalization duplication to avoid drift when registry evolves.
5. M7–M8 deepen detection & traceability; required before adding rotation cadence (M9).
6. M10–M11 extend multi-tenancy & dynamic policy safely atop hardened core.
7. M12 packages external consumption after stability and security layers mature.

### Detailed Milestones & Acceptance Criteria

#### M0 – Inventory & Instrumentation
Scope: Enumerate every settings/credentials route, add Prometheus counters/histograms, define audit diff schema (`old`, `new`, `mask`, `domain`, `changed_at`).
Acceptance:
- Route catalog file (`docs/technical-manual/settings-routes.md`) lists all verbs & auth scopes.
- Metrics: `settings_write_total`, `settings_write_latency_seconds`, `settings_read_total` present.
- Audit diff emitted for each write with masked secret fields (pattern: value replaced by `****` length-preserving mask).

#### M1 – Read-only Registry
Scope: Implement `SettingsRegistry` that loads typed domains on startup and caches them (ETag + version integer).
Acceptance:
- Registry object accessible via dependency injection; no mutation methods.
- Unit test ensures repeated access returns same instance; mismatch between DB & registry triggers warning.

#### M2 – Domain Schemas & Validation
Scope: Introduce domain Pydantic models; convert loose JSON sections into structured `UiSettings`, `LlmSettings`, `ToolingSettings`, `AuthSettings`, `LimitsSettings`.
Acceptance:
- Invalid field triggers 422 with `detail: [{loc, msg, type}]`.
- 100% coverage for schema conversions; legacy untyped write path blocked.

#### M3 – Transactional Write Path
Scope: Replace multi-endpoint writes with single sectioned POST; perform domain validation, diff generation, atomic commit, event publish.
Acceptance:
- Single commit covers all domains; partial failure rollback test passes.
- Kafka `config_updates` event includes `version`, `domains_changed`, `diff_hash`.

#### M4 – Secrets Backend & Rotation
Scope: Implement encryption with key versioning; support key rotation CLI (`rotate_key.py`) that re-encrypts values.
Acceptance:
- Secret record stores `{ciphertext, key_version, updated_at}`.
- Rotation increases key version and preserves decrypt ability; canary decrypt test passes.

#### M5 – Auth Hardening
Scope: Enforce token validation even if `REQUIRE_AUTH` previously false; remove deprecated internal token bypass for non-critical endpoints; scope-based access.
Acceptance:
- Auth off path removed (except explicitly flagged health endpoints).
- Restricted endpoint test unauthorized returns 401/403 with structured body.

#### M6 – Provider Normalization Service
Scope: Centralize model/base_url normalization logic; workers send only high-level model identifiers.
Acceptance:
- No calls in codebase to legacy normalization helper outside service.
- LLM invoke logs contain normalized provider fields.

#### M7 – Drift Detection
Scope: Periodic comparison between DB snapshot, registry cache, and last event version.
Acceptance:
- `/v1/config/drift` returns status `ok|warning|critical` and counts of mismatches.
- Simulated drift triggers `warning` and publishes alert metric.

#### M8 – Observability Expansion
Scope: Add structured logging fields `config_version`, `domains_changed` to write spans; propagate trace context.
Acceptance:
- Logs verified free of secret raw values; diff hashes present.
- Trace viewer shows `config.write` span with attributes.

#### M9 – Key Rotation Automation
Scope: Scheduled job or pipeline step rotates keys monthly; dry-run mode and rollback support.
Acceptance:
- Dry-run outputs prospective new key version mapping.
- Rotation job updates all rows; post-rotation decrypt validation 100%.

#### M10 – Multi-Tenant Partitioning
Scope: Per-tenant overrides layered on global base; precedence (tenant → global) enforced.
Acceptance:
- Tenant override read returns merged settings; removing override reverts to global.
- Cross-tenant access attempt blocked & audited.

#### M11 – Policy-Driven Dynamic Limits
Scope: Limits (rate, tool concurrency) enforced via cached policy decisions; registry updates invalidate caches.
Acceptance:
- Limit breaches return 429 with structured detail.
- p95 policy check latency < 10ms under load test.

#### M12 – Externalized Config Bundle
Scope: Export sanitized config bundle (`config_bundle_v<version>.tar.gz`) for air-gapped review.
Acceptance:
- Bundle excludes secrets; masked placeholders present; signature file SHA256 verified.
- Import tool validates signature and reconstructs registry snapshot.

### Risks & Mitigations
- Schema Migration Complexity (M2): Provide dual-read fallback for one release; log warnings for legacy format.
- Rotation Failures (M4/M9): Canary encryption + staged rollout; keep previous key version until success metrics confirmed.
- Policy Latency (M11): Cache decisions with TTL + event-driven invalidation; circuit breaker on policy backend.
- Drift False Positives (M7): Multi-source hash comparison and threshold before alerting.

### Metrics to Track Throughout
- `settings_validation_errors_total`
- `config_updates_events_total`
- `secrets_rotation_success_total` / `secrets_rotation_failure_total`
- `config_drift_checks_total` and `config_drift_mismatches_total`
- `policy_decision_latency_seconds`
- `settings_write_audit_masked_total`

### Immediate Next Action (You are here)
Proceed with M0: add route catalog + baseline metrics in code. After merging this section, implement instrumentation and open a short PR if required.

---
## 2025-11-09 Update — Master Roadmap Consolidation & Parallel Sprint Plan

This section consolidates the architectural roadmap with feature-flag strategy, streaming hardening, semantic recall, unified configuration/security, and release cadence. It defines parallel sprint execution. This document remains the single source of truth.

### Integrated Master Tracks
1. Capability Registry & Best Mode (feature flags → descriptors, profiles, health-aware degrade)
2. Streaming & UI Parity (single SSE stream, client event bus, zero polling, reconnection robustness)
3. Semantic Memory & Recall (embeddings ingestion, query-time similarity ranking, caching, recall metrics)
4. Unified Config & Secrets (M0–M12 milestones: instrumentation, schemas, transactional writes, encryption, rotation, drift, policy limits)
5. Tool Catalog & Runtime Config (Gateway-owned definitions, per-tenant flags, audited changes)
6. Reliability & Backpressure (consumer lag gauges, circuit breakers, alert templates)
7. LLM Model/Profile Centralization (Gateway sole authority; workers stop sending base_url)
8. Auditing & Compliance (masked diff events, traceability, export tooling)

### Capability Descriptor Schema (to be implemented)
Fields: `key`, `description`, `default_enabled`, `profiles: {minimal|standard|enhanced|max}`, `dependencies`, `degrade_strategy (auto|manual|none)`, `cost_impact (low|medium|high)`, `metrics_key`, `tags (observability|security|performance)`. State machine: `enabled` → (`degraded` | `disabled`). Transitions audited.

### Profiles (Default = enhanced)
minimal: critical path only (chat, memory write-through).  
standard: + basic tools, metrics, auth hardening.  
enhanced (default): all production features including embeddings ingestion and scheduler.  
max: enhanced + experimental (semantic recall, advanced caching) gated behind stability checks.

### Parallel Sprint Plan
Sprint 0 (Planning & Instrumentation, 2–3 days, parallel)
- Feature descriptor schema & examples documented.
- Unified Config M0: route inventory + metrics/audit diff schema.
- SSE event bus interface + canonical UI event list (progress, notification, list updates, heartbeat).
Exit: Documentation merged; no code side-effects; acceptance criteria clarified.

Sprint 1 (Enable Best Mode Safely, 4–6 days)
- Implement `features` registry module + metrics + `/v1/features` diagnostics.
- Refactor env flag lookups to registry (gateway, session_repository, embeddings helper).
- Implement SSE client bus (chat only) with jittered reconnect + heartbeat stall banner.
- Semantic recall design & cache strategy (vector similarity approach, LRU/hash plan).
- Docs + tests (registry unit tests, Playwright no-poll chat spec).
Exit: Enhanced profile active by default; registry metrics visible; chat polling eliminated.

Sprint 2 (Semantic Recall & Full Streaming, 1–2 weeks)
- Implement recall API (embed query → top-k memory slice). Hybrid filters (session, recency).
- Embedding cache implementation (LRU + normalized hash key).
- Migrate scheduler & memory dashboard to SSE bus (remove all polling).
- Add consumer lag gauges & circuit breakers; alert rule templates drafted.
Exit: Zero UI polling; recall latency & hit metrics published; alert templates ready.

Sprint 3 (Config & Secrets Hardening, 1–2 weeks)
- M1–M4: Typed domain schemas, transactional writes, secrets encryption, rotation CLI.
- Centralize LLM profile normalization; workers stop sending base_url.
Exit: Atomic masked writes; secrets encrypted; normalized profile flow validated.

Sprint 4 (Policy, Multi-Tenancy, Limits, 2 weeks)
- Auth hardening (REQUIRE_AUTH); OPA/OpenFGA gates for conversation/tool/memory.
- Multi-tenant override precedence; dynamic limits (rate/tool concurrency).
- Drift detection endpoint & health gating.
Exit: Policy decisions fast (<10ms p95); tenant isolation tests green; drift checks stable.

Sprint 5 (Parity Polish & Release Cadence, 1 week)
- Golden vs canonical UI screenshot diff optional gating.
- CI matrices (canonical + golden mode); release tagging & automated changelog.
- Observability dashboards updated (feature states, recall metrics, circuit breaker status).
Exit: CI green across matrices; v0.3.0 (semantic recall) tagged; dashboards live.

### Immediate Action Items (Start Now)
- Write feature descriptor schema doc (registry definitions & examples).
- Begin Unified Config M0 metrics & audit diff instrumentation design.
- Draft SSE event bus module interfaces (client & server publish contract).

### Key Success Metrics
- 0 raw `os.getenv` feature lookups after Sprint 1 (lint rule enforcement).
- UI network log shows no polling endpoints after Sprint 2.
- Recall p95 latency < 150ms local; cache hit-rate > 70% for repeated similar queries.
- Secrets encryption coverage 100%; rotation dry-run passes monthly.
- Policy decision latency p95 < 10ms; drift false positives < 1/week.

### Risk Mitigations Snapshot
- Registry Rollout: dual path (env var fallback) until Sprint 1 exit.
- Recall Accuracy: shadow evaluation before enabling for all profiles.
- Secrets Rotation: staged rotation with canary decrypt & rollback key retention.
- Policy Latency: local cache TTL + event-driven invalidation; circuit breaker fallback to deny with clear error.

### Release Cadence & Versioning
- v0.1.0-centralised (architecture) → v0.2.0-streaming-bus → v0.3.0-semantic-recall → v0.4.0-config-secrets → v0.5.0-multi-tenancy.
- Each release: automated changelog (diff of feature states + schema versions) & audit snapshot.

### Governance Note
All roadmap modifications must update this file first; PRs referencing roadmap changes include a diff of this section. Sprint exit reviews confirm metrics & acceptance criteria before advancing profile defaults.

— End of 2025-11-09 consolidation.


## 2025-11-09 Update — No‑Legacy Mandate & Somabrain Alignment (Authoritative)

This addendum enforces a strict “NO LEGACY ANYWHERE” policy and reconciles the Somabrain integration blueprint with the current implementation. It defines what “legacy” means, inventories gaps, and lays out a sprinted, prioritized plan to remove every legacy pathway and align all interactions through the Somabrain HTTP surface.

### Zero‑Legacy Definition (non‑negotiable)
- No stub/shim code paths that bypass real policy/security (e.g., placeholder OPA that always allows).
- No duplicate or competing implementations of the same concern (feature flags, Kafka producer, config normalization, health endpoints).
- No direct environment flag checks outside the central Feature Registry and Settings.
- No deprecated endpoints, polling loops, or hidden fallbacks; SSE‑only real‑time; one canonical API surface.
- No ambiguous integration boundaries: all SomaBrain interactions occur via its HTTP API at `SOMA_BASE_URL`.

### Somabrain Integration Boundary (final)
- Boundary: HTTP only. Do not import Somabrain internal Python modules in‑process; use the HTTP service surface consistently.
- Required endpoints (contract):
  - Health: `GET {SOMA_BASE_URL}/healthz` (primary), `GET /health` accepted as legacy alias.
  - Learning/Weights: `GET /v1/weights`, `POST /v1/weights/update`.
  - Context Builder: `POST /v1/context/build`.
  - Tenant Feature Flags: `GET /v1/flags/{tenant}/{flag}`.
  - Memory: `POST /v1/memory/remember`, `POST /v1/memory/link`, `POST /v1/plan/suggest` (where applicable).
  - Recall: `POST /v1/recall/query` (tenant‑scoped).

### Legacy Inventory (to be removed or unified)
- OPA placeholder middleware (`python/integrations/opa_middleware.py`) that never talks to real OPA/Somabrain policy → replace with HTTP adapter that evaluates policy remotely and enforces fail‑closed when configured.
- Duplicate health endpoints (`/health`, `/healthz`) and mixed targets (`/health` vs `/healthz`) → converge to `/healthz` in Gateway; probe Somabrain `/healthz` first; keep `/health` as alias only.
- Env‑flag checks scattered across code (`os.getenv("SA01_ENABLE_*"`, `ENABLE_*`) → replace with Feature Registry lookups; add lint rule to forbid direct getenv for flags.
- Dual outbox/Kafka producers across services vs Somabrain’s producer → keep local outbox pattern but unify headers/schema and health adaptation; centralize Kafka publisher behind one adapter (no competing producers).
- Local feature flags vs tenant flags in Somabrain Redis → add tenant override layer calling Somabrain `GET /v1/flags/{tenant}/{flag}` with TTL cache; registry provides defaults only.
- Any unused legacy modules (gRPC memory client references, polling UI calls, legacy credentials routes) → delete.

### Enforcement Principles
- Single source per concern: one place to evaluate policy, one publisher API, one feature flag gateway, one health probe path.
- Fail‑closed by default for security‑relevant flows (policy/memory/tool writes); surface clear denies and audit entries.
- Observability for every removed legacy pathway: add counters to ensure it stays at zero usage.

### Prioritized Sprint Plan (Legacy Eradication)

Sprint L0 — Policy & Health Hardening (3 days)
- Replace OPA stub with HTTP policy adapter calling Somabrain policy endpoint; wire into Gateway middleware; measure with `auth_requests_total`, `auth_duration_seconds`.
- Standardize health: Gateway serves `/healthz`; probes Somabrain `{SOMA_BASE_URL}/healthz` (fallback `/health`); UI banner uses `/v1/health` aggregate with Somabrain status folded in.
- Acceptance: Real denies produce 403 with structured reason; `/healthz` green only when Somabrain healthy; tests cover allow/deny and degrade.

Sprint L1 — Feature Flags Unification (3 days)
- Add tenant override path: Gateway resolves feature flags by calling Somabrain `GET /v1/flags/{tenant}/{flag}` with 1–2s TTL cache; Feature Registry provides profile defaults only.
- Add `/v1/feature-flags?tenant=...` endpoint returning merged view; UI and services consume only this path.
- Add lint rule forbidding `os.getenv("SA01_ENABLE_"` and direct env gating outside the registry.
- Acceptance: No direct getenv flag checks; per‑tenant flags effective and observable; tests verify TTL cache and fallback behavior.

Sprint L2 — Context & Learning Hooks (4 days)
- Inject `get_weights()` and `build_context()` into the chat prompt assembly path; record `learning_updates_total`, `learning_context_build_duration_seconds`.
- Hook reward/TD updates via `POST /v1/weights/update` on tool outcomes; ensure idempotency and backoff.
- Acceptance: Prompts include current weights and Somabrain‑built context; rewards post without raising; metrics present.

Sprint L3 — Eventing & Outbox Alignment (4 days)
- Centralize Kafka publisher behind one adapter; ensure uniform headers `{trace_id, request_id, tenant}`; align topics with Somabrain naming; keep durable Postgres outbox.
- Add trace injection/extraction on publish/consume flows; expose `trace_propagation_errors_total`.
- Acceptance: WAL/outbox publish path unified; traces link across Gateway↔Workers; no duplicate producer classes remain.

Sprint L4 — UI/Streaming Cleanup & Endpoint Purge (3 days)
- Verify UI uses SSE only, no polling; remove any legacy `/poll`, CSRF routes, and deprecated credential endpoints; align to `/v1/*` and `/ui/config.json` exclusively.
- Remove duplicate/obsolete endpoints and modules; add “legacy usage” counters to confirm zero usage in CI.
- Acceptance: Playwright `no-legacy-network` passes; counters stay zero; grep for legacy routes returns none.

### Definition of Done (No‑Legacy)
- Zero stub or dead code for policy, health, flags, eventing, or memory; any former shims deleted.
- No direct `os.getenv` feature checks; registry + tenant override only.
- Single health path (`/healthz`) in Gateway; Somabrain probed at `/healthz`.
- All Somabrain interactions through HTTP client; no internal module imports from Somabrain.
- UI/network tests show no polling or legacy endpoints; only `/v1/*` and `/ui/*` used.

### Acceptance & Metrics
- Security: 100% of protected routes pass through real policy adapter; `auth_requests_total{result="deny"}` increments on policy failure.
- Availability: `/healthz` reflects Somabrain state; outbox/backpressure adapts when Somabrain degrades; alerts fire accordingly.
- Observability: new metrics present — `learning_updates_total`, `learning_context_build_duration_seconds`, `trace_propagation_errors_total`, `feature_flag_remote_requests_total`.
- Hygiene: CI job runs `grep`/lint to forbid legacy patterns and fails if found.

### Risks & Mitigations
- Policy latency: cache allow/deny with short TTL; add circuit breaker → deny with reason if backend unavailable (configurable fail‑open in dev only).
- Flag staleness: small TTL cache + proactive refresh on write paths; degrade to defaults with audit.
- Eventing drift: publish contract and headers standardized; add contract tests for topics and headers.

### Immediate Next Actions (to schedule)
- Implement OPA HTTP adapter + middleware swap (L0).
- Add `/v1/feature-flags` merged endpoint + tenant override via Somabrain (L1).
- Wire `get_weights`/`build_context` + reward updates into chat/tool flows (L2).

This section is now part of the canonical roadmap. Any refactor or removal tied to the No‑Legacy mandate must first update this document with scope, acceptance, metrics, and tests, then proceed to implementation.

## 2025-11-09 Integration Summary — Somabrain Full Alignment (Clarification)

This summary captures the clarified objective: SomaAgent01 fully integrates Somabrain as the upstream AI brain over HTTP while retaining all valuable existing subsystems (gateway, workers, outbox/WAL, Kafka, UI, metrics, auditing). We eliminate only genuine legacy shims or duplicates; we do not discard functioning architecture components.

### Core Understanding
1. Somabrain is the authoritative service for: learning (weights/reward updates), context building, recall, tenant feature flags, policy enforcement, and memory graph operations.
2. SomaAgent01 remains authoritative for: durable message persistence (Postgres + WAL/outbox), event publishing (Kafka with standardized headers), session orchestration, tool execution sandbox, UI delivery, and composite observability.
3. Interaction mode: strictly HTTP (`SOMA_BASE_URL`) — no in‑process imports of Somabrain internals to preserve service boundary and upgrade independence.

### Retained Subsystems (Not Removed)
- Postgres durability (sessions, outbox, WAL, audit, settings).
- Redis/Kafka usage for caching and event bus.
- Existing Gateway + Workers patterns (routes, SSE streaming, tool executor) with refactors only where integration demands.
- Observability stack (Prometheus metrics, alerting templates, structured logging, tracing propagation) extended to include Somabrain call metrics.

### Removed / Replaced Items (True Legacy Only)
- Placeholder OPA middleware (local no‑op) → replaced by real HTTP policy adapter against Somabrain policy endpoint.
- Direct scattered `os.getenv` feature flag checks → replaced by Feature Registry + Somabrain tenant overrides.
- Duplicate health endpoints / inconsistent probes → converge on unified `/healthz` logic with Somabrain upstream probe.
- Any residual polling or deprecated endpoints (CSRF, legacy /poll) in UI → SSE-only pattern enforced.

### Integration Surface Mapping
| Concern | Somabrain Endpoint | SomaAgent01 Call Site | Notes |
|---------|--------------------|-----------------------|-------|
| Health | `GET /healthz` (fallback `/health`) | Gateway `/healthz`, outbox sync health probe | Classify normal/degraded/down; propagate metrics |
| Weights (read) | `GET /v1/weights` | Conversation prompt assembly pre-invoke | Embed weights into LLM context |
| Weights (update) | `POST /v1/weights/update` | Tool/result feedback handler | Reward/TD adjustments; idempotent key |
| Context build | `POST /v1/context/build` | Conversation loop before LLM invoke | Includes τ temperature & segmentation |
| Recall | `POST /v1/recall/query` | Optional recall enrichment stage | Tenant/session scoping & top‑k memory slice |
| Feature flags | `GET /v1/flags/{tenant}/{flag}` | Registry tenant override layer & `/v1/feature-flags` endpoint | TTL cache + fallback to profile defaults |
| Policy (OPA) | policy evaluate endpoint (exact path from Somabrain) | Gateway middleware & workers (memory/tool actions) | Fail‑closed unless configured fail‑open dev |
| Memory write | `POST /v1/memory/remember` | Tool executor & conversation worker write-through | Local WAL/outbox remains for durability |
| Memory link | `POST /v1/memory/link` | Async post-write linking task | Non-blocking; logs failures |
| Plan suggest | `POST /v1/plan/suggest` | Optional background suggestion trigger | Best-effort enhancement |

### Data Flow (Updated)
User → Gateway → (Policy check via Somabrain) → Conversation Worker → Context + Weights from Somabrain → LLM Invoke → Tool Executor (tool calls) → Memory write-through (Somabrain) + local WAL → Kafka publish (standard headers) → UI SSE stream.

### Observability Extensions
- New metrics: `somabrain_request_duration_seconds{endpoint,method}`, `somabrain_requests_total{endpoint,status}`, `learning_updates_total{outcome}`, `learning_context_build_duration_seconds`, `feature_flag_remote_requests_total{flag,tenant,result}`.
- Alerts: Somabrain error rate spike, policy denial surge, recall latency p95 > threshold.

### Reliability & Degrade Strategy
- If Somabrain recall or context build fails → degrade: skip enrichment but continue chat; feature state reported as `degraded`.
- If policy endpoint unavailable and fail‑closed → deny write/tool ops with clear error; if fail‑open (dev only) → proceed and metric logs decision.
- If memory write fails upstream → enqueue in local outbox for retry while preserving local persistence.

### Security Enforcement
- All memory writes/tool executions behind real policy evaluation; audit includes decision, tenant, action, resource.
- Feature flags controlling sensitive features (masking, error classification) originate from Somabrain overrides; local defaults only apply when remote unreachable (audited).

### Incremental Sprint Execution (High-Level)
- L0: Real policy adapter + health unification.
- L1: Tenant feature flag override integration + registry lint enforcement.
- L2: Weights/context injection + reward updates instrumentation.
- L3: Eventing/Kafka header standardization + trace linking.
- L4: UI hygiene and endpoint purge (legacy removal confirmation).

### Acceptance Summary
Upon completion of L4: all Somabrain responsibilities are exercised via HTTP endpoints; no stubbed legacy code remains; traces span entire request lifecycle; feature flags reflect tenant overrides; UI streams exclusively over SSE with enriched context and recall (when enabled).

### Next Immediate Action (Post-Append)
Start Sprint L0 implementation: swap OPA stub for HTTP adapter, centralized `/healthz` aggregator including Somabrain classification and new metrics.

This integration summary is now appended to the canonical roadmap and governs subsequent implementation decisions.

## 2025-11-09 Feature Expansion – Somabrain-Driven Additions & Readiness Matrix

This section enumerates net-new features that leverage Somabrain’s actual HTTP capabilities while preserving SomaAgent01’s durable, evented architecture. Each item lists readiness (Ready / Needs Instrumentation / Needs Extension), dependencies, and target metrics. These augment existing sprints and inform rapid development prioritization.

### Capability Reference (Somabrain HTTP Endpoints)
- Weights: `GET /v1/weights`, `POST /v1/weights/update`
- Context: `POST /v1/context/build`
- Feature Flags (tenant): `GET /v1/flags/{tenant}/{flag}`
- Recall: `POST /v1/recall/query`
- Policy: policy evaluate endpoint (OPA remote)
- Memory Ops: `POST /v1/memory/remember`, `POST /v1/memory/link`
- Planning: `POST /v1/plan/suggest`

### Feature Slate & Readiness
| Feature | Description | Readiness | Key Dependencies | Primary Metric |
|---------|-------------|-----------|------------------|----------------|
| Adaptive Context Orchestration | Dynamic prompt shaping using current weights + τ | Ready | weights, context.build | context_build_duration p95 |
| Reward-Driven Tuning | Tool/LLM outcomes → weights.update | Ready | weights.update | learning_updates_total |
| Proactive Semantic Suggestions | Background recall nudges for low-confidence turns | Ready (instrument) | recall.query | suggestion_latency p95 |
| Policy-Gated Auto-Actions | Safe auto-execution of low-risk plan steps | Instrument | policy evaluate, plan.suggest | auto_action_denied_total |
| Policy Explainability Console | View allow/deny trace details | Instrument | policy endpoint trace | policy_trace_latency |
| Learning KPI Dashboard | Surfacing reward volume & precision impact | Instrument | weights.update logs | recall_precision_delta |
| Recall Drift & Vector Health | Drift detection & re-embed trigger | Extension | recall.query + local stats | drift_events_total |
| Real-Time Tenant Flag Console | Merged effective flags per tenant | Ready | flags endpoint | flag_remote_latency p95 |
| Domain Profiles & Routing | Domain-based context/recall partitioning | Extension | context.build (tags) | domain_hit_ratio |
| Memory Graph Explorer | Visualize linked memory graph | Ready | memory.link | graph_nodes_rendered |
| Grounded Citations | Provenance inline with recall results | Instrument (verify payload) | recall.query metadata | citation_presence_rate |
| Cross-Session Surfacing | Suggest similar sessions for continuity | Instrument | recall.query (tenant scope) | session_overlap_suggestions |
| Safety Red Teaming Suite | Scheduled adversarial prompt tests | Ready | policy evaluate | redteam_findings_total |
| SLA-Aware Backpressure 2.0 | Dynamic outbox/WAL scaling via health & latency budgets | Ready | healthz, existing WAL | backpressure_activation_total |
| Data Retention & Privacy Zones | TTL & domain masking enforcement | Extension | policy + memory.write | retention_expiry_success_total |
| Delegated Sub-Tasks (Multi-Agent) | Plan decomposition into Celery task chains | Ready | plan.suggest + Celery | delegated_chain_duration |
| Experimentation Framework (A/B weights) | Variant weights evaluation + auto promote | Extension | weights.update (variant tagging) | variant_win_rate |

### Rapid Development Priority (Impact × Feasibility)
P0 (Ship first – core value, minimal friction): Adaptive Context, Reward Tuning, Real-Time Tenant Flag Console, SLA-Aware Backpressure 2.0, Proactive Semantic Suggestions (basic), Policy-Gated Auto-Actions (baseline deny/allow).
P1: Policy Explainability Console, Learning KPI Dashboard, Grounded Citations, Delegated Sub-Tasks.
P2: Recall Drift & Vector Health, Cross-Session Surfacing, Memory Graph Explorer, Data Retention & Privacy Zones.
P3: Domain Profiles & Routing, Experimentation Framework.

### Metrics to Add
- `somabrain_request_duration_seconds{endpoint,method}`
- `learning_updates_total{outcome}`
- `context_build_duration_seconds`
- `recall_query_duration_seconds` / `recall_results_total{hit}`
- `auto_actions_total{decision}`
- `policy_trace_requests_total` / `policy_trace_duration_seconds`
- `flag_remote_requests_total{flag,tenant,result}`
- `drift_events_total{cause}`

### Cross-Cutting Concerns
- **Tracing:** Ensure spans cover remote Somabrain calls with attributes (endpoint, tenant, status). Link Celery tasks via trace headers.
- **Security:** Auto-action feature always policy-gated + audit; never executes without explicit allow.
- **Degrade Modes:** Context build failure → fallback minimal prompt; recall failure → skip enrichment and mark feature degraded.
- **Caching:** Tenant flag lookups cached (TTL 1–2s); context and recall not cached (real-time relevance) except optional embedding LRU.

### Extension Requirements (Somabrain)
- Domain tagging in context/recall responses (for domain profile routing).
- Recall result provenance completeness (source type, id, created_at, confidence score).
- Policy trace endpoint providing decision path (rules matched, reasons) for explainability.
- Variant key in weights update payloads to support experimentation.

### Integration Risk Matrix
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Policy latency spike | Auto-actions stall | Local cache + circuit breaker |
| Recall cost growth | Token spend increases | Adaptive threshold & sampling |
| Drift false positives | Unnecessary re-embeds | Statistical smoothing (EWMA) |
| Flag endpoint instability | Feature gating inconsistency | TTL fallback + profile default audit |

### Immediate Follow-Up (Pre-Implementation)
1. Verify Somabrain recall payload includes provenance fields.
2. Confirm available policy trace capabilities; if absent, spec new endpoint.
3. Define reward mapping (tool result → scalar/feature vector) for weights updates.
4. Draft metrics additions & gauge cardinality review (avoid high-cardinality labels).

This feature expansion is now part of the canonical roadmap; future development must reference readiness classification and priority tiers before implementation.


