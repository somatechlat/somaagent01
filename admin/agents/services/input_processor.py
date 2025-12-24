"""Input processing for agent messages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from python.helpers import history
from python.helpers.print_style import PrintStyle


@dataclass
class UserMessage:
    """User message with optional attachments and system messages."""

    message: str
    attachments: list[str] = field(default_factory=list)
    system_message: list[str] = field(default_factory=list)


async def process_user_message(
    agent: "Agent", message: UserMessage, intervention: bool = False
) -> history.Message:
    """Process a user message and add it to agent history.

    Args:
        agent: The agent instance
        message: The user message to process
        intervention: Whether this is an intervention message

    Returns:
        The history message that was added
    """
    agent.history.new_topic()  # user message starts a new topic in history

    # Build message content
    content = agent.parse_prompt(
        "fw.user_message.md",
        message=message.message,
        attachments=message.attachments,
    )

    # Add system messages if present
    if message.system_message:
        for sys_msg in message.system_message:
            content = f"{sys_msg}\n\n{content}"

    # Add to history
    msg = agent.hist_add_message(ai=False, content=content)
    agent.last_user_message = msg

    # Log the message
    if not intervention:
        PrintStyle(font_color="cyan", padding=True).print(f"User: {message.message[:100]}...")

    return msg


async def process_intervention(agent: "Agent", message: UserMessage) -> history.Message:
    """Process an intervention message.

    Args:
        agent: The agent instance
        message: The intervention message

    Returns:
        The history message that was added
    """
    return await process_user_message(agent, message, intervention=True)
