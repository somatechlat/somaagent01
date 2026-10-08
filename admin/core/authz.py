"""Authorization catalog — the single source of truth for roles and permissions.

This module is the only place in somaAgent01 that defines what a permission is,
what a role is, and which permissions a role grants. Every authorization
decision in the product must resolve through here.

Before this module existed the same question was answered from four disagreeing
tables (``admin/core/permissions.py``, ``admin/auth/api_helpers.py``,
``admin/core/permission_matrix.py``, ``admin/common/session_security.py``). A
subject could therefore be denied by one call site and allowed by another for
the same action. That is a fail-open seam, and it is why this file is mandatory.

Design rules, none of them optional:

* **No wildcards.** A role that grants ``"*"`` cannot produce a permission
  trace, so it cannot be audited. Every granted authority is named. Callers
  must not special-case ``"*"``; there is nothing to special-case.
* **Fail-closed.** An unknown role, an unknown permission, or a missing role
  yields no authority. Absence of a mapping is denial, never a default grant.
* **Org-scoped.** Roles carry an explicit scope. Authority granted inside one
  organization does not extend to another; callers must pass the org identity
  alongside the role, and checks that cannot supply it must deny.

Conformance: ISO/IEC 27001:2022 A.5.15, A.5.18, A.8.2; ISO/IEC 42001:2023
A.6.2.3, A.7.3.

See ``docs/iso/SOMA-01-DEPLOY-001.md`` §5.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Mapping

__all__ = [
    "PermissionLevel",
    "PERMISSION_FAMILIES",
    "Permission",
    "PERMISSIONS",
    "ROLE_PERMISSIONS",
    "ROLE_PRIORITY",
    "ORG_ASSIGNABLE_ROLES",
    "AGENT_ASSIGNABLE_ROLES",
    "PROVISIONED_ROLES",
    "is_known_permission",
    "level_of",
    "permissions_for_roles",
    "permissions_for_role",
    "permissions_for_principal",
    "ACTION_ALIASES",
    "resolve_action",
    "validate_scopes",
]


class PermissionLevel(str, Enum):
    """The scope a permission operates at.

    Level 0 is ``SYSTEM``. It was previously labelled "God Mode", which is not
    a name an auditable product may use for a privilege tier.
    """

    SYSTEM = "system"
    ORG = "org"
    AGENT = "agent"
    RESOURCE = "resource"


#: The six permission families. Every permission name is ``"<family>:<verb>"``.
PERMISSION_FAMILIES: tuple[str, ...] = (
    "system",
    "org",
    "agent",
    "resource",
    "cognitive",
    "audit",
    "identity",
)


class Permission:
    """A single named authority."""

    __slots__ = ("name", "family", "level", "description")

    def __init__(self, name: str, level: PermissionLevel, description: str) -> None:
        family, _, _ = name.partition(":")
        if family not in PERMISSION_FAMILIES:
            raise ValueError(
                f"permission {name!r} is not in a known family; "
                f"expected one of {PERMISSION_FAMILIES}"
            )
        self.name = name
        self.family = family
        self.level = level
        self.description = description

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Permission({self.name!r}, level={self.level.value})"


def _build_catalog() -> dict[str, Permission]:
    """Build the catalog. Order is documentation; names are the contract."""

    entries: list[tuple[str, PermissionLevel, str]] = [
        # ---- identity: the principal itself, and nothing else ---------------
        # Below every other family. It names "me", never another principal, and
        # grants no ability to touch anyone's data but your own. Every role
        # holds it, because a role that could not read its own profile could not
        # log itself out.
        (
            "identity:self",
            PermissionLevel.RESOURCE,
            "Act on your own principal: profile, session, MFA",
        ),
        # ---- system: the runtime the agent runs on -------------------------
        ("system:view", PermissionLevel.SYSTEM, "Read infrastructure and service state"),
        ("system:configure", PermissionLevel.SYSTEM, "Change system-wide configuration"),
        ("system:ratelimit", PermissionLevel.SYSTEM, "Change rate limits"),
        ("system:read_metrics", PermissionLevel.SYSTEM, "Read platform metrics"),
        (
            "system:manage_integrations",
            PermissionLevel.SYSTEM,
            "Attach and detach external integrations",
        ),
        ("system:backup_read", PermissionLevel.SYSTEM, "Read backup inventory and status"),
        ("system:security_policy", PermissionLevel.SYSTEM, "Change security policy"),
        (
            "system:impersonate",
            PermissionLevel.SYSTEM,
            "Act on behalf of another tenant's administrator",
        ),
        # ---- org: one organization ---------------------------------------
        ("org:read", PermissionLevel.ORG, "Read an organization and its settings"),
        ("org:update", PermissionLevel.ORG, "Change organization settings"),
        ("org:manage", PermissionLevel.ORG, "Administrate an organization"),
        ("org:user_create", PermissionLevel.ORG, "Invite or create a member"),
        ("org:user_read", PermissionLevel.ORG, "Read members of an organization"),
        ("org:user_update", PermissionLevel.ORG, "Change a member record"),
        ("org:user_delete", PermissionLevel.ORG, "Remove a member"),
        ("org:user_activity", PermissionLevel.ORG, "Read a member's activity"),
        ("org:assign_roles", PermissionLevel.ORG, "Assign roles inside an organization"),
        ("org:apikey_create", PermissionLevel.ORG, "Issue an API key"),
        ("org:apikey_read", PermissionLevel.ORG, "Read API key metadata"),
        ("org:apikey_revoke", PermissionLevel.ORG, "Revoke an API key"),
        # ---- agent: one agent ---------------------------------------------
        ("agent:read", PermissionLevel.AGENT, "Read an agent and its state"),
        ("agent:create", PermissionLevel.AGENT, "Create an agent"),
        ("agent:update", PermissionLevel.AGENT, "Change an agent"),
        ("agent:delete", PermissionLevel.AGENT, "Delete an agent"),
        ("agent:start", PermissionLevel.AGENT, "Start an agent"),
        ("agent:stop", PermissionLevel.AGENT, "Stop an agent"),
        ("agent:view_logs", PermissionLevel.AGENT, "Read agent logs"),
        ("agent:export", PermissionLevel.AGENT, "Export an agent's configuration"),
        (
            "agent:configure_personality",
            PermissionLevel.AGENT,
            "Change persona and voice settings",
        ),
        ("agent:configure_tools", PermissionLevel.AGENT, "Change tool and capability bindings"),
        ("agent:manage_users", PermissionLevel.AGENT, "Manage who may act on an agent"),
        ("agent:activate_dev", PermissionLevel.AGENT, "Switch an agent into development mode"),
        ("agent:activate_trn", PermissionLevel.AGENT, "Switch an agent into training mode"),
        # ---- resource: conversations, memory, files, tools, chat -----------
        (
            "resource:conversation_create",
            PermissionLevel.RESOURCE,
            "Start a conversation",
        ),
        ("resource:conversation_read", PermissionLevel.RESOURCE, "Read a conversation"),
        ("resource:conversation_update", PermissionLevel.RESOURCE, "Rename or update a conversation"),
        ("resource:conversation_delete", PermissionLevel.RESOURCE, "Delete a conversation"),
        (
            "resource:conversation_send_message",
            PermissionLevel.RESOURCE,
            "Send a message in a conversation",
        ),
        (
            "resource:conversation_view_history",
            PermissionLevel.RESOURCE,
            "Read conversation history",
        ),
        ("resource:memory_read", PermissionLevel.RESOURCE, "Read memory"),
        ("resource:memory_write", PermissionLevel.RESOURCE, "Write memory"),
        ("resource:memory_search", PermissionLevel.RESOURCE, "Search memory"),
        ("resource:memory_delete", PermissionLevel.RESOURCE, "Delete memory"),
        ("resource:file_upload", PermissionLevel.RESOURCE, "Upload a file"),
        ("resource:file_read", PermissionLevel.RESOURCE, "Read a file"),
        ("resource:file_delete", PermissionLevel.RESOURCE, "Delete a file"),
        ("resource:tool_read", PermissionLevel.RESOURCE, "List tools"),
        ("resource:tool_execute", PermissionLevel.RESOURCE, "Execute a tool"),
        ("resource:tool_configure", PermissionLevel.RESOURCE, "Configure a tool"),
        ("resource:chat_send", PermissionLevel.RESOURCE, "Send a chat message"),
        ("resource:chat_view", PermissionLevel.RESOURCE, "Read chat"),
        ("resource:chat_delete", PermissionLevel.RESOURCE, "Delete chat"),
        # ---- cognitive: neuromodulator and persona tuning ------------------
        ("cognitive:view", PermissionLevel.AGENT, "Read neuromodulator and persona state"),
        ("cognitive:edit", PermissionLevel.AGENT, "Tune neuromodulators and persona knobs"),
        # ---- audit ---------------------------------------------------------
        ("audit:read", PermissionLevel.SYSTEM, "Read the audit trail"),
        ("audit:export", PermissionLevel.SYSTEM, "Export the audit trail"),
    ]

    catalog = {name: Permission(name, level, desc) for name, level, desc in entries}
    if len(catalog) != len(entries):
        raise RuntimeError("duplicate permission name in catalog")
    return catalog


#: Every permission the product recognizes. Anything not here is denied.
PERMISSIONS: Mapping[str, Permission] = _build_catalog()


# =============================================================================
# ROLES
# =============================================================================

#: Highest authority first. Used only for display ordering and for choosing a
#: single representative role; it never grants anything on its own.
ROLE_PRIORITY: tuple[str, ...] = (
    "sysadmin",
    "org_admin",
    "agent_owner",
    "agent_operator",
    "developer",
    "trainer",
    "member",
    "auditor",
)

_ORG_MEMBER_READ = frozenset(
    {
        "org:read",
        "org:user_read",
    }
)

_RESOURCE_USE = frozenset(
    {
        "resource:conversation_create",
        "resource:conversation_read",
        "resource:conversation_update",
        "resource:conversation_delete",
        "resource:conversation_send_message",
        "resource:conversation_view_history",
        "resource:memory_read",
        "resource:file_upload",
        "resource:file_read",
        "resource:chat_send",
        "resource:chat_view",
    }
)

_RESOURCE_OPERATE = _RESOURCE_USE | frozenset(
    {
        "resource:memory_search",
        "resource:tool_read",
        "resource:tool_execute",
    }
)

_RESOURCE_CONFIGURE = _RESOURCE_OPERATE | frozenset(
    {
        "resource:memory_write",
        "resource:memory_delete",
        "resource:file_delete",
        "resource:tool_configure",
        "resource:chat_delete",
    }
)

_AGENT_OPERATE = frozenset(
    {
        "agent:read",
        "agent:start",
        "agent:stop",
        "agent:view_logs",
    }
)

_AGENT_OWN = _AGENT_OPERATE | frozenset(
    {
        "agent:update",
        "agent:export",
        "agent:configure_personality",
        "agent:configure_tools",
    }
)


#: Held by every principal. Identity is not authority: it is the floor that
#: lets a holder read their own profile, end their own session and manage
#: their own MFA. Revoking it from a role is how you build a role that cannot
#: even log itself out — so it is listed here once rather than unioned into
#: each role and silently forgotten.
_EVERY_PRINCIPAL = frozenset({"identity:self"})


#: Role name -> the exact set of permissions it grants. Nothing else grants
#: anything. There is no wildcard entry and there must never be one.
#: Every entry includes ``_EVERY_PRINCIPAL``.
ROLE_PERMISSIONS: Mapping[str, frozenset[str]] = {
    # Operates the runtime: the only role that may change system-wide
    # configuration. Also holds ordinary use — a sysadmin who cannot send a
    # chat message is locked out of the product they run. The ordinary-use
    # grants are the named ``_RESOURCE_USE`` set plus ``agent:read``, exactly
    # what a ``member`` needs; nothing here is a union of other roles.
    "sysadmin": _EVERY_PRINCIPAL
    | _RESOURCE_USE
    | frozenset(
        {
            "agent:read",
            "system:view",
            "system:configure",
            "system:ratelimit",
            "system:read_metrics",
            "system:manage_integrations",
            "system:backup_read",
            "system:security_policy",
            "system:impersonate",
            "org:read",
            "audit:read",
            "audit:export",
        }
    ),
    # Administrates one organization: its people, its agents, its keys.
    # Holds read-only observability of the runtime (``system:view``,
    # ``system:read_metrics``, ``audit:read``) so an org admin can see what is
    # happening, but ``system:configure`` stays exclusive to ``sysadmin``.
    "org_admin": _EVERY_PRINCIPAL
    | _ORG_MEMBER_READ
    | frozenset(
        {
            "org:update",
            "org:manage",
            "org:user_create",
            "org:user_update",
            "org:user_delete",
            "org:user_activity",
            "org:assign_roles",
            "org:apikey_create",
            "org:apikey_read",
            "org:apikey_revoke",
            "agent:create",
            "agent:delete",
            "agent:manage_users",
            "audit:read",
            "system:view",
            "system:read_metrics",
        }
    )
    | _AGENT_OPERATE
    | _AGENT_OWN
    | _RESOURCE_CONFIGURE,
    # Owns one agent: configures it, does not administer the organization.
    "agent_owner": _EVERY_PRINCIPAL | _AGENT_OWN | _RESOURCE_OPERATE,
    # Runs one agent: starts, stops, reads logs. Cannot reconfigure it.
    "agent_operator": _EVERY_PRINCIPAL | _AGENT_OPERATE | _RESOURCE_OPERATE,
    # Engineering surface: capsules, tools, models, diagnostics. No org
    # administration, no security policy, no audit export.
    "developer": _EVERY_PRINCIPAL
    | frozenset(
        {
            "agent:read",
            "agent:update",
            "agent:view_logs",
            "agent:activate_dev",
            "agent:configure_tools",
            "system:view",
            "system:read_metrics",
        }
    )
    | _RESOURCE_CONFIGURE,
    # Cognitive state only: neuromodulators and persona knobs. Not tools, not
    # users, not security, not infrastructure.
    "trainer": _EVERY_PRINCIPAL
    | frozenset(
        {
            "cognitive:view",
            "cognitive:edit",
            "agent:read",
            "agent:view_logs",
            "agent:activate_trn",
        }
    )
    | _RESOURCE_USE
    | frozenset({"resource:memory_search"}),
    # Ordinary use of the agent. Never configuration.
    "member": _EVERY_PRINCIPAL | frozenset({"agent:read"}) | _RESOURCE_USE,
    # Independent reader of the record. Writes nothing.
    "auditor": _EVERY_PRINCIPAL
    | frozenset(
        {
            "audit:read",
            "audit:export",
            "org:read",
            "org:user_read",
            "org:user_activity",
            "org:apikey_read",
            "system:backup_read",
        }
    ),
}

for _role, _perms in ROLE_PERMISSIONS.items():
    if not _perms:
        raise RuntimeError(f"role {_role!r} grants nothing; a role must be explicit")
    _unknown = _perms - set(PERMISSIONS)
    if _unknown:
        raise RuntimeError(f"role {_role!r} grants unknown permissions: {sorted(_unknown)}")

if "*" in set().union(*ROLE_PERMISSIONS.values()):
    raise RuntimeError("wildcard authority is forbidden in the role catalog")

if set(ROLE_PERMISSIONS) != set(ROLE_PRIORITY):
    raise RuntimeError("ROLE_PERMISSIONS and ROLE_PRIORITY must name the same roles")


# =============================================================================
# ASSIGNABLE ROLE SETS
# =============================================================================

#: Roles an organization may assign to one of its members. ``sysadmin`` is
#: provisioned at install and is never assigned from inside an organization —
#: that is what keeps organization authority from reaching the system tier.
ORG_ASSIGNABLE_ROLES: tuple[str, ...] = (
    "org_admin",
    "developer",
    "trainer",
    "member",
    "auditor",
)

#: Roles assignable on one agent. Ownership is transferred, not assigned, so
#: ``agent_owner`` is granted by an ownership transfer rather than a role edit.
AGENT_ASSIGNABLE_ROLES: tuple[str, ...] = (
    "agent_operator",
    "trainer",
    "member",
)

#: Roles established outside the application, at install or by break-glass
#: procedure. Never offered in a role-assignment control.
PROVISIONED_ROLES: tuple[str, ...] = ("sysadmin", "agent_owner")


# =============================================================================
# RESOLUTION
# =============================================================================


def is_known_permission(name: str) -> bool:
    """True if ``name`` is a permission this product recognizes.

    An unrecognized name is not a permission. Callers must treat that as
    denial; nothing in this module grants a default.
    """
    return name in PERMISSIONS


def level_of(name: str) -> PermissionLevel:
    """Return the level of a known permission.

    Raises:
        KeyError: if the permission is unknown. Unknown permissions have no
            level and therefore no authority.
    """
    return PERMISSIONS[name].level


def permissions_for_role(role: str) -> frozenset[str]:
    """Permissions granted by one role.

    An unknown role grants nothing. This is deliberate: a typo in a role name
    must not silently escalate or silently vanish into a default.
    """
    return ROLE_PERMISSIONS.get(role, frozenset())


def permissions_for_principal(
    roles: Iterable[str] | None = None,
    scopes: Iterable[str] | None = None,
) -> frozenset[str]:
    """The authority a principal holds.

    A principal is one of two things, and the two must not be mixed:

    * **A person.** Identified by roles. Authority is what those roles grant.
    * **A delegation** — an API key. Identified by explicit scopes, a subset
      of the issuing principal's authority validated at issuance. Authority is
      exactly those scopes and nothing else.

    Passing ``scopes`` means "this is a key". A key holds no roles and must
    never inherit any: the whole point of a scoped key is that it carries less
    than its issuer. So when ``scopes`` is given, the roles argument is
    ignored rather than unioned in. Unioning would turn a deliberately narrow
    key into "whatever the caller also happens to hold".

    An empty scope set is an empty authority. ``validate_scopes`` refuses to
    issue one; if one is ever stored, it grants nothing.

    Unknown scopes contribute nothing. A scope that is not a catalog
    permission is not authority, and it does not become authority by sitting
    in a list.
    """
    if scopes is not None:
        return frozenset(s for s in scopes if s in PERMISSIONS)
    return permissions_for_roles(roles or [])


def permissions_for_roles(roles: Iterable[str]) -> frozenset[str]:
    """Union of the permissions granted by ``roles``.

    Unknown role names contribute nothing rather than being treated as an
    error, because a token may legitimately carry roles this deployment has
    not defined. They must never contribute authority they were not granted.
    """
    granted: set[str] = set()
    for role in roles:
        granted |= permissions_for_role(role)
    return frozenset(granted)


# =============================================================================
# ACTION SYNONYMS
# =============================================================================
#
# The catalog is the only vocabulary that grants authority. These three names
# are kept because settings policy documents already use them; each one is a
# synonym for a catalog permission and grants exactly what that permission
# grants, nothing more. Everything else that used to live here — "skin:upload",
# "auto", "multimodal.jobs.*" — was a second vocabulary, and a second
# vocabulary is where authority drifts. Those call sites now spend the catalog
# name directly.

#: Names that are not catalog permissions but that policy documents and older
#: callers still use, mapped onto the catalog permission each one actually
#: means. This is a translation table, not a second vocabulary: an action here
#: grants exactly what its target grants, nothing more.
#:
#: Reads and writes are separate authorities on purpose. Seeing that a service
#: exists and what shape it has is ``system:view``; changing it is
#: ``system:configure``. Collapsing them would either let every viewer edit
#: configuration or hide configuration from the people who operate it.
ACTION_ALIASES: Mapping[str, str] = {
    "settings:read": "system:view",
    "settings:write": "system:configure",
    "settings:edit": "system:configure",
}

for _action, _perm in ACTION_ALIASES.items():
    if _perm not in PERMISSIONS:
        raise RuntimeError(f"action {_action!r} aliases unknown permission {_perm!r}")


def resolve_action(action: str) -> str:
    """Map a policy action onto the catalog permission it requires.

    An action that maps to nothing is not authorized by anything. Callers must
    treat the ``KeyError`` as denial.

    Raises:
        KeyError: if the action has no catalog permission behind it.
    """
    if action in PERMISSIONS:
        return action
    return ACTION_ALIASES[action]


def validate_scopes(
    scopes: Iterable[str],
    issuer_permissions: Iterable[str],
) -> frozenset[str]:
    """Validate requested API-key scopes against the catalog and the issuer.

    An API key is a delegation, so it may never hold authority its issuer does
    not hold. Scopes must also be explicit: an empty request is refused rather
    than interpreted as "everything", which is how the previous implementation
    issued all-or-nothing keys.

    Args:
        scopes: Permissions the key is being issued for.
        issuer_permissions: Permissions held by the principal issuing the key.

    Returns:
        The validated scope set.

    Raises:
        ValueError: if no scopes are requested, if any scope is not a known
            permission, or if any scope exceeds the issuer's authority.
    """
    requested = [str(s) for s in scopes]
    if not requested:
        raise ValueError(
            "API key scopes must be explicit and non-empty; "
            "an unscoped key is refused rather than treated as unlimited"
        )

    unknown = sorted({s for s in requested if s not in PERMISSIONS})
    if unknown:
        raise ValueError(f"unknown permissions in scope: {unknown}")

    issuer = set(issuer_permissions)
    exceeded = sorted({s for s in requested if s not in issuer})
    if exceeded:
        raise ValueError(
            f"scopes exceed the issuing principal's authority: {exceeded}"
        )

    return frozenset(requested)
