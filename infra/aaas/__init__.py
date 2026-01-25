"""
AAAS - Agent As A Service Infrastructure Package.

This package contains the unified deployment configuration for running
all three SOMA components (Agent, Brain, Memory) as a single entity.

SomaAgent01 is the MASTER orchestrator.
SomaBrain and SomaFractalMemory are integrated as libraries.
"""

__version__ = "2.0.0"
__all__ = ["unified_settings", "unified_urls", "unified_wsgi", "unified_asgi", "db_router"]
