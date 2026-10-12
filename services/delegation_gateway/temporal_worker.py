"""Thin re-export — A2A Temporal worker lives in conversation_worker (WAVE 5).

There is exactly ONE Temporal worker process and ONE task queue. The A2A
workflow and ``handle_a2a`` activity were folded into
``services.conversation_worker.temporal_worker`` (same worker, same queue).
This module keeps the historical import path working and does **not**
construct a second ``Worker``.

If this file is executed directly, it starts the single conversation worker
(which registers A2AWorkflow alongside the rest) — never a second Worker.
"""

from __future__ import annotations

# Re-export the folded A2A surface for existing import sites.
from services.conversation_worker.temporal_worker import (  # noqa: F401
    A2AWorkflow,
    handle_a2a,
    main,
)

__all__ = ["A2AWorkflow", "handle_a2a", "main"]


if __name__ == "__main__":
    import asyncio

    # Same single worker + queue as services/conversation_worker/temporal_worker.py.
    asyncio.run(main())
