"""Granular Permission Definitions.

VIBE Rule 245 Compliant: Extracted from admin/permissions/granular.py.

Contains the canonical permission and role definitions:
- GRANULAR_PERMISSIONS: Resource:Action permission mappings
- PREDEFINED_ROLES: System role templates with permissions

Security Auditor: These definitions form the authorization baseline.
Django Architect: Aligned with ContentType pattern for SpiceDB integration.
"""

from __future__ import annotations

# =============================================================================
# GRANULAR PERMISSION DEFINITIONS
# Per Django ContentType pattern: resource:action
# =============================================================================

GRANULAR_PERMISSIONS: dict[str, dict[str, str]] = {
    # =========================================================================
    # PLATFORM (SAAS Admin - God Mode)
    # =========================================================================
    "platform": {
        "platform:manage": "Full platform management",
        "platform:read_metrics": "View platform metrics",
        "platform:manage_billing": "Manage billing settings",
        "platform:manage_features": "Enable/disable features",
        "platform:impersonate": "Impersonate tenant admins",
    },
    # =========================================================================
    # TENANTS
    # =========================================================================
    "tenant": {
        "tenant:create": "Create new tenants",
        "tenant:read": "View tenant details",
        "tenant:update": "Update tenant settings",
        "tenant:delete": "Delete tenants",
        "tenant:suspend": "Suspend/activate tenants",
        "tenant:manage_subscription": "Change subscription tier",
        "tenant:view_billing": "View billing information",
        "tenant:manage_users": "Manage tenant users",
    },
    # =========================================================================
    # USERS
    # =========================================================================
    "user": {
        "user:create": "Create users",
        "user:read": "View user details",
        "user:update": "Update user profiles",
        "user:delete": "Delete users",
        "user:assign_roles": "Assign roles to users",
        "user:revoke_roles": "Revoke roles from users",
        "user:reset_password": "Reset user passwords",
        "user:manage_mfa": "Enable/disable MFA",
        "user:view_activity": "View user activity logs",
    },
    # =========================================================================
    # AGENTS
    # =========================================================================
    "agent": {
        "agent:create": "Create agents",
        "agent:read": "View agent details",
        "agent:update": "Update agent config",
        "agent:delete": "Delete agents",
        "agent:start": "Start agents",
        "agent:stop": "Stop agents",
        "agent:configure_personality": "Edit personality",
        "agent:configure_tools": "Manage agent tools",
        "agent:view_logs": "View agent logs",
        "agent:export": "Export agent data",
    },
    # =========================================================================
    # CONVERSATIONS
    # =========================================================================
    "conversation": {
        "conversation:create": "Start conversations",
        "conversation:read": "View conversations",
        "conversation:update": "Edit conversations",
        "conversation:delete": "Delete conversations",
        "conversation:send_message": "Send messages",
        "conversation:view_history": "View full history",
        "conversation:export": "Export conversations",
        "conversation:search": "Search conversations",
    },
    # =========================================================================
    # MEMORY
    # =========================================================================
    "memory": {
        "memory:read": "View memories",
        "memory:create": "Create memories",
        "memory:update": "Update memories",
        "memory:delete": "Delete memories",
        "memory:search": "Search memories",
        "memory:export": "Export memories",
        "memory:configure_retention": "Memory retention settings",
    },
    # =========================================================================
    # TOOLS
    # =========================================================================
    "tool": {
        "tool:read": "View available tools",
        "tool:execute": "Execute tools",
        "tool:create": "Create custom tools",
        "tool:update": "Update tool config",
        "tool:delete": "Delete tools",
        "tool:approve": "Approve tool executions",
    },
    # =========================================================================
    # FILES & ASSETS
    # =========================================================================
    "file": {
        "file:upload": "Upload files",
        "file:read": "View/download files",
        "file:delete": "Delete files",
        "file:share": "Share files",
    },
    # =========================================================================
    # API KEYS
    # =========================================================================
    "apikey": {
        "apikey:create": "Create API keys",
        "apikey:read": "View API keys",
        "apikey:revoke": "Revoke API keys",
        "apikey:rotate": "Rotate API keys",
    },
    # =========================================================================
    # INTEGRATIONS
    # =========================================================================
    "integration": {
        "integration:create": "Create integrations",
        "integration:read": "View integrations",
        "integration:update": "Update integrations",
        "integration:delete": "Delete integrations",
        "integration:sync": "Trigger syncs",
    },
    # =========================================================================
    # AUDIT
    # =========================================================================
    "audit": {
        "audit:read": "View audit logs",
        "audit:export": "Export audit logs",
        "audit:configure_retention": "Audit retention",
    },
    # =========================================================================
    # BACKUP
    # =========================================================================
    "backup": {
        "backup:create": "Create backups",
        "backup:read": "View backups",
        "backup:restore": "Restore backups",
        "backup:delete": "Delete backups",
        "backup:configure_schedule": "Configure schedules",
    },
    # =========================================================================
    # BILLING
    # =========================================================================
    "billing": {
        "billing:view_invoices": "View invoices",
        "billing:view_usage": "View usage",
        "billing:manage_payment": "Manage payment methods",
        "billing:view_subscription": "View subscription",
        "billing:change_plan": "Change plans",
    },
    # =========================================================================
    # VOICE (AgentVoice Vox)
    # =========================================================================
    "voice": {
        "voice_persona:create": "Create voice personas",
        "voice_persona:read": "View voice personas",
        "voice_persona:update": "Update voice personas",
        "voice_persona:delete": "Delete voice personas",
        "voice_persona:set_default": "Set default persona",
        "voice_session:create": "Start voice sessions",
        "voice_session:read": "View voice sessions",
        "voice_session:terminate": "Terminate sessions",
        "voice_model:read": "View voice models",
        "voice_model:create": "Create voice models (admin)",
        "voice_model:update": "Update voice models (admin)",
        "voice_model:delete": "Delete voice models (admin)",
    },
}


# =============================================================================
# PREDEFINED ROLES WITH GRANULAR PERMISSIONS
# =============================================================================

PREDEFINED_ROLES: dict[str, dict] = {
    "saas_super_admin": {
        "name": "SAAS Super Administrator",
        "description": "Full platform access (God Mode)",
        "permissions": ["*"],  # All permissions
        "scope": "platform",
    },
    "tenant_admin": {
        "name": "Tenant Administrator",
        "description": "Full tenant management",
        "permissions": [
            "tenant:read",
            "tenant:update",
            "user:*",
            "agent:*",
            "conversation:*",
            "memory:*",
            "tool:*",
            "file:*",
            "apikey:*",
            "integration:*",
            "audit:read",
            "backup:read",
            "billing:view_*",
        ],
        "scope": "tenant",
    },
    "tenant_manager": {
        "name": "Tenant Manager",
        "description": "Manage users and agents",
        "permissions": [
            "tenant:read",
            "user:create",
            "user:read",
            "user:update",
            "agent:*",
            "conversation:read",
            "memory:read",
            "tool:read",
            "file:*",
        ],
        "scope": "tenant",
    },
    "agent_owner": {
        "name": "Agent Owner",
        "description": "Full control of assigned agents",
        "permissions": [
            "agent:read",
            "agent:update",
            "agent:start",
            "agent:stop",
            "agent:configure_personality",
            "agent:configure_tools",
            "agent:view_logs",
            "agent:export",
            "conversation:*",
            "memory:*",
            "tool:read",
            "tool:execute",
            "file:upload",
            "file:read",
        ],
        "scope": "agent",
    },
    "agent_operator": {
        "name": "Agent Operator",
        "description": "Operate agents, no config changes",
        "permissions": [
            "agent:read",
            "agent:start",
            "agent:stop",
            "agent:view_logs",
            "conversation:*",
            "memory:read",
            "memory:search",
            "tool:read",
            "tool:execute",
            "file:upload",
            "file:read",
        ],
        "scope": "agent",
    },
    "user": {
        "name": "Standard User",
        "description": "Chat and basic access",
        "permissions": [
            "agent:read",
            "conversation:create",
            "conversation:read",
            "conversation:send_message",
            "conversation:view_history",
            "memory:read",
            "file:upload",
            "file:read",
        ],
        "scope": "tenant",
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access",
        "permissions": [
            "agent:read",
            "conversation:read",
            "memory:read",
            "file:read",
        ],
        "scope": "tenant",
    },
    "billing_admin": {
        "name": "Billing Administrator",
        "description": "Manage billing only",
        "permissions": [
            "billing:*",
            "tenant:read",
        ],
        "scope": "tenant",
    },
    "security_auditor": {
        "name": "Security Auditor",
        "description": "Read-only security access",
        "permissions": [
            "audit:read",
            "audit:export",
            "user:read",
            "user:view_activity",
            "apikey:read",
            "backup:read",
        ],
        "scope": "tenant",
    },
}


def get_all_permissions() -> set[str]:
    """Return all valid permission IDs.

    Used for validation in role creation.
    """
    all_perms: set[str] = set()
    for resource_perms in GRANULAR_PERMISSIONS.values():
        all_perms.update(resource_perms.keys())
    return all_perms


def validate_permissions(permissions: list[str]) -> list[str]:
    """Validate a list of permissions.

    Args:
        permissions: List of permission IDs to validate.

    Returns:
        List of invalid permission IDs.
    """
    all_perms = get_all_permissions()
    return [
        p
        for p in permissions
        if p not in all_perms and p != "*" and not p.endswith(":*")
    ]


__all__ = [
    "GRANULAR_PERMISSIONS",
    "PREDEFINED_ROLES",
    "get_all_permissions",
    "validate_permissions",
]
