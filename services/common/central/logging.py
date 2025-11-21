"""Central logging utilities.

Provides a thin wrapper around the project's JSON logging configuration.
Only ``setup_logging`` is imported from the original implementation; a
convenient ``get_logger`` helper is added to avoid the previous shim that
existed in ``services.common.logging_config``.
"""

from __future__ import annotations

import logging

# The actual setup function lives in ``services.common.logging_config``.
from services.common.logging_config import setup_logging as _setup_logging


def setup_logging(default_level: str | None = None) -> None:
    """Initialize JSON structured logging.

    Delegates to the original ``setup_logging`` implementation.  The wrapper
    exists so that callers can import ``setup_logging`` from the central
    package without needing to know the underlying module location.
    """

    _setup_logging(default_level)


def get_logger(name: str = __name__) -> logging.Logger:
    """Return a standard ``logging.Logger`` instance.

    After ``setup_logging`` has been called, this logger will emit JSON
    formatted records automatically.
    """

    return logging.getLogger(name)


__all__ = ["setup_logging", "get_logger"]
