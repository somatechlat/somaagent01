"""
Circuit breaker patterns for SomaAgent01 canonical backend.
Real resilience for external service dependencies with no mocks.
"""

import asyncio
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
            status[name] = {
                "state": breaker.current_state.name,
                "fail_count": breaker._fail_counter,
                "fail_max": breaker._fail_max,
                "reset_timeout": breaker._reset_timeout,
                "last_failure_time": getattr(breaker, "_last_failure_time", None),
                "failure_count": getattr(breaker, "_failure_count", 0),
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
        """Actual query execution."""
        from python.integrations.postgres_client import postgres_pool

        async with postgres_pool.acquire() as conn:
            return await conn.execute(query, *args)


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
