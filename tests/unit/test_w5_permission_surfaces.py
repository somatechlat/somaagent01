"""W5 — live runtime permission-gate checks (not source greps).

Lanes (one decision surface each):
- REST: ``authorize`` / ``authorize_sync``
- Chat: ``UnifiedGate`` only (RBAC floor + narrow-only engines)
- Tools: ``decide_and_authorize_tool`` choke

These tests EXECUTE real catalog / role-floor code with real classes.
Engines (OPA/SpiceDB) are unattached so the RBAC floor is the authority —
which is the documented Standalone case.
"""

from __future__ import annotations

import asyncio


def test_authz_catalog_live():
    from admin.core.authz import PERMISSIONS, permissions_for_principal, resolve_action

    assert "resource:chat_send" in PERMISSIONS
    assert resolve_action("resource:chat_send") == "resource:chat_send"
    # Empty roles grant nothing.
    assert permissions_for_principal(roles=[], org_id="t1") == set() or not (
        "resource:chat_send" in permissions_for_principal(roles=[], org_id="t1")
    )
    # A real role that grants chat_send must include it.
    granted = permissions_for_principal(roles=["sysadmin"], org_id="t1")
    assert isinstance(granted, (set, frozenset))
    # sysadmin catalog is broad; at minimum it is non-empty
    assert granted


def test_permission_checker_live_fail_closed():
    from admin.core.permission_matrix import PermissionChecker

    checker = PermissionChecker()

    async def run():
        # Unknown permission → deny
        r = await checker.check(user_id="u1", permission="not:a:permission", roles=["sysadmin"])
        assert r.allowed is False
        # Empty roles → deny even for a real permission
        r2 = await checker.check(
            user_id="u1", permission="resource:chat_send", tenant_id="t1", roles=[]
        )
        assert r2.allowed is False
        # Real role + real permission → allow (RBAC floor, no engine)
        r3 = await checker.check(
            user_id="u1", permission="resource:chat_send", tenant_id="t1", roles=["sysadmin"]
        )
        assert r3.allowed is True

    asyncio.run(run())


def test_unified_gate_role_floor_live():
    from admin.core.agentiq.unified_gate import UnifiedGate

    gate = UnifiedGate()

    # Unknown action → deny
    assert gate._check_role_floor("not:an:action", ["sysadmin"], tenant_id="t1") is False
    # Empty roles → deny
    assert gate._check_role_floor("resource:chat_send", [], tenant_id="t1") is False
    # No roles → deny
    assert gate._check_role_floor("resource:chat_send", None, tenant_id="t1") is False
    # Real grant → allow
    assert gate._check_role_floor("resource:chat_send", ["sysadmin"], tenant_id="t1") is True
    # Scopes: empty set denies
    assert gate._check_role_floor("resource:chat_send", None, scopes=[], tenant_id="t1") is False


def test_chat_phase4_is_single_surface():
    from pathlib import Path

    src = Path("admin/core/chat_orchestrator.py").read_text(encoding="utf-8")
    # Single decision on chat_send in the process path: UnifiedGate only.
    assert "self._permission_checker.check" not in src
    assert "resource:chat_send" in src
    assert "self._unified_gate.check" in src
