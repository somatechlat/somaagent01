import os

import pytest

import models

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="requires OpenAI credentials to exercise the live rate limiter",
)


@pytest.mark.asyncio
async def test_rate_limiter_unified_call_smoke() -> None:
    provider = "openai"
    name = "gpt-4.1-mini"

    model = models.get_chat_model(
        provider=provider,
        name=name,
        model_config=models.ModelConfig(
            type=models.ModelType.CHAT,
            provider=provider,
            name=name,
            limit_requests=5,
            limit_input=15000,
            limit_output=1000,
        ),
    )

    response, reasoning = await model.unified_call(user_message="Tell me a joke")
    assert isinstance(response, str)
    assert reasoning is not None
