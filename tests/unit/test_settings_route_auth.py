"""The settings routes must authenticate the caller before ``authorize()`` asks.

``authorize()`` derives authority from ``request.auth``, and Django Ninja only
sets ``request.auth`` when the route carries an auth callback. The handlers in
``admin/core/api/settings_v2.py`` called ``authorize()`` but declared no
``auth=AuthBearer()``, so every HTTP request — a sysadmin's included — reached
the gate with no principal, the role floor saw zero roles, and the fail-closed
denial answered 403. The older gate suites (``test_settings_read_gate.py``)
call the handler directly with a stub request that carries ``.auth`` itself,
which is exactly why they passed while the operator's Settings tab did not.

These tests drive the real router through Ninja's test client, so a settings
route that drops its auth callback fails here. They also pin the read/write
split on the wire: ``GET`` is answered for ``system:view``, ``PUT`` for
``system:configure``, and a principal who holds neither is denied rather than
invited.

Run:
    pytest tests/unit/test_settings_route_auth.py -v
"""

from __future__ import annotations

import pytest

#: Tokens the fake decoder recognises. Anything else is an invalid credential,
#: so "no principal" and "wrong principal" stay two different outcomes.
_TOKEN_ROLES = {
    "ses_sysadmin": ["sysadmin"],
    "ses_member": ["member"],
    # org_admin holds system:view but not system:configure — the pair that
    # proves read authority does not leak into write authority.
    "ses_org_admin": ["org_admin"],
}


class _NoPolicy:
    """PolicyClient stand-in for a Standalone deployment: no engine attached.

    ``is_configured`` is part of the real PolicyClient contract; when it is
    False the policy layer is skipped and the RBAC floor decides — which is
    the layer under test here.
    """

    @property
    def is_configured(self) -> bool:
        return False


@pytest.fixture
def client(monkeypatch):
    """The real settings router, mounted and driven over HTTP."""
    from ninja import NinjaAPI
    from ninja.testing import TestAsyncClient

    import admin.common.auth as auth_mod
    import services.common.authorization as authz
    from admin.common.auth import TokenPayload
    from admin.common.exceptions import UnauthorizedError
    from admin.common.handlers import register_exception_handlers

    async def _decode(token: str) -> TokenPayload:
        roles = _TOKEN_ROLES.get(token)
        if roles is None:
            raise UnauthorizedError("Invalid or expired token")
        return TokenPayload(
            sub="00000000-0000-0000-0000-000000000001",
            exp=0,
            iat=0,
            iss="settings-route-test",
            realm_access={"roles": roles},
            tenant_id="default",
        )

    monkeypatch.setattr(auth_mod, "decode_token", _decode)
    monkeypatch.setattr(authz, "get_policy_client", lambda: _NoPolicy())

    # The store is a collaborator, not the gate: nothing here is granted by
    # the stubs — RBAC still decides before the handler reaches them.
    import admin.core.api.settings_v2 as s2

    monkeypatch.setattr(s2, "get_settings_from_db", lambda entity: None)
    monkeypatch.setattr(s2, "save_settings_to_db", lambda entity, values: True)
    monkeypatch.setattr(s2, "_emit_settings_changed", _noop)

    api = NinjaAPI(title="settings-route-test")
    register_exception_handlers(api)
    from admin.core.api.settings_v2 import router as settings_router

    api.add_router("/settings", settings_router)
    return TestAsyncClient(api)


async def _noop(*_args, **_kwargs) -> None:
    return None


class TestSettingsRoutesAuthenticateTheirCaller:
    """No principal reaches ``authorize()`` — so a route without auth is a 403."""

    @pytest.mark.asyncio
    async def test_sysadmin_lists_entities_via_cookie(self, client):
        """The operator path: httpOnly cookie, exactly as the Settings tab sends it."""
        response = await client.get("/settings/", COOKIES={"access_token": "ses_sysadmin"})
        assert response.status_code == 200
        entities = response.json()
        assert any(e["entity"] == "postgresql" for e in entities)

    @pytest.mark.asyncio
    async def test_sysadmin_reads_an_entity(self, client):
        """A sysadmin holds ``system:view``, so the read must reach the store."""
        response = await client.get(
            "/settings/postgresql",
            headers={"Authorization": "Bearer ses_sysadmin"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["entity"] == "postgresql"
        assert body["values"]

    @pytest.mark.asyncio
    async def test_sysadmin_writes_an_entity(self, client):
        """A sysadmin holds ``system:configure``, so the write must persist."""
        response = await client.put(
            "/settings/postgresql",
            json={"values": {"pool_size": 40}},
            headers={"Authorization": "Bearer ses_sysadmin"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_member_is_denied_not_invited(self, client):
        """Fail-closed: ``member`` holds neither system verb, so 403 — not a read."""
        response = await client.get(
            "/settings/postgresql",
            headers={"Authorization": "Bearer ses_member"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_no_credential_is_unauthenticated(self, client):
        """Without a principal the request is 401 — it never reaches the gate."""
        response = await client.get("/settings/postgresql")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_unknown_token_is_rejected_before_the_gate(self, client):
        response = await client.get(
            "/settings/postgresql",
            headers={"Authorization": "Bearer ses_not_a_session"},
        )
        assert response.status_code == 401


class TestSettingsActionsAreTheCatalogVerbs:
    """On the wire: reads are ``system:view``, writes are ``system:configure``."""

    @pytest.mark.asyncio
    async def test_read_authority_does_not_answer_a_write(self, client):
        """``org_admin`` may read (``system:view``) and may not write: the PUT
        is gated on ``system:configure`` and answers 403, not a silent save."""
        read = await client.get(
            "/settings/postgresql",
            headers={"Authorization": "Bearer ses_org_admin"},
        )
        assert read.status_code == 200, "org_admin holds system:view"

        write = await client.put(
            "/settings/postgresql",
            json={"values": {"pool_size": 40}},
            headers={"Authorization": "Bearer ses_org_admin"},
        )
        assert write.status_code == 403, "org_admin does not hold system:configure"

    @pytest.mark.asyncio
    async def test_entity_schema_is_gated_too(self, client):
        """The field catalog is configuration shape; it is gated like a read."""
        denied = await client.get(
            "/settings/schema/postgresql",
            headers={"Authorization": "Bearer ses_member"},
        )
        assert denied.status_code == 403

        allowed = await client.get(
            "/settings/schema/postgresql",
            headers={"Authorization": "Bearer ses_sysadmin"},
        )
        assert allowed.status_code == 200
        assert allowed.json()["entity"] == "postgresql"


# ---------------------------------------------------------------------------
# Structural pin — the bug class, not one route
# ---------------------------------------------------------------------------


def test_every_settings_route_declares_an_auth_callback():
    """A gated route with no auth callback is a production 403 for everyone.

    ``authorize()`` is necessary and not sufficient: it can only read roles
    that Django Ninja put on the request, and Ninja puts them there only when
    the route declares an auth callback. This walks both settings routers so
    the defect cannot reappear on a route nobody happened to click.
    """
    from admin.aaas.api.settings import router as aaas_router
    from admin.core.api.settings_v2 import router as core_router

    missing: list[str] = []
    for name, router in (
        ("admin/core/api/settings_v2.py", core_router),
        ("admin/aaas/api/settings.py", aaas_router),
    ):
        for path, view in router.path_operations.items():
            for op in view.operations:
                if not getattr(op, "auth_callbacks", None):
                    missing.append(f"{name} {path}")
    assert not missing, f"settings routes with no auth callback: {missing}"


# ---------------------------------------------------------------------------
# The second settings surface: admin/aaas/api/settings.py
# ---------------------------------------------------------------------------


@pytest.fixture
def aaas_client(monkeypatch):
    """The real aaas settings router, mounted and driven over HTTP.

    ``PlatformConfig`` is a collaborator, not the gate: its instance is
    stubbed so the sysadmin's *allow* path can be observed without a
    Postgres. Nothing here is granted by the stub — the auth callback and the
    ``authorize_sync()`` floor still decide every request.
    """
    from ninja import NinjaAPI
    from ninja.testing import TestClient

    import admin.common.auth as auth_mod
    import services.common.authorization as authz
    from admin.aaas.models import profiles
    from admin.common.auth import TokenPayload
    from admin.common.exceptions import UnauthorizedError
    from admin.common.handlers import register_exception_handlers

    async def _decode(token: str) -> TokenPayload:
        roles = _TOKEN_ROLES.get(token)
        if roles is None:
            raise UnauthorizedError("Invalid or expired token")
        return TokenPayload(
            sub="00000000-0000-0000-0000-000000000002",
            exp=0,
            iat=0,
            iss="settings-route-test",
            realm_access={"roles": roles},
            tenant_id="default",
        )

    class _Defaults:
        defaults = {
            "models": [{"id": "m1", "provider": "openai"}],
            "roles": [{"id": "member", "name": "Member"}],
        }

    monkeypatch.setattr(auth_mod, "decode_token", _decode)
    monkeypatch.setattr(authz, "get_policy_client", lambda: _NoPolicy())
    monkeypatch.setattr(
        profiles.PlatformConfig, "get_instance", classmethod(lambda cls: _Defaults())
    )

    api = NinjaAPI(title="aaas-settings-route-test")
    register_exception_handlers(api)
    from admin.aaas.api.settings import router as settings_router

    api.add_router("/settings", settings_router)
    return TestClient(api)


class TestAaaSSettingsRoutes:
    """Platform settings (models, roles, keys) sit on the same defect."""

    def test_sysadmin_may_read_models(self, aaas_client):
        response = aaas_client.get(
            "/settings/models",
            headers={"Authorization": "Bearer ses_sysadmin"},
        )
        assert response.status_code == 200
        assert response.json()[0]["id"] == "m1"

    def test_sysadmin_may_read_roles(self, aaas_client):
        response = aaas_client.get(
            "/settings/roles",
            headers={"Authorization": "Bearer ses_sysadmin"},
        )
        assert response.status_code == 200

    def test_member_is_denied(self, aaas_client):
        response = aaas_client.get(
            "/settings/models",
            headers={"Authorization": "Bearer ses_member"},
        )
        assert response.status_code == 403

    def test_no_credential_is_unauthenticated(self, aaas_client):
        response = aaas_client.get("/settings/models")
        assert response.status_code == 401
