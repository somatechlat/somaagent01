"""Capsule.chat_model must drive model selection.

The admin UI writes ``Capsule.chat_model`` (admin/llm/api.py set_slots).
``select_model`` has to honour that binding — otherwise the slot has zero
effect on the chat path.
"""

from __future__ import annotations

import os
import socket
import uuid

import pytest
from asgiref.sync import sync_to_async

from admin.core.model_router import select_model


def _postgres_available() -> bool:
    host = os.environ.get("SA01_DB_HOST", "localhost")
    port = int(os.environ.get("SA01_DB_PORT", "63932"))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.error, socket.timeout):
        return False


@sync_to_async
def _seed_pair() -> tuple[int, int, object]:
    """Two active capable models + a Capsule bound to the lower-priority one.

    Returns (preferred_id, high_priority_id, capsule_id).
    """
    from admin.aaas.models import Tenant
    from admin.core.models import Capsule
    from admin.llm.models import LLMModelConfig

    high = LLMModelConfig.objects.create(
        name=f"preferred-high-{uuid.uuid4().hex[:8]}",
        provider="groq",
        capabilities=["text"],
        priority=100,
        is_active=True,
    )
    low = LLMModelConfig.objects.create(
        name=f"preferred-low-{uuid.uuid4().hex[:8]}",
        provider="groq",
        capabilities=["text"],
        priority=10,
        is_active=True,
    )
    tenant = Tenant.objects.create(
        name="Preferred Tenant",
        slug=f"preferred-{uuid.uuid4().hex[:8]}",
    )
    capsule = Capsule.objects.create(
        name="Preferred Capsule",
        tenant=tenant,
        system_prompt="test",
        chat_model=low,
    )
    return low.id, high.id, capsule.id


@sync_to_async
def _load_capsule_chat_model_id(capsule_id: object) -> int | None:
    from admin.core.models import Capsule

    cap = Capsule.objects.get(id=capsule_id)
    return cap.chat_model_id


@sync_to_async
def _model_name(model_id: int) -> str:
    from admin.llm.models import LLMModelConfig

    return LLMModelConfig.objects.get(id=model_id).name


@sync_to_async
def _deactivate(model_id: int) -> None:
    from admin.llm.models import LLMModelConfig

    LLMModelConfig.objects.filter(id=model_id).update(is_active=False)


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_select_model_honours_capsule_chat_model_binding():
    """A capsule bound to the lower-priority model must win over priority."""
    low_id, high_id, capsule_id = await _seed_pair()
    preferred_model_id = await _load_capsule_chat_model_id(capsule_id)
    assert preferred_model_id == low_id

    selected = await select_model(
        {"text"},
        preferred_model_id=preferred_model_id,
    )

    assert selected.name == await _model_name(low_id)
    assert selected.name != await _model_name(high_id)


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_select_model_falls_through_when_preferred_is_inactive():
    """An inactive preferred model is skipped — warn and use the best active one."""
    low_id, high_id, _capsule_id = await _seed_pair()
    await _deactivate(low_id)

    selected = await select_model(
        {"text"},
        preferred_model_id=low_id,
    )

    assert selected.name == await _model_name(high_id)
