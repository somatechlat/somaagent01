"""Eye of God Django Ninja API Router.

Per Eye of God UIX Design Section 3.1

VIBE COMPLIANT:
- Real implementation (no stubs)
- JWT Bearer authentication
- Version 2.0.0 API
"""

from ninja import NinjaAPI
from ninja.security import HttpBearer
from typing import Optional
import jwt
import os
import logging

LOGGER = logging.getLogger(__name__)


class BearerAuth(HttpBearer):
    """JWT Bearer token authentication."""
    
    def authenticate(self, request, token: str) -> Optional[dict]:
        """
        Validate JWT token and return user info.
        
        Args:
            request: HTTP request
            token: Bearer token string
            
        Returns:
            User dict with id, tenant_id, role or None if invalid
        """
        try:
            secret = os.getenv('JWT_SECRET', 'dev-secret')
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            
            return {
                'user_id': payload.get('sub'),
                'tenant_id': payload.get('tenant_id'),
                'role': payload.get('role', 'member'),
                'email': payload.get('email'),
            }
        except jwt.ExpiredSignatureError:
            LOGGER.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            LOGGER.warning(f"Invalid JWT token: {e}")
            return None


# Main API instance
api = NinjaAPI(
    title="Eye of God API",
    version="2.0.0",
    urls_namespace="eog_api",
    auth=BearerAuth(),
    docs_url="/docs",
    openapi_url="/openapi.json",
    description="SomaAgent01 Eye of God UIX API - Django Ninja implementation",
)


# Health check endpoint (no auth required)
@api.get("/health", auth=None, tags=["System"])
def health_check(request):
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


# Import and register endpoint routers
from api.endpoints.settings import router as settings_router
from api.endpoints.themes import router as themes_router
from api.endpoints.modes import router as modes_router
from api.endpoints.memory import router as memory_router

# Register all routers
api.add_router("/settings", settings_router)
api.add_router("/themes", themes_router)
api.add_router("/modes", modes_router)
api.add_router("/memory", memory_router)

