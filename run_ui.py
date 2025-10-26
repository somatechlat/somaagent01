"""DEPRECATED: Standalone UI server has been removed.

This project serves the Web UI from the Gateway (same origin) to ensure
correct CSRF/cookie semantics and to simplify configuration. Use the Gateway
service at http://127.0.0.1:${GATEWAY_PORT:-20016}/.

Keeping this stub prevents accidental entrypoints from being used; importing
or executing this file will fail fast with a clear message.
"""

raise RuntimeError(
    "run_ui.py removed. Serve the UI from the Gateway only (http://127.0.0.1:${GATEWAY_PORT:-20016}/)."
)
