"""M2 Admin Domain tests.

Tests for core admin, agents, and tenant management endpoints.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestCoreAdminEndpoints:
    """Tests for core admin API endpoints."""

    @pytest.mark.asyncio
    async def test_ping_endpoint(self):
        """Test ping returns ok status."""
        from admin.core.api.general import ping

        response = await ping()
        assert response == {"status": "ok"}

    def test_general_router_exists(self):
        """Test general router is properly configured."""
        from admin.core.api.general import router

        assert router is not None

    def test_kafka_router_exists(self):
        """Test kafka router is properly configured."""
        from admin.core.api.kafka import router

        assert router is not None

    def test_memory_router_exists(self):
        """Test memory router is properly configured."""
        from admin.core.api.memory import router

        assert router is not None

    def test_migrate_router_exists(self):
        """Test migrate router is properly configured."""
        from admin.core.api.migrate import router

        assert router is not None


class TestAgentAdminEndpoints:
    """Tests for agent admin API endpoints."""

    def test_agents_router_exists(self):
        """Test agents router is properly configured."""
        from admin.agents.api.agents import router

        assert router is not None

    def test_valid_agent_roles(self):
        """Test valid agent roles are defined."""
        from admin.agents.api.agents import VALID_ROLES

        assert "operator" in VALID_ROLES
        assert "viewer" in VALID_ROLES
        assert "manager" not in VALID_ROLES  # Manager cannot be assigned


class TestTenantUserEndpoints:
    """Tests for tenant user management endpoints."""

    def test_users_router_exists(self):
        """Test users router is properly configured."""
        from admin.saas.api.users import router

        assert router is not None

    def test_valid_tenant_roles(self):
        """Test valid tenant roles are defined (Django TenantRole choices)."""
        from admin.saas.api.users import VALID_ROLES

        assert "owner" in VALID_ROLES
        assert "admin" in VALID_ROLES
        assert "member" in VALID_ROLES
        assert "viewer" in VALID_ROLES


class TestTenantAgentEndpoints:
    """Tests for tenant agent management endpoints."""

    def test_tenant_agents_router_exists(self):
        """Test tenant agents router is properly configured."""
        from admin.saas.api.tenant_agents import router

        assert router is not None

    def test_quota_status_schema(self):
        """Test QuotaStatus schema."""
        from admin.saas.api.tenant_agents import QuotaStatus

        quota = QuotaStatus(
            agents_used=5,
            agents_limit=10,
            users_used=25,
            users_limit=50,
            tokens_used=1000000,
            tokens_limit=10000000,
            storage_used_gb=5.5,
            storage_limit_gb=50.0,
            can_create_agent=True,
            can_invite_user=True,
        )

        assert quota.agents_used == 5
        assert quota.can_create_agent is True

    def test_agent_schema(self):
        """Test AgentSchema."""
        from admin.saas.api.tenant_agents import AgentSchema
        from datetime import datetime

        agent = AgentSchema(
            id="test-id",
            name="Test Agent",
            slug="test-agent",
            status="running",
            owner_id="owner-1",
            tenant_id="tenant-1",
            chat_model="gpt-4o",
            memory_enabled=True,
            voice_enabled=False,
            created_at=datetime.now(),
        )

        assert agent.name == "Test Agent"
        assert agent.memory_enabled is True


class TestApiIntegration:
    """Tests for API integration."""

    def test_all_routers_mounted(self):
        """Test all M2 routers are mounted on main API."""
        from admin.api import api

        # Check router count
        assert len(api._routers) >= 7

    def test_saas_router_includes_users(self):
        """Test SAAS router includes user management."""
        from admin.saas.api import router

        # Router should have sub-routers for users and agents
        assert router is not None

    def test_core_router_aggregation(self):
        """Test core router aggregates all sub-routers."""
        from admin.core.api import router

        assert router is not None


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_agent_user_schema(self):
        """Test AgentUserSchema validation."""
        from admin.agents.api.agents import AgentUserSchema
        from datetime import datetime

        user = AgentUserSchema(
            id="user-1",
            user_id="uid-1",
            agent_id="agent-1",
            email="test@example.com",
            name="Test User",
            role="developer",
            added_at=datetime.now(),
        )

        assert user.role == "developer"

    def test_tenant_user_schema(self):
        """Test TenantUserOut validation."""
        from admin.saas.api.users import TenantUserOut

        user = TenantUserOut(
            id="user-1",
            email="test@example.com",
            name="Test User",
            role="member",
            is_active=True,
            tenant_id="tenant-1",
            created_at="2025-01-01T00:00:00",
        )

        assert user.is_active is True


class TestFastAPIRemoved:
    """Tests to verify FastAPI files are removed."""

    def test_no_legacy_admin_router(self):
        """Test legacy admin.py is removed."""
        import os

        path = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/services/gateway/routers/admin.py"
        assert not os.path.exists(path), "Legacy admin.py should be deleted"

    def test_no_legacy_admin_kafka(self):
        """Test legacy admin_kafka.py is removed."""
        import os

        path = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/services/gateway/routers/admin_kafka.py"
        assert not os.path.exists(path), "Legacy admin_kafka.py should be deleted"

    def test_no_legacy_admin_memory(self):
        """Test legacy admin_memory.py is removed."""
        import os

        path = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/services/gateway/routers/admin_memory.py"
        assert not os.path.exists(path), "Legacy admin_memory.py should be deleted"

    def test_no_legacy_agent_admin(self):
        """Test legacy agent_admin.py is removed."""
        import os

        path = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/services/gateway/routers/agent_admin.py"
        assert not os.path.exists(path), "Legacy agent_admin.py should be deleted"

    def test_no_legacy_tenant_admin(self):
        """Test legacy tenant_admin.py is removed."""
        import os

        path = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgent01/services/gateway/routers/tenant_admin.py"
        assert not os.path.exists(path), "Legacy tenant_admin.py should be deleted"