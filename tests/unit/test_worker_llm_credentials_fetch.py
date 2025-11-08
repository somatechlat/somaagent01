import asyncio
import os
import types

import pytest


@pytest.mark.asyncio
async def test_worker_no_longer_fetches_llm_key(monkeypatch):
    from services.conversation_worker.main import ConversationWorker

    worker = ConversationWorker()
    worker.slm.api_key = "should-be-cleared"
    await worker._ensure_llm_key()
    assert worker.slm.api_key is None

