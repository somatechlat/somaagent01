"""Infrastructure tests for M1 - Django Ninja migration.

These tests verify the foundational infrastructure is working correctly.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class TestDjangoCheck:
    """Test Django configuration is valid."""

    def test_django_settings_configured(self):
        """Verify Django settings are properly configured."""
        from django.conf import settings

        assert settings.configured
        assert "ninja" in settings.INSTALLED_APPS
        assert "admin.core" in settings.INSTALLED_APPS
        assert "admin.saas" in settings.INSTALLED_APPS

    def test_all_apps_registered(self):
        """Verify all migration apps are registered."""
        from django.conf import settings

        required_apps = [
            "admin.core",
            "admin.agents",
            "admin.chat",
            "admin.files",
            "admin.features",
            "admin.utils",
            "admin.saas",
        ]

        for app in required_apps:
            assert app in settings.INSTALLED_APPS, f"Missing app: {app}"


class TestApiConfiguration:
    """Test NinjaAPI configuration."""

    def test_api_instance_created(self):
        """Verify API instance is created."""
        from admin.api import api

        assert api is not None
        assert api.title == "SomaAgent Platform API"
        assert api.version == "2.0.0"

    def test_api_has_docs_url(self):
        """Verify API documentation URL is configured."""
        from admin.api import api

        assert api.docs_url == "/docs"


class TestExceptionHandling:
    """Test exception handling utilities."""

    def test_api_error_to_dict(self):
        """Test ApiError serialization."""
        from admin.common.exceptions import ApiError

        error = ApiError(
            "Test error",
            status_code=400,
            error_code="test_error",
            details={"field": "test"},
        )

        result = error.to_dict()

        assert result["error"] == "test_error"
        assert result["message"] == "Test error"
        assert result["details"]["field"] == "test"

    def test_not_found_error(self):
        """Test NotFoundError formatting."""
        from admin.common.exceptions import NotFoundError

        error = NotFoundError("Tenant", "123")

        assert error.status_code == 404
        assert error.error_code == "not_found"
        assert "123" in error.message

    def test_forbidden_error(self):
        """Test ForbiddenError formatting."""
        from admin.common.exceptions import ForbiddenError

        error = ForbiddenError("delete", "tenant")

        assert error.status_code == 403
        assert error.error_code == "forbidden"

    def test_validation_error(self):
        """Test ValidationError formatting."""
        from admin.common.exceptions import ValidationError

        error = ValidationError(
            "Invalid email",
            field="email",
            errors=[{"loc": ["email"], "msg": "invalid format"}],
        )

        assert error.status_code == 400
        assert error.error_code == "validation_error"
        assert "email" in error.details["field"]


class TestResponseHelpers:
    """Test response formatting utilities."""

    def test_api_response(self):
        """Test standard API response."""
        from admin.common.responses import api_response

        result = api_response(
            {"id": "123", "name": "Test"},
            message="Success",
        )

        assert result["success"] is True
        assert result["data"]["id"] == "123"
        assert result["message"] == "Success"
        assert "timestamp" in result

    def test_paginated_response(self):
        """Test paginated response."""
        from admin.common.responses import paginated_response

        items = [{"id": i} for i in range(10)]
        result = paginated_response(
            items,
            total=100,
            page=1,
            page_size=10,
        )

        assert result["success"] is True
        assert len(result["data"]) == 10
        assert result["pagination"]["total_items"] == 100
        assert result["pagination"]["total_pages"] == 10
        assert result["pagination"]["has_next"] is True
        assert result["pagination"]["has_previous"] is False

    def test_created_response(self):
        """Test created response."""
        from admin.common.responses import created_response

        result = created_response(
            {"id": "123"},
            resource="Tenant",
            identifier="test-tenant",
        )

        assert result["success"] is True
        assert "created successfully" in result["message"]

    def test_deleted_response(self):
        """Test deleted response."""
        from admin.common.responses import deleted_response

        result = deleted_response("Tenant", "test-tenant")

        assert result["success"] is True
        assert "deleted successfully" in result["message"]


class TestAuthMiddleware:
    """Test authentication middleware."""

    def test_keycloak_config_from_env(self):
        """Test Keycloak configuration loading."""
        from admin.common.auth import KeycloakConfig

        config = KeycloakConfig(
            server_url="http://localhost:8080",
            realm="test",
            client_id="test-client",
        )

        assert config.issuer == "http://localhost:8080/realms/test"
        assert "certs" in config.jwks_url

    def test_token_payload_roles(self):
        """Test TokenPayload role extraction."""
        from admin.common.auth import TokenPayload

        payload = TokenPayload(
            sub="user-123",
            exp=9999999999,
            iat=1000000000,
            iss="http://keycloak/realms/test",
            realm_access={"roles": ["admin", "user"]},
        )

        assert payload.has_role("admin")
        assert payload.has_role("user")
        assert not payload.has_role("superadmin")

    @pytest.mark.asyncio
    async def test_auth_bearer_rejects_invalid_token(self):
        """Test AuthBearer rejects invalid tokens."""
        from admin.common.auth import AuthBearer

        auth = AuthBearer()

        # Mock request
        request = MagicMock()

        # Invalid token should return None
        result = await auth.authenticate(request, "invalid-token")
        assert result is None


class TestSchemas:
    """Test common Pydantic schemas."""

    def test_paginated_request_offset(self):
        """Test PaginatedRequest offset calculation."""
        from admin.common.schemas import PaginatedRequest

        req = PaginatedRequest(page=3, page_size=20)

        assert req.offset == 40  # (3-1) * 20

    def test_error_response_schema(self):
        """Test ErrorResponse schema."""
        from admin.common.schemas import ErrorResponse

        error = ErrorResponse(
            error="not_found",
            message="Resource not found",
        )

        assert error.success is False
        assert error.error == "not_found"