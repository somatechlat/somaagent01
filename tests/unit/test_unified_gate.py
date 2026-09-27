"""Unit tests for UnifiedGate permission checks.

Tests the three-layer permission gate:
1. OPA policy check (real HTTP call)
2. SpiceDB permission (real gRPC call)
3. Capsule scope check

All tests use the actual UnifiedGate implementation.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestUnifiedGate:
    """Test UnifiedGate permission checking."""

    @pytest.fixture
    def mock_capsule(self):
        """Create a mock capsule for testing."""
        capsule = MagicMock()
        capsule.id = "test-capsule-001"
        capsule.tenant_id = "test-tenant-001"
        # UnifiedGate.check() prefers capsule._cached_body and falls back to
        # capsule.body. MagicMock auto-vivifies any attribute into a truthy
        # mock, so _cached_body MUST be pinned to None here — otherwise the
        # fallback to the real dict below never runs and the scope check
        # fails closed against a MagicMock instead of this list.
        capsule._cached_body = None
        capsule.body = {
            "persona": {
                "tools": {
                    "enabled_capabilities": ["web_search", "code_execute"]
                }
            }
        }
        return capsule

    @pytest.mark.asyncio
    async def test_all_checks_pass(self, mock_capsule):
        """When all three checks pass, gate allows."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_check_opa', return_value=True), \
             patch.object(gate, '_check_spicedb', return_value=True):

            result = await gate.check(
                mock_capsule,
                action="chat:send",
                user_id="user-001",
                tenant_id="tenant-001",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_opa_denies(self, mock_capsule):
        """When OPA denies, gate denies."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_check_opa', return_value=False), \
             patch.object(gate, '_check_spicedb', return_value=True):

            result = await gate.check(
                mock_capsule,
                action="chat:send",
                user_id="user-001",
                tenant_id="tenant-001",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_spicedb_denies(self, mock_capsule):
        """When SpiceDB denies, gate denies."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_check_opa', return_value=True), \
             patch.object(gate, '_check_spicedb', return_value=False):

            result = await gate.check(
                mock_capsule,
                action="chat:send",
                user_id="user-001",
                tenant_id="tenant-001",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_scope_denies_tool(self, mock_capsule):
        """When capsule scope doesn't include tool, gate denies."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_check_opa', return_value=True), \
             patch.object(gate, '_check_spicedb', return_value=True):

            result = await gate.check(
                mock_capsule,
                action="tool:execute",
                resource="file_delete",  # NOT in enabled_capabilities
                user_id="user-001",
                tenant_id="tenant-001",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_scope_allows_tool(self, mock_capsule):
        """When capsule scope includes tool, gate allows."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_check_opa', return_value=True), \
             patch.object(gate, '_check_spicedb', return_value=True):

            result = await gate.check(
                mock_capsule,
                action="tool:execute",
                resource="web_search",  # IS in enabled_capabilities
                user_id="user-001",
                tenant_id="tenant-001",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_fail_closed_on_exception(self, mock_capsule):
        """Any exception causes gate to deny (fail-closed)."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_check_opa', side_effect=Exception("OPA down")):

            result = await gate.check(
                mock_capsule,
                action="chat:send",
                user_id="user-001",
                tenant_id="tenant-001",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_no_user_id_denies_spicedb(self, mock_capsule):
        """Missing user_id causes SpiceDB to deny."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_check_opa', return_value=True):

            result = await gate.check(
                mock_capsule,
                action="chat:send",
                user_id=None,
                tenant_id="tenant-001",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_endpoint_permission_fail_closed(self):
        """check_endpoint_permission fails closed on error."""
        from admin.core.agentiq.unified_gate import UnifiedGate

        gate = UnifiedGate()

        with patch.object(gate, '_get_policy_client', side_effect=Exception("OPA down")):

            result = await gate.check_endpoint_permission(
                user_id="user-001",
                tenant_id="tenant-001",
                permission="chat:send",
            )
            assert result is False
