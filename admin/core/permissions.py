"""
Permission Decorator for Django Ninja APIs
Implements require_permission decorator for route-level permission checks.

VIBE COMPLIANT:
- Pure Django implementation
- Uses JWT claims for permissions
- Supports wildcard (*) for super admin
- Per SRS-PERMISSION-JOURNEYS.md Section 10

7-Persona Implementation:
- 🔒 Security Auditor: Permission enforcement, 403 handling
- 🏗️ Django Architect: Decorator pattern, async support
"""

from functools import wraps
from typing import Callable, List
import logging

from ninja.errors import HttpError

logger = logging.getLogger(__name__)


# =============================================================================
# ROUTE → PERMISSION MAPPING (per SRS Section 7)
# =============================================================================

ROUTE_PERMISSIONS = {
    # Platform Admin
    "/api/v2/infrastructure/health": ["infra:view"],
    "/api/v2/infrastructure/*/config": ["infra:view"],
    "/api/v2/infrastructure/ratelimits": ["infra:view", "infra:ratelimit"],
    "/api/v2/observability/*": ["platform:read_metrics"],
    
    # Tenants
    "/api/v2/saas/tenants": ["tenant:read"],
    "/api/v2/saas/tenants/*": ["tenant:read"],
    "/api/v2/saas/tenants/*/suspend": ["tenant:suspend"],
    
    # Users
    "/api/v2/saas/users": ["user:read"],
    "/api/v2/saas/users/*": ["user:read"],
    "/api/v2/saas/users/*/roles": ["user:assign_roles"],
    
    # Agents
    "/api/v2/agents": ["agent:read"],
    "/api/v2/agents/*": ["agent:read"],
    "/api/v2/agents/*/start": ["agent:start"],
    "/api/v2/agents/*/stop": ["agent:stop"],
    
    # Conversations
    "/api/v2/conversations": ["conversation:read"],
    "/api/v2/conversations/*": ["conversation:read"],
    "/api/v2/conversations/*/messages": ["conversation:send_message"],
    
    # Memory
    "/api/v2/memory": ["memory:read"],
    "/api/v2/memory/search": ["memory:search"],
    "/api/v2/memory/*": ["memory:read"],
    
    # Audit
    "/api/v2/saas/audit": ["audit:read"],
    
    # Billing
    "/api/v2/saas/billing/*": ["platform:manage_billing"],
}


# =============================================================================
# PERMISSION EXTRACTOR
# =============================================================================


def get_user_permissions(auth) -> List[str]:
    """Extract permissions from auth context.
    
    Supports:
    - JWT claims with permissions array
    - User model with permissions property
    - Role-based permission lookup
    """
    if auth is None:
        return []
    
    # If auth is a dict (JWT claims)
    if isinstance(auth, dict):
        return auth.get("permissions", [])
    
    # If auth has permissions attribute
    if hasattr(auth, "permissions"):
        return list(auth.permissions)
    
    # If auth has roles, expand to permissions
    if hasattr(auth, "roles"):
        return _expand_roles_to_permissions(auth.roles)
    
    # If auth is a user object with role_name
    if hasattr(auth, "role_name"):
        return _get_role_permissions(auth.role_name)
    
    return []


def _expand_roles_to_permissions(roles: List[str]) -> List[str]:
    """Expand role names to their permissions."""
    permissions = set()
    for role in roles:
        permissions.update(_get_role_permissions(role))
    return list(permissions)


def _get_role_permissions(role_name: str) -> List[str]:
    """Get permissions for a role per SRS Section 8."""
    ROLE_PERMISSIONS = {
        "saas_super_admin": ["*"],
        "tenant_admin": [
            "tenant:read", "tenant:update",
            "user:create", "user:read", "user:update", "user:delete", "user:assign_roles",
            "agent:create", "agent:read", "agent:update", "agent:delete", "agent:start", "agent:stop",
            "conversation:create", "conversation:read", "conversation:delete", "conversation:send_message",
            "memory:read", "memory:search", "memory:delete",
            "tool:read", "tool:execute",
            "file:upload", "file:read", "file:delete",
            "apikey:create", "apikey:read", "apikey:revoke",
            "integration:read", "integration:update",
            "audit:read",
            "billing:view_invoices", "billing:view_usage",
        ],
        "agent_owner": [
            "agent:read", "agent:update", "agent:start", "agent:stop",
            "agent:configure_personality", "agent:configure_tools", "agent:view_logs", "agent:export",
            "conversation:create", "conversation:read", "conversation:delete", "conversation:send_message",
            "memory:read", "memory:search",
            "tool:read", "tool:execute",
            "file:upload", "file:read",
        ],
        "agent_operator": [
            "agent:read", "agent:start", "agent:stop", "agent:view_logs",
            "conversation:create", "conversation:read", "conversation:send_message",
            "memory:read", "memory:search",
            "tool:read", "tool:execute",
            "file:upload", "file:read",
        ],
        "user": [
            "agent:read",
            "conversation:create", "conversation:read", "conversation:send_message", "conversation:view_history",
            "memory:read",
            "file:upload", "file:read",
        ],
        "viewer": [
            "agent:read",
            "conversation:read",
            "memory:read",
            "file:read",
        ],
        "billing_admin": [
            "billing:view_invoices", "billing:view_usage", "billing:manage_payment", "billing:change_plan",
            "tenant:read",
        ],
        "security_auditor": [
            "audit:read", "audit:export",
            "user:read", "user:view_activity",
            "apikey:read",
            "backup:read",
        ],
        "infra_admin": [
            "infra:view", "infra:configure", "infra:ratelimit",
            "platform:read_metrics",
        ],
    }
    return ROLE_PERMISSIONS.get(role_name, [])


# =============================================================================
# PERMISSION DECORATOR
# =============================================================================


def require_permission(*permissions: str):
    """Decorator to require specific permissions for an API endpoint.
    
    Usage:
        @router.get("/endpoint")
        @require_permission("tenant:read")
        async def my_endpoint(request):
            ...
    
    Args:
        permissions: One or more permission strings. User needs ANY of them.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(request, *args, **kwargs):
            user_perms = get_user_permissions(getattr(request, 'auth', None))
            
            # Super admin has all permissions
            if "*" in user_perms:
                return await func(request, *args, **kwargs)
            
            # Check if user has any of the required permissions
            if not any(p in user_perms for p in permissions):
                logger.warning(
                    f"Permission denied: {permissions} required, "
                    f"user has {user_perms}"
                )
                raise HttpError(403, "Permission denied")
            
            return await func(request, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(request, *args, **kwargs):
            user_perms = get_user_permissions(getattr(request, 'auth', None))
            
            if "*" in user_perms:
                return func(request, *args, **kwargs)
            
            if not any(p in user_perms for p in permissions):
                logger.warning(
                    f"Permission denied: {permissions} required, "
                    f"user has {user_perms}"
                )
                raise HttpError(403, "Permission denied")
            
            return func(request, *args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def has_permission(auth, permission: str) -> bool:
    """Check if auth context has a specific permission.
    
    Useful for conditional logic in views.
    """
    user_perms = get_user_permissions(auth)
    return "*" in user_perms or permission in user_perms


def has_any_permission(auth, *permissions: str) -> bool:
    """Check if auth context has any of the specified permissions."""
    user_perms = get_user_permissions(auth)
    return "*" in user_perms or any(p in user_perms for p in permissions)


def has_all_permissions(auth, *permissions: str) -> bool:
    """Check if auth context has all specified permissions."""
    user_perms = get_user_permissions(auth)
    if "*" in user_perms:
        return True
    return all(p in user_perms for p in permissions)
