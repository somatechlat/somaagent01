# Disable this test when OpenAI API key is not set
__test__ = False

import sys
import os
import asyncio
import models

# Adjust sys.path after imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

provider = "openai"
name = "gpt-4.1-mini"

model = models.get_chat_model(
    provider=provider,
    name=name,
    model_config=models.ModelConfig(
        type=models.ModelType.CHAT,
        provider=provider,
        name=name,
        limit_requests = 5,
        limit_input = 15000,
        limit_output = 1000,
    )
    )

async def run():
    response, reasoning = await model.unified_call(
        user_message="Tell me a joke"
    )
    print("Response: ", response)
    print("Reasoning: ", reasoning)

asyncio.run(run())