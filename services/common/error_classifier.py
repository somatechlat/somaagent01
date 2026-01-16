"""Simple error classifier mapping exceptions/messages to structured metadata.

Adds: error_code (str), retriable (bool), retry_after (int|None).

This module is intentionally lightweight and rule-based to avoid bringing
in heavy dependencies. Rules are conservative to minimize false positives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None  # type: ignore

_ERROR_CLASSIFIER_RESULTS: any = None  # type: ignore


def _metrics_init() -> None:
    """Execute metrics init."""

    global _ERROR_CLASSIFIER_RESULTS
    if Counter is None or _ERROR_CLASSIFIER_RESULTS is not None:
        return
    try:
        _ERROR_CLASSIFIER_RESULTS = Counter(
            "error_classifier_results_total",
            "Classified error events",
            labelnames=("error_code", "retriable"),
        )
    except ValueError:
        pass


@dataclass(frozen=True)
class ErrorMeta:
    """Exception raised for ErrorMeta."""

    error_code: str
    retriable: bool = False
    retry_after: Optional[int] = None


def classify(exc: Optional[BaseException] = None, message: str | None = None) -> ErrorMeta:
    """Execute classify.

    Args:
        exc: The exc.
        message: The message.
    """

    _metrics_init()
    text = (message or "").strip()
    low = text.lower()

    # Timeouts
    if "timeout" in low or "timed out" in low:
        meta = ErrorMeta("timeout", retriable=True, retry_after=2)
        try:
            if _ERROR_CLASSIFIER_RESULTS is not None:
                _ERROR_CLASSIFIER_RESULTS.labels(meta.error_code, str(meta.retriable).lower()).inc()
        except Exception:
            pass
        return meta

    # Upstream rate limiting
    if "rate limit" in low or "too many requests" in low:
        meta = ErrorMeta("rate_limited", retriable=True, retry_after=5)
        try:
            if _ERROR_CLASSIFIER_RESULTS is not None:
                _ERROR_CLASSIFIER_RESULTS.labels(meta.error_code, str(meta.retriable).lower()).inc()
        except Exception:
            pass
        return meta

    # Auth errors
    if any(k in low for k in ("unauthorized", "forbidden", "invalid token", "not authorized")):
        meta = ErrorMeta("auth_failed", retriable=False)
        try:
            if _ERROR_CLASSIFIER_RESULTS is not None:
                _ERROR_CLASSIFIER_RESULTS.labels(meta.error_code, str(meta.retriable).lower()).inc()
        except Exception:
            pass
        return meta

    # Validation / user errors
    if any(k in low for k in ("invalid", "malformed", "missing", "bad request")):
        meta = ErrorMeta("invalid_request", retriable=False)
        try:
            if _ERROR_CLASSIFIER_RESULTS is not None:
                _ERROR_CLASSIFIER_RESULTS.labels(meta.error_code, str(meta.retriable).lower()).inc()
        except Exception:
            pass
        return meta

    # Connection / upstream
    if any(k in low for k in ("connection", "upstream", "gateway", "service unavailable")):
        meta = ErrorMeta("upstream_error", retriable=True, retry_after=3)
        try:
            if _ERROR_CLASSIFIER_RESULTS is not None:
                _ERROR_CLASSIFIER_RESULTS.labels(meta.error_code, str(meta.retriable).lower()).inc()
        except Exception:
            pass
        return meta

    # Default
    meta = ErrorMeta("internal_error", retriable=False)
    try:
        if _ERROR_CLASSIFIER_RESULTS is not None:
            _ERROR_CLASSIFIER_RESULTS.labels(meta.error_code, str(meta.retriable).lower()).inc()
    except Exception:
        pass
    return meta
