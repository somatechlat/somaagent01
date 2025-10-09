# Sprint Status – October 2025

This snapshot tracks delivery progress against the multi-sprint plan in `SPRINT_PLAN.md` and `ROADMAP_SPRINTS.md`. Status values use the following shorthand:

- ✅ **Complete** – Delivered and validated with automated tests.
- ⚠️ **Partial** – Key work shipped, but material gaps or follow-ups remain.
- ⏳ **Pending** – Not yet implemented in this codebase.

## Sprint 1 – API Stabilisation (✅ Complete)
- ✅ Cached OpenAPI schema served at `/openapi.json` and `/v1/openapi.json` via FastAPI override in `services/gateway/main.py`.
- ✅ All gateway routes refactored under the `/v1` namespace while preserving legacy aliases.
- ✅ Integration suite (`tests/integration/test_gateway_public_api.py`) exercises health, OpenAPI, and queue endpoints with `httpx.AsyncClient`.
- ✅ CI workflow `.github/workflows/ci.yml` runs Ruff lint + pytest on every PR.
- ✅ API docs refreshed in `docs/SomaAgent01_API.md`; version header middleware now injects `X-API-Version` automatically.

## Sprint 2 – Security & Governance (⚠️ Partial)
- ✅ JWT validation with Vault-backed secrets (`services/gateway/main.py`, `services/common/vault_secrets.py`).
- ✅ OPA decision hook and OpenFGA tenant checks enforced in `authorize_request`.
- ✅ Security-focused pytest coverage (`tests/unit/test_gateway_authorization.py`, denial scenarios) maintained.
- ⚠️ API key self-service UI exists only as prototype flows in `webui/js/settings.js`; finish hardening and wiring to a `/v1/keys` backend when available.
- ⚠️ Audit logging currently leverages structured logger calls but lacks a dedicated `gateway.audit` channel and SIEM integration docs.

## Sprint 3 – Observability & Resilience (⚠️ Partial)
- ✅ Shared OpenTelemetry utilities (`services/common/tracing.py`, `services/common/trace_context.py`) instrument FastAPI, HTTPX, asyncpg, and Redis.
- ✅ Circuit-breaker helpers delivered in `python/helpers/circuit_breaker.py` with pytest coverage (`tests/unit/test_circuit_breaker_*`).
- ⚠️ Prometheus alerts are in place (`infra/observability/alerts.yml`), but Grafana dashboards were removed from the default stack; recreate curated dashboards and document import steps.
- ⚠️ No automated load-test harness (Locust/k6) checked into `tests/` or `scripts/`; add scenarios targeting 500 concurrent sessions.
- ⚠️ Alerting rules reference legacy telemetry worker—needs pruning or replacement now that the worker is optional.

## Sprint 4 – Marketplace & Extensions (⚠️ Partial)
- ✅ Capsule registry FastAPI service (`services/capsule_registry/main.py`) persists metadata in Postgres, supports Cosign signing, and installs capsules under `/capsules/installed`.
- ✅ Gateway proxies exposed at `/v1/capsules/*` (and legacy `/capsules/*` aliases) bridge UI clients to the registry with unified auth/telemetry.
- ✅ Marketplace UI (`webui/marketplace.html` + `/webui/js/marketplace.js`) lists capsules, surfaces signatures, and issues one-click installs entirely through the gateway.
- ✅ Capsule SDK (`python/somaagent/capsule.py`) and GitHub Actions workflow (`.github/workflows/capsule.yml`) cover CLI usage and CI publish loop.
- ⚠️ Follow-up: expand UI to show install progress/history and document enterprise approval flows before marking the sprint fully complete.

## Sprint 5 – Performance & Scaling (⏳ Pending)
- Kafka partition scaling, autoscaling manifests, Redis tool-result caching, and benchmark suites are not yet implemented in this branch.

## Recommended Next Steps
1. Harden the API-key UI and wire it to a managed `/v1/keys` backend before claiming Sprint 2 completion.
2. Reintroduce Grafana dashboards (JSON exports) and link them from `docs/monitoring_quickstart.md`.
3. Check in a lightweight Locust or k6 harness under `tests/load/` with CI smoke targets.
4. Prune the legacy telemetry alert from Prometheus or ensure the service is part of the default stack.
5. For future sprints, create issues per outstanding item and track them on the project board referenced in `SPRINT_PLAN.md`.
