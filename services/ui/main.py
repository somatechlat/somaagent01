"""DEPRECATED: Standalone FastAPI UI has been removed.

The Gateway serves the Web UI same-origin at its root path. Start the Gateway
and open http://127.0.0.1:${GATEWAY_PORT:-20016}/.
"""

raise ImportError(
    "services/ui/main.py removed. Use the Gateway for serving the UI (single origin)."
)
