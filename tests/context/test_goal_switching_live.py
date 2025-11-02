import json

import pytest

from agent import AgentContext

from . import helpers

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures("event_loop")
async def test_goal_switching_context_window_is_sequenced():
    """Optional integration test that exercises a goal-switching dialogue against a live agent."""
    helpers.require_live()

    context = helpers.create_context()

    try:
        topic_a = "Draft a launch checklist for the WISTERIA marketing push."
        topic_b = (
            "Now ignore marketing and instead review this kubectl rollout status."  # goal switch
        )

        # First turn establishes marketing context
        reply_a = await helpers.run_turn(context, topic_a)
        window_a = context.agent0.get_data(context.agent0.DATA_NAME_CTX_WINDOW)
        assert window_a, "context window missing after first turn"
        assert topic_a in window_a["text"], "first topic not present in context window"

        # Second turn pivots to DevOps task
        reply_b = await helpers.run_turn(context, topic_b)
        snapshot = helpers.snapshot(context.agent0)
        window_b = snapshot["window"]
        assert window_b, "context window missing after goal switch"
        text_b = window_b.get("text", "")
        assert topic_b in text_b, "goal-switch prompt not surfaced to LLM"

        # Ensure the latest user topic appears after the first topic in the assembled prompt
        first_index = text_b.find(topic_a)
        second_index = text_b.find(topic_b)
        assert second_index != -1, "expected to find second topic in context"
        if first_index != -1:
            assert second_index > first_index, "second topic should appear later than initial topic"

        # Guard against stale memory fragments overwhelming the prompt by checking the recall extras themselves
        extras = snapshot["extras"]
        memories_block = extras["memories"]
        solutions_block = extras["solutions"]

        def _normalize_blob(blob) -> str:
            if blob is None:
                return ""
            if isinstance(blob, str):
                return blob
            try:
                return json.dumps(blob)
            except TypeError:
                return str(blob)

        memories_text = _normalize_blob(memories_block).lower()
        solutions_text = _normalize_blob(solutions_block).lower()
        combined_text = "\n".join(filter(None, [memories_text, solutions_text]))

        if combined_text.strip():
            assert (
                "kubectl" in combined_text or "rollout" in combined_text
            ), "memory recall extras should surface the new DevOps topic"

            marketing_hits = combined_text.count("wisteria")
            kubectl_hits = combined_text.count("kubectl") + combined_text.count("rollout")
            assert (
                marketing_hits <= kubectl_hits + 1
            ), "recall extras still biased toward the previous marketing topic"

        # Basic sanity: context token metadata tracks prompt size
        assert window_b.get("tokens", 0) > 0, "token count should be populated"

        helpers.record_artifact(
            "goal_switch",
            {
                "turns": [topic_a, topic_b],
                "responses": [reply_a, reply_b],
                "context_window": window_b,
                "extras": extras,
            },
        )

    finally:
        AgentContext.remove(context.id)
