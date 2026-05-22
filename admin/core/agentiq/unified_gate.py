"""
UnifiedGate - Single permission check combining all sources.

Security Auditor: FAIL-CLOSED principle. Any error = DENY.
PhD Analyst: OPA + SpiceDB + Capsule Scope check.
Django Architect: Async-first design with caching.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from admin.core.models import Capsule

logger = logging.getLogger(__name__)


class UnifiedGate:
    """
    Single gate for all permission checks.

    Combines:
    1. OPA policy check (from capsule.body.governance.opa_policies)
    2. SpiceDB permission (from capsule.body.governance.spicedb_relations)
    3. Capsule scope (from capsule.body.persona.tools.enabled_capabilities)

    Security: FAIL-CLOSED. Any failure = DENY.
    Performance: OPA is cached in-memory. SpiceDB has fallback.
    """

    def __init__(self) -> None:
        """Initialize UnifiedGate."""
        self._opa_cache: Dict[str, bool] = {}

    async def check(
        self,
        capsule: "Capsule",
        action: str,
        resource: str | None = None,
    ) -> bool:
        """
        Check if action is permitted for this capsule.

        Args:
            capsule: The Capsule with governance config
            action: Action to check (e.g., "tool:execute", "memory:write")
            resource: Optional resource identifier

        Returns:
            bool: True if permitted, False otherwise

        Note:
            FAIL-CLOSED: Any error returns False
        """
        try:
            # Extract governance from capsule.body
            body: Dict[str, Any] = capsule.body or {}
            governance = body.get("governance", {})

            # 1. OPA Policy Check (cached)
            opa_allowed = self._check_opa(governance.get("opa_policies", {}), action)
            if not opa_allowed:
                logger.debug("OPA denied action=%s for capsule=%s", action, capsule.id)
                return False

            # 2. SpiceDB Check (with fallback to capsule.governance)
            spicedb_allowed = await self._check_spicedb(
                governance.get("spicedb_relations", {}),
                action,
            )
            if not spicedb_allowed:
                logger.debug("SpiceDB denied action=%s for capsule=%s", action, capsule.id)
                return False

            # 3. Capsule Scope Check
            persona = body.get("persona", {})
            tools_config = persona.get("tools", {})
            scope_allowed = self._check_scope(
                tools_config.get("enabled_capabilities", []),
                action,
                resource,
            )
            if not scope_allowed:
                logger.debug(
                    "Scope denied action=%s resource=%s for capsule=%s",
                    action,
                    resource,
                    capsule.id,
                )
                return False

            return True

        except Exception as exc:
            # FAIL-CLOSED: Any error = DENY
            logger.warning(
                "UnifiedGate error for capsule=%s action=%s: %s",
                getattr(capsule, "id", "unknown"),
                action,
                exc,
            )
            return False

    def _check_opa(self, opa_policies: Dict[str, Any], action: str) -> bool:
        """
        Check OPA policy from capsule governance.

        VIBE SECURITY: FAIL-CLOSED. No policy defined = DENY.
        Cache uses hash of policies dict content (not object id) for cross-worker safety.
        """
        # Cache key using hash of policies content — safe across workers/processes
        try:
            cache_key = f"{hash(tuple(sorted(opa_policies.items())))}:{action}"
        except TypeError:
            # Fallback for nested dicts
            cache_key = f"{hash(str(opa_policies))}:{action}"
        if cache_key in self._opa_cache:
            return self._opa_cache[cache_key]

        # Parse action (e.g., "tool:execute" -> "tool_execution")
        policy_key = action.replace(":", "_")

        policy = opa_policies.get(policy_key, {})
        if not policy:
            # VIBE SECURITY: No policy defined = DENY (secure-by-default)
            logger.warning("No OPA policy defined for action=%s — denying", action)
            result = False
        else:
            result = policy.get("allow", False)

        self._opa_cache[cache_key] = result
        return result

    async def _check_spicedb(
        self,
        spicedb_relations: Dict[str, Any],
        action: str,
    ) -> bool:
        """
        Check SpiceDB permission.

        VIBE SECURITY: FAIL-CLOSED. No relation defined = DENY.
        """
        # Parse action for SpiceDB relation
        relation_key = action.replace(":", "_")

        # Check if relation exists and is allowed
        relation_value = spicedb_relations.get(relation_key)
        if relation_value is None:
            # Try alternate key format
            relation_value = spicedb_relations.get(f"can_{relation_key}")

        if relation_value is None:
            # VIBE SECURITY: No relation defined = DENY (secure-by-default)
            logger.warning("No SpiceDB relation defined for action=%s — denying", action)
            return False

        if isinstance(relation_value, bool):
            return relation_value
        if isinstance(relation_value, list):
            # Non-empty list = allowed
            return len(relation_value) > 0

        return False

    async def check_endpoint_permission(
        self,
        user_id: str,
        tenant_id: str | None,
        permission: str,
    ) -> bool:
        """Check endpoint-level permission (no capsule context).

        Used by @require_permission decorator.
        FAIL-CLOSED: any error = DENY.

        VIBE SECURITY: This currently requires explicit permission grants.
        Until real SpiceDB/OPA is wired, permissions must be defined in
        settings or the user is DENIED.
        """
        try:
            from django.conf import settings

            # Get explicit endpoint permissions mapping from settings
            endpoint_perms = getattr(settings, "ENDPOINT_PERMISSIONS", {})
            allowed_users = endpoint_perms.get(permission, [])

            # If no permission mapping exists, DENY (secure-by-default)
            if not allowed_users:
                logger.warning(
                    "No endpoint permission mapping for perm=%s — denying user=%s",
                    permission,
                    user_id,
                )
                return False

            # Allow if user is in explicit allow-list or "*" (all authenticated)
            if allowed_users == "*" or user_id in allowed_users:
                logger.debug("Endpoint permission granted: user=%s perm=%s", user_id, permission)
                return True

            logger.warning("Endpoint permission denied: user=%s perm=%s", user_id, permission)
            return False
        except Exception as exc:
            logger.warning("Endpoint permission error: %s", exc)
            return False

    def _check_scope(
        self,
        enabled_capabilities: list[str],
        action: str,
        resource: str | None,
    ) -> bool:
        """
        Check if action/resource is in capsule's enabled scope.

        For tool actions, check if tool is in enabled_capabilities.
        """
        if action.startswith("tool:") and resource:
            # Tool action - check if tool is enabled
            return resource in enabled_capabilities

        # Non-tool actions are allowed by default
        return True
