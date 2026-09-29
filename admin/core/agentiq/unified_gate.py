"""
UnifiedGate - Single permission check combining all sources.

Security Auditor: FAIL-CLOSED principle. Any error = DENY.
PhD Analyst: OPA + SpiceDB + Capsule Scope check.
Django Architect: Async-first design with caching.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from admin.core.models import Capsule

from services.common.policy_client import get_policy_client, PolicyClient, PolicyRequest
from services.common.spicedb_client import SpiceDBClient

logger = logging.getLogger(__name__)

#: SpiceDB's permission set is deliberately small. Catalog verbs map onto it
#: explicitly; a verb that is absent denies rather than falling through.
_SPICEDB_VERBS: Dict[str, str] = {
    "view": "view",
    "read": "view",
    "search": "view",
    "send": "view",
    "configure": "configure",
    "update": "configure",
    "create": "configure",
    "upload": "configure",
    "edit": "configure",
    "delete": "manage",
    "manage": "manage",
    "execute": "manage",
}

#: Catalog family -> SpiceDB resource type.
_SPICEDB_TYPES: Dict[str, str] = {
    "system": "tenant",
    "org": "tenant",
    "agent": "agent",
    "resource": "agent",
    "cognitive": "cognitive_state",
    "audit": "tenant",
}


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
        roles: Iterable[str] | None = None,
        scopes: Iterable[str] | None = None,
    ) -> bool:
        """
        Check if action is permitted for this capsule.

        Authorization is layered. Role-based access control is the floor and is
        decided first from ``admin.core.authz``. OPA and SpiceDB run after it
        and may only *narrow* the floor — neither can authorise anything the
        roles did not already grant. A principal with no roles is denied.

        Args:
            capsule: The Capsule with governance config
            action: A catalog permission name (``"resource:chat_send"``) or a
                policy action alias known to ``authz.resolve_action``
            resource: Optional resource identifier
            user_id: User ID for SpiceDB subject (required for real checks)
            tenant_id: Tenant ID for OPA context
            roles: Roles held by the caller. An empty or missing set is
                denial.
            scopes: Set only when the caller is a delegated API key. A key
                holds exactly these and no roles.

        Returns:
            bool: True if permitted, False otherwise

        Note:
            FAIL-CLOSED: Any error returns False
        """
        try:
            # 1. RBAC floor — the authority, decided before any policy engine.
            resolved_roles, resolved_scopes = await self._principal_for(
                user_id, tenant_id, roles, scopes
            )
            if not self._check_role_floor(action, resolved_roles, resolved_scopes):
                logger.debug(
                    "Role floor denied action=%s roles=%s", action, resolved_roles
                )
                return False

            # 2. OPA Policy Check (real HTTP call)
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

            # 3. SpiceDB Check (real gRPC call)
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

            # 4. Capsule Scope Check (async-safe: never touch sync ORM body)
            body: Dict[str, Any] = getattr(capsule, "_cached_body", None) or {}
            if not body and hasattr(capsule, "async_body"):
                try:
                    body = await capsule.async_body() or {}
                except Exception:
                    body = {}
            if not body:
                # An unloaded body yields an empty capability set. That denies
                # every tool action (nothing is known to be enabled) and leaves
                # non-tool actions to the role floor above. It is not a grant.
                body = {}
            persona = body.get("persona", {}) if isinstance(body, dict) else {}
            tools_config = persona.get("tools", {}) if isinstance(persona, dict) else {}
            scope_allowed = self._check_scope(
                (
                    tools_config.get("enabled_capabilities", [])
                    if isinstance(tools_config, dict)
                    else []
                ),
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

    async def _principal_for(
        self,
        user_id: str | None,
        tenant_id: str | None,
        roles: Iterable[str] | None,
        scopes: Iterable[str] | None,
    ) -> tuple[List[str], List[str] | None]:
        """Resolve the caller to (roles, scopes).

        When ``scopes`` is supplied the caller is a delegation and its roles
        are dropped. Otherwise roles are resolved from the membership record.
        """
        if scopes is not None:
            return [], list(scopes)
        return await self._roles_for(user_id, tenant_id), None

    async def _roles_for(self, user_id: str | None, tenant_id: str | None) -> List[str]:
        """Resolve the subject's roles from the membership record.

        FAIL-CLOSED: a subject with no recorded role has no authority. A missing
        role must never become a default grant. Resolution failure is denial,
        not an exception to swallow into an allow.
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
        except Exception:
            logger.exception("Role resolution failed (FAIL-CLOSED): user=%s", user_id)
            return []

    def _check_role_floor(
        self,
        action: str,
        roles: Iterable[str] | None,
        scopes: Iterable[str] | None = None,
    ) -> bool:
        """Decide the role-based floor for ``action``.

        This is the authority. ``resolve_action`` maps a policy action onto the
        catalog permission it stands for, and that permission must be one the
        caller's roles actually grant. Both halves fail closed: an action that
        maps to nothing is denied, and roles that grant nothing are denied.

        SpiceDB and OPA are not consulted here. They run afterwards and can
        only narrow what this method has already allowed.
        """
        from admin.core.authz import (
            PERMISSIONS,
            permissions_for_principal,
            resolve_action,
        )

        try:
            permission = resolve_action(action)
        except KeyError:
            logger.warning("Unknown action %r: no catalog permission stands behind it", action)
            return False

        if permission not in PERMISSIONS:  # pragma: no cover - resolve_action guarantees this
            return False

        # `scopes` is how a delegated key is passed. A key holds exactly its
        # scopes and never its issuer's roles, so the two are not unioned.
        if scopes is not None:
            if not scopes:
                return False
            return permission in permissions_for_principal(scopes=scopes)

        role_list = list(roles or [])
        if not role_list:
            return False

        return permission in permissions_for_principal(roles=role_list)

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
        client = self._get_policy_client()
        if not client.is_configured:
            # Narrowing layer absent. The role floor already decided; there is
            # no policy engine here to narrow it further. This is not a grant
            # invented from nothing — it is the floor standing unchallenged.
            return True

        try:
            request = PolicyRequest(
                tenant=tenant_id or str(capsule.tenant.id),
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
            logger.warning("SpiceDB check requires user_id (FAIL-CLOSED): action=%s", action)
            return False

        client = self._get_spicedb_client()
        if not client.is_configured:
            # Narrowing layer absent — see _check_opa.
            return True

        try:

            # Derive SpiceDB resource type and permission from action.
            # Catalog permissions are "<family>:<verb>", e.g.
            # "resource:chat_send". SpiceDB has a much smaller permission
            # set, so the verb is mapped explicitly rather than passed
            # through. An unmapped action is denied.
            if ":" not in action:
                logger.warning("Action %r is not a catalog name; denying", action)
                return False
            family, verb = action.split(":", 1)
            permission = _SPICEDB_VERBS.get(verb)
            if permission is None:
                logger.warning("No SpiceDB verb for action %r; denying", action)
                return False

            resource_type = _SPICEDB_TYPES.get(family, "agent")
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

        Layered the same way as ``check``: the catalog and the subject's roles
        decide first, and each policy engine narrows only if it is attached.
        FAIL-CLOSED: any error = DENY.
        """
        if not user_id:
            logger.warning("Endpoint permission check requires user_id (FAIL-CLOSED)")
            return False

        # Role floor first. A permission name that is not in the catalog, or
        # roles that do not grant it, is denied before any engine is consulted.
        from admin.core.authz import is_known_permission, permissions_for_roles

        if not is_known_permission(permission):
            logger.warning("Endpoint permission %r is not in the catalog; denying", permission)
            return False
        if permission not in permissions_for_roles(await self._roles_for(user_id, tenant_id)):
            return False

        # Then the narrowing layers, each consulted only when attached.
        try:
            client = self._get_policy_client()
            if client.is_configured:
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
                    logger.debug(
                        "OPA denied endpoint permission=%s user=%s", permission, user_id
                    )
                    return False

            sdb_client = self._get_spicedb_client()
            if not sdb_client.is_configured:
                return True
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
        Narrow tool execution to the capsule's enabled capabilities.

        This layer only speaks to tools. It is a filter that can remove
        authority the role floor already granted; it never adds any, and it is
        not the control that authorises non-tool actions. Those are decided by
        ``_check_role_floor`` alone. That is why the fall-through here is True
        for non-tool actions and not a default grant.

        A tool action is permitted only when the tool is named in
        ``enabled_capabilities``. An empty or missing capability list therefore
        denies every tool — a capsule that declares no tools executes none.
        """
        is_tool_action = action.startswith("tool:") or action in {
            "resource:tool_execute",
            "resource:tool_configure",
        }
        if is_tool_action:
            return bool(resource) and resource in enabled_capabilities

        return True
