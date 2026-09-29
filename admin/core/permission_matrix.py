"""
Permission Matrix - 4-Level Permission Cascade System.

Implements the hierarchical permission model:
- Level 0: System (runtime and platform administration)
- Level 1: Organization (within one organization)
- Level 2: Agent (per agent)
- Level 3: Resource (conversations, memory, files, tools)

Applied Personas:
- Security Auditor: FAIL-CLOSED on all checks
- PhD Developer: Clean hierarchy design
- Django Architect: Django ORM integration
- Performance: Cached permission lookups

The permission names and the role grants live in ``admin.core.authz`` and
nowhere else. This module supplies the *cascade*: which scope a permission
operates at, and how a check is evaluated against a policy engine. It must
never invent a permission or grant one.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Set, TYPE_CHECKING

from admin.core.authz import (
    PERMISSIONS,
    PermissionLevel,
    level_of,
    permissions_for_principal,
    permissions_for_roles,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class PermissionCheckResult:
    """Result of a permission check."""

    allowed: bool
    permission: str
    level: PermissionLevel
    reason: str
    cached: bool = False


# ========== PERMISSION CATALOG ==========
#
# Derived from admin.core.authz so the cascade levels and the catalog can
# never drift apart.

SYSTEM_PERMISSIONS: Set[str] = {
    name for name, perm in PERMISSIONS.items() if perm.level is PermissionLevel.SYSTEM
}
ORG_PERMISSIONS: Set[str] = {
    name for name, perm in PERMISSIONS.items() if perm.level is PermissionLevel.ORG
}
AGENT_PERMISSIONS: Set[str] = {
    name for name, perm in PERMISSIONS.items() if perm.level is PermissionLevel.AGENT
}
RESOURCE_PERMISSIONS: Set[str] = {
    name for name, perm in PERMISSIONS.items() if perm.level is PermissionLevel.RESOURCE
}

ALL_PERMISSIONS: Set[str] = set(PERMISSIONS)

# Backwards-compatible aliases. The old names described the same four tiers;
# the level-0 tier was colloquially called "God Mode", which is not a name an
# auditable product may use for a privilege tier. It is now SYSTEM.
PLATFORM_PERMISSIONS = SYSTEM_PERMISSIONS
TENANT_PERMISSIONS = ORG_PERMISSIONS


class SpiceDBClientProtocol(Protocol):
    """Protocol for SpiceDB client."""

    async def check_permission(
        self,
        subject: str,
        permission: str,
        resource: str,
    ) -> bool:
        """Check permission in SpiceDB."""
        ...


class PermissionChecker:
    """
    4-Level Permission Cascade Checker.

    Checks permissions through hierarchy:
    1. System level (runtime and platform administration)
    2. Organization level (within one organization)
    3. Agent level (per agent)
    4. Resource level (conversations, memory, files, tools)

    Authorization is layered, and the order is the security property:

    1. **Role-based access control** from ``admin.core.authz`` is the floor.
       It is the authority whenever no policy engine is attached — which is
       the normal Standalone case.
    2. **SpiceDB**, when attached, may only *narrow* that floor.

    Security: FAIL-CLOSED on any error, on any unknown permission, and
    whenever no authority can be established at all.
    """

    def __init__(
        self,
        spicedb_client: Optional[SpiceDBClientProtocol] = None,
    ) -> None:
        """Initialize permission checker."""
        self._spicedb = spicedb_client
        self._cache: Dict[str, bool] = {}

    async def check(
        self,
        user_id: str,
        permission: str,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
        scopes: Optional[List[str]] = None,
    ) -> PermissionCheckResult:
        """
        Check if user has permission.

        Args:
            user_id: User requesting permission
            permission: Permission string (e.g., "resource:chat_send")
            tenant_id: Tenant context
            agent_id: Agent context
            resource_id: Resource context
            roles: The subject's roles. Resolved from the database when
                omitted. An empty role set grants nothing.

        Returns:
            PermissionCheckResult with allowed/denied and reason
        """
        # Validate permission exists
        if permission not in ALL_PERMISSIONS:
            return PermissionCheckResult(
                allowed=False,
                permission=permission,
                level=PermissionLevel.RESOURCE,
                reason=f"Unknown permission: {permission}",
            )

        # Determine level
        level = self._get_level(permission)

        # Build cache key
        cache_key = f"{user_id}:{permission}:{tenant_id}:{agent_id}:{resource_id}"
        if cache_key in self._cache:
            return PermissionCheckResult(
                allowed=self._cache[cache_key],
                permission=permission,
                level=level,
                reason="Cached result",
                cached=True,
            )

        if roles is None:
            roles = await self._roles_for(user_id, tenant_id)

        # Floor: role-based access control. A delegated key is authorized by
        # its scopes alone and never by the issuer's roles.
        granted = permissions_for_principal(roles=roles, scopes=scopes)
        if permission not in granted:
            self._cache[cache_key] = False
            return PermissionCheckResult(
                allowed=False,
                permission=permission,
                level=level,
                reason=(
                    f"Role-based access control denies {permission} "
                    f"for roles {sorted(roles)}"
                ),
            )

        # Ceiling: SpiceDB may only narrow, never widen.
        if self._spicedb is not None:
            spicedb_allowed = await self._check_spicedb(
                user_id, permission, tenant_id, agent_id, resource_id
            )
            if not spicedb_allowed:
                self._cache[cache_key] = False
                return PermissionCheckResult(
                    allowed=False,
                    permission=permission,
                    level=level,
                    reason="Policy engine denied",
                )

        self._cache[cache_key] = True
        return PermissionCheckResult(
            allowed=True,
            permission=permission,
            level=level,
            reason="Role-based access control allowed",
        )

    async def _roles_for(self, user_id: str, tenant_id: Optional[str]) -> List[str]:
        """Resolve the subject's roles.

        FAIL-CLOSED: a subject with no recorded role has no authority. A
        missing role must never become a default grant.
        """
        if not user_id:
            return []
        try:
            from asgiref.sync import sync_to_async

            @sync_to_async
            def _load() -> List[str]:
                from admin.aaas.models import TenantUser

                qs = TenantUser.objects.filter(user_id=user_id, is_active=True)
                if tenant_id:
                    qs = qs.filter(tenant_id=tenant_id)
                return list(qs.values_list("role", flat=True))

            return await _load()
        except Exception as exc:  # noqa: BLE001 - resolution failure is denial
            logger.warning("Role resolution failed for %s; denying: %s", user_id, exc)
            return []

    def _get_level(self, permission: str) -> PermissionLevel:
        """Determine permission level from the catalog."""
        return level_of(permission)

    async def _check_spicedb(
        self,
        user_id: str,
        permission: str,
        tenant_id: Optional[str],
        agent_id: Optional[str],
        resource_id: Optional[str],
    ) -> bool:
        """Check permission via SpiceDB. Denies when SpiceDB is not attached.

        This method is only consulted as a narrowing constraint after
        role-based access control has already allowed the action.
        """
        if not self._spicedb:
            # No policy engine means no additional constraint — and never a
            # grant. Returning True here would widen access by adding an
            # authority that nothing justified. Returning False would deny
            # everyone in Standalone. Callers therefore must not reach this
            # path without an engine; if they do, deny.
            logger.warning(
                "PermissionChecker reached SpiceDB without an engine; denying (fail-closed)"
            )
            return False

        try:
            # Build resource string based on level
            level = self._get_level(permission)

            if level == PermissionLevel.SYSTEM:
                resource = "system:global"
            elif level == PermissionLevel.ORG:
                resource = f"org:{tenant_id or 'unknown'}"
            elif level == PermissionLevel.AGENT:
                resource = f"agent:{agent_id or 'unknown'}"
            else:
                resource = f"resource:{resource_id or 'unknown'}"

            return await self._spicedb.check_permission(
                subject=f"user:{user_id}",
                permission=permission.replace(":", "_"),
                resource=resource,
            )
        except Exception as exc:
            logger.warning("SpiceDB check failed: %s, DENYING", exc)
            return False  # FAIL-CLOSED

    async def list_user_permissions(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        roles: Optional[List[str]] = None,
    ) -> List[str]:
        """List all permissions for a user in context.

        Resolves roles once, then filters through the same cascade ``check``
        uses. A subject with no roles gets an empty list, not a default grant.
        """
        if roles is None:
            roles = await self._roles_for(user_id, tenant_id)

        granted = permissions_for_roles(roles)
        permissions: List[str] = []

        for perm in sorted(granted):
            result = await self.check(
                user_id=user_id,
                permission=perm,
                tenant_id=tenant_id,
                agent_id=agent_id,
                roles=roles,
            )
            if result.allowed:
                permissions.append(perm)

        return permissions

    def clear_cache(self) -> None:
        """Clear permission cache."""
        self._cache.clear()


def get_permission_level(permission: str) -> PermissionLevel:
    """Get permission level from the catalog.

    Raises:
        KeyError: if the permission is unknown. An unknown permission has no
            level and therefore no authority.
    """
    return level_of(permission)
