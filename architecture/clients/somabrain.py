"""Public façade for the SomaBrain client.

The canonical implementation resides in ``src.core.clients.somabrain``.  This
module re‑exports the symbols so that imports from ``architecture.clients``
continue to work while keeping a single source of truth.
"""

from src.core.clients.somabrain import SomaClient, SomaClientError

__all__ = ["SomaClient", "SomaClientError"]
