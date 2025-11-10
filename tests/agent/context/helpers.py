import json
import os
import time
from typing import Any, Dict, Optional

import pytest

from agent import Agent, AgentContext, UserMessage
from initialize import initialize_agent
from python.helpers.memory import Memory

CONTEXT_ENV_FLAG = "CONTEXT_QA_ENABLE"
DEFAULT_TIMEOUT = float(os.getenv("CONTEXT_QA_TIMEOUT", "180"))


def require_live() -> None:
    if not os.getenv(CONTEXT_ENV_FLAG):
        pytest.skip(f"set {CONTEXT_ENV_FLAG}=1 to run live context QA tests")


def create_context() -> AgentContext:
    config = initialize_agent()
    return AgentContext(config=config)


async def run_turn(context: AgentContext, text: str, *, timeout: Optional[float] = None) -> str:
    task = context.communicate(UserMessage(text))
    return await task.result(timeout=timeout or DEFAULT_TIMEOUT)


def snapshot(agent: Agent) -> Dict[str, Any]:
    window = agent.get_data(agent.DATA_NAME_CTX_WINDOW) or {"text": "", "tokens": 0}
    extras = (
        getattr(agent.loop_data, "extras_persistent", {})
        if getattr(agent, "loop_data", None)
        else {}
    )
    memories = extras.get("memories") if isinstance(extras, dict) else None
    solutions = extras.get("solutions") if isinstance(extras, dict) else None
    return {
        "window": window,
        "extras": {
            "memories": memories,
            "solutions": solutions,
        },
    }


def record_artifact(slug: str, payload: Dict[str, Any]) -> None:
    artifact_dir = os.getenv("CONTEXT_QA_ARTIFACT_DIR")
    if not artifact_dir:
        return
    os.makedirs(artifact_dir, exist_ok=True)
    timestamp = int(time.time())
    path = os.path.join(artifact_dir, f"{slug}_{timestamp}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


async def seed_memory(
    agent: Agent,
    text: str,
    *,
    area: str = Memory.Area.MAIN.value,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Insert a memory directly into the agent's backing store for deterministic tests."""
    db = await Memory.get(agent)
    meta = {"area": area, **(metadata or {})}
    memory_id = await db.insert_text(text, meta)
    return memory_id
