"""Authentication Helpers - Utility functions for auth API.

Extracted from admin/auth/api.py for 650-line compliance.

Roles and permissions are defined in ``admin.core.authz`` and nowhere else.
This module resolves them; it does not define them.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.utils import timezone

from admin.core.authz import (
    ROLE_PERMISSIONS,
    ROLE_PRIORITY,
    permissions_for_roles,
)

if TYPE_CHECKING:
    from admin.common.auth import TokenPayload

logger = logging.getLogger(__name__)

__all__ = [
    "ROLE_PRIORITY",
    "ROLE_PERMISSIONS",
    "determine_redirect_path",
    "get_highest_role",
    "get_permissions_for_roles",
    "update_last_login",
]


def determine_redirect_path(payload: "TokenPayload") -> str:
    """Determine redirect path based on user roles.

    Every path returned here is a real route in ``webui/src/main.ts``. The
    previous implementation sent platform administrators to ``/select-mode``,
    a god/tenant mode switcher that was deleted with the SaaS console; that
    redirect was a dead end.
    """
    # Role names come from the catalog vocabulary (ROLE_PRIORITY), not from
    # strings typed here. A renamed role used to send people to the wrong
    # console without failing anything.
    from admin.core.authz import ROLE_PRIORITY

    known = [r for r in ROLE_PRIORITY if r in set(payload.roles)]
    if not known:
        return "/chat"
    top = known[0]
    if top in ("sysadmin", "org_admin"):
        return "/saas/dashboard"
    if top in ("agent_owner", "developer"):
        return "/admin/agents"
    return "/chat"


def get_highest_role(roles: list[str]) -> str:
    """Get the highest priority role from the roles list.

    Returns ``"member"`` when no role is recognized. That is the least
    privileged role in the catalog, which is the correct fallback: an
    unrecognized role must never resolve to something more powerful.
    """
    for role in ROLE_PRIORITY:
        if role in roles:
            return role
    return "member"


def get_permissions_for_roles(roles: list[str]) -> list[str]:
    """Map roles to permissions.

    Unknown roles contribute nothing. A role name this deployment has not
    defined grants no authority.
    """
    return sorted(permissions_for_roles(roles))


async def update_last_login(payload: "TokenPayload") -> None:
    """Update user's last login timestamp if they exist in our database."""
    from admin.aaas.models import TenantUser

    try:

        @sync_to_async
        def _update_login():
            TenantUser.objects.filter(user_id=payload.sub).update(last_login_at=timezone.now())

        await _update_login()
    except Exception as e:
        logger.debug("Could not update last_login: %s", e)
