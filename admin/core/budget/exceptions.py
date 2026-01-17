"""Budget Exceptions — Fail-Closed Error Handling.

SRS Source: SRS-BUDGET-SYSTEM-2026-01-16 Section 10

Applied Personas:
- Security Auditor: Fail-closed by default
- UX Consultant: Clear error messages with context
- ISO Documenter: Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Dict

from admin.common.messages import get_message


class BudgetExhaustedError(Exception):
    """Budget limit exceeded — always results in HTTP 402.

    This exception is raised when a tenant's usage exceeds their plan limits.
    CRITICAL: This is a SECURITY exception - fail-closed by design.

    Attributes:
        tenant_id: The tenant who exceeded their budget
        metric: The metric code that was exceeded
        usage: Current usage value
        limit: Plan limit value
        period: Billing period (e.g., "month")
        http_status: Always 402 Payment Required
    """

    http_status: int = 402  # Payment Required

    def __init__(
        self,
        tenant_id: str,
        metric: str,
        usage: float,
        limit: float,
        period: str = "month",
    ) -> None:
        """Initialize budget exhausted error.

        Args:
            tenant_id: Tenant identifier
            metric: Metric code (e.g., "tokens", "images")
            usage: Current usage count
            limit: Plan limit
            period: Billing period
        """
        self.tenant_id = tenant_id
        self.metric = metric
        self.usage = usage
        self.limit = limit
        self.period = period

        # Use centralized message system (Rule 11)
        message = get_message(
            "BUDGET_EXHAUSTED",
            metric=metric,
            usage=int(usage),
            limit=int(limit),
            period=period,
        )
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API response.

        Returns:
            Error details dict for JSON response
        """
        return {
            "error": "budget_exhausted",
            "code": "BUDGET_EXHAUSTED",
            "metric": self.metric,
            "usage": self.usage,
            "limit": self.limit,
            "period": self.period,
            "message": str(self),
            "http_status": self.http_status,
        }


class BudgetCheckError(Exception):
    """Error checking budget (cache/db failure).

    SECURITY: On check failure, default to DENY (fail-closed).
    """

    def __init__(self, tenant_id: str, metric: str, reason: str) -> None:
        """Initialize budget check error.

        Args:
            tenant_id: Tenant identifier
            metric: Metric being checked
            reason: Failure reason
        """
        self.tenant_id = tenant_id
        self.metric = metric
        self.reason = reason
        super().__init__(f"Budget check failed for {tenant_id}/{metric}: {reason}")


class MetricNotFoundError(Exception):
    """Unknown metric code requested.

    This indicates a programming error - the metric code doesn't exist
    in the registry.
    """

    def __init__(self, metric: str) -> None:
        """Initialize metric not found error.

        Args:
            metric: The unknown metric code
        """
        self.metric = metric
        super().__init__(f"Unknown budget metric: {metric}")
