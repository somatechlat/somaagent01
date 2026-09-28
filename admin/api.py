"""Master API Configuration for SomaAgent01.

This module creates and configures the master NinjaAPI instance that serves
as the central router for all SomaAgent01 API endpoints.

**Technology Stack**:
    - 100% Pure Django Ninja (NO FastAPI)
    - Django 5.0 ORM (NO SQLAlchemy)
    - Keycloak OIDC Authentication
    - SpiceDB Authorization

**Port**: 20020 (API), 20080 (Frontend)

**Router Registry**:
    The following routers are mounted at ``/api/v2/``:

    Authentication & Authorization:
        - ``/auth`` - Login, token refresh, OAuth, SSO, MFA
        - ``/permissions`` - RBAC permission management
        - ``/apikeys`` - API key management
        - ``/sessions`` - User session management

    Core Platform:
        - ``/aaas`` - AAAS administration
        - ``/core`` - Core infrastructure
        - ``/agents`` - Agent management
        - ``/chat`` - Chat sessions
        - ``/capsules`` - Agent capsule management

    Memory & Cognitive:
        - ``/memory`` - Memory integration
        - ``/somabrain`` - SomaBrain cognitive API
        - ``/knowledge`` - RAG document retrieval
        - ``/embeddings`` - Vector generation

    Infrastructure:
        - ``/audit`` - Security logging
        - ``/observability`` - Prometheus, tracing
        - ``/metrics`` - Operational telemetry
        - ``/flink`` - Stream processing

Example:
    >>> from admin.api import api
    >>> api.title
    'SomaAgent Platform API'


    - Rule 1: NO BULLSHIT - Real Django Ninja, no abstractions
    - Rule 4: REAL IMPLEMENTATIONS ONLY - Production-grade router

See Also:
    - :doc:`AGENT.md <../AGENT>` for complete architecture overview
    - :doc:`docs/standards/SOMA-STD-CODING-001.md <../docs/standards/SOMA-STD-CODING-001>`
"""

from __future__ import annotations

import importlib
import logging
from functools import lru_cache

from ninja import NinjaAPI

from admin.common.handlers import register_exception_handlers

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def create_api() -> NinjaAPI:
    """Create and configure the master NinjaAPI instance."""
    api = NinjaAPI(
        title="SomaAgent Platform API",
        version="2.0.0",
        description="Complete SomaAgent Platform API - 100% Django Ninja",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # Register global exception handlers
    register_exception_handlers(api)

    # =========================================================================
    # HELPER: Safe router addition (handles autoreload)
    # =========================================================================
    from ninja.errors import ConfigError as NinjaConfigError

    def safe_add_router(prefix: str, router):
        """Add router safely, skipping if already attached."""
        try:
            api.add_router(prefix, router)
        except NinjaConfigError:
            # Router already attached (autoreload safety)
            pass

    # =========================================================================
    # MOUNT ALL DOMAIN ROUTERS - 100% Django Ninja
    # =========================================================================

    # Auth (CRITICAL - must be first for login/token endpoints)
    from admin.auth.api import router as auth_router

    safe_add_router("/auth", auth_router)

    # AAAS Admin
    from admin.aaas.api import router as aaas_router

    safe_add_router("/aaas", aaas_router)

    # Core Infrastructure
    from admin.core.api import router as core_router

    safe_add_router("/core", core_router)

    # Agents
    from admin.agents.api import router as agents_router

    safe_add_router("/agents", agents_router)

    # Features (Migrated to Core Features System)
    # Feature flags admin — removed: unmounted and the package was dead.

    # Chat
    from admin.chat.api import router as chat_router

    safe_add_router("/chat", chat_router)

    # Files & Attachments
    from admin.files.api import router as files_router

    safe_add_router("/files", files_router)

    # Utils
    from admin.utils.api import router as utils_router

    safe_add_router("/utils", utils_router)

    # Tools (NEW)
    from admin.tools.api import router as tools_router

    safe_add_router("/tools", tools_router)

    # UI / Skins (NEW)
    from admin.ui.api import router as ui_router

    safe_add_router("/ui", ui_router)

    # Multimodal (NEW)
    from admin.multimodal.api import router as multimodal_router

    safe_add_router("/multimodal", multimodal_router)

    # Memory (NEW)
    from admin.memory.api import router as memory_router

    safe_add_router("/memory", memory_router)

    # Gateway Operations (NEW)
    from admin.gateway.api import router as gateway_router

    safe_add_router("/gateway", gateway_router)

    # Capsules (NEW)
    from admin.capsules.api import router as capsules_router

    safe_add_router("/capsules", capsules_router)

    # =========================================================================
    # NEW ROUTERS - 2025-12-24 Session
    # =========================================================================

    # SomaBrain Memory (cognitive memory)
    from admin.somabrain.api_router import router as somabrain_router

    safe_add_router("/somabrain", somabrain_router)

    # Invitations — removed: stub-only, no Invitation model exists
    # NOTE: MFA and Password Reset are now sub-routers in auth/api.py
    # /auth/mfa and /auth/password are mounted inside the auth router

    # Voice API (Whisper + Kokoro TTS)
    from admin.voice.api import router as voice_router

    safe_add_router("/voice", voice_router)

    # Workflows (Temporal) — removed: stub-only, no production impl

    # Data Export (GDPR) — removed: stub-only, no ExportTask model exists

    # Observability (Prometheus, Tracing)
    from admin.observability.api import router as observability_router

    safe_add_router("/observability", observability_router)

    # Assets (Storage + Provenance)
    from admin.assets.api import router as assets_router

    safe_add_router("/assets", assets_router)

    # Capabilities (Registry + Circuit Breakers) — removed: stub-only, no production impl
    # A2A (Agent-to-Agent Workflows) — removed: stub-only, no production impl

    # Quality Gating (Asset Critic + Retry)
    from admin.quality.api import router as quality_router

    safe_add_router("/quality", quality_router)

    # Notifications (Real-time events) — real store-backed router lives in admin.notifications.api package
    from admin.notifications.api import router as notifications_router

    safe_add_router("/notifications", notifications_router)

    # Analytics (Metrics and reports) — removed: stub-only, no production impl
    # Search (Full-text search) — removed: stub-only, no production impl

    # Config (System configuration + Feature flags)
    from admin.config.api import router as config_router

    safe_add_router("/config", config_router)

    # Rate Limiting (Quotas + Throttling)
    from admin.ratelimit.api import router as ratelimit_router

    safe_add_router("/ratelimit", ratelimit_router)

    # Scheduling (Background jobs + Celery) — removed: stub-only, no production impl
    # Events (Real-time SSE streaming) — removed: stub-only, no production impl

    # Integrations (Third-party services)
    from admin.integrations.api import router as integrations_router

    safe_add_router("/integrations", integrations_router)

    # Plugins (Extensibility system)
    from admin.plugins.api import router as plugins_router

    safe_add_router("/plugins", plugins_router)

    # Capsule Module host (WP D1) — real module registry + orchestrator hooks
    from admin.modules.api import router as modules_router

    safe_add_router("/modules", modules_router)

    # Bridge channel data model (WP D2) — Channel/BridgeSession/Inbound/Outbound
    from admin.bridges.api import router as bridges_router

    safe_add_router("/bridges", bridges_router)

    # Audit (Security logging)
    from admin.audit.api import router as audit_router

    safe_add_router("/audit", audit_router)

    # Permissions (RBAC) — removed: every handler minted a uuid4 and
    # returned {"created/updated/deleted": True} without touching Role.

    # Sessions (User session management)
    from admin.sessions.api import router as sessions_router

    safe_add_router("/sessions", sessions_router)

    # Webhooks (Outbound event delivery) — removed: create/rotate_secret
    # handed back signing secrets that were never stored.

    # Tenants (Multi-tenant management) — removed: a second facade over
    # admin.aaas.models.Tenant with its own incompatible schema. The real
    # CRUD is /aaas/tenants.

    # Usage (Metering and billing) — removed: reported measured zeros over
    # a real UsageRecord table it never queried.

    # Users (User management) — removed: delete_user claimed a GDPR
    # deletion while the account stayed live.

    # Files V2 (Enhanced file management)
    from admin.filesv2.api import router as filesv2_router

    safe_add_router("/filesv2", filesv2_router)

    # Knowledge (RAG document retrieval) — removed: get_document invented
    # a document for any id; search returned empty as if it had run.

    # Embeddings (Vector generation)
    from admin.embeddings.api import router as embeddings_router

    safe_add_router("/embeddings", embeddings_router)

    # Prompts (Prompt templates) — removed: get_prompt returned a canned
    # template for any id; rollback_version claimed a rollback it never did.

    # Models (LLM catalog) — removed: an unknown model id fell back to
    # gpt-4o data instead of 404. The real catalog is /llm.

    # LLM model settings (LLMModelConfig CRUD, providers, slots, presets) — C5
    from admin.llm.api import router as llm_config_router

    safe_add_router("/llm", llm_config_router)

    # Completions (LLM inference) — removed: every endpoint was 501, the real
    # inference path is the V3 chat orchestrator.
    # Feedback (User ratings) — removed: stub-only, submissions were discarded.

    # Metrics (Operational telemetry) — removed: /metrics published a
    # hardcoded Prometheus payload with invented counters. Fabricated
    # monitoring is worse than none.

    # Logging API (Structured logging)
    from admin.logging_api.api import router as logging_api_router

    safe_add_router("/logging", logging_api_router)

    # Traces (Distributed tracing) — removed: get_trace fabricated a span
    # tree for any trace id.

    # Auth Config (Hierarchical auth) — removed: update_platform_config
    # claimed an MFA/OAuth policy change it never persisted, and
    # test_platform_provider reported success without connecting.

    # Secrets (Credential management — Vault-backed provider keys, write-only)
    try:
        secrets_module = importlib.import_module("admin.secrets.api")
        safe_add_router("/secrets", secrets_module.router)
    except ModuleNotFoundError:
        logger.warning("Secrets router not found; /secrets is disabled.")

    # Orchestrator (Workflow coordination) — removed: fabricated
    # workflows, runs and pipelines. The real Temporal wiring is
    # services/delegation_gateway/temporal_worker.py.

    # Granular Permissions (RBAC V2) — removed: same fabricated CRUD as
    # /permissions; list_custom_roles was the only real reader.

    return api


# Create the singleton API instance
api = create_api()
