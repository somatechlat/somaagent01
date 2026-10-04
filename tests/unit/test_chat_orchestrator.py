"""Chat Orchestrator Unit Tests — VIBE Compliant.

NO mocks, NO fakes — uses real Django ORM and real infrastructure where available.
Skipped gracefully when infrastructure is unavailable.
"""

from __future__ import annotations

import os
import socket
import uuid
from typing import Any

import pytest
from asgiref.sync import sync_to_async

from admin.common.messages import ErrorCode, get_message
from admin.core.chat_orchestrator import (
    ChatResult,
    ChatTurn,
    V3ChatOrchestrator,
)
from admin.core.models import Capsule
from admin.core.permission_matrix import (
    PermissionChecker,
    PermissionCheckResult,
    PermissionLevel,
)


def _postgres_available() -> bool:
    """Check if PostgreSQL is available."""
    host = os.environ.get("SA01_DB_HOST", "localhost")
    port = int(os.environ.get("SA01_DB_PORT", "63932"))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.error, socket.timeout):
        return False


def _llm_available() -> bool:
    """Check whether Vault holds a provider key for any LLM provider.

    Model credentials live in the agent's model administration (Vault
    ``secret/agent/api_keys/{provider}_api_key``), not in the environment —
    so this must ask the secret manager, the same way the runtime does.
    """
    try:
        from services.common.unified_secret_manager import UnifiedSecretManager

        manager = UnifiedSecretManager()
    except Exception:
        return False
    for provider in ("groq", "openai", "anthropic", "openrouter"):
        key = manager.get_provider_key(provider)
        if key and key not in ("None", "NA"):
            return True
    return False


@pytest.fixture(autouse=True)
def reset_orchestrator_state():
    """Reset orchestrator and circuit breaker singletons between tests."""
    import admin.core.chat_orchestrator as co_module
    from services.common.circuit_breaker import reset_all_circuit_breakers

    co_module._orchestrator_instance = None
    reset_all_circuit_breakers()
    yield


@sync_to_async
def _create_test_tenant() -> Any:
    """Create a Tenant for tests.

    ``@sync_to_async`` because every caller is an ``async def`` test: the
    sync ORM must not run on the event loop. Same shape the handlers use.

    No tier. Subscription tiers left with billing: an organisation is a
    partition, not a plan.
    """
    from admin.aaas.models import Tenant

    return Tenant.objects.create(
        name="Test Tenant",
        slug=f"test-tenant-{uuid.uuid4().hex[:8]}",
    )


@sync_to_async
def _create_test_capsule(tenant: Any, governance: dict | None = None) -> Capsule:
    """Create a Capsule for tests."""
    persona_config: dict = {
        "knobs": {"intelligence_level": 5, "autonomy_level": 5, "resource_budget": 0.1}
    }
    if governance:
        persona_config["governance"] = governance
    return Capsule.objects.create(
        name="Test Capsule",
        tenant=tenant,
        system_prompt="You are a helpful assistant.",
        persona_config=persona_config,
    )


@sync_to_async
def _create_test_member(tenant: Any, role: str = "member") -> str:
    """Create a real TenantUser and return its subject id.

    Roles are not attached to a call, they are recorded on a membership. A
    subject with no row has no roles, and no roles is denial — so the denied
    paths below simply use no row, and the allowed paths create one.
    """
    from admin.aaas.models import TenantUser

    user_id = uuid.uuid4()
    TenantUser.objects.create(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user_id,
        email=f"{user_id}@example.test",
        display_name="Test Member",
        role=role,
        is_active=True,
    )
    return str(user_id)


def _create_test_conversation(tenant_id: str) -> Any:
    """Create a Conversation for tests."""
    from admin.chat.models import Conversation

    return Conversation.objects.create(
        agent_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),  # use a fresh tenant id to avoid FK issues
        title="Test Conversation",
    )


class DenyingPermissionChecker(PermissionChecker):
    """Permission checker that always denies (for testing denied paths)."""

    async def check(
        self,
        user_id: str,
        permission: str,
        tenant_id: str | None = None,
        agent_id: str | None = None,
        resource_id: str | None = None,
        roles: list[str] | None = None,
    ) -> PermissionCheckResult:
        return PermissionCheckResult(
            allowed=False,
            permission=permission,
            level=PermissionLevel.RESOURCE,
            reason="Test permission denial",
        )


class AllowingGate:
    """Collaborator double: a gate that offers no narrowing.

    Injected where the test is about a later phase, so this phase is not the
    variable under test. It is not a stand-in for infrastructure — the
    permission tests below run the real ``PermissionChecker`` and the real
    ``UnifiedGate`` against real rows.
    """

    async def check(self, *args, **kwargs):
        return True

    async def check_endpoint_permission(self, *args, **kwargs):
        return True


class DenyingGate:
    """Collaborator double: a gate that always narrows to denial.

    Used only to reach the gate-denied branch, which needs the role floor to
    pass and the gate to refuse. Without a policy engine attached the real gate
    has nothing left to narrow with, so this stands in for an engine that
    refuses.
    """

    async def check(self, *args, **kwargs):
        return False

    async def check_endpoint_permission(self, *args, **kwargs):
        return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_turn_permission_denied():
    """A subject with no membership row is denied at the role floor.

    This is the real ``PermissionChecker``. Denial does not come from a
    substituted checker: the subject simply holds no role, and no role is
    denial.
    """
    tenant = await _create_test_tenant()
    capsule = await _create_test_capsule(tenant)

    orchestrator = V3ChatOrchestrator()
    turn = ChatTurn(
        capsule=capsule,
        user_id="user-with-no-membership",
        tenant_id=str(tenant.id),
        user_message="Hello",
    )

    result = await orchestrator.process_turn(turn)

    assert isinstance(result, ChatResult)
    assert result.response == get_message(ErrorCode.DEGRADED_PERMISSION_DENIED)
    assert result.turn_id


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_turn_gate_denied():
    """A gate that refuses is reported as a gate denial, not a floor denial.

    The subject is a real member, so the role floor passes. The gate is the
    layer that refuses, which is the branch this test is about.
    """
    tenant = await _create_test_tenant()
    capsule = await _create_test_capsule(tenant)
    user_id = await _create_test_member(tenant, role="member")

    orchestrator = V3ChatOrchestrator(unified_gate=DenyingGate())
    turn = ChatTurn(
        capsule=capsule,
        user_id=user_id,
        tenant_id=str(tenant.id),
        user_message="Hello",
    )

    result = await orchestrator.process_turn(turn)

    assert isinstance(result, ChatResult)
    assert result.response == get_message(ErrorCode.DEGRADED_GATE_DENIED)
    assert "UnifiedGate rejected resource:chat_send" in result.errors
    assert result.turn_id


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_turn_passes_identity_roles_to_the_gate():
    """The gate is checked with the turn's authenticated roles.

    A live session subject is a ``LocalIdentity`` UUID that need not have a
    ``TenantUser`` row. The role floor must see the token roles rather than
    re-query membership and deny a member.
    """
    tenant = await _create_test_tenant()
    capsule = await _create_test_capsule(tenant)

    class RecordingGate:
        """Collaborator double: records the roles the orchestrator passed."""

        seen_roles: Any = None

        async def check(self, *args, **kwargs):
            RecordingGate.seen_roles = kwargs.get("roles")
            return False

        async def check_endpoint_permission(self, *args, **kwargs):
            return False

    orchestrator = V3ChatOrchestrator(unified_gate=RecordingGate())
    turn = ChatTurn(
        capsule=capsule,
        user_id=str(uuid.uuid4()),
        tenant_id=str(tenant.id),
        user_message="Hello",
        roles=["member"],
    )

    result = await orchestrator.process_turn(turn)

    assert RecordingGate.seen_roles == ["member"]
    assert result.response == get_message(ErrorCode.DEGRADED_GATE_DENIED)


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(not _llm_available(), reason="LLM API key not configured")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_turn_returns_chat_result():
    """process_turn() returns a ChatResult with response, model_used, turn_id."""
    from admin.chat.models import Conversation
    from admin.llm.models import LLMModelConfig

    tenant = await _create_test_tenant()
    capsule = await _create_test_capsule(
        tenant,
        governance={
            "opa_policies": {"chat_send": {"allow": True}},
            "spicedb_relations": {"chat_send": True},
        },
    )
    LLMModelConfig.objects.create(
        name="gpt-4o-mini",
        provider="openai",
        capabilities=["text"],
        priority=80,
        is_active=True,
    )
    conversation = Conversation.objects.create(
        agent_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        title="Test Conversation",
    )

    user_id = await _create_test_member(tenant, role="member")
    orchestrator = V3ChatOrchestrator(unified_gate=AllowingGate())
    turn = ChatTurn(
        capsule=capsule,
        user_id=user_id,
        tenant_id=str(tenant.id),
        user_message="Say 'hello world' and nothing else.",
        conversation_id=str(conversation.id),
    )

    result = await orchestrator.process_turn(turn)

    assert isinstance(result, ChatResult)
    assert result.response
    assert result.model_used
    assert result.turn_id
    assert result.phase_completed >= 8


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(not _llm_available(), reason="LLM API key not configured")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_stream_turn_yields_tokens():
    """stream_turn() yields tokens from the LLM."""
    from admin.chat.models import Conversation
    from admin.llm.models import LLMModelConfig

    tenant = await _create_test_tenant()
    capsule = await _create_test_capsule(
        tenant,
        governance={
            "opa_policies": {"chat_send": {"allow": True}},
            "spicedb_relations": {"chat_send": True},
        },
    )
    LLMModelConfig.objects.create(
        name="gpt-4o-mini",
        provider="openai",
        capabilities=["text"],
        priority=80,
        is_active=True,
    )
    conversation = Conversation.objects.create(
        agent_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        title="Test Conversation",
    )

    orchestrator = V3ChatOrchestrator(unified_gate=AllowingGate())
    turn = ChatTurn(
        capsule=capsule,
        user_id="user-123",
        tenant_id=str(tenant.id),
        user_message="Say 'hi' and nothing else.",
        conversation_id=str(conversation.id),
    )

    tokens = []
    async for token in orchestrator.stream_turn(turn):
        tokens.append(token)

    assert len(tokens) > 0
    full_response = "".join(tokens)
    assert full_response
