"""Master API configuration for Django Ninja.

100% Pure Django Ninja - No FastAPI
"""

from __future__ import annotations

from ninja import NinjaAPI

from admin.common.handlers import register_exception_handlers


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
    # MOUNT ALL DOMAIN ROUTERS - 100% Django Ninja
    # =========================================================================
    
    # SAAS Admin
    from admin.saas.api import router as saas_router
    api.add_router("/saas", saas_router)
    
    # Core Infrastructure
    from admin.core.api import router as core_router
    api.add_router("/core", core_router)
    
    # Agents
    from admin.agents.api import router as agents_router
    api.add_router("/agents", agents_router)
    
    # Features
    from admin.features.api import router as features_router
    api.add_router("/features", features_router)
    
    # Chat
    from admin.chat.api import router as chat_router
    api.add_router("/chat", chat_router)
    
    # Files & Attachments
    from admin.files.api import router as files_router
    api.add_router("/files", files_router)
    
    # Utils
    from admin.utils.api import router as utils_router
    api.add_router("/utils", utils_router)
    
    # Tools (NEW)
    from admin.tools.api import router as tools_router
    api.add_router("/tools", tools_router)
    
    # UI / Skins (NEW)
    from admin.ui.api import router as ui_router
    api.add_router("/ui", ui_router)
    
    # Multimodal (NEW)
    from admin.multimodal.api import router as multimodal_router
    api.add_router("/multimodal", multimodal_router)
    
    # Memory (NEW)
    from admin.memory.api import router as memory_router
    api.add_router("/memory", memory_router)
    
    # Gateway Operations (NEW)
    from admin.gateway.api import router as gateway_router
    api.add_router("/gateway", gateway_router)
    
    # Capsules (NEW)
    from admin.capsules.api import router as capsules_router
    api.add_router("/capsules", capsules_router)
    
    # Notifications (NEW)
    from admin.notifications.api import router as notifications_router
    api.add_router("/notifications", notifications_router)
    
    return api


# Create the singleton API instance
api = create_api()
