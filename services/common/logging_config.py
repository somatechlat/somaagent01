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

    level_name = default_level or cfg.env("LOG_LEVEL", "INFO") or "INFO"
    level = getattr(logging, level_name.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Drop any pre-existing handlers to guarantee consistent formatting.
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    _LOGGING_INITIALISED = True


def get_logger(name: str = __name__) -> logging.Logger:
    """Return a standard logger instance.

    Historically callers imported ``get_logger`` from this module.  It now
    simply forwards to ``logging.getLogger`` after ``setup_logging`` has
    configured the JSON formatter.
    """

    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Public helper used by legacy imports
# ---------------------------------------------------------------------------
# NOTE: The ``get_logger`` helper was a compatibility shim for legacy imports.
# It has been removed to comply with the "no shim" policy. Routers now obtain
# loggers via the standard ``logging.getLogger`` after ``setup_logging`` has
# been called during service start‑up.
