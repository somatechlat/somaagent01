"""A missing tenant must deny, never be silently remapped to \"default\".

T-5: fail-closed at every boundary. ``tenant_id or "default"`` on an
authorization path means a request with no tenant is evaluated as if it
belonged to tenant ``default`` — the authorisation check then answers for the
wrong subject.

Measured on:
- ``admin/core/agentiq/unified_gate.py`` (OPA evaluate + SpiceDB check)
- ``admin/core/somabrain_client.py`` (memory write)
"""

from __future__ import annotations

import inspect

from admin.core.agentiq import unified_gate as ug
from admin.core import somabrain_client as sc


def test_unified_gate_never_defaults_the_tenant():
    src = inspect.getsource(ug)
    assert 'tenant_id or "default"' not in src
    assert 'tenant_id or "default"' not in src
    assert "or \"default\"" not in src.replace("resource_id=tenant_id", "")


def test_somabrain_client_never_defaults_the_tenant():
    src = inspect.getsource(sc)
    assert 'tenant_id or tenant or "default"' not in src


def test_unified_gate_has_no_default_tenant_literal_at_all():
    """No authorization path may name a fallback tenant."""
    src = inspect.getsource(ug)
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if "or \"default\"" in stripped or "or 'default'" in stripped:
            raise AssertionError(f"silent default tenant on an authz path: {stripped!r}")
