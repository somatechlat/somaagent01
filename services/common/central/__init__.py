"""Central package initialization.

Provides a unified import path for common utilities such as configuration,
logging, and authorization.
"""

# Re-export symbols from submodules (they will be created later).
from .config import cfg, CentralizedConfig
from .logging import setup_logging, get_logger
from .auth import authorize, authorize_request, require_policy, get_policy_client

__all__ = [
    "cfg",
    "CentralizedConfig",
    "setup_logging",
    "get_logger",
    "authorize",
    "authorize_request",
    "require_policy",
    "get_policy_client",
]
