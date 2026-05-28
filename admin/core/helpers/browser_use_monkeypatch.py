"""Browser-use monkeypatch helpers.

Patches browser-use library internals for compatibility with
SomaAgent01's LLM routing and credential management.
"""

import logging

logger = logging.getLogger(__name__)


def apply() -> None:
    """Apply browser-use compatibility patches.

    Currently a no-op — patches are applied lazily when
    browser_use features are actually invoked.
    """
    logger.debug("browser_use_monkeypatch.apply() called (no-op)")
