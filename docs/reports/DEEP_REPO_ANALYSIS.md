# SomaAgent01 Deep Repo Analysis

Date: 2026-01-25

This report reflects a deep scan of code, docs, and infra in the repo. It focuses on architectural overlap, duplicated logic, drift between docs and code, and concrete defects/risks found in the current implementation.

## Scope and method

Scanned: top-level layout, docs, infra compose files, core service modules, auth/chat pipelines, configuration systems, and frontend views.

High-signal files reviewed include:
- `AGENT.md`
- `docs/README.md`, `docs/deployment/DEPLOYMENT.md`, `docs/deployment/DEPLOYMENT_MODES.md`, `docs/standards/SOMA_TOKEN_FORMAT.md`, `docs/design/INVENTORY.md`
- `infra/standalone/docker-compose.yml`, `infra/aaas/docker-compose.yml`
- `admin/api.py`, `admin/auth/api.py`, `admin/common/auth.py`, `admin/common/session_manager.py`
- `admin/chat/api/chat.py`, `admin/conversations/api.py`, `admin/core/chat_orchestrator.py`
- `services/common/chat_service.py` and `services/common/chat/*`
- `services/common/simple_context_builder.py`, `services/common/simple_governor.py`
- `services/common/model_router.py`, `admin/core/model_router.py`
- `services/gateway/auth.py`, `services/common/authorization.py`
- `services/common/spicedb_client.py`, `services/common/openfga_client.py`
- `services/gateway/consumers/chat.py`
- `config/settings_registry.py`, `services/gateway/settings.py`, `admin/core/infrastructure/settings_api.py`
- `webui/src/views/*`

## Repo shape (quick signal)

- Python files: 670
- Web UI views: 94 TypeScript view files under `webui/src/views`

The system is a large modular monolith with a gateway service, plus extensive infra and SRS documentation.

## Major documentation drift and inconsistencies

These are concrete mismatches that will mislead implementation, deployment, or onboarding.

1) Missing/incorrect referenced docs and files
- `AGENT.md` references `docs/development/VIBE_CODING_RULES.md`, but that file does not exist.
- Root `README.md` is empty, while `docs/README.md` is the actual entry point.
- `docs/README.md` and `docs/deployment/DEPLOYMENT.md` reference a top-level `docker-compose.yml`, but the repo only includes compose files under `infra/` (e.g. `infra/standalone/docker-compose.yml`, `infra/aaas/docker-compose.yml`).

2) Port namespace mismatches
- `docs/deployment/DEPLOYMENT.md` mixes 20xxx and default ports (e.g. Postgres 5432, Redis 6379, Milvus 19530).
- `infra/standalone/docker-compose.yml` uses 20xxx ports (e.g. Postgres 20432, Redis 20379).
- `infra/aaas/docker-compose.yml` uses 63xxx ports (e.g. Postgres 63932, Redis 63979, Milvus 63953).
This is a major source of confusion for local vs AAAS deployments.

3) Deployment mode taxonomy conflicts
- `docs/deployment/DEPLOYMENT_MODES.md` uses `SA01_DEPLOYMENT_MODE="AAAS"` or `"STANDALONE"`.
- `config/settings_registry.py` also supports `STANDALONE` and `AAAS`.
- `admin/core/management/commands/preflight.py` enforces only `DEV` or `PROD`.
This is a direct contradiction between docs and runtime validation.

4) Environment variable naming conflicts
- `services/gateway/settings.py` uses `SA01_*` variables (e.g. `SA01_KEYCLOAK_URL`).
- `admin/common/auth.py` expects `KEYCLOAK_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`.
- `admin/core/infrastructure/settings_api.py` reads legacy names like `POSTGRES_HOST`, `REDIS_URL`, `KAFKA_BROKERS`, `KEYCLOAK_URL`.
- `admin/core/management/commands/preflight.py` explicitly forbids legacy env names (e.g. `POSTGRES_DSN`, `REDIS_URL`).
This creates a split-brain config system where different subsystems cannot be configured consistently.

5) Docs list components/services not present in code
- `docs/design/INVENTORY.md` lists `services.conversation_worker`, `services.tool_executor`, `services.memory_replicator`, `services.delegation_gateway` but these folders are not in the repo.
- `docs/README.md` cites ChromaDB as a vector store option, but no ChromaDB integration exists in code or infra.

## Architectural overlap and duplication

These are parallel implementations of the same concept that are likely to drift or conflict.

1) Chat pipeline duplication (four concurrent flows)
- `admin/chat/api/chat.py` implements chat endpoints with direct DB access + SomaBrain interactions.
- `admin/conversations/api.py` implements overlapping conversation endpoints and calls `services/common/chat_service.py` (but this router is not mounted in `admin/api.py`).
- `services/common/chat_service.py` + `services/common/chat/*` implement a split chat pipeline with SimpleGovernor, ContextBuilder, ModelRouter, and memory bridge.
- `admin/core/chat_orchestrator.py` defines a separate 12-phase pipeline (V3 Chat Orchestrator) with different abstractions (AgentIQ, ToolDiscovery).
This is a major architectural split: there is no single canonical chat pipeline. Behavior, telemetry, and correctness will diverge.

2) Model routing duplication
- `admin/core/model_router.py` and `services/common/model_router.py` both implement model selection and capability detection.
These are different implementations with similar APIs and will inevitably diverge.

3) Context building duplication
- `services/common/simple_context_builder.py` provides a concrete context builder with SomaBrain + circuit breaker integration.
- `admin/core/application/use_cases/conversation/build_context.py` defines a parallel context building use case and protocol-based interface.
Multiple entry points exist for building context, with no unifying abstraction or wiring.

4) Session management duplication
- `admin/common/session_manager.py` implements Redis-backed auth sessions for users.
- `services/common/chat/session_manager.py` manages agent sessions tied to conversations, but uses the same class name `SessionManager`.
The identical class name with different semantics is a source of confusion and import collisions.

5) Authorization stack duplication
- JWT validation is in `admin/common/auth.py` (JOSE) and `services/gateway/auth.py` (PyJWT).
- Policy enforcement exists in `services/common/authorization.py` (OPA) and also in `services/gateway/auth.py` (OPA).
- Fine-grained auth has both `services/common/spicedb_client.py` and `services/common/openfga_client.py`.
There is no single source of truth for authz decisions; multiple systems co-exist without a clear ownership boundary.

6) Brain/Memory adapters in parallel
- `admin/core/somabrain_client.py` provides a SomaBrain client.
- `services/common/adapters/brain_http.py`, `services/common/adapters/brain_direct.py`, `services/common/adapters/memory_http.py`, `services/common/adapters/memory_direct.py` implement parallel client layers.
This duplicates the "how to talk to SomaBrain/Memory" logic.

## Concrete implementation gaps and defects

These are direct issues in current code that can cause errors or hidden no-ops.

1) Incomplete code path in message sending
- `services/common/chat/message_service.py` has an unfinished refactor with a literal `pass` and inline "let's fix" commentary in the middle of the critical message-storage path.
This is a high-risk logic defect: the user message storage logic is inconsistent and likely to behave unpredictably.

2) Placeholder logic still in core path
- `admin/core/chat_orchestrator.py` returns placeholder LLM output in `_invoke_llm`.
- `admin/core/tool_system.py` has a placeholder MCP tool execution path.
- `admin/a2a/api.py` describes a "placeholder" tool execution.
- `admin/somabrain/api.py` uses a placeholder tenant extraction.
- `admin/multimodal/execution.py` returns placeholder output for image/diagram/screenshot paths.
The placeholders are in high-value paths; they must be either implemented or explicitly removed from production routes.

3) TODOs in production-critical paths
- `admin/core/budget/gate.py` has a TODO for tenant-level toggles in `_is_metric_enabled`.
Given this is a budget gate, leaving TODOs here undermines billing enforcement.

4) Orphaned or unmounted functionality
- `admin/conversations/api.py` implements real endpoints but is not mounted in `admin/api.py`, meaning it is not reachable.
This is likely dead code or a wiring bug.

## System-wide risk summary (from overlaps)

1) Behavioral divergence
Parallel implementations (chat, model routing, authz, context building) will produce different outputs depending on which pathway is invoked, undermining reliability and testability.

2) Security and compliance risk
Multiple auth systems (Keycloak JWT, OPA, SpiceDB, OpenFGA) without a clear authoritative layer introduces gaps, inconsistent authorization, and difficulty auditing.

3) Deployment fragility
Conflicting environment variable expectations and deployment mode taxonomies mean different services will fail to start or silently misconfigure.

4) Documentation trust gap
Significant doc drift makes it easy for developers or operators to run the system incorrectly, and it slows down onboarding.

## Recommendations (highest leverage)

1) Declare a single canonical chat pipeline
Pick one: `services/common/chat_service.py` (current production path) or `admin/core/chat_orchestrator.py` (V3 pipeline). Remove or hard-disable the other entry points, then update routers to use the canonical path only.

2) Consolidate model router and context builder
Merge `admin/core/model_router.py` and `services/common/model_router.py`. Do the same for context building. Create one public interface and one implementation, then route all call sites through it.

3) Unify deployment modes and env vars
Define the authoritative taxonomy for `SA01_DEPLOYMENT_MODE` (AAAS/STANDALONE vs DEV/PROD) and enforce it consistently in:
- `config/settings_registry.py`
- `services/gateway/settings.py`
- `admin/core/management/commands/preflight.py`
- docs under `docs/deployment/`

4) Resolve placeholder/unfinished code in the live path
Specifically fix `services/common/chat/message_service.py` (remove the `pass` and normalize the memory/write flow), then audit for other placeholder logic in production endpoints.

5) Repair docs to match reality
Update `docs/README.md`, `docs/deployment/DEPLOYMENT.md`, and `docs/design/INVENTORY.md` with:
- Correct compose file locations
- Actual port namespaces (20xxx vs 63xxx)
- Actual services that exist
- Actual env var names

## Suggested follow-up deliverables

- A dependency map or sequence diagram for the chosen canonical chat pipeline.
- A config schema document that defines the single source of truth for all env vars.
- A cleanup plan that removes or deprecates overlapping modules (authz, model routing, context building).

