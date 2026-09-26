"""
Triad Service Adapters - Factory Functions for Brain and Memory Access.

This module provides the central factory functions that return the appropriate
adapter based on deployment mode:

- AAAS mode  → DirectMemoryAdapter (in-process)
- Standalone → HTTPMemoryAdapter (distributed)

VIBE Compliance:
- Rule 100: Centralized configuration via DeploymentMode
- Rule 2: Real implementations only
"""

from __future__ import annotations

import logging

from services.common.deployment_mode import DeploymentMode
from services.common.protocols import MemoryServiceProtocol

logger = logging.getLogger(__name__)


def get_memory_service(namespace: str = "default") -> MemoryServiceProtocol:
    """
    Factory function to get the appropriate Memory service adapter.

    Args:
        namespace: Memory namespace for isolation

    Returns:
        - DirectMemoryAdapter if AAAS mode (in-process)
        - HTTPMemoryAdapter if Standalone mode (distributed)
    """
    if DeploymentMode.is_aaas():
        logger.info('Using DirectMemoryAdapter (AAAS in-process mode)')
        from services.common.adapters.memory_direct import get_direct_memory_adapter

        return get_direct_memory_adapter(namespace=namespace)
    else:
        logger.info('Using HTTPMemoryAdapter (distributed mode)')
        from services.common.adapters.memory_http import get_http_memory_adapter

        return get_http_memory_adapter(namespace=namespace)


# Convenience exports
__all__ = [
    "get_memory_service",
    "MemoryServiceProtocol",
]
