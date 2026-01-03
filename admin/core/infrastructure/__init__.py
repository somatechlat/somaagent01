"""Infrastructure module for SAAS administration.

VIBE COMPLIANT - Django ORM models and real health checks.
"""

from admin.core.infrastructure.health_checker import (
    HealthCheckResult,
    InfrastructureHealthChecker,
    health_checker,
)
from admin.core.infrastructure.models import (
    EnforcementPolicy,
    InfrastructureConfig,
    RateLimitPolicy,
    ServiceHealth,
    ServiceStatus,
)

__all__ = [
    # Models
    "RateLimitPolicy",
    "ServiceHealth",
    "InfrastructureConfig",
    "EnforcementPolicy",
    "ServiceStatus",
    # Health Checker
    "HealthCheckResult",
    "InfrastructureHealthChecker",
    "health_checker",
]
