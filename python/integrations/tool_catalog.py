from __future__ import annotations

# Expose a stable singleton for tests: integrations.tool_catalog.catalog
from python.tools.catalog import catalog  # noqa: F401

__all__ = ["catalog"]
