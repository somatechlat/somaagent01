"""Admin roles hold ordinary use and keep separation of duties.

``sysadmin`` and ``org_admin`` were briefly rewritten as
``frozenset().union(*ROLE_PERMISSIONS.values())`` — a transitive escalation
amplifier in which a permission added to any role, even ``member``, silently
reached both administrators. That is not "cannot rot"; it is "cannot reason
about". This file pins the correct shape from both directions:

* every ordinary-use permission a ``member`` needs is held by both admins, so
  operating the product does not lock you out of using it;
* ``system:configure`` stays exclusive to ``sysadmin`` and ``org:manage``
  stays exclusive to ``org_admin``;
* the grants are enumerated — the exact frozensets are asserted, not a
  superset — so no permission can arrive by transitive union.

No database and no infrastructure: the catalog is pure Python.
"""

from __future__ import annotations

from admin.core.authz import (
    ROLE_PERMISSIONS,
    permissions_for_role,
)

# ---------------------------------------------------------------------------
# Ordinary use: what an operator must still be able to do
# ---------------------------------------------------------------------------

#: Exactly what ``member`` holds. Ordinary use of the agent, never
#: configuration. If these are not a subset of both admin roles, the people
#: who run the product cannot use it.
_ORDINARY_USE = frozenset(
    {
        "identity:self",
        "agent:read",
        "resource:conversation_create",
        "resource:conversation_read",
        "resource:conversation_send_message",
        "resource:conversation_view_history",
        "resource:memory_read",
        "resource:file_upload",
        "resource:file_read",
        "resource:chat_send",
        "resource:chat_view",
    }
)


def test_member_is_exactly_ordinary_use():
    """The ordinary-use set is the member role — one vocabulary, no second one."""
    assert permissions_for_role("member") == _ORDINARY_USE


def test_sysadmin_holds_every_ordinary_use_permission():
    """A sysadmin who cannot send a chat message is locked out of the product."""
    sysadmin = permissions_for_role("sysadmin")
    missing = _ORDINARY_USE - sysadmin
    assert not missing, f"sysadmin lacks ordinary use: {sorted(missing)}"


def test_org_admin_holds_every_ordinary_use_permission():
    """An org admin administers people and agents; they also use the agent."""
    org_admin = permissions_for_role("org_admin")
    missing = _ORDINARY_USE - org_admin
    assert not missing, f"org_admin lacks ordinary use: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Separation of duties — the two names stay two jobs
# ---------------------------------------------------------------------------


def test_system_configure_is_exclusive_to_sysadmin():
    """The runtime is configured by exactly one role."""
    assert "system:configure" in permissions_for_role("sysadmin")
    for role, perms in ROLE_PERMISSIONS.items():
        if role == "sysadmin":
            continue
        assert "system:configure" not in perms, role


def test_org_manage_is_exclusive_to_org_admin():
    """An organization is administrated by exactly one role."""
    assert "org:manage" in permissions_for_role("org_admin")
    for role, perms in ROLE_PERMISSIONS.items():
        if role == "org_admin":
            continue
        assert "org:manage" not in perms, role


def test_sysadmin_and_org_admin_remain_distinct_roles():
    """Two names, two jobs. Identical grants would be one role wearing a hat."""
    assert permissions_for_role("sysadmin") != permissions_for_role("org_admin")


# ---------------------------------------------------------------------------
# Enumerated grants — the exact frozensets, never a superset
# ---------------------------------------------------------------------------
#
# If these were asserted as supersets, a transitive union would pass. They are
# asserted as equality so any permission that arrives from anywhere other than
# the explicit grant list fails here.

_SYSADMIN = frozenset(
    {
        "identity:self",
        "agent:read",
        "audit:export",
        "audit:read",
        "org:read",
        "resource:chat_send",
        "resource:chat_view",
        "resource:conversation_create",
        "resource:conversation_read",
        "resource:conversation_send_message",
        "resource:conversation_view_history",
        "resource:file_read",
        "resource:file_upload",
        "resource:memory_read",
        "system:backup_read",
        "system:configure",
        "system:impersonate",
        "system:manage_integrations",
        "system:ratelimit",
        "system:read_metrics",
        "system:security_policy",
        "system:view",
    }
)

_ORG_ADMIN = frozenset(
    {
        "identity:self",
        "agent:configure_personality",
        "agent:configure_tools",
        "agent:create",
        "agent:delete",
        "agent:export",
        "agent:manage_users",
        "agent:read",
        "agent:start",
        "agent:stop",
        "agent:update",
        "agent:view_logs",
        "audit:read",
        "org:apikey_create",
        "org:apikey_read",
        "org:apikey_revoke",
        "org:assign_roles",
        "org:manage",
        "org:read",
        "org:update",
        "org:user_activity",
        "org:user_create",
        "org:user_delete",
        "org:user_read",
        "org:user_update",
        "resource:chat_delete",
        "resource:chat_send",
        "resource:chat_view",
        "resource:conversation_create",
        "resource:conversation_delete",
        "resource:conversation_read",
        "resource:conversation_send_message",
        "resource:conversation_view_history",
        "resource:file_delete",
        "resource:file_read",
        "resource:file_upload",
        "resource:memory_delete",
        "resource:memory_read",
        "resource:memory_search",
        "resource:memory_write",
        "resource:tool_configure",
        "resource:tool_execute",
        "resource:tool_read",
        "system:read_metrics",
        "system:view",
    }
)


def test_sysadmin_grants_are_exactly_the_enumerated_set():
    """Equality, not containment: nothing may arrive by transitive union."""
    assert permissions_for_role("sysadmin") == _SYSADMIN


def test_org_admin_grants_are_exactly_the_enumerated_set():
    """Equality, not containment: nothing may arrive by transitive union."""
    assert permissions_for_role("org_admin") == _ORG_ADMIN


def test_no_admin_is_the_union_of_all_roles():
    """The old ``_ADMIN_FLOOR`` was this set. It must not come back.

    The union of every role is larger than either admin: it carries trainer
    cognitive knobs, developer activation verbs and auditor export authority
    into roles that were never granted them.
    """
    union_of_everything = frozenset().union(*ROLE_PERMISSIONS.values())
    assert permissions_for_role("sysadmin") != union_of_everything
    assert permissions_for_role("org_admin") != union_of_everything
    # Concrete members of the union that no admin may hold.
    for leaked in ("cognitive:edit", "agent:activate_dev", "agent:activate_trn"):
        assert leaked in union_of_everything
        assert leaked not in permissions_for_role("sysadmin")
        assert leaked not in permissions_for_role("org_admin")
