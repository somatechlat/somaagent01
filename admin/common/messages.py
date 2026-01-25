"""Centralized Error Codes and Messages — I18N Ready.

VIBE RULE 11: All user-facing text MUST use get_message().
This module is the SINGLE SOURCE OF TRUTH for all messages.
"""

from enum import Enum

from django.utils.translation import gettext_lazy as _


class ErrorCode(str, Enum):
    """Error codes for all modules."""

    # Generic
    INTERNAL_ERROR = "internal_error"
    INVALID_REQUEST = "invalid_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"

    # Auth
    AUTH_INVALID_TOKEN = "auth_invalid_token"
    AUTH_EXPIRED_TOKEN = "auth_expired_token"
    AUTH_MISSING_TOKEN = "auth_missing_token"
    AUTH_PERMISSION_DENIED = "auth_permission_denied"

    # AAAS - Tiers
    TIER_NOT_FOUND = "tier_not_found"
    TIER_ACTIVE_TENANTS = "tier_has_active_tenants"

    # AAAS - Features
    FEATURE_NOT_FOUND = "feature_not_found"
    FEATURE_NOT_ON_TIER = "feature_not_on_tier"
    FEATURE_DEPENDENCY_MISSING = "feature_dependency_missing"

    # AAAS - Tenants
    TENANT_NOT_FOUND = "tenant_not_found"
    TENANT_SUSPENDED = "tenant_suspended"
    TENANT_QUOTA_EXCEEDED = "tenant_quota_exceeded"

    # Capsule
    CAPSULE_NOT_FOUND = "capsule_not_found"
    CAPSULE_INVALID = "capsule_invalid"
    CAPSULE_SIGNATURE_FAILED = "capsule_signature_failed"

    # Chat
    CONVERSATION_NOT_FOUND = "conversation_not_found"
    MESSAGE_TOO_LONG = "message_too_long"

    # Memory
    MEMORY_RECALL_FAILED = "memory_recall_failed"
    MEMORY_STORE_FAILED = "memory_store_failed"

    # Tools
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_PERMISSION_DENIED = "tool_permission_denied"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"

    # LLM
    LLM_NO_CAPABLE_MODEL = "llm_no_capable_model"
    LLM_ALL_FALLBACKS_FAILED = "llm_all_fallbacks_failed"
    LLM_RATE_LIMITED = "llm_rate_limited"

    # Billing
    BILLING_PAYMENT_FAILED = "billing_payment_failed"
    BILLING_SUBSCRIPTION_EXPIRED = "billing_subscription_expired"

    # Budget
    BUDGET_EXHAUSTED = "budget_exhausted"
    BUDGET_CHECK_FAILED = "budget_check_failed"


class SuccessCode(str, Enum):
    """Success codes for confirmations."""

    # Generic
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"

    # AAAS
    TIER_DEACTIVATED = "tier_deactivated"
    FEATURE_REMOVED = "feature_removed"

    # Capsule
    CAPSULE_CREATED = "capsule_created"
    CAPSULE_EXPORTED = "capsule_exported"
    CAPSULE_IMPORTED = "capsule_imported"

    # Chat
    MESSAGE_SENT = "message_sent"

    # Memory
    MEMORY_STORED = "memory_stored"


# I18N-Ready Messages using Django gettext_lazy
MESSAGES: dict[str | ErrorCode | SuccessCode, str] = {
    # Generic
    ErrorCode.INTERNAL_ERROR: _("An unexpected error occurred"),
    ErrorCode.INVALID_REQUEST: _("The request payload is invalid"),
    ErrorCode.UNAUTHORIZED: _("Authentication required"),
    ErrorCode.FORBIDDEN: _("You do not have permission to perform this action"),
    ErrorCode.NOT_FOUND: _("Resource not found"),
    ErrorCode.VALIDATION_ERROR: _("Validation failed: {details}"),
    # Auth
    ErrorCode.AUTH_INVALID_TOKEN: _("Invalid authentication token"),
    ErrorCode.AUTH_EXPIRED_TOKEN: _("Authentication token has expired"),
    ErrorCode.AUTH_MISSING_TOKEN: _("Authentication token is required"),
    ErrorCode.AUTH_PERMISSION_DENIED: _("Permission denied for action '{action}'"),
    # AAAS
    ErrorCode.TIER_NOT_FOUND: _("Subscription tier not found"),
    ErrorCode.TIER_ACTIVE_TENANTS: _("Cannot delete tier with {count} active tenants"),
    ErrorCode.FEATURE_NOT_FOUND: _("Feature '{feature}' not found"),
    ErrorCode.FEATURE_NOT_ON_TIER: _("Feature '{feature}' not available on your tier"),
    ErrorCode.FEATURE_DEPENDENCY_MISSING: _(
        "Feature '{feature}' requires missing dependency: {dependency}"
    ),
    ErrorCode.TENANT_NOT_FOUND: _("Tenant not found"),
    ErrorCode.TENANT_SUSPENDED: _("Your account has been suspended"),
    ErrorCode.TENANT_QUOTA_EXCEEDED: _("Quota exceeded: {resource}"),
    # Capsule
    ErrorCode.CAPSULE_NOT_FOUND: _("Agent not found"),
    ErrorCode.CAPSULE_INVALID: _("Invalid agent configuration"),
    ErrorCode.CAPSULE_SIGNATURE_FAILED: _("Agent signature verification failed"),
    # Chat
    ErrorCode.CONVERSATION_NOT_FOUND: _("Conversation not found"),
    ErrorCode.MESSAGE_TOO_LONG: _("Message exceeds maximum length of {max_length} characters"),
    # Memory
    ErrorCode.MEMORY_RECALL_FAILED: _("Failed to recall memories"),
    ErrorCode.MEMORY_STORE_FAILED: _("Failed to store memory"),
    # Tools
    ErrorCode.TOOL_NOT_FOUND: _("Tool '{name}' not found"),
    ErrorCode.TOOL_PERMISSION_DENIED: _("Permission denied for tool '{name}'"),
    ErrorCode.TOOL_EXECUTION_FAILED: _("Tool '{name}' execution failed: {error}"),
    # LLM
    ErrorCode.LLM_NO_CAPABLE_MODEL: _("No model available with required capabilities"),
    ErrorCode.LLM_ALL_FALLBACKS_FAILED: _("All LLM providers are currently unavailable"),
    ErrorCode.LLM_RATE_LIMITED: _("Rate limit exceeded, please try again later"),
    # Billing
    ErrorCode.BILLING_PAYMENT_FAILED: _("Payment processing failed"),
    ErrorCode.BILLING_SUBSCRIPTION_EXPIRED: _("Your subscription has expired"),
    # Budget
    ErrorCode.BUDGET_EXHAUSTED: _(
        "{metric} limit exceeded: {usage}/{limit} used this {period}. Upgrade your plan."
    ),
    ErrorCode.BUDGET_CHECK_FAILED: _("Budget check failed, please try again"),
    # Success
    SuccessCode.CREATED: _("Successfully created"),
    SuccessCode.UPDATED: _("Successfully updated"),
    SuccessCode.DELETED: _("Successfully deleted"),
    SuccessCode.TIER_DEACTIVATED: _("Tier '{name}' deactivated"),
    SuccessCode.FEATURE_REMOVED: _("Feature '{code}' removed from tier"),
    SuccessCode.CAPSULE_CREATED: _("Agent created successfully"),
    SuccessCode.CAPSULE_EXPORTED: _("Agent exported successfully"),
    SuccessCode.CAPSULE_IMPORTED: _("Agent imported successfully"),
    SuccessCode.MESSAGE_SENT: _("Message sent"),
    SuccessCode.MEMORY_STORED: _("Memory stored successfully"),
}


def get_message(code: ErrorCode | SuccessCode | str, **kwargs: object) -> str:
    """Get formatted, translated message for code.

    Args:
        code: Error or success code from enum
        **kwargs: Format arguments for message template

    Returns:
        Formatted, translated message string

    Example:
        >>> get_message(ErrorCode.TIER_ACTIVE_TENANTS, count=5)
        "Cannot delete tier with 5 active tenants"
    """
    msg = MESSAGES.get(code, _("Unknown error"))
    if kwargs:
        # Force evaluation of lazy string for formatting
        return str(msg).format(**kwargs)
    return str(msg)

