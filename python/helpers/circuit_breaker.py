"""Simple circuit‑breaker decorator used by tools that call external services.
It tracks consecutive failures and opens the circuit after a configurable threshold.
While the circuit is open, calls raise ``CircuitOpenError`` immediately.
After ``reset_timeout`` seconds the circuit attempts a single trial call.
"""

import time
import functools
from typing import Callable, TypeVar, Any
from prometheus_client import Counter

T = TypeVar("T")

# Prometheus metrics for circuit‑breaker state changes
CB_OPENED = Counter('circuit_breaker_opened_total', 'Total number of times the circuit breaker opened')
CB_CLOSED = Counter('circuit_breaker_closed_total', 'Total number of times the circuit breaker closed after a successful trial')
CB_TRIAL = Counter('circuit_breaker_trial_total', 'Total number of trial calls while the circuit is open')

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
        state = {
            "failures": 0,
            "circuit_open": False,
            "opened_at": 0.0,
        }

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if state["circuit_open"]:
                # Check if reset timeout has elapsed
                if time.time() - state["opened_at"] >= reset_timeout:
                    # Try a single trial call
                    CB_TRIAL.inc()
                    try:
                        result = func(*args, **kwargs)
                    except Exception:
                        # Still failing – keep circuit open and reset timer
                        state["opened_at"] = time.time()
                        raise CircuitOpenError("Circuit still open after trial call")
                    else:
                        # Success – close circuit
                        state["circuit_open"] = False
                        state["failures"] = 0
                        CB_CLOSED.inc()
                        return result
                else:
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
# from python.helpers.circuit_breaker import circuit_breaker, CircuitOpenError
# @circuit_breaker(failure_threshold=3, reset_timeout=20)
# async def call_external_api(...):
#     ...