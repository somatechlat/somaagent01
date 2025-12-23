"""Centralized Error Codes and Messages.

VIBE COMPLIANT - No hardcoded strings, centralized management.
"""

from enum import Enum

class ErrorCode(str, Enum):
    # Generic
    INTERNAL_ERROR = "internal_error"
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    
    # SAAS - Tiers
    TIER_NOT_FOUND = "tier_not_found"
    TIER_ACTIVE_TENANTS = "tier_has_active_tenants"
    
    # SAAS - Features
    FEATURE_NOT_FOUND = "feature_not_found"
    FEATURE_NOT_ON_TIER = "feature_not_on_tier"
    
    # SAAS - Tenants
    TENANT_NOT_FOUND = "tenant_not_found"


class SuccessCode(str, Enum):
    TIER_DEACTIVATED = "tier_deactivated"
    FEATURE_REMOVED = "feature_removed"


MESSAGES = {
    ErrorCode.INTERNAL_ERROR: "An unexpected error occurred",
    ErrorCode.INVALID_REQUEST: "The request payload is invalid",
    ErrorCode.TIER_NOT_FOUND: "Subscription tier not found",
    ErrorCode.TIER_ACTIVE_TENANTS: "Cannot delete tier with {count} active tenants",
    ErrorCode.FEATURE_NOT_FOUND: "Feature '{code}' not found",
    ErrorCode.FEATURE_NOT_ON_TIER: "Feature '{code}' not found on tier",
    
    SuccessCode.TIER_DEACTIVATED: "Tier '{name}' deactivated",
    SuccessCode.FEATURE_REMOVED: "Feature '{code}' removed from tier",
}


def get_message(code: str, **kwargs) -> str:
    """Get formatted message for code."""
    msg = MESSAGES.get(code, "Unknown code")
    if kwargs:
        return msg.format(**kwargs)
    return msg
