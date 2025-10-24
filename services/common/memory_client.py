"""Deprecated: legacy MemoryService client has been removed.

This module was part of the retired gRPC-based memory_service. All code paths
must use `python.integrations.soma_client.SomaClient` instead. Importing this
module now raises an ImportError to surface accidental usage.
"""

raise ImportError(
    "services.common.memory_client is removed. Use python.integrations.soma_client.SomaClient."
)

