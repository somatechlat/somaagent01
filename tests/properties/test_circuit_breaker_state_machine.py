"""Property 16: Circuit breaker three-state machine.

Validates: Requirements 47.1-47.5

Ensures circuit breaker transitions CLOSED → OPEN after threshold failures,
OPEN → HALF_OPEN after cooldown, and HALF_OPEN → CLOSED on success (or back
to OPEN on failure).
"""

import time

import pybreaker
import pytest

from services.gateway.circuit_breakers import ResilientService


def test_circuit_breaker_transitions_three_states():
    service = ResilientService(
        "test",
        {"fail_max": 1, "reset_timeout": 0.05, "exclude": [pybreaker.CircuitBreakerError]},
    )

    def fail():
        raise RuntimeError("boom")

    def succeed():
        return "ok"

    # CLOSED -> OPEN on first failure (fail_max=1) => pybreaker raises CircuitBreakerError
    with pytest.raises(pybreaker.CircuitBreakerError):
        service.call(fail)
    assert service.breaker.current_state == "open" or getattr(
        service.breaker.current_state, "name", None
    ) == "open"

    # OPEN -> HALF_OPEN after cooldown
    time.sleep(0.06)
    # first call after cooldown enters HALF_OPEN and executes
    assert service.call(succeed) == "ok"
    state = service.breaker.current_state
    assert state == "closed" or getattr(state, "name", None) == "closed"

    # Re-open by failing again after another cooldown
    time.sleep(0.06)
    with pytest.raises(pybreaker.CircuitBreakerError):
        service.call(fail)
    state = service.breaker.current_state
    assert state == "open" or getattr(state, "name", None) == "open"
