"""Settings reads are gated the same way writes are.

`PUT /settings/{entity}` has always called ``authorize()``. ``GET`` did not —
it returned a service's whole configuration shape to anyone who could reach
the route. That is the hole this suite exists to hold shut.

It also pins the read/write split in the permission catalog: seeing that a
service exists and what shape it has is ``system:view``; changing it is
``system:configure``. If those two ever collapse, one of these fails.

Run:
    pytest tests/unit/test_settings_read_gate.py -v
"""

from __future__ import annotations

import pytest

from admin.common.exceptions import ForbiddenError, ValidationError


class AllowPolicy:
    """PolicyClient stand-in that allows. The gate under test is the RBAC floor."""

    @property
    def is_configured(self) -> bool:
        return True

    async def evaluate(self, request) -> bool:  # noqa: ANN001
        return True


class RecordingPolicy:
    """PolicyClient stand-in that records the question asked."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    @property
    def is_configured(self) -> bool:
        return True

    async def evaluate(self, request) -> bool:  # noqa: ANN001
        self.calls.append((request.tenant, request.action, request.resource))
        return True


class Request:
    """Request stand-in carrying the subject authorize() reads."""

    def __init__(self, roles: list[str] | None = None) -> None:
        self.headers = {"X-Tenant-Id": "tenant-a"}
        self.auth = {"roles": ["sysadmin"] if roles is None else roles}


def _allow_policy(monkeypatch) -> None:
    import services.common.authorization as authz

    monkeypatch.setattr(authz, "get_policy_client", lambda: AllowPolicy())


def _stub_store(monkeypatch, overrides: dict | None = None) -> list[str]:
    """Point the read path at a stand-in store.

    Consistent with ``test_settings_write_gate.py``, which stubs
    ``save_settings_to_db`` the same way: the gate is the thing under test,
    the table is a collaborator. Nothing here is granted by the stub — the
    RBAC and policy layers still decide.
    """
    import admin.core.api.settings_v2 as s2

    seen: list[str] = []

    def _read(entity: str):
        seen.append(entity)
        return overrides

    monkeypatch.setattr(s2, "get_settings_from_db", _read)
    return seen


class TestSettingsReadGate:
    """GET /settings/{entity} and GET /settings/ require system:view."""

    @pytest.mark.asyncio
    async def test_read_requires_the_read_action(self, monkeypatch):
        """The policy question must be the read permission — not the write one."""
        client = RecordingPolicy()
        import services.common.authorization as authz

        monkeypatch.setattr(authz, "get_policy_client", lambda: client)
        _stub_store(monkeypatch)

        from admin.core.api.settings_v2 import get_settings

        await get_settings(Request(), "postgresql")  # type: ignore[arg-type]
        assert client.calls, "the read must reach the policy layer"
        assert client.calls[0][1] == "system:view"
        assert client.calls[0][2] == "settings"

    @pytest.mark.asyncio
    async def test_unprivileged_role_cannot_read(self, monkeypatch):
        """`member` holds no system permission. Seeing service topology is not
        something an ordinary user gets by being logged in."""
        _allow_policy(monkeypatch)
        from admin.core.api.settings_v2 import get_settings

        with pytest.raises(ForbiddenError):
            await get_settings(Request(roles=["member"]), "postgresql")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_no_roles_at_all_is_denied(self, monkeypatch):
        """Fail-closed: an unauthenticated request carries no roles and no
        authority. Not even a read."""
        _allow_policy(monkeypatch)
        from admin.core.api.settings_v2 import get_settings

        with pytest.raises(ForbiddenError):
            await get_settings(Request(roles=[]), "postgresql")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_sysadmin_may_read(self, monkeypatch):
        _allow_policy(monkeypatch)
        seen = _stub_store(monkeypatch)
        from admin.core.api.settings_v2 import get_settings

        result = await get_settings(Request(), "postgresql")  # type: ignore[arg-type]
        assert result.entity == "postgresql"
        assert seen == ["postgresql"], "the gate must not stop the read reaching the store"
        assert result.values, "a read must return the entity's shape"

    @pytest.mark.asyncio
    async def test_list_services_is_gated_too(self, monkeypatch):
        """The inventory of what the platform is wired to is itself
        configuration. It does not get to be public just because it is a list."""
        _allow_policy(monkeypatch)
        from admin.core.api.settings_v2 import list_services

        with pytest.raises(ForbiddenError):
            await list_services(Request(roles=["member"]))  # type: ignore[arg-type]

        entities = await list_services(Request())  # type: ignore[arg-type]
        assert any(e["entity"] == "postgresql" for e in entities)

    @pytest.mark.asyncio
    async def test_gate_runs_before_entity_validation(self, monkeypatch):
        """No probing which entity names are valid without authority."""
        _allow_policy(monkeypatch)
        from admin.core.api.settings_v2 import get_settings

        with pytest.raises(ForbiddenError):
            await get_settings(Request(roles=["member"]), "not-a-real-entity")  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_unknown_entity_rejected_after_auth(self, monkeypatch):
        _allow_policy(monkeypatch)
        from admin.core.api.settings_v2 import get_settings

        with pytest.raises(ValidationError):
            await get_settings(Request(), "not-a-real-entity")  # type: ignore[arg-type]


class TestSettingsTopologyReadOnly:
    """Bootstrap topology is readable through the API but not writable.

    It is readable because operators need to see the shape of what they are
    running. It is not writable because pointing the process at a different
    Postgres from inside a request is not an operation — that is a deploy.
    """

    @pytest.mark.asyncio
    async def test_topology_key_is_refused_on_write(self, monkeypatch):
        _allow_policy(monkeypatch)
        from admin.core.api.settings_v2 import SettingsUpdateRequest, update_settings

        payload = SettingsUpdateRequest(values={"host": "somewhere-else"})
        with pytest.raises(ValidationError):
            await update_settings(  # type: ignore[arg-type]
                Request(), "postgresql", payload
            )

    @pytest.mark.asyncio
    async def test_tuning_key_still_writes(self, monkeypatch):
        _allow_policy(monkeypatch)
        import admin.core.api.settings_v2 as s2

        saved: list[tuple[str, dict]] = []
        monkeypatch.setattr(
            s2, "save_settings_to_db", lambda e, v: saved.append((e, v)) or True
        )
        monkeypatch.setattr(s2, "_emit_settings_changed", _noop_audit)

        from admin.core.api.settings_v2 import SettingsUpdateRequest, update_settings

        payload = SettingsUpdateRequest(values={"pool_size": 40})
        result = await update_settings(Request(), "postgresql", payload)  # type: ignore[arg-type]
        assert result.success is True
        assert saved and saved[0][1] == {"pool_size": 40}

    @pytest.mark.asyncio
    async def test_declared_shape_comes_from_the_registry(self, monkeypatch):
        """Topology values are not re-declared in the API layer. They resolve
        through the settings registry, so there is one place that knows a
        deployment's shape."""
        _allow_policy(monkeypatch)
        _stub_store(monkeypatch)  # nothing written -> the declared shape
        from admin.core.api.settings_v2 import get_settings, seed_defaults

        result = await get_settings(Request(), "postgresql")  # type: ignore[arg-type]
        assert result.values == seed_defaults("postgresql")
        assert result.values["host"], "topology must resolve, not be blank"
        assert result.source in ("registry", "default", "database")


async def _noop_audit(*_args, **_kwargs) -> None:
    return None
