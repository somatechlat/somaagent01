"""A SomaBrain outage must degrade the turn, not abort it.

`_recall_memories` returns ``None`` when recall raised (an outage). The context
builder treated ``None`` as "the caller forgot to call recall" and raised
``ValueError`` — so a brain outage turned into a hard turn failure. The user
asked for a failsafe and a degradation strategy: the turn continues and the
memory lane says so, rather than the chat dying.
"""

from __future__ import annotations

import asyncio

from admin.core.context.builder import ContextBuilder


class _FakeCapsule:
    """Minimal stand-in for the Capsule attributes the builder reads."""

    id = "cap-test"
    persona_config: dict = {}


def test_none_memory_hits_degrade_instead_of_raising():
    """Recall that did not run because of an outage is not a caller bug."""
    builder = ContextBuilder()
    lane = asyncio.run(
        builder._build_memory_lane(
            capsule=_FakeCapsule(),
            query="hello",
            persona={},
            budget=100,
            memory_hits=None,
        )
    )
    assert isinstance(lane, str)
    assert "memory" in lane.lower()


def test_empty_memory_hits_still_render_an_honest_empty_lane():
    """Recall that ran and found nothing must not claim memory is unavailable."""
    builder = ContextBuilder()
    lane = asyncio.run(
        builder._build_memory_lane(
            capsule=_FakeCapsule(),
            query="hello",
            persona={},
            budget=100,
            memory_hits=[],
        )
    )
    assert isinstance(lane, str)
    assert "unavailable" not in lane.lower()
