"""Phase C — OPA gate on the settings write path (SOMA-SETTINGS-MODEL-001.md).

The settings PUT endpoint is a privileged write: it must be authorized through
OPA before anything is persisted. The gate is fail-closed — an OPA error or an
unreachable policy endpoint denies the write; it never lets it through.

Run:
    pytest tests/unit/test_settings_write_gate.py -v
"""

from __future__ import annotations

import pytest

from admin.common.exceptions import ForbiddenError, ValidationError


class RecordingPolicyClient:
    """Recording stand-in for PolicyClient: logs each call, returns a scripted verdict.

    `is_configured` is part of the real PolicyClient contract, and it is
    load-bearing here: `authorize()` skips the policy layer entirely when a
    client is not configured, which would leave these tests asserting on a
    call that never happened.
    """

    def __init__(self, allowed: bool | None, error: Exception | None = None) -> None:
        self.allowed = allowed
        self.error = error
        self.calls: list[tuple[str, str, str]] = []

    @property
    def is_configured(self) -> bool:
        return True

    async def evaluate(self, request) -> bool:  # noqa: ANN001 - PolicyRequest
        self.calls.append((request.tenant, request.action, request.resource))
        if self.error is not None:
            raise self.error
        return bool(self.allowed)


class MinimalRequest:
    """Minimal request stand-in carrying what authorize() reads.

    `auth` is the subject, not a bypass: `authorize()` is two-layered and
    the RBAC floor runs first. A request with no roles is denied before OPA
    is ever consulted, which is correct — and which would leave these tests
    exercising the wrong layer. `sysadmin` is the role that holds
    `system:configure`, so it is the subject a settings write actually is.
    """

    def __init__(self, tenant: str = "tenant-a", roles: list[str] | None = None) -> None:
        self.headers = {"X-Tenant-Id": tenant}
        self.auth = {"roles": ["sysadmin"] if roles is None else roles}


def _install_policy(monkeypatch, client: RecordingPolicyClient) -> None:
    import services.common.authorization as authz

    monkeypatch.setattr(authz, "get_policy_client", lambda: client)


class RecordingPublisher:
    """Recording stand-in for DurablePublisher: logs publishes."""

    def __init__(self) -> None:
        self.published: list[tuple[str, dict, dict]] = []

    async def publish(self, topic: str, payload: dict, **kwargs) -> bool:  # noqa: ANN001
        self.published.append((topic, payload, kwargs))
        return True


def _install_saver(monkeypatch) -> list[tuple[str, dict]]:
    saved: list[tuple[str, dict]] = []
    import admin.core.api.settings_v2 as s2
    import services.common.publisher as pub_mod

    async def _get_publisher():
        return RecordingPublisher()

    monkeypatch.setattr(s2, "save_settings_to_db", lambda e, v: saved.append((e, v)) or True)
    monkeypatch.setattr(pub_mod, "get_durable_publisher", _get_publisher)
    return saved


async def _update(entity: str = "somabrain", values: dict | None = None):
    from admin.core.api.settings_v2 import SettingsUpdateRequest, update_settings

    payload = SettingsUpdateRequest(values=values if values is not None else {"voice_model": "m"})
    return await update_settings(MinimalRequest(), entity, payload)  # type: ignore[arg-type]


class TestSettingsWriteGate:
    """PUT /settings/{entity} is OPA-gated and fail-closed."""

    @pytest.mark.asyncio
    async def test_denied_write_raises_forbidden_and_saves_nothing(self, monkeypatch):
        _install_policy(monkeypatch, RecordingPolicyClient(allowed=False))
        saved = _install_saver(monkeypatch)

        with pytest.raises(ForbiddenError):
            await _update()
        assert saved == [], "a denied write must not reach persistence"

    @pytest.mark.asyncio
    async def test_opa_error_fails_closed(self, monkeypatch):
        """OPA unreachable/errored must deny, never allow (no bypass)."""
        _install_policy(
            monkeypatch, RecordingPolicyClient(allowed=None, error=ConnectionError("opa down"))
        )
        saved = _install_saver(monkeypatch)

        with pytest.raises(ForbiddenError):
            await _update()
        assert saved == [], "an OPA outage must not become an open write path"

    @pytest.mark.asyncio
    async def test_allowed_write_persists(self, monkeypatch):
        _install_policy(monkeypatch, RecordingPolicyClient(allowed=True))
        saved = _install_saver(monkeypatch)

        result = await _update(entity="somabrain", values={"voice_model": "m2"})
        assert result.success is True
        assert saved and saved[0][0] == "somabrain"
        assert saved[0][1]["voice_model"] == "m2"

    @pytest.mark.asyncio
    async def test_gate_asks_settings_write_on_settings(self, monkeypatch):
        """The policy question asked must be system:configure on resource settings."""
        client = RecordingPolicyClient(allowed=True)
        _install_policy(monkeypatch, client)
        _install_saver(monkeypatch)

        await _update()
        assert client.calls and client.calls[0][1] == "system:configure"
        assert client.calls[0][2] == "settings"

    @pytest.mark.asyncio
    async def test_tenant_header_reaches_policy(self, monkeypatch):
        client = RecordingPolicyClient(allowed=True)
        _install_policy(monkeypatch, client)
        _install_saver(monkeypatch)

        from admin.core.api.settings_v2 import SettingsUpdateRequest, update_settings

        payload = SettingsUpdateRequest(values={"voice_model": "m"})
        await update_settings(MinimalRequest(tenant="tenant-z"), "somabrain", payload)  # type: ignore[arg-type]
        assert client.calls and client.calls[0][0] == "tenant-z"

    @pytest.mark.asyncio
    async def test_unknown_entity_requires_auth_first(self, monkeypatch):
        """Gate runs before entity validation — no unauthenticated probing."""
        _install_policy(monkeypatch, RecordingPolicyClient(allowed=False))
        with pytest.raises(ForbiddenError):
            await _update(entity="not-a-real-entity")

    @pytest.mark.asyncio
    async def test_unknown_entity_rejected_after_auth(self, monkeypatch):
        _install_policy(monkeypatch, RecordingPolicyClient(allowed=True))
        saved = _install_saver(monkeypatch)

        with pytest.raises(ValidationError):
            await _update(entity="not-a-real-entity")
        assert saved == []
