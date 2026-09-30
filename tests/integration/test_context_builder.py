"""Context Builder Integration Tests — VIBE Compliant.

NO mocks, NO fakes — uses real Django ORM, real tiktoken, and real SomaBrain when available.
Skipped gracefully when infrastructure is unavailable.
"""

from __future__ import annotations

import os
import socket
import uuid
from typing import Any

import pytest
import tiktoken

from types import SimpleNamespace

from admin.core.context import build_context, BuiltContext
from admin.core.models import Capsule


def _postgres_available() -> bool:
    """Check if PostgreSQL is available."""
    host = os.environ.get("SA01_DB_HOST", "localhost")
    port = int(os.environ.get("SA01_DB_PORT", "63932"))
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (socket.error, socket.timeout):
        return False


def _somabrain_available() -> bool:
    """Check if SomaBrain API is available."""
    try:
        with socket.create_connection(("localhost", 63996), timeout=2):
            return True
    except (socket.error, socket.timeout):
        return False


def _create_test_tenant() -> Any:
    """Create a Tenant for tests.

    No tier. Subscription tiers left with billing: an organisation is a
    partition, not a plan.
    """
    from admin.aaas.models import Tenant

    return Tenant.objects.create(
        name="Test Tenant",
        slug=f"test-tenant-{uuid.uuid4().hex[:8]}",
    )


def _create_test_capsule(tenant: Any, persona: dict | None = None) -> Capsule:
    """Create a Capsule for tests."""
    persona_config = persona or {
        "core": {"system_prompt": "You are a helpful assistant."},
        "knobs": {"intelligence_level": 5, "autonomy_level": 5, "resource_budget": 0.1},
        "memory": {"recall_limit": 5, "similarity_threshold": 0.7},
    }
    return Capsule.objects.create(
        name="Test Capsule",
        tenant=tenant,
        system_prompt=persona_config.get("core", {}).get(
            "system_prompt", "You are a helpful assistant."
        ),
        persona_config=persona_config,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_build_context_returns_all_five_lanes():
    """build_context() returns a BuiltContext with all 5 lanes populated."""
    tenant = _create_test_tenant()
    capsule = _create_test_capsule(tenant)

    context = await build_context(
        capsule=capsule,
        user_message="Hello",
        history=[{"role": "user", "content": "Previous message"}],
        memory_hits=[],
    )

    assert isinstance(context, BuiltContext)
    assert context.system != ""
    assert context.history != ""
    assert context.memory != ""
    assert context.tools != ""
    assert context.buffer != ""
    assert context.total_tokens >= 0


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_build_context_respects_token_budget():
    """Context respects token budget via budget_override."""
    tenant = _create_test_tenant()
    long_system = "A" * 2000
    persona = {
        "core": {"system_prompt": long_system},
        "knobs": {"intelligence_level": 5, "autonomy_level": 5, "resource_budget": 0.1},
        "memory": {"recall_limit": 5, "similarity_threshold": 0.7},
    }
    capsule = _create_test_capsule(tenant, persona=persona)

    budget_override = {"system": 10, "history": 10, "memory": 10, "tools": 10, "buffer": 10}
    long_history = [{"role": "user", "content": "B" * 2000} for _ in range(10)]
    long_message = "C" * 2000

    context = await build_context(
        capsule=capsule,
        user_message=long_message,
        history=long_history,
        memory_hits=[],
        budget_override=budget_override,
    )

    # Approximate token count from builder should respect budget
    assert context.total_tokens <= 50

    # Real tiktoken count on the assembled prompt should also be bounded
    enc = tiktoken.get_encoding("cl100k_base")
    prompt = context.to_prompt()
    real_tokens = len(enc.encode(prompt))
    # Allow some margin because the builder uses ~4 chars per token approximation
    assert real_tokens <= 100

    # Each lane should be truncated
    assert len(context.system) <= 10 * 4 + 4  # budget*4 plus small margin
    assert len(context.buffer) <= 10 * 4 + 4


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.skipif(not _somabrain_available(), reason="SomaBrain not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_memory_lane_includes_recalled_memories_when_brain_available():
    """Memory lane formats whatever MemoryGateway.recall() returned.

    The builder does not read memory. The caller recalls and passes the hits;
    this asserts the lane renders them. One read path, and it is not here.
    """
    tenant = _create_test_tenant()
    capsule = _create_test_capsule(tenant)

    hits = [
        SimpleNamespace(
            text="Integration test memory about pineapples",
            score=0.91,
            coord="mem-1",
        )
    ]

    context = await build_context(
        capsule=capsule,
        user_message="Tell me about pineapples",
        history=[],
        memory_hits=hits,
    )

    assert "pineapples" in context.memory


@pytest.mark.skipif(not _postgres_available(), reason="PostgreSQL not available")
@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_memory_lane_requires_hits():
    """A caller that did not recall is a bug, not a fallback.

    ``memory_hits=None`` used to silently fall back to a second client and,
    failing that, to the string ``"[Memory recall unavailable]"`` — a lane
    that looked populated while holding nothing. Now it raises. ``[]`` is the
    honest spelling of "recall ran and found nothing".
    """
    tenant = _create_test_tenant()
    capsule = _create_test_capsule(tenant)

    with pytest.raises(ValueError, match="memory_hits is required"):
        await build_context(
            capsule=capsule,
            user_message="Hello",
            history=[{"role": "user", "content": "Previous message"}],
            memory_hits=None,
        )
