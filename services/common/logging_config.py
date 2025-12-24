"""Django-compatible structured JSON logging configuration for SomaAgent services.

This module provides the JSON formatter class referenced by Django's LOGGING
setting in services.gateway.settings. All logging configuration flows through
Django's dictConfig - this module only provides the formatter implementation.

Django LOGGING is the SINGLE SOURCE OF TRUTH for log configuration.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict


class DjangoJSONFormatter(logging.Formatter):
    """JSON log formatter for Django's LOGGING dictConfig.
    
    This formatter renders log records as JSON for downstream aggregation
    systems (ELK, CloudWatch, etc.). It is referenced in settings.LOGGING
    using the "()" factory syntax.
    
    Usage in settings.py:
        LOGGING = {
            "formatters": {
                "json": {
                    "()": "services.common.logging_config.DjangoJSONFormatter",
                },
            },
            ...
        }
    """

    def format(self, record: logging.LogRecord) -> str:
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

        # Capture extra kwargs passed to logging calls for structured metadata.
        standard_attrs = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in log_data or key in standard_attrs:
                continue
            log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False, default=str)


# Compatibility alias for legacy code (to be removed after full migration)
JSONFormatter = DjangoJSONFormatter


def get_logger(name: str = "") -> logging.Logger:
    """Return a configured logger using Django's LOGGING configuration.
    
    This is a convenience function for getting loggers. Since Django configures
    logging at startup via settings.LOGGING, simply calling logging.getLogger()
    returns a logger with the correct formatters and handlers attached.
    
    Args:
        name: Logger name, typically __name__. Empty string returns root logger.
        
    Returns:
        Configured logging.Logger instance.
    """
    return logging.getLogger(name)


__all__ = [
    "DjangoJSONFormatter",
    "JSONFormatter",  # Legacy alias
    "get_logger",
]
