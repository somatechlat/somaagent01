import asyncio
import os
import pytest

from services.conversation_worker.main import ConversationWorker


class FakePublisher:
    def __init__(self):
        self.events = []

    async def publish(self, topic, event, dedupe_key=None, session_id=None, tenant=None):
        self.events.append((topic, event))
        # Mirror DurablePublisher minimal return contract for tests
        return {"status": "queued", "topic": topic}


class FakeSoma:
    def __init__(self, items_per_page=3, last_page_items=1):
        self.items_per_page = items_per_page
        self.last_page_items = last_page_items

    async def recall(self, query, *, top_k=8, universe=None, session_id=None, conversation_id=None, chunk_size=None, chunk_index=None, **kwargs):
        # Return a decreasing number of items to trigger early stop on second page
        idx = int(chunk_index or 0)
        if idx == 0:
            n = int(chunk_size or self.items_per_page)
        else:
            n = min(int(chunk_size or self.items_per_page), self.last_page_items)
        return {"results": [{"id": f"m-{idx}-{i}", "score": 1.0} for i in range(n)]}


@pytest.mark.asyncio
async def test_background_recall_emits_context_updates(monkeypatch):
    # Keep paging small for fast test
    os.environ["SOMABRAIN_RECALL_TOPK"] = "5"
    os.environ["SOMABRAIN_RECALL_CHUNK_SIZE"] = "3"
    worker = ConversationWorker()
    # Swap heavy publisher with a fake
    fake_pub = FakePublisher()
    worker.publisher = fake_pub
    # Swap soma client with a fake that returns predictable pages
    worker.soma = FakeSoma(items_per_page=3, last_page_items=1)

    stop_event = asyncio.Event()

    # Minimal base metadata and analysis
    base_metadata = {"tenant": "default", "universe_id": "wm"}
    analysis = {"intent": "question", "sentiment": "neutral", "tags": []}

    # Run background recall for a short time
    task = asyncio.create_task(
        worker._background_recall_context(
            session_id="s-1",
            persona_id=None,
            base_metadata=base_metadata,
            analysis_metadata=analysis,
            query="What is SomaBrain?",
            stop_event=stop_event,
        )
    )

    await asyncio.sleep(0.1)
    stop_event.set()
    try:
        await asyncio.wait_for(task, timeout=1.0)
    except asyncio.TimeoutError:
        task.cancel()

    # Ensure at least one context.update was published with recall details
    emitted = [e for (topic, e) in fake_pub.events if (e or {}).get("type") == "context.update"]
    assert emitted, "expected at least one context.update event"
    # Validate metadata content hints
    md = emitted[0].get("metadata", {})
    assert md.get("source") == "memory"
    extra = md.copy()
    # ensure recall payload was attached
    assert "recall" in extra
