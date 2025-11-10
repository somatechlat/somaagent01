import json

import pytest

from agent import AgentContext

from . import helpers

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures("event_loop")
async def test_conflicting_directives_favor_latest_instruction():
    helpers.require_live()
    context = helpers.create_context()

    try:
        initial_directive = "Please schedule the staging deployment for 17:00 UTC and confirm."
        correction = "Actually cancel the staging deployment. Instead, prepare the production rollout checklist."

        await helpers.run_turn(context, initial_directive)
        reply_correction = await helpers.run_turn(context, correction)

        snap = helpers.snapshot(context.agent0)
        window_text = snap["window"].get("text", "").lower()
        assert window_text, "context window should not be empty after conflicting directives"
        assert (
            "cancel" in window_text
        ), "latest cancellation directive not emphasized in context window"
        assert (
            "production" in window_text or "prod" in window_text
        ), "updated production focus missing from context window"

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
            assert (
                "cancel" in combined_extras or "production" in combined_extras
            ), "memory recall extras still biased toward the initial staging instruction"

        helpers.record_artifact(
            "conflicting_directives",
            {
                "turns": [initial_directive, correction],
                "responses": [reply_correction],
                "context_window": snap["window"],
                "extras": extras,
            },
        )

    finally:
        AgentContext.remove(context.id)
