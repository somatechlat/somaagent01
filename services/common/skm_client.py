"""Legacy SKM client has been removed.

This module is intentionally disabled. The project now uses SomaBrain as the
sole memory backend. Import and use `python.integrations.somabrain_client.SomaBrainClient`
instead. Any attempt to import this module should fail fast to prevent
accidental regressions.
"""

raise ImportError(
    "services.common.skm_client has been removed. Use python.integrations.somabrain_client.SomaBrainClient."
)

"""Deprecated: SomaKamachiq client has been removed.

All runtime code must use current integrations; this module intentionally raises
ImportError to surface accidental usage.
"""

raise ImportError("services.common.skm_client is removed. Do not import.")
