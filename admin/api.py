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
    # MOUNT DOMAIN ROUTERS
    # =========================================================================
    
    # SAAS Admin (complete)
    from admin.saas.api import router as saas_router
    api.add_router("/saas", saas_router)
    
    # Core Admin
    from admin.core.api import router as core_router
    api.add_router("/core", core_router)
    
    # Agents
    from admin.agents.api import router as agents_router
    api.add_router("/agents", agents_router)
    
    # Features (placeholder for M3)
    from admin.features.api import router as features_router
    api.add_router("/features", features_router)
    
    # Chat (placeholder for M4)
    from admin.chat.api import router as chat_router
    api.add_router("/chat", chat_router)
    
    # Files (placeholder for M5)
    from admin.files.api import router as files_router
    api.add_router("/files", files_router)
    
    # Utils (placeholder for M6)
    from admin.utils.api import router as utils_router
    api.add_router("/utils", utils_router)
    
    return api


# Create the singleton API instance
api = create_api()
