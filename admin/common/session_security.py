"""Session security helpers for permission and authorization resolution."""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class PermissionResolver:
    """Resolves user permissions from SpiceDB and role-based fallbacks."""

    def __init__(self, fail_open: Optional[bool] = None):
        """Initialize PermissionResolver.

        Args:
            fail_open: Optional explicit fail-open flag. When None, the value is
                resolved from SettingsRegistry or the SA01_AUTHZ_FAIL_OPEN env var.
        """
        self._fail_open = fail_open

    def _is_fail_open(self) -> bool:
        """Determine whether authorization should fail open."""
        if self._fail_open is not None:
            return self._fail_open

        try:
            from config.settings_registry import SettingsRegistry

            settings = SettingsRegistry.get()
            return bool(settings.sa01_authz_fail_open)
        except Exception:
            return os.getenv("SA01_AUTHZ_FAIL_OPEN", "false").lower() in {"1", "true", "yes", "on"}

    async def resolve_permissions(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str],
    ) -> list[str]:
        """Resolve permissions from SpiceDB and roles.

        Per design.md Section 5.3:
        - Query SpiceDB for fine-grained permissions
        - Fall back to role-based permissions if SpiceDB unavailable
        - Cache permissions in session

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            roles: User roles from token

        Returns:
            List of permission strings
        """
        permissions = set()
        fail_open = self._is_fail_open()

        # Try SpiceDB first
        try:
            from services.common.spicedb_client import get_spicedb_client

            spicedb = await get_spicedb_client()
            spicedb_permissions = await spicedb.get_permissions(user_id, tenant_id)
            permissions.update(spicedb_permissions)
            logger.debug(
                "SpiceDB permissions resolved: user=%s, permissions=%s",
                user_id,
                spicedb_permissions,
            )
        except Exception as e:
            # Fail closed by default. Role fallback requires explicit override.
            if fail_open:
                logger.warning(
                    "SpiceDB unavailable, using role-based permissions due to SA01_AUTHZ_FAIL_OPEN: %s",
                    e,
                )
            else:
                logger.error(
                    "SpiceDB unavailable and fail-open disabled; returning no derived permissions: %s",
                    e,
                )
                return []

        # Add role-based permissions as fallback/supplement
        role_permissions = self._get_permissions_for_roles(roles)
        permissions.update(role_permissions)

        return list(permissions)

    def _get_permissions_for_roles(self, roles: list[str]) -> list[str]:
        """Get permissions based on roles.

        Per design.md Section 5.3:
        - Role hierarchy: admin > developer > trainer > user
        - Each role inherits lower role permissions
        """
        permissions = set()

        role_permission_map = {
            "admin": [
                "view",
                "use",
                "develop",
                "train",
                "administrate",
                "manage",
                "agents:create",
                "agents:delete",
                "agents:configure",
                "users:manage",
                "tenants:manage",
            ],
            "developer": [
                "view",
                "use",
                "develop",
                "train",
                "agents:create",
                "agents:configure",
            ],
            "trainer": [
                "view",
                "use",
                "train",
                "agents:train",
            ],
            "user": [
                "view",
                "use",
                "conversations:create",
                "conversations:view",
            ],
        }

        for role in roles:
            role_lower = role.lower()
            if role_lower in role_permission_map:
                permissions.update(role_permission_map[role_lower])

        return list(permissions)

    async def get_accessible_agents(
        self,
        user_id: str,
    ) -> list[str]:
        """Get list of agent IDs user can access.

        Per design.md Section 5.3:
        - Query SpiceDB for agents with 'view' permission
        - Used for agent list filtering

        Args:
            user_id: User ID

        Returns:
            List of agent IDs
        """
        try:
            from services.common.spicedb_client import get_spicedb_client

            spicedb = await get_spicedb_client()
            agent_ids = await spicedb.lookup_resources(
                user_id=user_id,
                resource_type="agent",
                permission="view",
            )
            logger.debug("Accessible agents resolved: user=%s, count=%s", user_id, len(agent_ids))
            return agent_ids
        except Exception as e:
            logger.warning("SpiceDB lookup failed, returning empty list: %s", e)
            return []


__all__ = ["PermissionResolver"]
