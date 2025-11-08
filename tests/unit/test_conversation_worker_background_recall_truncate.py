import asyncio
import os

import pytest

from services.conversation_worker.main import ConversationWorker


class FakePublisher:
    def __init__(self):
        self.events = []

    async def publish(self, topic, event, dedupe_key=None, session_id=None, tenant=None):
        self.events.append((topic, event))
        return {"status": "queued", "topic": topic}


class FakeSoma:
    def __init__(self, n_items=25):
        self.n_items = n_items

    async def recall(self, query, **kwargs):
        # Return many results to trigger clamping
        items = [
            {"id": f"m-{i}", "score": 1.0, "payload": {"text": "x" * 200}}
            for i in range(self.n_items)
        ]
        return {"results": items}


@pytest.mark.asyncio
async def test_background_recall_metadata_is_clamped(monkeypatch):
    # Set aggressive limits for the test to ensure truncation happens
    os.environ["SOMABRAIN_CONTEXT_UPDATE_MAX_ITEMS"] = "3"
    os.environ["SOMABRAIN_CONTEXT_UPDATE_MAX_STRING"] = "50"
    os.environ["SOMABRAIN_CONTEXT_UPDATE_MAX_BYTES"] = "2000"

    worker = ConversationWorker()
    worker.publisher = FakePublisher()
    worker.soma = FakeSoma(n_items=20)

    stop_event = asyncio.Event()
    base_metadata = {"tenant": "default", "universe_id": "wm"}
    analysis = {"intent": "question", "sentiment": "neutral", "tags": []}

    await worker._background_recall_context(
        session_id="s-1",
        persona_id=None,
        base_metadata=base_metadata,
        analysis_metadata=analysis,
        query="What is SomaBrain?",
        stop_event=stop_event,
    )

    emitted = [
        e for (topic, e) in worker.publisher.events if (e or {}).get("type") == "context.update"
    ]
    assert emitted, "expected at least one context.update event"
    md = emitted[0].get("metadata") or {}
    rec = md.get("recall")
    # When clamped, either rec is summarized or results are truncated to <= 4 (3 + note)
    if isinstance(rec, dict) and "_summary" in rec:
        assert "truncated" in rec["_summary"]
    elif isinstance(rec, dict) and isinstance(rec.get("results"), list):
        assert len(rec["results"]) <= 4
