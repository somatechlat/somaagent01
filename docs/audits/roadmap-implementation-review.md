# Roadmap Implementation Review — somaAgent01 (2025-11-10)

This report summarizes how the current codebase aligns with the canonical roadmap in `docs/roadmap/`, highlights gaps and risks, and recommends prioritized next steps.

## Executive Summary
- Directionally aligned: core architectural intents are present — runtime config facade, feature registry, Somabrain wrappers, unified gateway surface, observability, notifications, scheduler compatibility, and SSE-first UI stance.
- Partial centralization: `services/common/runtime_config.py` and `ConfigRegistry` exist and are wired in the gateway, but many modules still read env vars directly for operational behavior.
- Integration scaffolding: Somabrain HTTP integration helpers and gateway proxy endpoints are implemented; Celery worker scaffolding exists; notifications and scheduler compatibility routes are present.
- Test/integration posture: A large test suite exists but requires local infra (Postgres, Kafka, OPA, Redis, Somabrain) and test-mode guards. Running `pytest -q` without infra yields broad failures dominated by event loop misuse and external dependency timeouts.

Net: The codebase has implemented a substantial portion of the roadmap’s architecture. The next wins are consolidating env access behind the facade, tightening async lifecycle for tests, and gating external dependencies in test-mode.

## What’s Implemented (Matches Roadmap)
- Configuration & Flags
  - `services/common/runtime_config.py`: C0 facade with `settings()`, `flag()`, `config_snapshot()`, and dynamic update hooks via `ConfigRegistry`.
  - `services/common/config_registry.py`: JSONSchema-backed snapshot with checksum/version and subscriber callbacks.
  - `services/common/features.py`: Feature descriptor schema with profiles and env migration overrides.

- Somabrain Integration
  - `python/integrations/somabrain_client.py`: HTTP helpers for weights, context, flags, update; compatibility alias to `SomaClient`.
  - Gateway endpoints: `/v1/weights`, `/v1/context`, `/v1/learning/reward`, `/v1/flags/{flag}` with basic metrics (`somabrain_requests_total`, latency histogram) and authorization hooks where applicable.

- Gateway Centralization (selected)
  - `services/gateway/main.py`: Consolidated metrics; SSE-first stance; notifications API with TTL janitor; scheduler compatibility endpoints; uploads with AV hooks; speech STT/TTS scaffolds; runtime overlays from UI settings; DLQ/outbox integration; config update listener consuming `config_updates`.
  - Health/readiness aliases (`/ready`, `/live`, `/healthz`) and Prometheus server startup with lazy aux initialization.

- Observability
  - `observability/metrics.py`: Rich collector with gauges/counters/histograms and helper APIs; mirrors feature profile/state; runtime config instrumentation.

- Stores & Infra Abstractions
  - Postgres-backed stores for sessions, outbox, memory replica, notifications, tool catalog, profiles, telemetry; Redis caches.
  - Event bus and durable publisher with WAL/outbox fallback.

- Roadmap Docs (comprehensive and current)
  - Canonical and consolidated roadmaps, dev-prod parity plan, sprint plans, No‑Legacy mandate, streaming/event-bus hardening, config/secrets hardening, Celery integration design.

## Gaps vs. Roadmap (Most Impactful)
1) Central Config Enforcement
   - Many modules still call `os.getenv` directly for operational behavior (beyond bootstrap/settings modules). Examples: gateway helpers for uploads, AV, speech, rate-limiters, and various services.
   - No lint/test gate yet for “no direct getenv outside config/bootstrap”.

2) Async Lifecycle & Test Mode
   - Tests fail broadly without infra; many “event loop already running/closed” errors indicate missing `pytest.mark.asyncio` or calling `asyncio.run()` under running loops in helpers/CLIs.
   - Background tasks and network clients (Aiokafka/asyncpg) start during tests and don’t always close cleanly, causing resource warnings and loop-close exceptions.

3) External Dependency Gating
   - Policy enforced paths return 403 in tests without a configured/mocked OPA/OpenFGA and Somabrain, breaking tool and ingest flows.
   - Kafka/Postgres connectivity assumed in many code paths; need clean short-circuits in TESTING mode or dependency stubs/mocks.

4) SSE/Event Bus Consolidation (UI)
   - Roadmap specifies a single client stream and central event bus. Server emits chat/tool events, but parity for scheduler/memory invalidations and unified UI bus is still a roadmap item.

5) Metrics Label Consistency
   - Prometheus collector reuse errors (“Incorrect label names”) suggest tests import multiple times with different label cardinality or redefinition. Needs consistent factories + reuse across test sessions.

6) Celery Integration
   - Worker scaffolding present (`services/celery_worker/`), but unified scheduler API (`/v1/ui/scheduler/*`) and flag-driven switching are not fully wired. Current scheduler routes are a compatibility layer.

## Quick Evidence Map (Files → Roadmap Items)
- Central config facade: `services/common/runtime_config.py` (C0 implemented). Registry: `services/common/config_registry.py`. Linter/test enforcement: missing.
- Somabrain integration: `python/integrations/somabrain_client.py`; gateway handlers in `services/gateway/main.py` (Phase 0 endpoints present).
- Notifications: `services/gateway/main.py` (API + TTL janitor); `services/common/notifications_store.py`.
- Scheduler: compatibility routes in gateway; no complete `/v1/ui/scheduler/*` yet.
- Observability: `observability/metrics.py`, gateway metrics server and rich counters/histograms.
- Dev‑prod parity: many elements present; env centralization and health‑gating incomplete in tests without infra.

## Recommended Next Steps (Prioritized)
P0 — Test Mode & Event Loop Hygiene (foundation)
- Add strict TESTING mode guards to skip background starters (Kafka producers, metrics server, periodic tasks). Ensure all test clients/CLIs avoid `asyncio.run()` within running loops; convert helpers to awaitables under `pytest.mark.asyncio`.
- Provide minimal in-memory/no-op adapters for bus/publisher/policy in TESTING to avoid external connections.

P1 — Config Centralization Enforcement
- Migrate high-impact env reads in gateway/services to `cfg.settings()`/`cfg.flag()` where feasible.
- Add linter rule and unit test (e.g., `tests/unit/test_no_direct_getenv.py`) to block stray `os.getenv(` outside `services/common/settings_*`, `runtime_config`, and specific bootstrap modules.

P2 — Policy/Dependency Stubs for Tests
- Introduce a test-mode policy client that deterministically allows/denies based on headers/markers to replace 403s in unit/integration tests.
- Add in-memory outbox/publisher option in TESTING to avoid Kafka/DB where the test intent is not persistence.

P3 — Scheduler API Canonicalization
- Implement `/v1/ui/scheduler/*` with adapter interface (`APScheduler` first), add JWT scopes, and bridge the existing compatibility routes until UI is migrated.

P4 — Metrics Consistency
- Ensure all metric collectors are created via helper factories that reuse existing collectors on repeated imports (pattern already used in gateway; extend across modules used in tests).

P5 — CI Parity Job & Docs
- Add a lightweight CI matrix job that runs with TESTING mode, dependency stubs, and skips infra-bound tests. Document local runbooks for full stack vs. TESTING.

## Risks & Mitigations
- Over-mocking can hide regressions: keep TESTING mode faithful to real code paths; use no-op transports with identical interfaces and record metrics to catch usage.
- Drift between facade and env: keep SA01Settings authoritative, and gradually route reads to it; publish “settings snapshot” at startup and in `/v1/health` for visibility.

## Verification Pointers
- After P0/P1: `pytest -q` should reduce failures from event loop errors and 403s to specific contract issues.
- Grep gate: repository-wide grep for `os.getenv(` outside allowed modules should return zero (or approved allowlist) once centralization completes.
- Gateway health: `/healthz` returns ok with Somabrain off only when strict-mode allows degrade; otherwise surfaces clear error with metrics.

---
Report generated by reading docs under `docs/roadmap/*`, scanning key modules (`services/*`, `integrations/*`, `python/integrations/*`, `observability/*`), and running the test suite locally (without external infra).
