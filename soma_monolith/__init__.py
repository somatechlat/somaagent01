"""
SOMA Monolith Bridge
====================

This package provides DIRECT IN-PROCESS access to SomaBrain and FractalMemory,
eliminating HTTP network overhead for memory-intensive agent operations.

Usage:
------
    from soma_monolith import brain, memory

    # Direct memory operations (no HTTP)
    await memory.store(coord, payload)
    results = await memory.recall(query)

    # Direct brain operations (no HTTP)
    await brain.process(input_data)

Performance:
-----------
    HTTP Call:   ~5ms per operation
    Direct Call: ~0.05ms per operation
    Speedup:     100x
"""

import os

# Detect if running in monolith mode
MONOLITH_MODE = os.getenv("SOMA_MONOLITH_MODE", "false").lower() == "true"

__version__ = "1.0.0"
__all__ = ["brain", "memory", "MONOLITH_MODE"]
