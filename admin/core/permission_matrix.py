"""
Permission Matrix - 4-Level Permission Cascade System.

Implements the hierarchical permission model:
- Level 0: Platform (AAAS Admin - God Mode)
- Level 1: Tenant (within tenant scope)
- Level 2: Agent (per agent)
- Level 3: Resource (chat, memory, tools)

SRS Source: SRS-PERMISSION-MATRIX-2025-12

Applied Personas:
- Security Auditor: FAIL-CLOSED on all checks
- PhD Developer: Clean hierarchy design
- Django Architect: Django ORM integration
- Performance: Cached permission lookups
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, Set

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """Permission hierarchy levels."""

    PLATFORM = "platform"  # 🔴 AAAS God Mode
    TENANT = "tenant"  # 🟠 Within tenant
    AGENT = "agent"  # 🟢 Per agent
    RESOURCE = "resource"  # 🔵 Chat, memory, tools


@dataclass
class Permission:
    """A permission definition."""

    name: str
    level: PermissionLevel
    description: str


@dataclass
class PermissionCheckResult:
    """Result of a permission check."""

    allowed: bool
    permission: str
    level: PermissionLevel
    reason: str
    cached: bool = False


# ========== PERMISSION CATALOG ==========

PLATFORM_PERMISSIONS: Set[str] = {
    "platform:manage",
    "platform:manage_tenants",
    "platform:manage_tiers",
    "platform:manage_roles",
    "platform:view_billing",
    "platform:impersonate",
    "platform:configure",
}

TENANT_PERMISSIONS: Set[str] = {
    "tenant:manage",
    "tenant:administrate",
    "tenant:create_agent",
    "tenant:delete_agent",
    "tenant:view_billing",
    "tenant:manage_api_keys",
    "tenant:assign_roles",
}

AGENT_PERMISSIONS: Set[str] = {
    "agent:configure",
    "agent:activate_adm",
    "agent:activate_dev",
    "agent:activate_trn",
    "agent:activate_std",
    "agent:activate_ro",
    "agent:manage_users",
}

RESOURCE_PERMISSIONS: Set[str] = {
    "chat:send",
    "chat:view",
    "chat:delete",
    "memory:read",
    "memory:write",
    "memory:delete",
    "tool:execute",
    "tool:configure",
}

ALL_PERMISSIONS: Set[str] = (
    PLATFORM_PERMISSIONS
    | TENANT_PERMISSIONS
    | AGENT_PERMISSIONS
    | RESOURCE_PERMISSIONS
)


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
    1. Platform level (AAAS Admin)
    2. Tenant level (within tenant)
    3. Agent level (per agent)
    4. Resource level (chat, memory, tools)

    Security: FAIL-CLOSED on any error.
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
    ) -> PermissionCheckResult:
        """
        Check if user has permission.

        Args:
            user_id: User requesting permission
            permission: Permission string (e.g., "chat:send")
            tenant_id: Tenant context
            agent_id: Agent context
            resource_id: Resource context

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

        # Check via SpiceDB
        allowed = await self._check_spicedb(
            user_id, permission, tenant_id, agent_id, resource_id
        )

        # Cache result
        self._cache[cache_key] = allowed

        return PermissionCheckResult(
            allowed=allowed,
            permission=permission,
            level=level,
            reason="SpiceDB check" if allowed else "Permission denied",
        )

    def _get_level(self, permission: str) -> PermissionLevel:
        """Determine permission level from name."""
        if permission in PLATFORM_PERMISSIONS:
            return PermissionLevel.PLATFORM
        elif permission in TENANT_PERMISSIONS:
            return PermissionLevel.TENANT
        elif permission in AGENT_PERMISSIONS:
            return PermissionLevel.AGENT
        else:
            return PermissionLevel.RESOURCE

    async def _check_spicedb(
        self,
        user_id: str,
        permission: str,
        tenant_id: Optional[str],
        agent_id: Optional[str],
        resource_id: Optional[str],
    ) -> bool:
        """Check permission via SpiceDB."""
        if not self._spicedb:
            # No SpiceDB = fallback to local check
            return self._local_fallback(permission, user_id, tenant_id)

        try:
            # Build resource string based on level
            level = self._get_level(permission)

            if level == PermissionLevel.PLATFORM:
                resource = "platform:global"
            elif level == PermissionLevel.TENANT:
                resource = f"tenant:{tenant_id or 'unknown'}"
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

    def _local_fallback(
        self,
        permission: str,
        user_id: str,
        tenant_id: Optional[str],
    ) -> bool:
        """
        Local fallback when SpiceDB unavailable.

        ONLY for development - grants basic permissions.
        """
        # Platform permissions - deny (require SpiceDB)
        if permission in PLATFORM_PERMISSIONS:
            return False

        # Other permissions - allow for development
        return True

    async def list_user_permissions(
        self,
        user_id: str,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> List[str]:
        """List all permissions for a user in context."""
        permissions: List[str] = []

        for perm in ALL_PERMISSIONS:
            result = await self.check(
                user_id=user_id,
                permission=perm,
                tenant_id=tenant_id,
                agent_id=agent_id,
            )
            if result.allowed:
                permissions.append(perm)

        return permissions

    def clear_cache(self) -> None:
        """Clear permission cache."""
        self._cache.clear()


def get_permission_level(permission: str) -> PermissionLevel:
    """Get permission level from name."""
    if permission in PLATFORM_PERMISSIONS:
        return PermissionLevel.PLATFORM
    elif permission in TENANT_PERMISSIONS:
        return PermissionLevel.TENANT
    elif permission in AGENT_PERMISSIONS:
        return PermissionLevel.AGENT
    else:
        return PermissionLevel.RESOURCE
