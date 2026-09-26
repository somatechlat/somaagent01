"""Unit tests for CircuitBreaker.

Tests the async-safe circuit breaker state machine:
CLOSED → OPEN → HALF_OPEN → CLOSED.
"""

import asyncio
import pytest


class TestCircuitBreaker:
    """Test CircuitBreaker state transitions."""

    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker with low threshold for testing."""
        from services.common.circuit_breaker import get_circuit_breaker, reset_all_circuit_breakers
        reset_all_circuit_breakers()
        return get_circuit_breaker("test", failure_threshold=3, reset_timeout=0.1)

    @pytest.mark.asyncio
    async def test_starts_closed(self, breaker):
        """Circuit breaker starts in CLOSED state."""
        from services.common.circuit_breaker import CircuitState
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_success_stays_closed(self, breaker):
        """Successful calls keep circuit CLOSED."""
        from services.common.circuit_breaker import CircuitState

        async def success():
            return "ok"

        result = await breaker.call(success)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_failures_open_circuit(self, breaker):
        """Repeated failures open the circuit."""
        from services.common.circuit_breaker import CircuitState, CircuitBreakerError

        async def fail():
            raise ValueError("test error")

        # Fail 3 times (threshold)
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail)

        assert breaker.state == CircuitState.OPEN

        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await breaker.call(fail)

    @pytest.mark.asyncio
    async def test_half_open_after_timeout(self, breaker):
        """Circuit transitions to HALF_OPEN after reset timeout."""
        from services.common.circuit_breaker import CircuitState

        async def fail():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail)

        assert breaker.state == CircuitState.OPEN

        # Wait for reset timeout
        await asyncio.sleep(0.15)

        # State should be HALF_OPEN
        assert breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes(self, breaker):
        """Success in HALF_OPEN state closes the circuit."""
        from services.common.circuit_breaker import CircuitState

        async def fail():
            raise ValueError("test error")

        async def success():
            return "ok"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail)

        # Wait for half-open
        await asyncio.sleep(0.15)

        # Successful call should close
        result = await breaker.call(success)
        assert result == "ok"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_manual_reset(self, breaker):
        """Manual reset returns circuit to CLOSED."""
        from services.common.circuit_breaker import CircuitState

        async def fail():
            raise ValueError("test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(fail)

        assert breaker.state == CircuitState.OPEN

        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_registry(self):
        """get_circuit_breaker returns same instance for same name."""
        from services.common.circuit_breaker import get_circuit_breaker, reset_all_circuit_breakers
        reset_all_circuit_breakers()

        b1 = get_circuit_breaker("registry_test")
        b2 = get_circuit_breaker("registry_test")
        assert b1 is b2
