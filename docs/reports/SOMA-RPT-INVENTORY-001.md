# System Inventory

## Document Control

| Field | Value |
|---|---|
| Document Title | System Inventory |
| Document Identifier | SOMA-RPT-INVENTORY-001 |
| Version | 1.1.0 |
| Date | 2026-10-03 |
| Status | Draft |
| Author | SomaTech Engineering |
| Approver | — |
| Classification | Internal |
| ISO Reference | ISO 9001:2015 — Quality Management Systems — Requirements |
| Next Review | 2027-01-03 |

## Revision History

| Version | Date | Author | Description |
|---|---|---|---|
| 1.0.0 | 2026-09-28 | SomaTech Engineering | Initial issue. Brought under ISO document control. |
| 1.1.0 | 2026-10-03 | SomaTech Engineering | Re-derived from the tree. Removed `admin.features` (never existed as a package; `admin/core/features/` was deleted in `b98bbb2d`) and ChromaDB (zero code or infra presence). `admin.aaas` no longer does billing — commerce tables dropped in migration `0006`. Vector store is Milvus only, reached via SomaBrain (T-1), not managed by `admin.memory`. Service list expanded to every `services/*/` directory. |


**Architecture Version**: 2.0 (Django Migration Complete)
**Re-derived**: 2026-10-03 from `ls admin/*/` and `ls services/*/`.

## Django Apps (`admin/`)

Directories under `admin/` at time of re-derivation. One line each, from the
module's own responsibility. `admin/api.py` is the master Django Ninja router
(a file, not a package).

1.  **`admin.aaas`**: Multi-tenancy, identity, sessions, profiles. No billing — commerce tables (`SubscriptionTier`, `UsageRecord`) were dropped in `admin/aaas/migrations/0006_drop_commerce_tables.py`.
2.  **`admin.agents`**: Agent lifecycle & configuration.
3.  **`admin.assets`**: Asset records.
4.  **`admin.auth`**: Authentication (login, token, OAuth, SSO).
5.  **`admin.bridges`**: External messaging bridges (e.g. WhatsApp).
6.  **`admin.capsules`**: Capsule definitions and instances.
7.  **`admin.chat`**: Chat API endpoints.
8.  **`admin.common`**: Shared utilities, messages, auth helpers.
9.  **`admin.config`**: Configuration surfaces.
10. **`admin.core`**: Chat orchestrator, models, agentiq, context, helpers. **No** `budget/` and **no** `features/` — both deleted in `b98bbb2d`.
11. **`admin.embeddings`**: Embedding model profiles and API.
12. **`admin.files`**: File management & storage.
13. **`admin.filesv2`**: File storage v2.
14. **`admin.flink`**: Stream-processing hooks.
15. **`admin.gateway`**: Gateway-side request handling.
16. **`admin.llm`**: LLM integration & provider abstraction.
17. **`admin.logging_api`**: Logging API surface.
18. **`admin.memory`**: Memory integration hooks (not an SFM client — T-1).
19. **`admin.modules`**: Capsule module system.
20. **`admin.multimodal`**: Vision & audio processing.
21. **`admin.notifications`**: Alerting.
22. **`admin.observability`**: Observability surfaces.
23. **`admin.orchestrator`**: Service orchestration.
24. **`admin.plugins`**: Plugin surfaces.
25. **`admin.quality`**: Quality gates.
26. **`admin.ratelimit`**: Rate-limit surfaces.
27. **`admin.secrets`**: Secrets surfaces (Vault-backed).
28. **`admin.sessions`**: Session surfaces.
29. **`admin.somabrain`**: SomaBrain-facing API router.
30. **`admin.tools`**: Tool execution engine.
31. **`admin.ui`**: UI backend surfaces.
32. **`admin.utils`**: Cross-cutting utilities.
33. **`admin.voice`**: Speech-to-text & TTS.

## Services (`services/`)

Executable services managed by Docker / supervisord.

-   **`services.gateway`**: ASGI entrypoint, Django settings, URL routing, WebSocket consumers.
-   **`services.common`**: Shared modules, including the T-1 memory seam (`memory_contract.py`, `memory_gateway.py`, `adapters/somabrain_adapter.py`).
-   **`services.conversation_worker`**: Kafka/Temporal async chat processor.
-   **`services.tool_executor`**: Secure tool sandbox.
-   **`services.memory_replicator`**: Replays the agent WAL into SomaBrain via `MemoryGateway` (T-1).
-   **`services.delegation_gateway`**: Agent-to-agent coordination.
-   **`services.delegation_worker`**: Delegation worker.
-   **`services.bridge_worker`**: Bridge drivers.
-   **`services.multimodal`**: Multimodal processing.

## Infrastructure

-   **PostgreSQL**: Primary data store (Django ORM).
-   **Redis**: Cache, sessions, rate-limit backend (`services/common/rate_limiter.py`).
-   **Kafka**: Event bus (`services/common/event_bus.py`).
-   **Milvus**: Vector store. **Not ChromaDB** — there is zero ChromaDB code or infrastructure in this repository. Milvus is owned by SomaBrain/SFM; the agent reaches memory only through SomaBrain (T-1) and never holds an SFM or Milvus client.
-   **Vault**: Secrets (house policy: Vault-only, no `.env` secrets).
-   **Keycloak**: Identity (OIDC).
-   **SpiceDB / OPA**: Authorization. `UnifiedGate` makes real gRPC/HTTP calls; some high-level RBAC endpoints remain stubbed.
