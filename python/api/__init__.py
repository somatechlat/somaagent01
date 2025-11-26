"""
FastAPI API module for SomaAgent01 with FastA2A integration.
Provides HTTP endpoints for task triggering and monitoring.
"""

from .router import app, router

__all__ = ["app", "router"]
