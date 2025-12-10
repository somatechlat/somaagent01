"""Response generation for agent LLM calls."""

from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from langchain_core.messages import BaseMessage

import models


def get_chat_model(agent: "Agent"):
    """Get the chat model for the agent.

    Args:
        agent: The agent instance

    Returns:
        The configured chat model
    """
    return models.get_chat_model(
        agent.config.chat_model.provider,
        agent.config.chat_model.name,
        **agent.config.chat_model.build_kwargs(),
    )


def get_utility_model(agent: "Agent"):
    """Get the utility model for the agent.

    Args:
        agent: The agent instance

    Returns:
        The configured utility model
    """
    return models.get_chat_model(
        agent.config.utility_model.provider,
        agent.config.utility_model.name,
        **agent.config.utility_model.build_kwargs(),
    )


async def call_chat_model(
    agent: "Agent",
    messages: list[BaseMessage],
    response_callback: Optional[Callable] = None,
    reasoning_callback: Optional[Callable] = None,
) -> tuple[str, str]:
    """Call the chat model with messages.

    Args:
        agent: The agent instance
        messages: List of messages to send
        response_callback: Optional callback for response streaming
        reasoning_callback: Optional callback for reasoning streaming

    Returns:
        Tuple of (response, reasoning)
    """
    model = get_chat_model(agent)

    response, reasoning = await models.call_model(
        model=model,
        messages=messages,
        response_callback=response_callback,
        reasoning_callback=reasoning_callback,
        rate_limiter_callback=agent.rate_limiter_callback,
    )

    return response, reasoning


async def call_utility_model(
    agent: "Agent",
    system: str,
    msg: str,
    callback: Optional[Callable] = None,
) -> str:
    """Call the utility model for auxiliary tasks.

    Args:
        agent: The agent instance
        system: System prompt
        msg: User message
        callback: Optional streaming callback

    Returns:
        Model response
    """
    model = get_utility_model(agent)

    call_data = {"callback": callback}

    async def stream_callback(chunk: str, total: str):
        if call_data["callback"]:
            await call_data["callback"](chunk)

    response, _ = await models.call_model(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": msg},
        ],
        response_callback=stream_callback if callback else None,
    )

    return response


async def apply_neuromodulation(agent: "Agent", response: str) -> str:
    """Apply neuromodulation effects to response based on cognitive state.

    Adjusts response characteristics based on current neuromodulator levels:
    - High dopamine: More exploratory/creative responses
    - High serotonin: More patient/empathetic responses
    - High noradrenaline: More focused/alert responses

    Args:
        agent: The agent instance
        response: The original response

    Returns:
        Response (neuromodulation affects agent behavior, not text directly)
    """
    # Neuromodulation affects cognitive parameters, not the response text itself
    # The actual modulation happens in cognitive.apply_neuromodulation()
    # This function exists for potential future response-level adjustments
    neuromods = agent.data.get("neuromodulators", {})

    # Log neuromodulator state for observability
    if neuromods:
        from python.helpers.print_style import PrintStyle

        dopamine = neuromods.get("dopamine", 0.4)
        serotonin = neuromods.get("serotonin", 0.5)
        if dopamine > 0.7 or serotonin > 0.7:
            PrintStyle(font_color="cyan", padding=False).print(
                f"Neuromodulation active: dopamine={dopamine:.2f}, serotonin={serotonin:.2f}"
            )

    return response
