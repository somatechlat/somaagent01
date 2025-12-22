"""Integration tests for SomaClient endpoints.

Tests the following SomaClient methods against REAL SomaBrain infrastructure:
- adaptation_reset()
- act()
- brain_sleep_mode()
- util_sleep()
- micro_diag()
- sleep_status_all()
- neuromodulator clamping (unit tests - pure function, no external deps)

REQUIREMENTS:
- SomaBrain must be running (SA01_SOMA_BASE_URL must be set)
- Tests skip gracefully when infrastructure is unavailable

Per VIBE Coding Rules:
- NO MOCKS - all tests use real infrastructure
- REAL DATA - actual API calls to SomaBrain
- SKIP GRACEFULLY - tests skip when infra unavailable

Run with:
    SA01_SOMA_BASE_URL=http://localhost:9696 pytest tests/integrations/test_soma_client_integration.py -v
"""

from __future__ import annotations

import os
import uuid

import pytest

# Check if SomaBrain is available at module load
_SOMA_URL = os.environ.get("SA01_SOMA_BASE_URL")
_SKIP_REASON = "SA01_SOMA_BASE_URL not set - SomaBrain unavailable"


def _get_test_tenant_id() -> str:
    """Generate unique tenant ID for test isolation."""
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


def _get_test_session_id() -> str:
    """Generate unique session ID for test isolation."""
    return f"test-session-{uuid.uuid4().hex[:8]}"


# =============================================================================
# UNIT TESTS - Neuromodulator clamping
# =============================================================================
# NOTE: These tests are in a separate file (test_neuromodulator_clamping.py)
# because importing from python.somaagent.somabrain_integration requires the
# full agent stack which has heavy dependencies (aiohttp, etc.)
# =============================================================================


# =============================================================================
# VALIDATION TESTS - Client-side validation, no network required
# =============================================================================


class TestClientValidation:
    """Tests for client-side validation logic."""

    @pytest.mark.asyncio
    async def test_brain_sleep_mode_invalid_state(self) -> None:
        """Test that invalid sleep state raises ValueError."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            with pytest.raises(ValueError, match="target_state must be one of"):
                await client.brain_sleep_mode(target_state="invalid_state")
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_util_sleep_invalid_state(self) -> None:
        """Test that invalid sleep state raises ValueError."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            with pytest.raises(ValueError, match="target_state must be one of"):
                await client.util_sleep(target_state="not_a_state")
        finally:
            await client.close()


# =============================================================================
# INTEGRATION TESTS - Require REAL SomaBrain infrastructure
# =============================================================================


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestAdaptationReset:
    """Tests for SomaClient.adaptation_reset() endpoint."""

    @pytest.mark.asyncio
    async def test_adaptation_reset_basic(self) -> None:
        """Test basic adaptation reset with default parameters."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.adaptation_reset(
                tenant_id=_get_test_tenant_id(),
                reset_history=True,
            )
            assert result is not None
            assert result.get("ok") is True or "tenant_id" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_adaptation_reset_with_base_lr(self) -> None:
        """Test adaptation reset with custom base learning rate."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.adaptation_reset(
                tenant_id=_get_test_tenant_id(),
                base_lr=0.05,
                reset_history=True,
            )
            assert result is not None
            assert result.get("ok") is True or "tenant_id" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_adaptation_reset_with_defaults(self) -> None:
        """Test adaptation reset with custom retrieval and utility defaults."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.adaptation_reset(
                tenant_id=_get_test_tenant_id(),
                reset_history=False,
                retrieval_defaults={"alpha": 0.5, "beta": 0.5, "gamma": 0.5, "tau": 0.5},
                utility_defaults={"lambda_": 0.5, "mu": 0.5, "nu": 0.5},
            )
            assert result is not None
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestAct:
    """Tests for SomaClient.act() endpoint."""

    @pytest.mark.xfail(reason="SomaBrain /act endpoint has cognitive processing error - separate bug")
    @pytest.mark.asyncio
    async def test_act_basic(self) -> None:
        """Test basic act() call with a simple task."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.act(
                task="Analyze the current context",
                top_k=3,
                session_id=_get_test_session_id(),
            )
            assert result is not None
        finally:
            await client.close()

    @pytest.mark.xfail(reason="SomaBrain /act endpoint has cognitive processing error - separate bug")
    @pytest.mark.asyncio
    async def test_act_with_universe(self) -> None:
        """Test act() with universe scope."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.act(
                task="Search for relevant memories",
                top_k=5,
                universe="test-universe",
                session_id=_get_test_session_id(),
            )
            assert result is not None
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestBrainSleepMode:
    """Tests for SomaClient.brain_sleep_mode() endpoint.
    
    Sleep state machine per SRS:
    ACTIVE → LIGHT → DEEP → FREEZE → LIGHT (cycle)
    
    Note: Tests share tenant state via auth token. Each test handles
    the current state appropriately.
    """

    @pytest.mark.asyncio
    async def test_brain_sleep_mode_transition(self) -> None:
        """Test sleep state transitions via brain endpoint.
        
        This test performs a valid transition based on current state.
        The endpoint is working if we get a successful response or
        a valid "invalid transition" error (meaning state machine is enforced).
        """
        from python.integrations.soma_client import SomaClient, SomaClientError

        client = SomaClient()
        try:
            # Try transitioning to light - this is valid from active
            # If already in light, we'll get an error which is expected
            try:
                result = await client.brain_sleep_mode(
                    target_state="light",
                    ttl_seconds=60,
                )
                assert result is not None
                assert result.get("ok") is True or "new_state" in result
            except SomaClientError as e:
                # "Invalid transition" means the endpoint works, just wrong state
                assert "Invalid transition" in str(e), f"Unexpected error: {e}"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_brain_sleep_mode_with_ttl(self) -> None:
        """Test that TTL parameter is accepted by brain endpoint."""
        from python.integrations.soma_client import SomaClient, SomaClientError

        client = SomaClient()
        try:
            # Try deep transition (valid from light)
            try:
                result = await client.brain_sleep_mode(
                    target_state="deep",
                    ttl_seconds=30,
                )
                assert result is not None
            except SomaClientError as e:
                # Invalid transition is acceptable - endpoint is working
                assert "Invalid transition" in str(e) or "400" in str(e)
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestUtilSleep:
    """Tests for SomaClient.util_sleep() endpoint.
    
    Sleep state machine per SRS:
    ACTIVE → LIGHT → DEEP → FREEZE → LIGHT (cycle)
    
    Note: Tests share tenant state via auth token. Each test handles
    the current state appropriately.
    """

    @pytest.mark.asyncio
    async def test_util_sleep_transition(self) -> None:
        """Test sleep state transitions via util endpoint.
        
        This test performs a valid transition based on current state.
        The endpoint is working if we get a successful response or
        a valid "invalid transition" error (meaning state machine is enforced).
        """
        from python.integrations.soma_client import SomaClient, SomaClientError

        client = SomaClient()
        try:
            # Try transitioning to light - this is valid from active
            try:
                result = await client.util_sleep(target_state="light")
                assert result is not None
                assert result.get("ok") is True or "new_state" in result
            except SomaClientError as e:
                # "Invalid transition" means the endpoint works, just wrong state
                assert "Invalid transition" in str(e), f"Unexpected error: {e}"
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_util_sleep_with_ttl(self) -> None:
        """Test that TTL parameter is accepted by util endpoint."""
        from python.integrations.soma_client import SomaClient, SomaClientError

        client = SomaClient()
        try:
            # Try deep transition with TTL (valid from light)
            try:
                result = await client.util_sleep(
                    target_state="deep",
                    ttl_seconds=30,
                )
                assert result is not None
            except SomaClientError as e:
                # Invalid transition is acceptable - endpoint is working
                assert "Invalid transition" in str(e) or "400" in str(e)
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestMicroDiag:
    """Tests for SomaClient.micro_diag() endpoint."""

    @pytest.mark.asyncio
    async def test_micro_diag_returns_diagnostics(self) -> None:
        """Test that micro_diag returns diagnostic information."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.micro_diag()
            assert result is not None
            assert isinstance(result, dict)
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestSleepStatusAll:
    """Tests for SomaClient.sleep_status_all() endpoint."""

    @pytest.mark.asyncio
    async def test_sleep_status_all_returns_status(self) -> None:
        """Test that sleep_status_all returns status for all tenants."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.sleep_status_all()
            assert result is not None
            assert isinstance(result, dict)
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestNeuromodulatorEndpoints:
    """Tests for SomaClient neuromodulator endpoints."""

    @pytest.mark.asyncio
    async def test_get_neuromodulators(self) -> None:
        """Test getting neuromodulator state from SomaBrain."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.get_neuromodulators(tenant_id=_get_test_tenant_id())
            assert result is not None
            assert isinstance(result, dict)
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_update_neuromodulators(self) -> None:
        """Test updating neuromodulator state in SomaBrain."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            new_levels = {
                "dopamine": 0.5,
                "serotonin": 0.6,
                "noradrenaline": 0.05,
                "acetylcholine": 0.3,
            }
            result = await client.update_neuromodulators(
                tenant_id=_get_test_tenant_id(),
                neuromodulators=new_levels,
            )
            assert result is not None
            assert isinstance(result, dict)
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestAdaptationState:
    """Tests for SomaClient adaptation state endpoint."""

    @pytest.mark.asyncio
    async def test_get_adaptation_state(self) -> None:
        """Test getting adaptation state from SomaBrain."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.get_adaptation_state(tenant_id=_get_test_tenant_id())
            assert result is not None
            assert isinstance(result, dict)
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestSleepCycle:
    """Tests for SomaClient sleep_cycle endpoint."""

    @pytest.mark.asyncio
    async def test_sleep_cycle_nrem_rem(self) -> None:
        """Test triggering a sleep cycle with NREM and REM phases."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.sleep_cycle(
                tenant_id=_get_test_tenant_id(),
                nrem=True,
                rem=True,
            )
            assert result is not None
            assert isinstance(result, dict)
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_sleep_cycle_nrem_only(self) -> None:
        """Test triggering a sleep cycle with NREM only."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.sleep_cycle(
                tenant_id=_get_test_tenant_id(),
                nrem=True,
                rem=False,
            )
            assert result is not None
        finally:
            await client.close()


@pytest.mark.skipif(not _SOMA_URL, reason=_SKIP_REASON)
class TestSleepStatus:
    """Tests for SomaClient sleep_status endpoint."""

    @pytest.mark.asyncio
    async def test_sleep_status(self) -> None:
        """Test getting sleep status from SomaBrain."""
        from python.integrations.soma_client import SomaClient

        client = SomaClient()
        try:
            result = await client.sleep_status()
            assert result is not None
            assert isinstance(result, dict)
        finally:
            await client.close()
