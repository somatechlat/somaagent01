"""Structured JSON logging configuration for SomaAgent services."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from src.core.config import cfg

_LOGGING_INITIALISED = False


class JSONFormatter(logging.Formatter):
    """Render log records as JSON for downstream aggregation systems."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # The ``extra`` kwarg is flattened into the log record attributes.
        # Capture anything non-standard so that structured metadata survives.
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_data or key in standard_attrs:
                continue
            log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(default_level: str | None = None) -> None:
    """Configure root logging with JSON formatting if not already configured."""

    global _LOGGING_INITIALISED
    if _LOGGING_INITIALISED:
        return

    env_level = cfg.env("LOG_LEVEL", default_level or "INFO")
    level_name = (default_level or env_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Drop any pre-existing handlers to guarantee consistent formatting.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    _LOGGING_INITIALISED = True


# ---------------------------------------------------------------------------
# Compatibility helper
# ---------------------------------------------------------------------------
def get_logger(name: str = "") -> logging.Logger:
    """Return a configured :class:`logging.Logger`.

    Legacy code in the project expects a ``get_logger`` function that returns a
    logger instance with JSON formatting already applied.  The original
    implementation was removed during refactoring, causing import errors.

    This helper ensures that :func:`setup_logging` is executed exactly once and
    then retrieves (or creates) a logger with the supplied ``name``.  An empty
    name yields the root logger, matching typical usage patterns.
    """
    # Ensure the global logging configuration is initialised exactly once.
    setup_logging()
    return logging.getLogger(name)


__all__ = [
    "setup_logging",
    "get_logger",
    "JSONFormatter",
]
