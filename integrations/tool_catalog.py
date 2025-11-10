import builtins as _builtins

from python.integrations.tool_catalog import catalog

# Provide a convenient global name for tests expecting bare `catalog` in scope
try:
    _builtins.catalog = catalog  # type: ignore[attr-defined]
except Exception:
    pass

__all__ = ["catalog"]
