"""Transcript persistence — Message rows are the conversation transcript.

ARCH-INVARIANTS §3 (docs/architecture/SOMA-ARCH-INVARIANTS-001.md): Postgres
``Message`` rows are the conversation transcript. They are **not** semantic
memory. A turn that reaches the phase-4 gate MUST leave its input in the
transcript even when every later phase fails.

NO mocks, NO fakes. Real Django ORM rows, real permission membership, real
LLM-path failures (unreachable base URL / fail-closed credential gate).
"""

from __future__ import annotations

import os
import re
import socket
import uuid

import pytest
from asgiref.sync import sync_to_async

from admin.core.chat_orchestrator import (
    ChatTurn,
    V3ChatOrchestrator,
)
from admin.core.models import Capsule

_COORD_RE = re.compile(r"^-?\d+(\.\d+)?(,-?\d+(\.\d+)?){2}$")


def _postgres_available() -> bool:
    """True when the test Postgres answers a TCP connect."""
    host = os.environ.get("SA01_DB_HOST", "localhost")
    port = int(os.environ.get("SA01_DB_PORT", "63932"))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.error, socket.timeout):
        return False


def _llm_available() -> bool:
    """True when Vault holds a provider key for any LLM provider.

    Credentials live in Vault (``secret/agent/api_keys/{provider}_api_key``),
    never in the environment. Missing credentials mean the test SKIPs — never
    a dummy past a real gate.
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


class AllowingGate:
    """Collaborator double: a gate that offers no narrowing.

    Injected only where the test is about transcript persistence, not about
    the gate. The role floor still runs the real ``PermissionChecker``.
    """

    async def check(self, *args, **kwargs):
        return True

    async def check_endpoint_permission(self, *args, **kwargs):
        return True


@sync_to_async
def _create_tenant() -> object:
    from admin.aaas.models import Tenant

    return Tenant.objects.create(
        name="Transcript Tenant",
        slug=f"transcript-{uuid.uuid4().hex[:8]}",
    )


@sync_to_async
def _create_capsule(tenant: object) -> Capsule:
    return Capsule.objects.create(
        name="Transcript Capsule",
        tenant=tenant,
        system_prompt="You are a helpful assistant.",
        persona_config={"knobs": {"intelligence_level": 5, "autonomy_level": 5}},
    )


@sync_to_async
def _create_member(tenant: object, role: str = "member") -> str:
    from admin.aaas.models import TenantUser

    user_id = uuid.uuid4()
    TenantUser.objects.create(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=user_id,
        email=f"{user_id}@example.test",
        display_name="Transcript Member",
        role=role,
        is_active=True,
    )
    return str(user_id)


@sync_to_async
def _create_conversation(tenant: object) -> object:
    from admin.chat.models import Conversation

    return Conversation.objects.create(
        agent_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        tenant_id=tenant.id,
        title="Transcript Conversation",
    )


@sync_to_async
def _create_model_config(name: str, priority: int, *, api_base: str = "") -> object:
    from admin.llm.models import LLMModelConfig

    return LLMModelConfig.objects.create(
        name=name,
        provider="groq",
        api_base=api_base,
        capabilities=["text"],
        priority=priority,
        is_active=True,
    )


@sync_to_async
def _message_rows(conversation_id: str) -> list:
    from admin.chat.models import Message

    return list(
        Message.objects.filter(conversation_id=conversation_id).order_by("created_at")
    )


@sync_to_async
def _conversation_row(conversation_id: str) -> object:
    from admin.chat.models import Conversation

    return Conversation.objects.get(id=conversation_id)


# ---------------------------------------------------------------------------
# 1. Successful turn → user + assistant transcript rows, message_count == 2
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(not _llm_available(), reason="LLM API key not configured")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_successful_turn_persists_user_and_assistant_transcript():
    """A completed process_turn writes both transcript rows and bumps the count.

    Roles arrive in order (user, assistant) and ``Conversation.message_count``
    is 2 — the field is created 0 and must be maintained.
    """
    tenant = await _create_tenant()
    capsule = await _create_capsule(tenant)
    await _create_model_config("transcript-success-model", priority=80)
    conversation = await _create_conversation(tenant)
    user_id = await _create_member(tenant, role="member")

    orchestrator = V3ChatOrchestrator(unified_gate=AllowingGate())
    turn = ChatTurn(
        capsule=capsule,
        user_id=user_id,
        tenant_id=str(tenant.id),
        user_message="Say 'hello transcript' and nothing else.",
        conversation_id=str(conversation.id),
    )

    result = await orchestrator.process_turn(turn)

    assert result.turn_id
    assert result.phase_completed >= 8

    rows = await _message_rows(str(conversation.id))
    assert [m.role for m in rows] == ["user", "assistant"]
    assert rows[0].content == "Say 'hello transcript' and nothing else."
    assert rows[1].content == result.response

    conv = await _conversation_row(str(conversation.id))
    assert conv.message_count == 2


# ---------------------------------------------------------------------------
# 2. Failed LLM call → exactly one user row (the input is still recorded)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_failed_llm_turn_still_records_user_transcript(monkeypatch):
    """A turn whose LLM invocation fails still leaves the user input in the table.

    The LLM path fails for real: ``SA01_LITELLM_GLOBAL_KWARGS`` points the
    client at an unreachable base URL (nothing listens on 127.0.0.1:1). No
    mock replaces the client. If no provider credential is provisioned in
    Vault the real fail-closed gate (``LLMNotConfiguredError``) is the failure
    — also not a mock. Either way the phase-4 gate has already passed and the
    input must be on disk.
    """
    monkeypatch.setenv(
        "SA01_LITELLM_GLOBAL_KWARGS",
        '{"api_base": "http://127.0.0.1:1"}',
    )

    tenant = await _create_tenant()
    capsule = await _create_capsule(tenant)
    await _create_model_config(
        "transcript-dead-model",
        priority=80,
        api_base="http://127.0.0.1:1",
    )
    conversation = await _create_conversation(tenant)
    user_id = await _create_member(tenant, role="member")

    orchestrator = V3ChatOrchestrator(unified_gate=AllowingGate())
    turn = ChatTurn(
        capsule=capsule,
        user_id=user_id,
        tenant_id=str(tenant.id),
        user_message="This input must survive the failed LLM call.",
        conversation_id=str(conversation.id),
    )

    result = await orchestrator.process_turn(turn)

    # The turn did not produce an assistant completion.
    assert result.errors or result.phase_completed < 12

    rows = await _message_rows(str(conversation.id))
    assert len(rows) == 1
    assert rows[0].role == "user"
    assert rows[0].content == "This input must survive the failed LLM call."

    conv = await _conversation_row(str(conversation.id))
    assert conv.message_count == 1


# ---------------------------------------------------------------------------
# 3. coordinate is a real coord; text lives in the content column
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_message_coordinate_is_coord_and_text_lives_in_content():
    """``Message.coordinate`` holds a seam coordinate; text is in ``content``.

    ``make_coord`` is the one coordinate scheme (memory_contract). The row
    must store that CSV float triple in ``coordinate`` and the turn text in a
    real text column — not the reverse.
    """
    from datetime import datetime, UTC

    from services.common.memory_contract import make_coord

    tenant = await _create_tenant()
    conversation = await _create_conversation(tenant)
    text = "Turn text belongs in the content column."
    coord = make_coord(str(tenant.id), "episodic", datetime.now(UTC), text)

    orchestrator = V3ChatOrchestrator(unified_gate=AllowingGate())
    await orchestrator._persist_message(
        conversation_id=str(conversation.id),
        tenant_id=str(tenant.id),
        role="user",
        text=text,
        coordinate=coord,
    )
    await orchestrator._bump_message_count(str(conversation.id))

    rows = await _message_rows(str(conversation.id))
    assert len(rows) == 1
    msg = rows[0]

    assert msg.content == text
    assert msg.coordinate == coord
    assert _COORD_RE.match(msg.coordinate), f"not a coord CSV: {msg.coordinate!r}"
    assert msg.coordinate != msg.content

    conv = await _conversation_row(str(conversation.id))
    assert conv.message_count == 1
