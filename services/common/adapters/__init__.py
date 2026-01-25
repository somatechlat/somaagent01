"""
Triad Service Adapters - Factory Functions for Brain and Memory Access.

This module provides the central factory functions that return the appropriate
adapter based on deployment mode:

- SOMA_SINGLE_PROCESS=true → DirectBrainAdapter, DirectMemoryAdapter
- SOMA_SINGLE_PROCESS=false → HTTPBrainAdapter, HTTPMemoryAdapter

VIBE Compliance:
- Rule 100: Centralized configuration
- Rule 2: Real implementations only
"""

from __future__ import annotations

import os
import logging

from services.common.protocols import BrainServiceProtocol, MemoryServiceProtocol

logger = logging.getLogger(__name__)

# Deployment mode detection
SOMA_SINGLE_PROCESS = os.environ.get("SOMA_SINGLE_PROCESS", "false").lower() == "true"
SOMA_AAAS_MODE = os.environ.get("SOMA_AAAS_MODE", "false").lower() == "true"


def get_brain_service() -> BrainServiceProtocol:
    """
    Factory function to get the appropriate Brain service adapter.

    Returns:
        - DirectBrainAdapter if SOMA_SINGLE_PROCESS=true
        - HTTPBrainAdapter if SOMA_SINGLE_PROCESS=false
    """
    if SOMA_SINGLE_PROCESS:
        logger.info("🧠 Using DirectBrainAdapter (single-process mode)")
        from services.common.adapters.brain_direct import get_direct_brain_adapter

        return get_direct_brain_adapter()
    else:
        logger.info("🌐 Using HTTPBrainAdapter (distributed mode)")
        from services.common.adapters.brain_http import get_http_brain_adapter

        return get_http_brain_adapter()


def get_memory_service(namespace: str = "default") -> MemoryServiceProtocol:
    """
    Factory function to get the appropriate Memory service adapter.

    Args:
        namespace: Memory namespace for isolation

    Returns:
        - DirectMemoryAdapter if SOMA_SINGLE_PROCESS=true
        - HTTPMemoryAdapter if SOMA_SINGLE_PROCESS=false
    """
    if SOMA_SINGLE_PROCESS:
        logger.info("💾 Using DirectMemoryAdapter (single-process mode)")
        from services.common.adapters.memory_direct import get_direct_memory_adapter

        return get_direct_memory_adapter(namespace=namespace)
    else:
        logger.info("🌐 Using HTTPMemoryAdapter (distributed mode)")
        from services.common.adapters.memory_http import get_http_memory_adapter

        return get_http_memory_adapter(namespace=namespace)


# Convenience exports
__all__ = [
    "get_brain_service",
    "get_memory_service",
    "BrainServiceProtocol",
    "MemoryServiceProtocol",
    "SOMA_SINGLE_PROCESS",
    "SOMA_AAAS_MODE",
]
