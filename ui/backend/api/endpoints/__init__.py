"""
Eye of God API - Endpoints Package
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT: Real endpoint barrel export
"""

from api.endpoints.settings import router as settings_router
from api.endpoints.themes import router as themes_router  
from api.endpoints.modes import router as modes_router
from api.endpoints.memory import router as memory_router

__all__ = [
    "settings_router",
    "themes_router",
    "modes_router",
    "memory_router",
]
