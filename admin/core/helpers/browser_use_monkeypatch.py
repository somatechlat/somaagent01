"""Browser-use monkeypatch helpers.

Patches browser-use library internals for compatibility with
SomaAgent01's LLM routing and credential management.
"""

import logging

logger = logging.getLogger(__name__)


def apply() -> None:
    """Apply browser-use compatibility patches.

    Currently a no-op while browser-use integration is pending.
    Logs at debug level so callers can verify the patch hook ran.
    """
    logger.debug("browser-use monkeypatch is a no-op; skipping")
