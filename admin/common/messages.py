"""Centralized Error Codes and Messages — I18N Ready.

VIBE RULE 11: All user-facing text MUST use get_message().
This module is the SINGLE SOURCE OF TRUTH for all messages.
"""

from enum import Enum
from typing import Any

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
    FRONTEND_NOT_BUILT = "frontend_not_built"

    # Auth
    AUTH_INVALID_TOKEN = "auth_invalid_token"
    AUTH_EXPIRED_TOKEN = "auth_expired_token"
    AUTH_MISSING_TOKEN = "auth_missing_token"
    AUTH_PERMISSION_DENIED = "auth_permission_denied"
    AUTH_INVALID_OR_EXPIRED_TOKEN = "auth_invalid_or_expired_token"
    AUTH_SESSION_EXPIRED = "auth_session_expired"
    TOKEN_INVALID_OR_EXPIRED = "token_invalid_or_expired"
    API_KEY_NOT_FOUND = "api_key_not_found"
    INVALID_PERMISSIONS = "invalid_permissions"

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

    # AAAS - Integrations
    LAGO_NOT_CONFIGURED = "lago_not_configured"

    # Capsule
    CAPSULE_NOT_FOUND = "capsule_not_found"
    CAPSULE_INVALID = "capsule_invalid"
    CAPSULE_SIGNATURE_FAILED = "capsule_signature_failed"

    # Chat
    CONVERSATION_NOT_FOUND = "conversation_not_found"
    MESSAGE_TOO_LONG = "message_too_long"

    # Voice
    SESSION_NOT_ACTIVE = "session_not_active"

    # Memory
    MEMORY_RECALL_FAILED = "memory_recall_failed"
    MEMORY_STORE_FAILED = "memory_store_failed"
    MEMORY_DELETE_FAILED = "memory_delete_failed"

    # Tools
    TOOL_NOT_FOUND = "tool_not_found"
    TOOL_PERMISSION_DENIED = "tool_permission_denied"
    TOOL_EXECUTION_FAILED = "tool_execution_failed"
    TOOL_MISSING_ARGUMENT = "tool_missing_argument"
    TOOL_INVALID_ARGUMENT = "tool_invalid_argument"
    TOOL_FILE_NOT_FOUND = "tool_file_not_found"
    TOOL_PATH_NOT_ALLOWED = "tool_path_not_allowed"
    TOOL_SERVICE_NOT_CONFIGURED = "tool_service_not_configured"
    TOOL_URL_INVALID = "tool_url_invalid"
    TOOL_ATTACHMENT_NOT_FOUND = "tool_attachment_not_found"
    TOOL_ATTACHMENT_FETCH_FAILED = "tool_attachment_fetch_failed"
    TOOL_INGESTION_FAILED = "tool_ingestion_failed"
    TOOL_EXTRACTION_FAILED = "tool_extraction_failed"
    TOOL_POLICY_EVALUATION_FAILED = "tool_policy_evaluation_failed"
    TOOL_POLICY_DENIED = "tool_policy_denied"
    TOOL_EXECUTION_DENIED = "tool_execution_denied"
    TOOL_UNHANDLED_ERROR = "tool_unhandled_error"
    TOOL_EXECUTION_TIMEOUT = "tool_execution_timeout"

    # LLM
    LLM_NO_CAPABLE_MODEL = "llm_no_capable_model"
    LLM_ALL_FALLBACKS_FAILED = "llm_all_fallbacks_failed"
    LLM_RATE_LIMITED = "llm_rate_limited"
    LLM_DEGRADED_MODEL_UNAVAILABLE = "llm_degraded_model_unavailable"
    LLM_DEGRADED_TIMEOUT = "llm_degraded_timeout"
    LLM_DEGRADED_CIRCUIT_OPEN = "llm_degraded_circuit_open"

    # Degradation
    DEGRADED_PERMISSION_DENIED = "degraded_permission_denied"
    DEGRADED_GATE_DENIED = "degraded_gate_denied"

    # Billing
    BILLING_PAYMENT_FAILED = "billing_payment_failed"
    BILLING_SUBSCRIPTION_EXPIRED = "billing_subscription_expired"

    # Integrations
    LAGO_ERROR = "lago_error"
    SMTP_SEND_FAILED = "smtp_send_failed"
    BILLING_INVALID_SIGNATURE = "billing_invalid_signature"
    BILLING_INVALID_JSON = "billing_invalid_json"

    # Budget
    BUDGET_EXHAUSTED = "budget_exhausted"
    BUDGET_CHECK_FAILED = "budget_check_failed"

    # Vault / Secrets
    VAULT_ADDR_MISSING = "vault_addr_missing"
    VAULT_UNREACHABLE = "vault_unreachable"

    # Files
    FILE_SIZE_EXCEEDED = "file_size_exceeded"

    # Rate Limit
    RATE_LIMIT_NOT_FOUND = "rate_limit_not_found"
    RATE_LIMIT_INVALID_POLICY = "rate_limit_invalid_policy"
    RATE_LIMIT_KEY_EXISTS = "rate_limit_key_exists"
    RATE_LIMIT_RULE_EXISTS = "rate_limit_rule_exists"
    RATE_LIMIT_NOT_DEFINED = "rate_limit_not_defined"

    # Config
    CONFIG_RUNTIME_UPDATE_NOT_SUPPORTED = "config_runtime_update_not_supported"
    CONFIG_TENANT_MODEL_PENDING = "config_tenant_model_pending"

    # Policy
    POLICY_BLOCKED = "policy_blocked"

    # SomaBrain
    SOMABRAIN_UNAVAILABLE = "somabrain_unavailable"

    # SSO
    SSO_ISSUER_URL_REQUIRED = "sso_issuer_url_required"
    SSO_OIDC_DISCOVERY_FAILED = "sso_oidc_discovery_failed"
    SSO_SERVER_URL_REQUIRED = "sso_server_url_required"
    SSO_DOMAIN_REQUIRED = "sso_domain_required"
    SSO_UNKNOWN_PROVIDER = "sso_unknown_provider"
    SSO_TEST_FAILED = "sso_test_failed"


class SuccessCode(str, Enum):
    """Success codes for confirmations."""

    # Generic
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"

    # AAAS
    TIER_DEACTIVATED = "tier_deactivated"
    FEATURE_REMOVED = "feature_removed"
    LAGO_PLANS_SYNCED = "lago_plans_synced"

    # Capsule
    CAPSULE_CREATED = "capsule_created"
    CAPSULE_EXPORTED = "capsule_exported"
    CAPSULE_IMPORTED = "capsule_imported"

    # Chat
    MESSAGE_SENT = "message_sent"

    # Voice
    PERSONA_DELETED = "persona_deleted"
    PERSONA_SET_DEFAULT = "persona_set_default"
    SESSION_TERMINATED = "session_terminated"
    TEST_EMAIL_SENT = "test_email_sent"

    # Memory
    MEMORY_STORED = "memory_stored"
    MEMORY_QUEUED_FOR_SYNC = "memory_queued_for_sync"
    MEMORY_DELETED = "memory_deleted"

    # Brain
    WEBSOCKET_STREAMING = "websocket_streaming"
    ASSET_MARKED_FOR_DELETION = "asset_marked_for_deletion"
    THREAD_RESET = "thread_reset"
    THREAD_TERMINATED = "thread_terminated"
    ADAPTATION_RESET = "adaptation_reset"
    AGENT_AWAKENED = "agent_awakened"

    # SSO
    SSO_OIDC_REACHABLE = "sso_oidc_reachable"
    SSO_LDAP_VALIDATED = "sso_ldap_validated"
    SSO_PROVIDER_VALIDATED = "sso_provider_validated"
    SSO_CONFIGURED = "sso_configured"

    # Auth
    INVITATION_RESENT = "invitation_resent"
    DOWNLOAD_LINK_VALID = "download_link_valid"
    EXPORT_DELETED = "export_deleted"
    DELETION_REQUEST_CANCELLED = "deletion_request_cancelled"
    CONNECTION_SUCCESSFUL = "connection_successful"
    TOKEN_VALID = "token_valid"
    PASSWORD_CHANGED = "password_changed"
    API_KEY_SAVE_WARNING = "api_key_save_warning"
    API_KEY_REVOKED = "api_key_revoked"
    BACKUP_CODE_ACCEPTED = "backup_code_accepted"
    VERIFICATION_EMAIL_SENT = "verification_email_sent"

    # Voice
    VOICE_WEBSOCKET_CONNECTED = "voice_websocket_connected"

    # Billing
    PAYMENT_METHOD_REFERENCE_STORED = "payment_method_reference_stored"


# I18N-Ready Messages using Django gettext_lazy
MESSAGES: dict[str | ErrorCode | SuccessCode, str | Any] = {
    # Generic
    ErrorCode.FRONTEND_NOT_BUILT: _(
        "Frontend not built. Run: cd webui && npm run build"
    ),
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
    ErrorCode.AUTH_INVALID_OR_EXPIRED_TOKEN: _("Invalid or expired token"),
    ErrorCode.AUTH_SESSION_EXPIRED: _("Session expired. Please log in again."),
    ErrorCode.TOKEN_INVALID_OR_EXPIRED: _("Token is invalid or expired"),
    ErrorCode.API_KEY_NOT_FOUND: _("API key {key_id} not found"),
    ErrorCode.INVALID_PERMISSIONS: _("Invalid permissions"),
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
    ErrorCode.LAGO_NOT_CONFIGURED: _("Lago not configured"),
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
    ErrorCode.MEMORY_DELETE_FAILED: _("Delete failed"),
    # Tools
    ErrorCode.TOOL_NOT_FOUND: _("Tool '{name}' not found"),
    ErrorCode.TOOL_PERMISSION_DENIED: _("Permission denied for tool '{name}'"),
    ErrorCode.TOOL_EXECUTION_FAILED: _("Tool '{name}' execution failed: {error}"),
    ErrorCode.TOOL_MISSING_ARGUMENT: _("Missing required argument: {arg}"),
    ErrorCode.TOOL_INVALID_ARGUMENT: _("Invalid argument: {arg}"),
    ErrorCode.TOOL_FILE_NOT_FOUND: _("File not found: {path}"),
    ErrorCode.TOOL_PATH_NOT_ALLOWED: _("Access outside work directory is not allowed"),
    ErrorCode.TOOL_SERVICE_NOT_CONFIGURED: _("Service not configured: {service}"),
    ErrorCode.TOOL_URL_INVALID: _("Invalid URL provided"),
    ErrorCode.TOOL_ATTACHMENT_NOT_FOUND: _("Attachment not found"),
    ErrorCode.TOOL_ATTACHMENT_FETCH_FAILED: _("Failed to fetch attachment"),
    ErrorCode.TOOL_INGESTION_FAILED: _("Ingestion failed"),
    ErrorCode.TOOL_EXTRACTION_FAILED: _("No text could be extracted"),
    ErrorCode.TOOL_POLICY_EVALUATION_FAILED: _("Policy evaluation failed."),
    ErrorCode.TOOL_POLICY_DENIED: _("Policy denied tool execution."),
    ErrorCode.TOOL_EXECUTION_DENIED: _("Policy denied tool execution"),
    ErrorCode.TOOL_UNHANDLED_ERROR: _("Unhandled tool executor error."),
    ErrorCode.TOOL_EXECUTION_TIMEOUT: _("Tool execution timed out"),
    # LLM
    ErrorCode.LLM_NO_CAPABLE_MODEL: _("No model available with required capabilities"),
    ErrorCode.LLM_ALL_FALLBACKS_FAILED: _("All LLM providers are currently unavailable"),
    ErrorCode.LLM_RATE_LIMITED: _("Rate limit exceeded, please try again later"),
    ErrorCode.LLM_DEGRADED_MODEL_UNAVAILABLE: _(
        "System degraded: Model selection unavailable. Using fallback context."
    ),
    ErrorCode.LLM_DEGRADED_TIMEOUT: _(
        "System degraded: LLM request timed out. Please retry shortly."
    ),
    ErrorCode.LLM_DEGRADED_CIRCUIT_OPEN: _(
        "System degraded: LLM service temporarily unavailable. Using cached context only."
    ),
    ErrorCode.DEGRADED_PERMISSION_DENIED: _("Permission denied"),
    ErrorCode.DEGRADED_GATE_DENIED: _("Gate denied"),
    # Billing
    ErrorCode.BILLING_PAYMENT_FAILED: _("Payment processing failed"),
    ErrorCode.BILLING_SUBSCRIPTION_EXPIRED: _("Your subscription has expired"),
    ErrorCode.BILLING_INVALID_SIGNATURE: _("Invalid signature"),
    ErrorCode.BILLING_INVALID_JSON: _("Invalid JSON"),
    # Budget
    ErrorCode.BUDGET_EXHAUSTED: _(
        "{metric} limit exceeded: {usage}/{limit} used this {period}. Upgrade your plan."
    ),
    ErrorCode.BUDGET_CHECK_FAILED: _("Budget check failed, please try again"),
    # Vault / Secrets
    ErrorCode.VAULT_ADDR_MISSING: _(
        "Vault address is required in production mode. Set VAULT_ADDR in your environment."
    ),
    ErrorCode.VAULT_UNREACHABLE: _(
        "Vault is unreachable at {addr} in production mode. All system secrets must be stored in Vault."
    ),
    # Files
    ErrorCode.FILE_SIZE_EXCEEDED: _(
        "File size exceeds declared size"
    ),
    # Rate Limit
    ErrorCode.RATE_LIMIT_NOT_FOUND: _("Rate limit policy '{key}' not found"),
    ErrorCode.RATE_LIMIT_INVALID_POLICY: _("Invalid policy. Must be one of: {policies}"),
    ErrorCode.RATE_LIMIT_KEY_EXISTS: _("Rate limit key already exists"),
    ErrorCode.RATE_LIMIT_RULE_EXISTS: _("Rate limit already exists"),
    ErrorCode.RATE_LIMIT_NOT_DEFINED: _("No rate limits defined"),
    # Config
    ErrorCode.CONFIG_RUNTIME_UPDATE_NOT_SUPPORTED: _(
        "Runtime system config update not supported. Update env vars."
    ),
    ErrorCode.CONFIG_TENANT_MODEL_PENDING: _("Tenant config model pending"),
    # Policy
    ErrorCode.POLICY_BLOCKED: _(
        "Message blocked by policy. Please contact your administrator if you believe this is an error."
    ),
    # SomaBrain
    ErrorCode.SOMABRAIN_UNAVAILABLE: _("SomaBrain unavailable"),
    # SSO
    ErrorCode.SSO_ISSUER_URL_REQUIRED: _("Issuer URL is required"),
    ErrorCode.SSO_OIDC_DISCOVERY_FAILED: _("OIDC discovery failed: HTTP {status_code}"),
    ErrorCode.SSO_SERVER_URL_REQUIRED: _("Server URL is required"),
    ErrorCode.SSO_DOMAIN_REQUIRED: _("Domain/Tenant ID is required"),
    ErrorCode.SSO_UNKNOWN_PROVIDER: _("Unknown provider: {provider}"),
    ErrorCode.SSO_TEST_FAILED: _("Test failed: {error}"),
    # Voice
    ErrorCode.SESSION_NOT_ACTIVE: _("Session is not active (status: {status})"),
    SuccessCode.PERSONA_DELETED: _("Persona deleted"),
    SuccessCode.PERSONA_SET_DEFAULT: _("Persona set as default"),
    SuccessCode.SESSION_TERMINATED: _("Session terminated"),
    SuccessCode.TEST_EMAIL_SENT: _("Test email sent"),
    # Integrations
    ErrorCode.LAGO_ERROR: _("Lago error: {status}"),
    ErrorCode.SMTP_SEND_FAILED: _("Failed to send test email"),
    # Success
    SuccessCode.CREATED: _("Successfully created"),
    SuccessCode.UPDATED: _("Successfully updated"),
    SuccessCode.DELETED: _("Successfully deleted"),
    SuccessCode.TIER_DEACTIVATED: _("Tier '{name}' deactivated"),
    SuccessCode.FEATURE_REMOVED: _("Feature '{feature_code}' removed from tier"),
    SuccessCode.LAGO_PLANS_SYNCED: _("Synced {count} plans from Lago"),
    SuccessCode.CAPSULE_CREATED: _("Agent created successfully"),
    SuccessCode.CAPSULE_EXPORTED: _("Agent exported successfully"),
    SuccessCode.CAPSULE_IMPORTED: _("Agent imported successfully"),
    SuccessCode.MESSAGE_SENT: _("Message sent"),
    SuccessCode.MEMORY_STORED: _("Memory stored"),
    SuccessCode.MEMORY_QUEUED_FOR_SYNC: _("Memory queued for sync"),
    SuccessCode.MEMORY_DELETED: _("Memory deleted"),
    SuccessCode.WEBSOCKET_STREAMING: _("Connect to WebSocket for streaming response"),
    SuccessCode.ASSET_MARKED_FOR_DELETION: _("Asset marked for deletion"),
    SuccessCode.THREAD_RESET: _("Thread reset to initial state"),
    SuccessCode.THREAD_TERMINATED: _("Thread terminated"),
    SuccessCode.ADAPTATION_RESET: _("Adaptation parameters reset to defaults"),
    SuccessCode.AGENT_AWAKENED: _("Agent awakened"),
    SuccessCode.SSO_OIDC_REACHABLE: _("OIDC provider is reachable and configured correctly."),
    SuccessCode.SSO_LDAP_VALIDATED: _("LDAP server {server_url} configuration validated."),
    SuccessCode.SSO_PROVIDER_VALIDATED: _("{provider} configuration validated."),
    SuccessCode.SSO_CONFIGURED: _("{provider} configured successfully."),
    SuccessCode.INVITATION_RESENT: _("Invitation resent"),
    SuccessCode.DOWNLOAD_LINK_VALID: _("Download link valid for 1 hour"),
    SuccessCode.EXPORT_DELETED: _("Export deleted"),
    SuccessCode.DELETION_REQUEST_CANCELLED: _("Deletion request cancelled"),
    SuccessCode.CONNECTION_SUCCESSFUL: _("Connection successful"),
    SuccessCode.TOKEN_VALID: _("Token is valid"),
    SuccessCode.PASSWORD_CHANGED: _("Password changed successfully"),
    SuccessCode.API_KEY_SAVE_WARNING: _("Save this key now - it cannot be retrieved again"),
    SuccessCode.API_KEY_REVOKED: _("API key {key_id} revoked"),
    SuccessCode.BACKUP_CODE_ACCEPTED: _("Backup code accepted"),
    SuccessCode.VERIFICATION_EMAIL_SENT: _(
        "Verification email sent. Please check your inbox."
    ),
    SuccessCode.VOICE_WEBSOCKET_CONNECTED: _(
        "Voice WebSocket connected. Send 'start_session' to begin."
    ),
    SuccessCode.PAYMENT_METHOD_REFERENCE_STORED: _(
        "Payment method reference stored. Stripe verification required for full card details."
    ),
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
