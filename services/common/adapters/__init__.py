"""
Triad Service Adapters - Factory Functions for Brain and Memory Access.

This module provides the central factory functions that return the appropriate
adapter based on deployment mode:

- SOMA_AAAS_MODE=true  → DirectMemoryAdapter (in-process)
- SOMA_AAAS_MODE=false → HTTPMemoryAdapter (distributed)

VIBE Compliance:
- Rule 100: Centralized configuration
- Rule 2: Real implementations only
"""

from __future__ import annotations

import logging
import os

from services.common.protocols import MemoryServiceProtocol

logger = logging.getLogger(__name__)

# Deployment mode detection (canonical: SOMA_AAAS_MODE only)
SOMA_AAAS_MODE = os.environ.get("SOMA_AAAS_MODE", "false").lower() == "true"


def get_memory_service(namespace: str = "default") -> MemoryServiceProtocol:
    """
    Factory function to get the appropriate Memory service adapter.

    Args:
        namespace: Memory namespace for isolation

    Returns:
        - DirectMemoryAdapter if SOMA_AAAS_MODE=true (in-process)
        - HTTPMemoryAdapter if SOMA_AAAS_MODE=false (distributed)
    """
    if SOMA_AAAS_MODE:
        logger.info("💾 Using DirectMemoryAdapter (AAAS in-process mode)")
        from services.common.adapters.memory_direct import get_direct_memory_adapter

        return get_direct_memory_adapter(namespace=namespace)
    else:
        logger.info("🌐 Using HTTPMemoryAdapter (distributed mode)")
        from services.common.adapters.memory_http import get_http_memory_adapter

        return get_http_memory_adapter(namespace=namespace)


# Convenience exports
__all__ = [
    "get_memory_service",
    "MemoryServiceProtocol",
    "SOMA_AAAS_MODE",
]
