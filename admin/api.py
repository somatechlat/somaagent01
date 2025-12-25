"""Master API configuration for Django Ninja.

100% Pure Django Ninja - No FastAPI
"""

from __future__ import annotations

from functools import lru_cache

from ninja import NinjaAPI

from admin.common.handlers import register_exception_handlers


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
            pass  # Router already attached (autoreload)

    # =========================================================================
    # MOUNT ALL DOMAIN ROUTERS - 100% Django Ninja
    # =========================================================================

    # Auth (CRITICAL - must be first for login/token endpoints)
    from admin.auth.api import router as auth_router

    safe_add_router("/auth", auth_router)

    # SAAS Admin
    from admin.saas.api import router as saas_router

    safe_add_router("/saas", saas_router)

    # Core Infrastructure
    from admin.core.api import router as core_router

    safe_add_router("/core", core_router)

    # Agents
    from admin.agents.api import router as agents_router

    safe_add_router("/agents", agents_router)

    # Features
    from admin.features.api import router as features_router

    safe_add_router("/features", features_router)

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

    # Billing Webhooks (Lago)
    from admin.billing.webhooks import router as billing_webhooks_router

    safe_add_router("/webhooks", billing_webhooks_router)

    # SomaBrain Memory (cognitive memory)
    from admin.somabrain.api import router as somabrain_router

    safe_add_router("/somabrain", somabrain_router)

    # Invitations (standalone, not under /auth)
    from admin.auth.invitations import router as invitations_router

    safe_add_router("/invitations", invitations_router)

    # NOTE: MFA and Password Reset are now sub-routers in auth/api.py
    # /auth/mfa and /auth/password are mounted inside the auth router

    # Voice API (Whisper + Kokoro TTS)
    from admin.voice.api import router as voice_router

    safe_add_router("/voice", voice_router)

    # Workflows (Temporal)
    from admin.workflows.api import router as workflows_router

    safe_add_router("/workflows", workflows_router)

    # Data Export (GDPR)
    from admin.export.api import router as export_router

    safe_add_router("/export", export_router)

    # Observability (Prometheus, Tracing)
    from admin.observability.api import router as observability_router

    safe_add_router("/observability", observability_router)

    # Assets (Storage + Provenance)
    from admin.assets.api import router as assets_router

    safe_add_router("/assets", assets_router)

    # Capabilities (Registry + Circuit Breakers)
    from admin.capabilities.api import router as capabilities_router

    safe_add_router("/capabilities", capabilities_router)

    # Quality Gating (Asset Critic + Retry)
    from admin.quality.api import router as quality_router

    safe_add_router("/quality", quality_router)

    # A2A (Agent-to-Agent Workflows)
    from admin.a2a.api import router as a2a_router

    safe_add_router("/a2a", a2a_router)

    # Notifications (Real-time events)
    from admin.notifications.api import router as notifications_router

    safe_add_router("/notifications", notifications_router)

    # Analytics (Metrics and reports)
    from admin.analytics.api import router as analytics_router

    safe_add_router("/analytics", analytics_router)

    # Search (Full-text search)
    from admin.search.api import router as search_router

    safe_add_router("/search", search_router)

    # Config (System configuration + Feature flags)
    from admin.config.api import router as config_router

    safe_add_router("/config", config_router)

    # Rate Limiting (Quotas + Throttling)
    from admin.ratelimit.api import router as ratelimit_router

    safe_add_router("/ratelimit", ratelimit_router)

    # Scheduling (Background jobs + Celery)
    from admin.scheduling.api import router as scheduling_router

    safe_add_router("/scheduling", scheduling_router)

    # Templates (Agent + Prompt templates)
    from admin.templates.api import router as templates_router

    safe_add_router("/templates", templates_router)

    # Events (Real-time SSE streaming)
    from admin.events.api import router as events_router

    safe_add_router("/events", events_router)

    # Integrations (Third-party services)
    from admin.integrations.api import router as integrations_router

    safe_add_router("/integrations", integrations_router)

    # Plugins (Extensibility system)
    from admin.plugins.api import router as plugins_router

    safe_add_router("/plugins", plugins_router)

    # Backup (Disaster recovery)
    from admin.backup.api import router as backup_router

    safe_add_router("/backup", backup_router)

    # Audit (Security logging)
    from admin.audit.api import router as audit_router

    safe_add_router("/audit", audit_router)

    # Permissions (RBAC)
    from admin.permissions.api import router as permissions_router

    safe_add_router("/permissions", permissions_router)

    # API Keys (Programmatic access)
    from admin.apikeys.api import router as apikeys_router

    safe_add_router("/apikeys", apikeys_router)

    # Sessions (User session management)
    from admin.sessions.api import router as sessions_router

    safe_add_router("/sessions", sessions_router)

    # Webhooks (Outbound event delivery)
    from admin.webhooks.api import router as webhooks_router

    safe_add_router("/webhooks", webhooks_router)

    # Tenants (Multi-tenant management)
    from admin.tenants.api import router as tenants_router

    safe_add_router("/tenants", tenants_router)

    # Usage (Metering and billing)
    from admin.usage.api import router as usage_router

    safe_add_router("/usage", usage_router)

    # Conversations (Chat management)
    from admin.conversations.api import router as conversations_router

    safe_add_router("/conversations", conversations_router)

    # Users (User management)
    from admin.users.api import router as users_router

    safe_add_router("/users", users_router)

    # Tools (Agent tools)
    from admin.tools.api import router as tools_router

    safe_add_router("/tools", tools_router)

    # Files V2 (Enhanced file management)
    from admin.filesv2.api import router as filesv2_router

    safe_add_router("/filesv2", filesv2_router)

    # Knowledge (RAG document retrieval)
    from admin.knowledge.api import router as knowledge_router

    safe_add_router("/knowledge", knowledge_router)

    # Embeddings (Vector generation)
    from admin.embeddings.api import router as embeddings_router

    safe_add_router("/embeddings", embeddings_router)

    # Prompts (Prompt templates)
    from admin.prompts.api import router as prompts_router

    safe_add_router("/prompts", prompts_router)

    # Models (LLM catalog)
    from admin.models.api import router as models_router

    safe_add_router("/models", models_router)

    # Completions (LLM inference)
    from admin.completions.api import router as completions_router

    safe_add_router("/completions", completions_router)

    # Feedback (User ratings)
    from admin.feedback.api import router as feedback_router

    safe_add_router("/feedback", feedback_router)

    # Metrics (Operational telemetry)
    from admin.metrics.api import router as metrics_router

    safe_add_router("/metrics", metrics_router)

    # Logging API (Structured logging)
    from admin.logging_api.api import router as logging_api_router

    safe_add_router("/logging", logging_api_router)

    return api


# Create the singleton API instance
api = create_api()
