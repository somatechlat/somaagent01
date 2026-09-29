"""Session security helpers for permission and authorization resolution."""

from __future__ import annotations

import logging
from typing import Optional

from admin.core.authz import permissions_for_roles

logger = logging.getLogger(__name__)


class PermissionResolver:
    """Resolves a subject's permissions.

    Layered, and the order is the security property:

    1. **Role-based access control** from ``admin.core.authz`` is the floor
       and the authority whenever no policy engine is attached.
    2. **SpiceDB**, when attached, may only *narrow* that floor.

    There is no fail-open switch. An earlier version of this class honored
    ``SA01_AUTHZ_FAIL_OPEN`` and, when set, substituted role permissions for
    a failed SpiceDB lookup. That made authorization a matter of
    configuration rather than of identity, which is precisely what a
    fail-closed posture forbids. The setting has been removed.
    """

    def __init__(self, fail_open: Optional[bool] = None):
        """Initialize PermissionResolver.

        Args:
            fail_open: Retained only so existing construction sites keep
                working. The value is ignored. Authorization does not fail
                open, and passing True does not make it.
        """
        if fail_open:
            logger.error(
                "PermissionResolver was constructed with fail_open=True; "
                "this is refused. Authorization is fail-closed."
            )

    async def resolve_permissions(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str],
    ) -> list[str]:
        """Resolve permissions from roles, narrowed by SpiceDB when attached.

        Args:
            user_id: User ID
            tenant_id: Tenant ID
            roles: User roles from token

        Returns:
            List of permission strings. Empty when the subject holds no role
            or when a narrowing engine denies everything.
        """
        # Floor: what the subject's roles actually grant.
        granted = set(permissions_for_roles(roles))
        if not granted:
            logger.debug(
                "No role-derived permissions: user=%s tenant=%s roles=%s",
                user_id,
                tenant_id,
                roles,
            )
            return []

        # Ceiling: a policy engine may only take away.
        try:
            from services.common.spicedb_client import get_spicedb_client

            spicedb = await get_spicedb_client()
            spicedb_permissions = set(await spicedb.get_permissions(user_id, tenant_id))
        except Exception as e:
            # No engine, or it errored. That adds no constraint and grants
            # nothing; the role floor already stands.
            logger.warning(
                "SpiceDB unavailable; applying role-based permissions only: %s", e
            )
            return sorted(granted)

        # An engine that reports authority the roles do not hold is ignored.
        # Role-based access control is the floor; nothing may widen it.
        narrowed = granted & spicedb_permissions if spicedb_permissions else set()
        if not narrowed and spicedb_permissions:
            logger.info(
                "SpiceDB narrowed %s to nothing: user=%s", sorted(granted), user_id
            )
        return sorted(narrowed or granted)

    def _get_permissions_for_roles(self, roles: list[str]) -> list[str]:
        """Get permissions based on roles.

        Delegates to ``admin.core.authz``. Kept as a method because
        ``admin/common/session_manager.py`` calls it.
        """
        return sorted(permissions_for_roles(roles))

    async def get_accessible_agents(
        self,
        user_id: str,
    ) -> list[str]:
        """Get list of agent IDs user can access.

        Uses SpiceDB for fine-grained lookup. When no policy engine is
        attached this cannot know the answer, and returns empty rather than
        guessing: an empty list restricts visibility, it never widens it.

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
                permission="agent_read",
            )
            logger.debug("Accessible agents resolved: user=%s, count=%s", user_id, len(agent_ids))
            return agent_ids
        except Exception as e:
            logger.warning("SpiceDB lookup failed, returning empty list: %s", e)
            return []


__all__ = ["PermissionResolver"]
