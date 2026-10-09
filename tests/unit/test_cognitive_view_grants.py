"""``cognitive:view`` is held by the two roles that operate an agent.

Reading neuromodulator and persona state is a read of the agent's cognitive
surface. It was granted to ``trainer`` alone, so a ``sysadmin`` running the
platform — and the ``agent_owner`` whose persona they are configuring — were
denied the very panel the UI shows them, while the trainer who does not own
the agent was not.

The grant is explicit and named: no wildcard reaches ``cognitive:view``, and
``cognitive:edit`` stays where it was — the trainer tunes, the operator and
owner look. ``test_role_superset.py`` pins ``cognitive:edit`` out of both
administrators; this suite pins ``cognitive:view`` into them.

Run:
    pytest tests/unit/test_cognitive_view_grants.py -v
"""

from __future__ import annotations

from admin.core.authz import permissions_for_role, ROLE_PERMISSIONS


def test_sysadmin_holds_cognitive_view():
    """The operator who runs the platform may read the cognitive state."""
    assert "cognitive:view" in permissions_for_role("sysadmin")


def test_agent_owner_holds_cognitive_view():
    """The owner configures persona and neuromodulators, so they must see them."""
    assert "cognitive:view" in permissions_for_role("agent_owner")


def test_the_grants_are_named_not_wildcarded():
    """No wildcard anywhere: the catalog requires a permission trace."""
    for role, perms in ROLE_PERMISSIONS.items():
        assert "*" not in perms, role
    assert "cognitive:view" in permissions_for_role("sysadmin")


def test_cognitive_edit_stays_out_of_both():
    """A read grant is not a tuning grant. Tuning remains the trainer's."""
    assert "cognitive:edit" not in permissions_for_role("sysadmin")
    assert "cognitive:edit" not in permissions_for_role("agent_owner")
    assert "cognitive:edit" in permissions_for_role("trainer")


def test_ordinary_roles_do_not_gain_the_read():
    """Seeing another agent's cognitive state is not what being logged in means."""
    for role in ("member", "auditor"):
        assert "cognitive:view" not in permissions_for_role(role), role


def test_authorize_answers_the_cognitive_view_action_for_sysadmin():
    """The catalog verb the cognitive routes actually ask for."""
    from admin.core.authz import resolve_action

    assert resolve_action("cognitive:view") == "cognitive:view"
    assert "cognitive:view" in permissions_for_role("sysadmin")
    assert "cognitive:view" in permissions_for_role("agent_owner")
