"""Authentication Helpers - Utility functions for auth API.

Extracted from admin/auth/api.py for 650-line compliance.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.utils import timezone
from asgiref.sync import sync_to_async

if TYPE_CHECKING:
    from admin.common.auth import TokenPayload

logger = logging.getLogger(__name__)


# Role priority for determining highest role
ROLE_PRIORITY = [
    "saas_admin",
    "tenant_sysadmin",
    "tenant_admin",
    "agent_owner",
    "developer",
    "trainer",
    "user",
    "viewer",
]

# Role to permissions mapping
ROLE_PERMISSIONS = {
    "saas_admin": [
        "platform:manage",
        "platform:manage_tenants",
        "platform:manage_tiers",
        "platform:manage_roles",
        "platform:impersonate",
        "tenant:manage",
        "agent:configure",
        "chat:send",
        "memory:read",
        "memory:write",
    ],
    "tenant_sysadmin": [
        "tenant:manage",
        "tenant:assign_roles",
        "tenant:view_billing",
        "agent:configure",
        "agent:create",
        "agent:delete",
        "chat:send",
        "memory:read",
        "memory:write",
    ],
    "tenant_admin": [
        "tenant:administrate",
        "agent:configure",
        "chat:send",
        "memory:read",
        "memory:write",
    ],
    "agent_owner": [
        "agent:configure",
        "agent:manage_users",
        "chat:send",
        "memory:read",
        "memory:write",
    ],
    "developer": [
        "agent:activate_dev",
        "chat:send",
        "memory:read",
        "memory:write",
    ],
    "trainer": [
        "agent:activate_trn",
        "cognitive:view",
        "cognitive:edit",
        "chat:send",
        "memory:read",
        "memory:write",
    ],
    "user": [
        "chat:send",
        "memory:read",
    ],
    "viewer": [
        "chat:view",
        "memory:read",
    ],
}


def determine_redirect_path(payload: "TokenPayload") -> str:
    """Determine redirect path based on user roles.

    - saas_admin, tenant_sysadmin -> /select-mode (mode selection)
    - tenant_admin, agent_owner -> /dashboard
    - user, viewer -> /chat
    """
    roles = set(payload.roles)
    if "saas_admin" in roles:
        return "/select-mode"
    elif "tenant_sysadmin" in roles:
        return "/select-mode"
    elif "tenant_admin" in roles:
        return "/dashboard"
    elif "agent_owner" in roles:
        return "/dashboard"
    else:
        return "/chat"


def get_highest_role(roles: list[str]) -> str:
    """Get the highest priority role from the roles list."""
    for role in ROLE_PRIORITY:
        if role in roles:
            return role
    return "user"


def get_permissions_for_roles(roles: list[str]) -> list[str]:
    """Map roles to permissions."""
    permissions = set()
    for role in roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    return list(permissions)


async def update_last_login(payload: "TokenPayload") -> None:
    """Update user's last login timestamp if they exist in our database."""
    from admin.saas.models import TenantUser

    try:
        @sync_to_async
        def _update_login():
            TenantUser.objects.filter(user_id=payload.sub).update(last_login_at=timezone.now())
        await _update_login()
    except Exception as e:
        logger.debug(f"Could not update last_login: {e}")


__all__ = [
    "ROLE_PRIORITY",
    "ROLE_PERMISSIONS",
    "determine_redirect_path",
    "get_highest_role",
    "get_permissions_for_roles",
    "update_last_login",
]
