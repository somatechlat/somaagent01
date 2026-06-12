"""
UnifiedGate - Single permission check combining all sources.

Security Auditor: FAIL-CLOSED principle. Any error = DENY.
PhD Analyst: OPA + SpiceDB + Capsule Scope check.
Django Architect: Async-first design with caching.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from admin.core.models import Capsule

from services.common.policy_client import PolicyClient, PolicyRequest, get_policy_client
from services.common.spicedb_client import SpiceDBClient, get_spicedb_client

logger = logging.getLogger(__name__)


class UnifiedGate:
    """
    Single gate for all permission checks.

    Combines:
    1. OPA policy check (real HTTP call to OPA server)
    2. SpiceDB permission (real gRPC call to SpiceDB)
    3. Capsule scope (from capsule.body.persona.tools.enabled_capabilities)

    Security: FAIL-CLOSED. Any failure = DENY.
    Performance: OPA is cached by PolicyClient. SpiceDB has connection reuse.
    """

    def __init__(self) -> None:
        """Initialize UnifiedGate."""
        self._policy_client: Optional[PolicyClient] = None
        self._spicedb_client: Optional[SpiceDBClient] = None

    def _get_policy_client(self) -> PolicyClient:
        if self._policy_client is None:
            self._policy_client = get_policy_client()
        return self._policy_client

    def _get_spicedb_client(self) -> SpiceDBClient:
        if self._spicedb_client is None:
            self._spicedb_client = SpiceDBClient()
        return self._spicedb_client

    async def check(
        self,
        capsule: "Capsule",
        action: str,
        resource: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> bool:
        """
        Check if action is permitted for this capsule.

        Args:
            capsule: The Capsule with governance config
            action: Action to check (e.g., "tool:execute", "memory:write")
            resource: Optional resource identifier
            user_id: User ID for SpiceDB subject (required for real checks)
            tenant_id: Tenant ID for OPA context

        Returns:
            bool: True if permitted, False otherwise

        Note:
            FAIL-CLOSED: Any error returns False
        """
        try:
            # 1. OPA Policy Check (real HTTP call)
            opa_allowed = await self._check_opa(
                action=action,
                resource=resource,
                capsule=capsule,
                user_id=user_id,
                tenant_id=tenant_id,
            )
            if not opa_allowed:
                logger.debug("OPA denied action=%s for capsule=%s", action, capsule.id)
                return False

            # 2. SpiceDB Check (real gRPC call)
            spicedb_allowed = await self._check_spicedb(
                action=action,
                resource=resource,
                capsule=capsule,
                user_id=user_id,
                tenant_id=tenant_id,
            )
            if not spicedb_allowed:
                logger.debug("SpiceDB denied action=%s for capsule=%s", action, capsule.id)
                return False

            # 3. Capsule Scope Check
            body: Dict[str, Any] = capsule.body or {}
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

    async def _check_opa(
        self,
        action: str,
        resource: str | None,
        capsule: "Capsule",
        user_id: str | None,
        tenant_id: str | None,
    ) -> bool:
        """
        Check OPA policy via real HTTP call to OPA server.

        VIBE SECURITY: FAIL-CLOSED. Any error = DENY.
        """
        try:
            client = self._get_policy_client()
            request = PolicyRequest(
                tenant=tenant_id or str(capsule.tenant_id),
                persona_id=None,
                action=action,
                resource=resource or str(capsule.id),
                context={
                    "user_id": user_id,
                    "capsule_id": str(capsule.id),
                },
            )
            return await client.evaluate(request)
        except Exception as exc:
            logger.exception("OPA check failed (FAIL-CLOSED): %s", exc)
            return False

    async def _check_spicedb(
        self,
        action: str,
        resource: str | None,
        capsule: "Capsule",
        user_id: str | None,
        tenant_id: str | None,
    ) -> bool:
        """
        Check SpiceDB permission via real gRPC call.

        VIBE SECURITY: FAIL-CLOSED. Missing user_id or any error = DENY.
        """
        if not user_id:
            logger.warning(
                "SpiceDB check requires user_id (FAIL-CLOSED): action=%s", action
            )
            return False

        try:
            client = self._get_spicedb_client()

            # Derive SpiceDB resource type and permission from action.
            # action format: "domain:permission" (e.g., "chat:send", "tool:execute")
            if ":" in action:
                domain, permission = action.split(":", 1)
            else:
                domain, permission = "agent", action

            resource_type_map = {
                "chat": "conversation",
                "memory": "memory",
                "tool": "tool",
                "voice": "voice_session",
                "cognitive": "cognitive_state",
            }
            resource_type = resource_type_map.get(domain, "agent")
            resource_id = resource or str(capsule.id)

            return await client.check_permission(
                user_id=user_id,
                permission=permission,
                resource_type=resource_type,
                resource_id=resource_id,
            )
        except Exception as exc:
            logger.exception("SpiceDB check failed (FAIL-CLOSED): %s", exc)
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

        Calls real OPA and SpiceDB engines.
        """
        if not user_id:
            logger.warning("Endpoint permission check requires user_id (FAIL-CLOSED)")
            return False

        try:
            # 1. OPA check
            client = self._get_policy_client()
            opa_allowed = await client.evaluate(
                PolicyRequest(
                    tenant=tenant_id or "default",
                    persona_id=None,
                    action=permission,
                    resource="endpoint",
                    context={"user_id": user_id},
                )
            )
            if not opa_allowed:
                logger.debug("OPA denied endpoint permission=%s user=%s", permission, user_id)
                return False

            # 2. SpiceDB check
            sdb_client = self._get_spicedb_client()
            return await sdb_client.check_permission(
                user_id=user_id,
                permission=permission,
                resource_type="tenant",
                resource_id=tenant_id or "default",
            )
        except Exception as exc:
            logger.warning("Endpoint permission error (FAIL-CLOSED): %s", exc)
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
