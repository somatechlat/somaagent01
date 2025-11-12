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


@pytest.mark.asyncio
async def test_background_recall_uses_sse_when_enabled(monkeypatch):
    os.environ["SOMABRAIN_USE_RECALL_SSE"] = "true"

    worker = ConversationWorker()
    worker.publisher = FakePublisher()

    # Provide a fake SSE emitter yielding two events then finishing
    async def fake_recall_stream_events(payload, request_timeout=None):
        yield {"kind": "recall", "page": 0, "memories": [1, 2]}
        yield {"kind": "recall", "page": 1, "memories": [3]}

    # Replace with a simple object that has recall_stream_events
        async def recall_stream_events(self, payload, request_timeout=None):
            async for e in fake_recall_stream_events(payload, request_timeout):
                yield e


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

    # Expect context.update events with status == recall_sse
    sse_updates = [
        e for (topic, e) in worker.publisher.events if (e or {}).get("type") == "context.update"
    ]
    assert sse_updates, "expected SSE-driven context updates"
    statuses = [((ev.get("metadata") or {}).get("status")) for ev in sse_updates]
    assert any(s == "recall_sse" for s in statuses)
