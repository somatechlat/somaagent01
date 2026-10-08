"""Authorization catalog — fail-closed rules.

These pin the properties that were violated before ``admin.core.authz``
existed: a wildcard role that could not be traced, four disagreeing role
tables, an API key whose scopes defaulted to "everything", and a gate that
allowed every non-tool action by default.

No database and no infrastructure: the catalog is pure Python, so these run
everywhere and cannot be skipped into silence.
"""

from __future__ import annotations

import pytest

from admin.core.authz import (
    AGENT_ASSIGNABLE_ROLES,
    ACTION_ALIASES,
    ORG_ASSIGNABLE_ROLES,
    PERMISSION_FAMILIES,
    PERMISSIONS,
    PROVISIONED_ROLES,
    ROLE_PERMISSIONS,
    ROLE_PRIORITY,
    is_known_permission,
    level_of,
    PermissionLevel,
    permissions_for_principal,
    permissions_for_role,
    permissions_for_roles,
    resolve_action,
    validate_scopes,
)


# ---------------------------------------------------------------------------
# The catalog itself
# ---------------------------------------------------------------------------


def test_every_permission_is_in_a_known_family():
    """A permission name outside the six families is not a permission."""
    for name in PERMISSIONS:
        family = name.split(":", 1)[0]
        assert family in PERMISSION_FAMILIES, name
        assert name.count(":") == 1, name


def test_no_role_grants_a_wildcard():
    """A wildcard cannot produce a permission trace, so it cannot be audited.

    This was literally granted: ``{"id": "admin", "permissions": ["*"]}``.
    """
    granted = set().union(*ROLE_PERMISSIONS.values())
    assert "*" not in granted
    for role, perms in ROLE_PERMISSIONS.items():
        for perm in perms:
            assert "*" not in perm, (role, perm)


def test_every_role_grants_only_catalog_permissions():
    for role, perms in ROLE_PERMISSIONS.items():
        assert perms, f"role {role!r} grants nothing"
        unknown = perms - set(PERMISSIONS)
        assert not unknown, (role, sorted(unknown))


def test_role_names_are_one_vocabulary():
    """ROLE_PERMISSIONS and ROLE_PRIORITY must name the same roles.

    Two tables that disagree is how one call site allowed what another denied.
    """
    assert set(ROLE_PERMISSIONS) == set(ROLE_PRIORITY)


def test_unknown_permission_has_no_level():
    """An unrecognized name is denial, never a default grant."""
    assert not is_known_permission("chat:send")
    assert not is_known_permission("admin")
    assert not is_known_permission("")
    with pytest.raises(KeyError):
        level_of("nonsense")


# ---------------------------------------------------------------------------
# Role resolution
# ---------------------------------------------------------------------------


def test_unknown_role_grants_nothing():
    """A typo in a role name must not escalate and must not vanish into a default."""
    assert permissions_for_role("no_such_role") == frozenset()
    assert permissions_for_roles(["no_such_role"]) == frozenset()
    assert permissions_for_roles([]) == frozenset()
    assert permissions_for_roles([]) == frozenset()


def test_provisioned_roles_are_never_assignable():
    """sysadmin is provisioned at install; agent_owner is transferred.

    Offering either in a role-assignment control lets organization authority
    reach outside the organization.
    """
    assert set(PROVISIONED_ROLES) == {"sysadmin", "agent_owner"}
    assert "sysadmin" not in ORG_ASSIGNABLE_ROLES
    assert "agent_owner" not in ORG_ASSIGNABLE_ROLES
    assert "sysadmin" not in AGENT_ASSIGNABLE_ROLES


def test_roles_are_scoped_to_their_tier():
    """sysadmin is the only system tier; org_admin cannot reach it."""
    sysadmin = permissions_for_role("sysadmin")
    org_admin = permissions_for_role("org_admin")

    assert "system:configure" in sysadmin
    assert "system:configure" not in org_admin
    # org_admin administrates one organization, not the runtime
    assert "org:manage" in org_admin
    assert "org:manage" not in sysadmin


def test_developer_and_trainer_are_distinct():
    """They are two jobs, not one. The trainer tunes cognitive state; the
    developer works the engineering surface.
    """
    developer = permissions_for_role("developer")
    trainer = permissions_for_role("trainer")

    assert "cognitive:edit" in trainer
    assert "cognitive:edit" not in developer

    assert "agent:configure_tools" in developer
    assert "agent:configure_tools" not in trainer

    assert "agent:activate_dev" in developer
    assert "agent:activate_dev" not in trainer
    assert "agent:activate_trn" in trainer
    assert "agent:activate_trn" not in developer


def test_auditor_writes_nothing():
    """The auditor is an independent reader of the record."""
    auditor = permissions_for_role("auditor")
    write_verbs = ("create", "update", "delete", "write", "upload", "execute", "configure")
    for perm in auditor:
        verb = perm.split(":", 1)[1]
        assert not verb.startswith(write_verbs), perm


# ---------------------------------------------------------------------------
# Action aliases
# ---------------------------------------------------------------------------


def test_action_aliases_only_point_at_catalog_permissions():
    for action, perm in ACTION_ALIASES.items():
        assert is_known_permission(perm), (action, perm)


def test_unknown_action_is_denied():
    """An action that maps to nothing is authorized by nothing."""
    for bad in ["nonsense", "chat:send", "admin", "", "view", "skin:nonexistent"]:
        with pytest.raises(KeyError):
            resolve_action(bad)


def test_catalog_names_resolve_to_themselves():
    assert resolve_action("resource:chat_send") == "resource:chat_send"
    assert resolve_action("system:configure") == "system:configure"


def test_retired_action_vocabulary_no_longer_resolves():
    """These were real call-site strings. Each one now has to be written as
    the catalog permission that stands for it, or be denied.
    """
    for retired in [
        "chat:send",
        "memory:write",
        "tool:execute",
        # Retired when the last call sites moved onto catalog names. These
        # were never permissions — they were a second vocabulary, and a second
        # vocabulary is where authority drifts.
        "auto",
        "skin:upload",
        "skin:update",
        "skin:delete",
        "skin:approve",
        "skin:reject",
        "multimodal.jobs.create",
        "multimodal.jobs.read",
        "multimodal.assets.read",
    ]:
        assert retired not in ACTION_ALIASES
        with pytest.raises(KeyError):
            resolve_action(retired)


# ---------------------------------------------------------------------------
# API key scopes — a key is a delegation
# ---------------------------------------------------------------------------


def test_scopes_must_be_explicit_and_non_empty():
    """An unscoped key used to mean "everything". It is now refused."""
    with pytest.raises(ValueError, match="non-empty"):
        validate_scopes([], permissions_for_roles(["sysadmin"]))


def test_scopes_must_name_known_permissions():
    with pytest.raises(ValueError, match="unknown permissions"):
        validate_scopes(["resource:chat_send", "not-a-permission"], permissions_for_roles(["sysadmin"]))


def test_scopes_may_not_exceed_the_issuer():
    """A delegation cannot hold authority its issuer does not hold."""
    member = permissions_for_roles(["member"])
    with pytest.raises(ValueError, match="exceed"):
        validate_scopes(["audit:export"], member)
    with pytest.raises(ValueError, match="exceed"):
        validate_scopes(["system:configure", "resource:chat_send"], member)


def test_valid_scopes_are_returned_unchanged():
    member = permissions_for_roles(["member"])
    assert validate_scopes(["resource:chat_send"], member) == frozenset({"resource:chat_send"})
    assert validate_scopes(["resource:chat_send", "resource:memory_read"], member) == {
        "resource:chat_send",
        "resource:memory_read",
    }


# ---------------------------------------------------------------------------
# UnifiedGate layering
# ---------------------------------------------------------------------------


def test_gate_floor_denies_without_roles():
    from admin.core.agentiq.unified_gate import UnifiedGate

    gate = UnifiedGate()
    assert gate._check_role_floor("resource:chat_send", []) is False
    assert gate._check_role_floor("resource:chat_send", None) is False
    assert gate._check_role_floor("resource:chat_send", ["no_such_role"]) is False


def test_gate_floor_enforces_the_catalog():
    from admin.core.agentiq.unified_gate import UnifiedGate

    gate = UnifiedGate()
    assert gate._check_role_floor("resource:chat_send", ["member"]) is True
    assert gate._check_role_floor("audit:export", ["member"]) is False
    assert gate._check_role_floor("audit:export", ["auditor"]) is True
    assert gate._check_role_floor("system:configure", ["org_admin"]) is False
    assert gate._check_role_floor("system:configure", ["sysadmin"]) is True


def test_roles_that_run_agents_hold_resource_tool_execute():
    """Every role that operates agents passes the floor for tool calls.

    §11.1 makes the RBAC floor layer 1 of every tool action and §11.2 maps
    those actions onto ``resource:tool_execute``. A runner role without the
    grant would be able to start and configure its agents and then have
    every tool call denied by ``UnifiedGate`` — and the grant must be the
    named permission, never a wildcard (pinned by
    ``test_no_role_grants_a_wildcard``).
    """
    from admin.core.agentiq.unified_gate import UnifiedGate

    gate = UnifiedGate()
    runners = ("sysadmin", "org_admin", "agent_owner", "agent_operator", "developer")
    for role in runners:
        assert "resource:tool_execute" in permissions_for_role(role), role
        assert gate._check_role_floor("resource:tool_execute", [role]) is True, role

    # Roles that never run agents keep no tool authority: the floor stays a
    # floor, not a ladder. ``member`` denial is separately pinned through the
    # choke by ``test_tool_policy_choke``.
    for role in ("member", "trainer", "auditor"):
        assert "resource:tool_execute" not in permissions_for_role(role), role
        assert gate._check_role_floor("resource:tool_execute", [role]) is False, role


def test_gate_rejects_actions_outside_the_catalog():
    from admin.core.agentiq.unified_gate import UnifiedGate

    gate = UnifiedGate()
    assert gate._check_role_floor("admin", ["sysadmin"]) is False
    assert gate._check_role_floor("chat:send", ["sysadmin"]) is False


@pytest.mark.asyncio
async def test_gate_principal_prefers_caller_roles_over_a_second_store():
    """Caller-supplied roles are the principal; membership is only a fallback.

    The chat path surfaces roles from the authenticated identity
    (``TokenPayload.realm_access`` / ``LocalIdentity.roles``). Re-querying
    ``TenantUser`` is a second store that returned an empty set while
    ``/auth/me`` showed the right ones, so the role floor denied a member.
    An omitted role set (``None``) still resolves from membership; an empty
    list is still "no roles" and still denies.
    """
    from admin.core.agentiq.unified_gate import UnifiedGate

    gate = UnifiedGate()
    roles, scopes = await gate._principal_for(
        "user-with-no-tenantuser-row", "tenant", ["member"], None
    )
    assert roles == ["member"]
    assert scopes is None

    empty, _ = await gate._principal_for("user", "tenant", [], None)
    assert empty == []


@pytest.mark.asyncio
async def test_gate_check_allows_member_from_caller_roles_without_membership_row():
    """A real ``UnifiedGate`` lets a member chat when the caller carries roles.

    No OPA and no SpiceDB are attached in Standalone, so the role floor is the
    only layer. It must see the authenticated roles rather than an empty
    membership lookup.
    """
    from admin.core.agentiq.unified_gate import UnifiedGate

    class _Capsule:
        id = "capsule-1"
        tenant_id = "tenant-1"
        _cached_body = {}

    gate = UnifiedGate()
    assert (
        await gate.check(
            _Capsule(),
            action="resource:chat_send",
            user_id="identity-uuid-with-no-tenantuser-row",
            tenant_id="tenant-1",
            roles=["member"],
        )
        is True
    )
    assert (
        await gate.check(
            _Capsule(),
            action="resource:chat_send",
            user_id="identity-uuid-with-no-tenantuser-row",
            tenant_id="tenant-1",
            roles=[],
        )
        is False
    )


def test_capsule_scope_denies_tools_that_are_not_enabled():
    """A capsule that declares no tools executes none.

    The previous fall-through allowed every action that was not a tool action
    with no authority behind it at all.
    """
    from admin.core.agentiq.unified_gate import UnifiedGate

    gate = UnifiedGate()
    assert gate._check_scope([], "tool:execute", "bash") is False
    assert gate._check_scope(["bash"], "tool:execute", "bash") is True
    assert gate._check_scope(["bash"], "tool:execute", "rm") is False
    assert gate._check_scope([], "resource:tool_execute", "bash") is False


def test_levels_are_the_four_declared_tiers():
    """Level 0 is SYSTEM. It is not called "God Mode" in an auditable product."""
    assert [level.value for level in PermissionLevel] == ["system", "org", "agent", "resource"]
    assert level_of("system:configure") is PermissionLevel.SYSTEM
    assert level_of("org:manage") is PermissionLevel.ORG
    assert level_of("agent:update") is PermissionLevel.AGENT
    assert level_of("resource:chat_send") is PermissionLevel.RESOURCE


# ---------------------------------------------------------------------------
# Principals: a person is roles, a delegation is scopes
# ---------------------------------------------------------------------------


def test_a_key_holds_its_scopes_and_never_its_issuers_roles():
    """A scoped key is a narrowing of its issuer.

    Unioning roles back in would turn a deliberately narrow key into "whatever
    the caller also happens to hold", which is the escalation the scope list
    exists to prevent.
    """
    # scopes present -> roles ignored entirely
    assert permissions_for_principal(roles=["sysadmin"], scopes=["resource:chat_send"]) == {
        "resource:chat_send"
    }
    assert permissions_for_principal(roles=["sysadmin"], scopes=[]) == frozenset()


def test_unknown_scopes_contribute_no_authority():
    """A scope that is not a catalog permission is not authority."""
    assert permissions_for_principal(scopes=["not-a-permission"]) == frozenset()
    assert permissions_for_principal(scopes=["resource:chat_send", "nope"]) == {
        "resource:chat_send"
    }


def test_a_person_is_authorized_by_roles_alone():
    assert permissions_for_principal(roles=["member"]) == permissions_for_roles(["member"])
    assert permissions_for_principal(roles=[], scopes=None) == frozenset()
    assert permissions_for_principal() == frozenset()


def test_api_key_prefix_is_recognizable():
    """Issued keys must be distinguishable from JWTs so the auth path can
    route them to the right verifier instead of parsing them as JWTs.
    """
    from admin.common.auth import API_KEY_PREFIX

    assert API_KEY_PREFIX == "sk_"
