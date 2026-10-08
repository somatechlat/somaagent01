"""New capsules carry the default kit through the W2.5 scope choke (§11.2).

``Capsule.save`` seeds real ``Capability`` rows and links them on first
insert, so ``body.enabled_capabilities`` names the default kit and
``UnifiedGate._check_scope`` lets each kit tool through the
``resource:tool_execute`` floor. Before that seed a capsule was born with an
empty capability set — ``enabled_capabilities`` empty, every tool action
denied by the choke no matter what its ``tool_policy`` listed.

Real rows only: a JSON-only "capability" would satisfy a fake body and still
deny at the gate, so these tests run against Postgres (``db``).
"""

from __future__ import annotations

import uuid

import pytest

from admin.core.agentiq.unified_gate import UnifiedGate
from admin.core.models import Capability, Capsule
from services.tool_executor.default_tools import DEFAULT_AGENT_TOOLS


@pytest.fixture
def capsule(db):
    """A brand-new capsule through the real creation path (``save``)."""
    from admin.aaas.models import Tenant

    tenant = Tenant.objects.create(
        name=f"Kit Seed Tenant {uuid.uuid4().hex[:8]}",
        slug=f"kit-seed-{uuid.uuid4().hex[:8]}",
    )
    return Capsule.objects.create(
        name="Kit Seed Capsule",
        tenant=tenant,
        status=Capsule.STATUS_ACTIVE,
    )


def test_new_capsule_seeds_real_capability_rows(capsule):
    """Every default-kit tool exists as an enabled row in ``capabilities``."""
    rows = set(
        Capability.objects.filter(name__in=DEFAULT_AGENT_TOOLS, is_enabled=True).values_list(
            "name", flat=True
        )
    )
    missing = set(DEFAULT_AGENT_TOOLS) - rows
    assert not missing, f"default kit rows not seeded: {sorted(missing)}"


def test_new_capsule_body_enables_the_default_kit(capsule):
    """``enabled_capabilities`` — the list ``_check_scope`` reads — names the kit."""
    tools = capsule.body["persona"]["tools"]
    enabled = tools["enabled_capabilities"]
    missing = set(DEFAULT_AGENT_TOOLS) - set(enabled)
    assert not missing, f"kit tools missing from enabled_capabilities: {sorted(missing)}"
    registry = tools["tool_registry"]
    assert set(DEFAULT_AGENT_TOOLS) <= set(registry)


def test_scope_choke_passes_the_kit_and_still_denies_unlisted(capsule):
    """Each kit tool clears ``_check_scope``; an unlisted tool does not."""
    gate = UnifiedGate()
    enabled = capsule.body["persona"]["tools"]["enabled_capabilities"]
    for name in DEFAULT_AGENT_TOOLS:
        assert gate._check_scope(enabled, "resource:tool_execute", name) is True, name
    assert gate._check_scope(enabled, "resource:tool_execute", "shell_exec") is False
    assert gate._check_scope([], "resource:tool_execute", "timestamp") is False


def test_role_floor_and_scope_together_allow_a_runner_to_run_the_kit(capsule):
    """Layer 1 and layer 4 for one tool call: runner roles + real scope.

    The floor is checked with the catalog, the scope with the real body —
    the two layers §11.1 chains for every tool action.
    """
    gate = UnifiedGate()
    enabled = capsule.body["persona"]["tools"]["enabled_capabilities"]
    assert gate._check_role_floor("resource:tool_execute", ["sysadmin"]) is True
    assert gate._check_scope(enabled, "resource:tool_execute", "timestamp") is True
    # A member passes neither layer.
    assert gate._check_role_floor("resource:tool_execute", ["member"]) is False


def test_seeding_is_a_union_and_never_rewrites_an_existing_row(capsule):
    """``get_or_create`` fills what is missing; an admin-edited row survives."""
    edited = Capability.objects.get(name="timestamp")
    edited.description = "operator-edited description"
    edited.save()

    from admin.aaas.models import Tenant

    second = Capsule.objects.create(
        name="Kit Seed Capsule",
        tenant=Tenant.objects.create(
            name=f"Kit Seed Tenant 2 {uuid.uuid4().hex[:8]}",
            slug=f"kit-seed-2-{uuid.uuid4().hex[:8]}",
        ),
    )

    assert Capability.objects.filter(name="timestamp").count() == 1
    edited.refresh_from_db()
    assert edited.description == "operator-edited description"
    linked = set(second.capabilities.values_list("name", flat=True))
    assert set(DEFAULT_AGENT_TOOLS) <= linked
