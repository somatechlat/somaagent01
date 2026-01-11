"""Module lifecycle_metrics."""

from __future__ import annotations

import time

from prometheus_client import Histogram, REGISTRY

# Centralized lifecycle histograms used by all services/workers
_startup = None
_shutdown = None


def _ensure_metrics():
    """Execute ensure metrics."""

    global _startup, _shutdown
    if _startup is not None and _shutdown is not None:
        return _startup, _shutdown
    # Avoid duplicate registration errors in test runs by checking existing collectors
    for c in list(REGISTRY._collector_to_names.keys()):  # type: ignore[attr-defined]
        if getattr(c, "_name", "") == "service_startup_seconds":
            _startup = c
        if getattr(c, "_name", "") == "service_shutdown_seconds":
            _shutdown = c
    if _startup is None:
        _startup = Histogram(
            "service_startup_seconds",
            "Time taken for a service to initialize before entering its main loop",
            labelnames=("service",),
        )
    if _shutdown is None:
        _shutdown = Histogram(
            "service_shutdown_seconds",
            "Time taken for a service to shut down and release resources",
            labelnames=("service",),
        )
    return _startup, _shutdown


def now() -> float:
    """Execute now."""

    return time.perf_counter()


def observe_startup(service: str, started_at: float) -> None:
    """Execute observe startup.

    Args:
        service: The service.
        started_at: The started_at.
    """

    try:
        elapsed = max(0.0, time.perf_counter() - float(started_at))
        _ensure_metrics()[0].labels(service).observe(elapsed)
    except Exception:
        # Metrics must never break startup
        pass


def observe_shutdown(service: str, started_at: float) -> None:
    """Execute observe shutdown.

    Args:
        service: The service.
        started_at: The started_at.
    """

    try:
        elapsed = max(0.0, time.perf_counter() - float(started_at))
        _ensure_metrics()[1].labels(service).observe(elapsed)
    except Exception:
        # Metrics must never break shutdown
        pass
