"""Resilience primitives for generic usage."""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, TypeVar, Optional

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Raised when call is rejected due to open circuit."""

    pass


class AsyncCircuitBreaker:
    """A thread-safe, async-aware circuit breaker.

    Implements standard Closed -> Open -> Half-Open state machine.
    """

    def __init__(
        self,
        name: str,
        fail_max: int = 5,
        reset_timeout: int = 30,
        exclude_exceptions: Optional[list[type[Exception]]] = None,
    ):
        self._name = name
        self._fail_max = fail_max
        self._reset_timeout = reset_timeout
        self._exclude_exceptions = tuple(exclude_exceptions or [])

        self._state = CircuitState.CLOSED
        self._fail_count = 0
        self._last_fail_time = 0.0
        self._lock = asyncio.Lock()

    @property
    def current_state(self) -> str:
        return self._state.value

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Call async function with circuit breaker protection."""
        async with self._lock:
            # Check state transition
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._last_fail_time
                if elapsed > self._reset_timeout:
                    LOGGER.info(f"Circuit '{self._name}' trying HALF_OPEN after {elapsed:.1f}s")
                    self._state = CircuitState.HALF_OPEN
                    self._update_metric()
                else:
                    raise CircuitBreakerError(f"Circuit '{self._name}' is OPEN")

            # Allow single call in HALF_OPEN (simple implementation: concurrent calls race)

        try:
            result = await func(*args, **kwargs)

            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    LOGGER.info(f"Circuit '{self._name}' recovered to CLOSED")
                    self._state = CircuitState.CLOSED
                    self._update_metric()
                self._fail_count = 0

            return result

        except Exception as e:
            if isinstance(e, self._exclude_exceptions):
                raise

            async with self._lock:
                self._fail_count += 1
                self._last_fail_time = time.monotonic()

                if self._state == CircuitState.HALF_OPEN:
                    LOGGER.warning(f"Circuit '{self._name}' probe failed. Re-opening.")
                    self._state = CircuitState.OPEN
                    self._update_metric()
                elif self._state == CircuitState.CLOSED and self._fail_count >= self._fail_max:
                    LOGGER.warning(
                        f"Circuit '{self._name}' opened after {self._fail_count} failures. "
                        f"Last error: {type(e).__name__}"
                    )
                    self._state = CircuitState.OPEN
                    self._update_metric()
            raise

    def _update_metric(self) -> None:
        """Report current state to metrics."""
        from admin.core.observability.metrics import metrics_collector

        # Map state to int: CLOSED=0, OPEN=1, HALF_OPEN=2
        val = 0
        if self._state == CircuitState.OPEN:
            val = 1
        elif self._state == CircuitState.HALF_OPEN:
            val = 2

        metrics_collector.track_circuit_state(self._name, val)
