"""Browser-use monkeypatch helpers.

Patches browser-use library internals for compatibility with
SomaAgent01's LLM routing and credential management.
"""

import logging

logger = logging.getLogger(__name__)


def apply() -> None:
    """Apply browser-use compatibility patches.

    Raises:
        RuntimeError: Patches are not yet implemented.
    """
    raise RuntimeError("browser-use monkeypatch is not implemented")
