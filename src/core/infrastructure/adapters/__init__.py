"""Infrastructure adapters implementing domain ports.

These adapters wrap existing production implementations to provide
domain port interface compliance. They add NO new functionality -
only interface compliance.
"""

from .event_bus_adapter import KafkaEventBusAdapter
from .execution_engine_adapter import ExecutionEngineAdapter
from .memory_adapter import SomaBrainMemoryAdapter
from .policy_adapter import OPAPolicyAdapter
from .secret_manager_adapter import SecretManagerAdapter
from .session_cache_adapter import RedisSessionCacheAdapter
from .session_repository_adapter import PostgresSessionRepositoryAdapter
from .tool_registry_adapter import ToolRegistryAdapter

__all__ = [
    "PostgresSessionRepositoryAdapter",
    "RedisSessionCacheAdapter",
    "KafkaEventBusAdapter",
    "OPAPolicyAdapter",
    "SomaBrainMemoryAdapter",
    "SecretManagerAdapter",
    "ToolRegistryAdapter",
    "ExecutionEngineAdapter",
]
