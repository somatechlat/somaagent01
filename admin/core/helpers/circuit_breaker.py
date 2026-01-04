"""Simple circuit-breaker decorator used by tools that call external services.
It tracks consecutive failures and opens the circuit after a configurable threshold.
While the circuit is open, calls raise ``CircuitOpenError`` immediately.
After ``reset_timeout`` seconds the circuit attempts a single trial call.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import os
import time
from typing import Any, Callable, TypeVar

from prometheus_client import Counter, start_http_server

T = TypeVar("T")

# Prometheus metrics for circuit‑breaker state changes
CB_OPENED = Counter(
    "circuit_breaker_opened_total", "Total number of times the circuit breaker opened"
)
CB_CLOSED = Counter(
    "circuit_breaker_closed_total",
    "Total number of times the circuit breaker closed after a successful trial",
)
CB_TRIAL = Counter(
    "circuit_breaker_trial_total", "Total number of trial calls while the circuit is open"
)

LOGGER = logging.getLogger(__name__)
_EXPORTER_STARTED = False


def ensure_metrics_exporter() -> None:
    """Start the standalone Prometheus exporter if a port is configured.

    The helper is opt-in to avoid binding ports in every consumer process. Set
    ``CIRCUIT_BREAKER_METRICS_PORT`` (and optionally ``CIRCUIT_BREAKER_METRICS_HOST``)
    in the environment of a long-lived service and call this function during
    startup to expose the counters defined in this module.
    """

    global _EXPORTER_STARTED

    if _EXPORTER_STARTED:
        return

    raw_port = (os.environ.get("CIRCUIT_BREAKER_METRICS_PORT", "") or "").strip()
    if not raw_port:
        return

    try:
        port = int(raw_port)
    except ValueError:
        LOGGER.warning(
            "Invalid CIRCUIT_BREAKER_METRICS_PORT (not an integer)",
            extra={"value": raw_port},
        )
        return

    if port <= 0:
        # Zero or negative disables the exporter; allow consumers to opt-out.
        LOGGER.debug(
            "Circuit breaker metrics exporter disabled via non-positive port",
            extra={"port": port},
        )
        return

    host = os.environ.get("CIRCUIT_BREAKER_METRICS_HOST", "0.0.0.0") or "0.0.0.0"
    try:
        start_http_server(port, addr=host)
    except Exception as exc:  # pragma: no cover - binding failures depend on host env
        LOGGER.warning(
            "Failed to start circuit breaker metrics exporter",
            extra={"host": host, "port": port, "error": str(exc)},
        )
        return

    _EXPORTER_STARTED = True
    LOGGER.info(
        "Circuit breaker metrics exporter listening",
        extra={"host": host, "port": port},
    )


class CircuitOpenError(RuntimeError):
    """Raised when the circuit is open and a call is blocked."""


def circuit_breaker(
    *,
    failure_threshold: int = 5,
    reset_timeout: float = 30.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Return a decorator that wraps ``func`` with circuit‑breaker logic.

    Parameters
    ----------
    failure_threshold:
        Number of consecutive failures before opening the circuit.
    reset_timeout:
        Seconds to wait before attempting to close the circuit again.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """Execute decorator.

            Args:
                func: The func.
            """

        state = {
            "failures": 0,
            "circuit_open": False,
            "opened_at": 0.0,
        }

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> T:
                """Execute async wrapper.
                    """

                if state["circuit_open"]:
                    if time.time() - state["opened_at"] >= reset_timeout:
                        CB_TRIAL.inc()
                        try:
                            result = await func(*args, **kwargs)
                        except Exception:
                            state["opened_at"] = time.time()
                            raise CircuitOpenError("Circuit still open after trial call")
                        else:
                            state["circuit_open"] = False
                            state["failures"] = 0
                            CB_CLOSED.inc()
                            return result
                    raise CircuitOpenError("Circuit is open; call blocked")

                try:
                    return await func(*args, **kwargs)
                except Exception:
                    state["failures"] += 1
                    if state["failures"] >= failure_threshold:
                        state["circuit_open"] = True
                        state["opened_at"] = time.time()
                        CB_OPENED.inc()
                    raise

            return async_wrapper

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            """Execute wrapper.
                """

            if state["circuit_open"]:
                if time.time() - state["opened_at"] >= reset_timeout:
                    CB_TRIAL.inc()
                    try:
                        result = func(*args, **kwargs)
                    except Exception:
                        state["opened_at"] = time.time()
                        raise CircuitOpenError("Circuit still open after trial call")
                    else:
                        state["circuit_open"] = False
                        state["failures"] = 0
                        CB_CLOSED.inc()
                        return result
                raise CircuitOpenError("Circuit is open; call blocked")

            try:
                return func(*args, **kwargs)
            except Exception:
                state["failures"] += 1
                if state["failures"] >= failure_threshold:
                    state["circuit_open"] = True
                    state["opened_at"] = time.time()
                    CB_OPENED.inc()
                raise

        return wrapper

    return decorator


# Example usage in a tool (pseudo‑code):
# from admin.core.helpers.circuit_breaker import circuit_breaker, CircuitOpenError
# @circuit_breaker(failure_threshold=3, reset_timeout=20)
# async def call_external_api(...):
#     ...