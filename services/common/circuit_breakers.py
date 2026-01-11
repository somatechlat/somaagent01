"""
Circuit Breaker Pattern Implementation - Django Native.


following the standard circuit breaker pattern for resilience.

🎓 PhD Developer | 🔍 PhD Analyst | ✅ PhD QA | 📚 ISO Documenter
🔒 Security Auditor | ⚡ Performance Engineer | 🎨 UX Consultant
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Callable, Optional, Type

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states following standard pattern."""

    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, message: str = "Circuit breaker is open"):
        """Initialize the instance."""

        self.circuit_name = circuit_name
        super().__init__(f"{circuit_name}: {message}")


class CircuitBreaker:
    """
    Circuit Breaker implementation for resilient service calls.



    Usage:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

        try:
            result = await breaker.call(async_function, *args, **kwargs)
        except CircuitBreakerError:
            # Handle circuit open state
            pass

    Attributes:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to catch as failure
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        name: str = "default",
    ):
        """Initialize the instance."""

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout transition."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit {self.name} transitioning to HALF_OPEN")
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    @property
    def success_count(self) -> int:
        """Get current success count."""
        return self._success_count

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs,
    ):
        """
        Execute a function through the circuit breaker.

        Args:
            func: Async or sync callable to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func if successful

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If func raises and circuit allows
        """
        async with self._lock:
            current_state = self.state

            # Fast fail if circuit is open
            if current_state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    self.name, f"Circuit open after {self._failure_count} failures"
                )

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success - reset counters
            await self._record_success()
            return result

        except self.expected_exception as e:
            # Failure - record and possibly open circuit
            await self._record_failure()
            raise

    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            self._success_count += 1

            if self._state == CircuitState.HALF_OPEN:
                # Success in half-open means we can close the circuit
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info(f"Circuit {self.name} closed after successful test")
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = max(0, self._failure_count - 1)

    async def _record_failure(self) -> None:
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open means back to open
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit {self.name} re-opened after failed test")
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit {self.name} opened after {self._failure_count} failures"
                    )

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info(f"Circuit {self.name} manually reset")

    def force_open(self) -> None:
        """Force the circuit to open state."""
        self._state = CircuitState.OPEN
        self._last_failure_time = time.time()
        logger.warning(f"Circuit {self.name} forced open")

    def __repr__(self) -> str:
        """Return object representation."""

        return (
            f"<CircuitBreaker name={self.name} state={self._state.value} "
            f"failures={self._failure_count}>"
        )


# Convenience functions for common patterns
def create_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    """Create a named circuit breaker with standard settings."""
    return CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
    )


# Default circuit breakers for core services
_circuit_breakers: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = create_circuit_breaker(name)
    return _circuit_breakers[name]


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers (useful for testing)."""
    for breaker in _circuit_breakers.values():
        breaker.reset()
