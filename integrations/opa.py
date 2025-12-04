"""OPA integration placeholder.

The original repository contained a broken ``opa.py`` that caused syntax
errors and invalid imports. The functional policy enforcement now lives in
``python/integrations/opa_middleware.py``. This stub provides the minimal
symbols expected by any legacy import paths while remaining syntactically
correct.
"""


def opa_client():
    """Return a no‑op client.

    The real OPA client is not required for the current codebase. Returning
    ``None`` satisfies type‑checkers and import statements.
    """
    return None


__all__ = ["opa_client"]
