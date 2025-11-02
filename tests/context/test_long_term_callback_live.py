import json

import pytest

from agent import AgentContext

from . import helpers

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures("event_loop")
async def test_long_term_fact_is_recalled():
    helpers.require_live()
    context = helpers.create_context()

    try:
        fact_summary = (
            "Billing API requires OAuth scope https://www.googleapis.com/auth/cloud-billing"
        )
        diversion = "Switch gears and outline three marketing tactics for the Wisteria launch."
        question = "What OAuth scope does the Billing API require?"

        await helpers.seed_memory(
            context.agent0,
            text=fact_summary,
            metadata={"topic": "billing", "importance": 5},
        )
        await helpers.run_turn(context, diversion)
        reply_question = await helpers.run_turn(context, question)

        snap = helpers.snapshot(context.agent0)
        window_text = snap["window"].get("text", "").lower()
        expected_scope = "https://www.googleapis.com/auth/cloud-billing"
        scope_lower = expected_scope.lower()
        reply_lower = reply_question.lower()
        assert (
            scope_lower in reply_lower or scope_lower in window_text
        ), "agent failed to recall the stored Billing API scope"

        extras = snap["extras"]
        combined_extras = "\n".join(
            filter(
                None,
                [
                    (
                        json.dumps(extras["memories"], ensure_ascii=False)
                        if extras["memories"]
                        else ""
                    ),
                    (
                        json.dumps(extras["solutions"], ensure_ascii=False)
                        if extras["solutions"]
                        else ""
                    ),
                ],
            )
        ).lower()
        if combined_extras.strip():
            assert scope_lower in combined_extras, "memory recall extras missing the OAuth scope"

        helpers.record_artifact(
            "long_term_callback",
            {
                "turns": [fact_summary, diversion, question],
                "responses": [reply_question],
                "context_window": snap["window"],
                "extras": extras,
            },
        )

    finally:
        AgentContext.remove(context.id)
