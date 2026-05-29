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

from admin.common.messages import ErrorCode, get_message
from admin.core.chat_orchestrator import (
    ChatResult,
    ChatTurn,
    V3ChatOrchestrator,
)
from admin.core.models import Capsule, PendingMemory
from admin.core.permission_matrix import (
    PermissionCheckResult,
    PermissionChecker,
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
    """Check if LLM API key is configured."""
    return bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
    )


@pytest.fixture(autouse=True)
def reset_orchestrator_state():
    """Reset orchestrator and circuit breaker singletons between tests."""
    import admin.core.chat_orchestrator as co_module
    from services.common.circuit_breaker import reset_all_circuit_breakers

    co_module._orchestrator_instance = None
    reset_all_circuit_breakers()
    yield


def _create_test_tier() -> Any:
    """Create a SubscriptionTier for tests."""
    from admin.aaas.models import SubscriptionTier

    return SubscriptionTier.objects.create(name="Test Tier", slug=f"test-tier-{uuid.uuid4().hex[:8]}")


def _create_test_tenant(tier: Any) -> Any:
    """Create a Tenant for tests."""
    from admin.aaas.models import Tenant

    return Tenant.objects.create(
        name="Test Tenant",
        slug=f"test-tenant-{uuid.uuid4().hex[:8]}",
        tier=tier,
    )


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
    ) -> PermissionCheckResult:
        return PermissionCheckResult(
            allowed=False,
            permission=permission,
            level=PermissionLevel.RESOURCE,
            reason="Test permission denial",
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_turn_permission_denied():
    """process_turn() with permission denied returns degraded result."""
    tier = _create_test_tier()
    tenant = _create_test_tenant(tier)
    capsule = _create_test_capsule(tenant)

    orchestrator = V3ChatOrchestrator(permission_checker=DenyingPermissionChecker())
    turn = ChatTurn(
        capsule=capsule,
        user_id="user-123",
        tenant_id=str(tenant.id),
        user_message="Hello",
    )

    result = await orchestrator.process_turn(turn)

    assert isinstance(result, ChatResult)
    assert result.response == get_message(ErrorCode.DEGRADED_PERMISSION_DENIED)
    assert "Test permission denial" in result.errors
    assert result.turn_id


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_turn_gate_denied():
    """process_turn() with gate denied returns degraded result."""
    tier = _create_test_tier()
    tenant = _create_test_tenant(tier)
    # Default UnifiedGate denies when no OPA/SpiceDB policies are defined
    capsule = _create_test_capsule(tenant)

    orchestrator = V3ChatOrchestrator()
    turn = ChatTurn(
        capsule=capsule,
        user_id="user-123",
        tenant_id=str(tenant.id),
        user_message="Hello",
    )

    result = await orchestrator.process_turn(turn)

    assert isinstance(result, ChatResult)
    assert result.response == get_message(ErrorCode.DEGRADED_GATE_DENIED)
    assert "UnifiedGate rejected chat:send" in result.errors
    assert result.turn_id


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(not _llm_available(), reason="LLM API key not configured")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_turn_returns_chat_result():
    """process_turn() returns a ChatResult with response, model_used, turn_id."""
    from admin.chat.models import Conversation
    from admin.llm.models import LLMModelConfig

    tier = _create_test_tier()
    tenant = _create_test_tenant(tier)
    capsule = _create_test_capsule(
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

    orchestrator = V3ChatOrchestrator()
    turn = ChatTurn(
        capsule=capsule,
        user_id="user-123",
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

    tier = _create_test_tier()
    tenant = _create_test_tenant(tier)
    capsule = _create_test_capsule(
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

    orchestrator = V3ChatOrchestrator()
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


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_store_turn_stores_messages():
    """_store_turn() stores user and assistant messages to PostgreSQL."""
    from admin.chat.models import Conversation, Message

    conversation = _create_test_conversation("test-tenant")
    orchestrator = V3ChatOrchestrator()

    await orchestrator._store_turn(
        conversation_id=str(conversation.id),
        tenant_id="test-tenant",
        user_message="Hello assistant",
        assistant_response="Hello user",
        model_id="openai/gpt-4o-mini",
        elapsed_ms=150,
        token_count_out=5,
    )

    messages = list(Message.objects.filter(conversation_id=conversation.id).order_by("created_at"))
    assert len(messages) == 2

    user_msg = messages[0]
    assert user_msg.role == "user"
    assert user_msg.coordinate == "Hello assistant"
    assert user_msg.token_count > 0

    assistant_msg = messages[1]
    assert assistant_msg.role == "assistant"
    assert assistant_msg.coordinate == "Hello user"
    assert assistant_msg.model == "openai/gpt-4o-mini"
    assert assistant_msg.latency_ms == 150
    assert assistant_msg.token_count == 5

    conversation.refresh_from_db()
    assert conversation.message_count == 2


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_queue_pending_memory_creates_pending_memory():
    """_queue_pending_memory() creates PendingMemory when Brain is down."""
    orchestrator = V3ChatOrchestrator()

    await orchestrator._queue_pending_memory(
        tenant_id="test-tenant",
        namespace="chat_history",
        payload={
            "role": "assistant",
            "content": "Hello user",
            "conversation_id": "conv-123",
            "model": "openai/gpt-4o-mini",
            "latency_ms": 150,
        },
    )

    pending = list(PendingMemory.objects.filter(tenant_id="test-tenant", namespace="chat_history"))
    assert len(pending) == 1
    assert pending[0].payload["content"] == "Hello user"
    assert not pending[0].synced
