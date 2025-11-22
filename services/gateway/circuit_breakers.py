"""
Circuit breaker patterns for SomaAgent01 canonical backend.
Real resilience for external service dependencies with no mocks.
"""

import asyncio
import time
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict

import pybreaker

from observability.metrics import metrics_collector


class CircuitBreakerConfig:
    """Configuration for circuit breakers."""

    SOMATRAIN = {"fail_max": 5, "reset_timeout": 60, "exclude": [pybreaker.CircuitBreakerError]}

    POSTGRES = {"fail_max": 3, "reset_timeout": 30, "exclude": [pybreaker.CircuitBreakerError]}

    KAFKA = {"fail_max": 4, "reset_timeout": 45, "exclude": [pybreaker.CircuitBreakerError]}


class ResilientService:
    """Base class for services with circuit breaker protection."""

    def __init__(self, name: str, config: Dict):
        self.name = name
        self.breaker = pybreaker.CircuitBreaker(**config)
        self.breaker.name = name

        # Track circuit breaker state changes
        self.breaker.on_open = self._on_breaker_open
        self.breaker.on_close = self._on_breaker_close
        self.breaker.on_half_open = self._on_breaker_half_open

    def _on_breaker_open(self):
        """Handle circuit breaker opening."""
        metrics_collector.track_error("circuit_breaker_open", self.name)
        print(f"⚠️ Circuit breaker OPEN for {self.name}")

    def _on_breaker_close(self):
        """Handle circuit breaker closing."""
        print(f"✅ Circuit breaker CLOSED for {self.name}")

    def _on_breaker_half_open(self):
        """Handle circuit breaker half-open."""
        print(f"🔄 Circuit breaker HALF-OPEN for {self.name}")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection."""
        return self.breaker.call(func, *args, **kwargs)

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Call async function with circuit breaker protection."""
        return await self.breaker.call_async(func, *args, **kwargs)


# Global circuit breakers
circuit_breakers = {
    "somabrain": ResilientService("somabrain", CircuitBreakerConfig.SOMATRAIN),
    "postgres": ResilientService("postgres", CircuitBreakerConfig.POSTGRES),
    "kafka": ResilientService("kafka", CircuitBreakerConfig.KAFKA),
}


class CircuitBreakerMixin:
    """Mixin to add circuit breaker protection to services."""

    def __init__(self, service_name: str):
        self.circuit_breaker = circuit_breakers.get(service_name)
        if not self.circuit_breaker:
            raise ValueError(f"No circuit breaker configured for {service_name}")

    def protected_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        return self.circuit_breaker.call(func, *args, **kwargs)

    async def protected_call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        return await self.circuit_breaker.call_async(func, *args, **kwargs)


def circuit_breaker_wrapper(service_name: str):
    """Decorator for circuit breaker protection."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            breaker = circuit_breakers[service_name]
            return breaker.call(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            breaker = circuit_breakers[service_name]
            return await breaker.call_async(func, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class CircuitBreakerHealth:
    """Health check for circuit breakers."""

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Get circuit breaker status for all services."""
        status = {}

        for name, service in circuit_breakers.items():
            breaker = service.breaker
            state_obj = getattr(breaker, "current_state", None)
            state_name = getattr(state_obj, "name", str(state_obj))
            status[name] = {
                "state": state_name,
                "fail_count": getattr(breaker, "_fail_counter", None),
                "fail_max": getattr(breaker, "_fail_max", None),
                "reset_timeout": getattr(breaker, "_reset_timeout", None),
                "last_failure_time": getattr(breaker, "_last_failure_time", None),
                "failure_count": getattr(breaker, "_failure_count", None),
            }

        return {"circuit_breakers": status, "timestamp": datetime.utcnow().isoformat()}


# Protected service wrappers
class ProtectedSomaClient:
    """SomaBrain client with circuit breaker protection."""

    def __init__(self):
        self.breaker = circuit_breakers["somabrain"]
        self.client = None  # Will be set by actual client

    async def get_weights(self):
        """Protected weight retrieval."""
        return await self.breaker.call_async(self.client.get_weights)

    async def build_context(self, *args, **kwargs):
        """Protected context building."""
        return await self.breaker.call_async(self.client.build_context, *args, **kwargs)


class ProtectedPostgresClient:
    """Postgres client with circuit breaker protection."""

    def __init__(self):
        self.breaker = circuit_breakers["postgres"]

    async def execute_query(self, query: str, *args):
        """Protected query execution."""
        return await self.breaker.call_async(self._execute_query, query, *args)

    async def _execute_query(self, query: str, *args):
        """Actual query execution - postgres_client not available."""
        raise NotImplementedError("PostgreSQL client not available")


class ProtectedKafkaClient:
    """Kafka client with circuit breaker protection."""

    def __init__(self):
        self.breaker = circuit_breakers["kafka"]

    async def send_message(self, topic: str, message: str):
        """Protected message sending."""
        return await self.breaker.call_async(self._send_message, topic, message)

    async def _send_message(self, topic: str, message: str):
        """Actual message sending."""
        from services.common.event_bus import KafkaEventBus

        bus = KafkaEventBus()
        await bus.send(topic, message)


class CircuitState:
    """Circuit breaker state enumeration."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker wrapper for compatibility."""
    
    def __init__(self, name: str = None, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 fail_max: int = None, reset_timeout: int = None, expected_exception: type = Exception):
        # Handle both parameter naming conventions
        self.name = name or "default"
        self.fail_max = fail_max or failure_threshold
        self.reset_timeout = reset_timeout or recovery_timeout
        self.expected_exception = expected_exception
        self._fail_counter = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time = None
        
    @property
    def current_state(self):
        """Get current circuit breaker state."""
        return self._state
    
    @property
    def state(self):
        """Compatibility alias returning an object with .value."""
        class StateWrapper:
            def __init__(self, val):
                self.value = val
        return StateWrapper(self._state)
        
    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self._fail_counter += 1
        self._last_failure_time = time.time()
        if self._fail_counter >= self.fail_max:
            self._state = CircuitState.OPEN
            
    def record_success(self):
        """Record a success and potentially close the circuit."""
        self._fail_counter = 0
        if self._state == CircuitState.OPEN:
            self._state = CircuitState.CLOSED
            
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self._state == CircuitState.CLOSED:
            return True
        elif self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self.reset_timeout:
                self._state = CircuitState.HALF_OPEN
                return True
            return False
        elif self._state == CircuitState.HALF_OPEN:
            return True
        return False


class CircuitBreakerRegistry:
    """Registry for managing circuit breakers."""
    
    def __init__(self):
        self._breakers = circuit_breakers
    
    def get_breaker(self, name: str):
        """Get a circuit breaker by name."""
        return self._breakers.get(name)
    
    def get_all_breakers(self):
        """Get all circuit breakers."""
        return self._breakers
    
    def get_breaker_status(self, name: str) -> Dict[str, Any]:
        """Get status of a specific circuit breaker."""
        breaker = self.get_breaker(name)
        if not breaker:
            return {"error": f"Circuit breaker '{name}' not found"}
        
        return {
            "name": name,
            "state": breaker.breaker.current_state.name,
            "fail_count": breaker.breaker._fail_counter,
            "fail_max": breaker.breaker._fail_max,
            "reset_timeout": breaker.breaker._reset_timeout,
        }
    
    def get_all_statuses(self) -> Dict[str, Any]:
        """Get status of all circuit breakers."""
        statuses = {}
        for name, breaker in self._breakers.items():
            statuses[name] = self.get_breaker_status(name)
        return {"circuit_breakers": statuses}
    
    # Static methods for compatibility with circuit_endpoints.py
    @staticmethod
    def list_circuits():
        """List all circuit breaker names."""
        return list(circuit_breakers.keys())
    
    @staticmethod
    def get_circuit(name: str):
        """Get a circuit breaker by name for compatibility."""
        if name in circuit_breakers:
            # Return a wrapper object compatible with circuit_endpoints expectations
            breaker = circuit_breakers[name]
            return CircuitBreakerWrapper(breaker)
        return None


class CircuitBreakerWrapper:
    """Wrapper to make ResilientService compatible with circuit_endpoints expectations."""
    
    def __init__(self, resilient_service):
        self.service = resilient_service
        self.breaker = resilient_service.breaker
        
    @property
    def state(self):
        """Get circuit breaker state."""
        # Return an object with a value attribute for compatibility
        state_name = self.breaker.current_state.name
        class StateWrapper:
            def __init__(self, name):
                self.value = name.upper() if name else "CLOSED"
        return StateWrapper(state_name)
    
    @property
    def failure_count(self):
        """Get failure count."""
        return getattr(self.breaker, '_fail_counter', 0)
    
    @property
    def last_failure_time(self):
        """Get last failure time."""
        return getattr(self.breaker, '_last_failure_time', None)
    
    @property
    def success_count(self):
        """Get success count."""
        return 0  # Not tracked in pybreaker
    
    @property
    def failure_threshold(self):
        """Get failure threshold."""
        return getattr(self.breaker, '_fail_max', 5)
    
    @property
    def recovery_timeout(self):
        """Get recovery timeout."""
        return getattr(self.breaker, '_reset_timeout', 60)
    
    @property
    def last_state_change(self):
        """Get last state change time."""
        return getattr(self.breaker, '_last_failure_time', None)


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()
