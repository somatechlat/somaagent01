"""Feature System Exceptions.

SRS Source: SRS-FEATURE-FLAGS-2026-01-16
"""

from typing import Any, Dict, Optional

from admin.common.messages import ErrorCode, get_message


class FeatureError(Exception):
    """Base class for feature exceptions."""
    pass


class FeatureDisabledError(FeatureError):
    """Raised when a feature is disabled or not allowed for the tenant."""

    def __init__(
        self,
        feature_code: str,
        tenant_id: str,
        reason: str = "plan_restriction",
    ):
        self.feature_code = feature_code
        self.tenant_id = tenant_id
        self.reason = reason
        self.http_status = 403
        message = get_message(
            ErrorCode.FEATURE_NOT_ON_TIER,
            feature=feature_code,
        )
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": "feature_disabled",
            "code": self.feature_code,
            "reason": self.reason,
            "message": str(self),
        }
