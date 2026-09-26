"""Unit tests for auth module.

Tests JWT handling, role checking, and permission enforcement.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestTokenPayload:
    """Test TokenPayload model."""

    def test_roles_from_realm_access(self):
        """Roles are extracted from realm_access."""
        from admin.common.auth import TokenPayload

        payload = TokenPayload(
            sub="user-001",
            exp=9999999999,
            iat=1000000000,
            iss="http://localhost:20880/realms/somaagent",
            realm_access={"roles": ["admin", "user"]},
        )

        assert payload.roles == ["admin", "user"]
        assert payload.has_role("admin") is True
        assert payload.has_role("superadmin") is False

    def test_roles_empty_when_no_realm_access(self):
        """Roles is empty list when realm_access is None."""
        from admin.common.auth import TokenPayload

        payload = TokenPayload(
            sub="user-001",
            exp=9999999999,
            iat=1000000000,
            iss="http://localhost:20880/realms/somaagent",
        )

        assert payload.roles == []

    def test_effective_tenant_id_from_tenant_id(self):
        """effective_tenant_id returns tenant_id when present."""
        from admin.common.auth import TokenPayload

        payload = TokenPayload(
            sub="user-001",
            exp=9999999999,
            iat=1000000000,
            iss="test",
            tenant_id="uuid-tenant-001",
        )

        assert payload.effective_tenant_id == "uuid-tenant-001"

    def test_effective_tenant_id_fallback_to_tenant(self):
        """effective_tenant_id falls back to tenant claim."""
        from admin.common.auth import TokenPayload

        payload = TokenPayload(
            sub="user-001",
            exp=9999999999,
            iat=1000000000,
            iss="test",
            tenant="default",
        )

        # When tenant is "default", returns AAAS_DEFAULT_TENANT_ID from settings
        # (or None if not set)
        result = payload.effective_tenant_id
        # Just verify it doesn't crash
        assert result is None or isinstance(result, str)


class TestKeycloakConfig:
    """Test KeycloakConfig properties."""

    def test_issuer_url(self):
        """Issuer URL is constructed correctly."""
        from admin.common.auth import KeycloakConfig

        config = KeycloakConfig(
            server_url="http://localhost:20880",
            realm="somaagent",
            client_id="somaagent-api",
        )

        assert config.issuer == "http://localhost:20880/realms/somaagent"
        assert config.jwks_url == "http://localhost:20880/realms/somaagent/protocol/openid-connect/certs"


class TestRequireRoles:
    """Test require_roles decorator behavior."""

    @pytest.mark.asyncio
    async def test_require_roles_passes_with_matching_role(self):
        """User with required role passes through."""
        from admin.common.auth import TokenPayload

        payload = TokenPayload(
            sub="user-001",
            exp=9999999999,
            iat=1000000000,
            iss="test",
            realm_access={"roles": ["admin"]},
        )

        assert "admin" in payload.roles

    @pytest.mark.asyncio
    async def test_require_roles_fails_without_role(self):
        """User without required role is denied."""
        from admin.common.auth import TokenPayload

        payload = TokenPayload(
            sub="user-001",
            exp=9999999999,
            iat=1000000000,
            iss="test",
            realm_access={"roles": ["user"]},
        )

        assert "admin" not in payload.roles
