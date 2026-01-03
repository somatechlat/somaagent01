"""Prometheus metrics for the voice subsystem.

Metrics are defined lazily – they are created on first import to avoid side effects
when the module is imported in environments that do not expose a Prometheus
endpoint (e.g., unit tests).  The VIBE rule **NO SIDE‑EFFECTS AT IMPORT** is thus
observed.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

# Counter for total number of voice sessions started.
VOICE_SESSIONS_TOTAL = Counter(
    "voice_sessions_total",
    "Total number of voice interaction sessions started",
)

# Counter for errors occurring in any voice component.
VOICE_ERRORS_TOTAL = Counter(
    "voice_errors_total",
    "Total number of errors raised by the voice subsystem",
    ["component"],
)

# Histogram for request duration (in seconds) per session.
VOICE_SESSION_DURATION_SECONDS = Histogram(
    "voice_session_duration_seconds",
    "Duration of a voice session",
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60, float("inf")),
)


def record_error(component: str) -> None:
    """Increment the error counter for a given component.

    Parameters
    ----------
    component:
        Name of the subsystem where the error originated (e.g., ``"capture"``).
    """
    VOICE_ERRORS_TOTAL.labels(component=component).inc()
