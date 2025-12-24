"""Removed legacy UI proxy package.

This package previously exposed a /v1/ui/poll endpoint and proxied UI calls.
SSE-only Gateway UI removed the need for a proxy; package kept as empty to
avoid import errors in historical scripts.
"""

# Ensures router and helpers are importable by Django Ninja add_router in gateway.
