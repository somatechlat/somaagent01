"""Tests for the internal ``_enforce_policy`` helper.

The VIBE rules require that security checks are exercised and verified.  These
tests monkey‑patch the global ``policy_client`` used by ``core_tasks`` to simulate
both allowed and denied decisions.
"""

import pytest

from python.tasks import core_tasks


def test_enforce_policy_allows(monkeypatch):
    """When the policy client returns ``True`` the helper should not raise."""
    # Patch the ``evaluate`` method to always return ``True``
    monkeypatch.setattr(
        core_tasks, "policy_client", type("Mock", (), {"evaluate": lambda self, req: True})()
    )
    # Should complete without exception
    core_tasks._enforce_policy(
        task_name="test_task",
        tenant_id="tenant1",
        action="test_action",
        resource={"name": "test_resource"},
    )


def test_enforce_policy_denied(monkeypatch):
    """When the policy client returns ``False`` a ``PermissionError`` is raised."""
    monkeypatch.setattr(
        core_tasks, "policy_client", type("Mock", (), {"evaluate": lambda self, req: False})()
    )
    with pytest.raises(PermissionError):
        core_tasks._enforce_policy(
            task_name="test_task",
            tenant_id="tenant1",
            action="test_action",
            resource={"name": "test_resource"},
        )
