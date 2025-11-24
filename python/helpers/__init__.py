"""Helper utilities package.

The project expects a ``python.helpers`` module containing utilities such as a
``TunnelManager``.  The original implementation was missing, causing import
errors in the ``services.gateway.routers.tunnel`` router.  This package provides
the minimal functionality required by the UI: creating a deterministic tunnel
URL, retrieving it, and stopping the tunnel.

Only the public API used by the router is implemented – additional features can
be added later without breaking existing behavior.
"""
"""Helper utilities for SomaAgent.

This package exposes shared helper modules used across services and tests.
"""
