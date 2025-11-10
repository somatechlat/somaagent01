"""Legacy OPA shim removed.

This module remains to satisfy old import paths but does not expose
policy middleware anymore. Imports should be removed from callers.
"""

policy = None
client = None
__all__ = ["policy", "client"]
