"""Conversation orchestration for agent message flow."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent, AgentContext

from admin.core.helpers import history


class LoopData:
    """Data container for message loop iterations."""

    def __init__(self, **kwargs):
        """Initialize the instance."""

        self.iteration = -1
        self.system: list[str] = []
        self.user_message: Optional[history.Message] = None
        self.history_output: list[history.OutputMessage] = []
        self.extras_persistent: OrderedDict[str, history.MessageContent] = OrderedDict()
        self.last_response = ""
        self.params_persistent: dict[str, Any] = {}

        # Override values with kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


async def run_message_loop(agent: "Agent", loop_data: LoopData) -> str:
    """Run the main message loop for agent processing.

    Args:
        agent: The agent instance
        loop_data: Loop state data

    Returns:
        Final response from the agent
    """
    from admin.core.helpers.extension import call_extensions
    from admin.core.helpers.print_style import PrintStyle

    printer = PrintStyle(italic=True, font_color="#b3ffd9", padding=False)

    while True:
        agent.context.streaming_agent = agent
        loop_data.iteration += 1

        # Call message_loop_start extensions
        await call_extensions(agent, "message_loop_start", loop_data=loop_data)

        try:
            # Prepare prompt
            prompt = await agent.prepare_prompt(loop_data=loop_data)

            # Call before_main_llm_call extensions
            await call_extensions(agent, "before_main_llm_call", loop_data=loop_data)

            # Define callbacks
            async def reasoning_callback(chunk: str, full: str, p=printer):
                """Execute reasoning callback.

                    Args:
                        chunk: The chunk.
                        full: The full.
                        p: The p.
                    """

                await agent.handle_intervention()
                if chunk == full:
                    p.print("Reasoning: ")
                p.stream(chunk)
                await agent.handle_reasoning_stream(full)

            async def stream_callback(chunk: str, full: str, p=printer):
                """Execute stream callback.

                    Args:
                        chunk: The chunk.
                        full: The full.
                        p: The p.
                    """

                await agent.handle_intervention()
                if chunk == full:
                    p.print("Response: ")
                p.stream(chunk)
                await agent.handle_response_stream(full)

            # Call main LLM
            agent_response, _reasoning = await agent.call_chat_model(
                messages=prompt,
                response_callback=stream_callback,
                reasoning_callback=reasoning_callback,
            )

            await agent.handle_intervention(agent_response)

            # Check for repeated response
            if loop_data.last_response == agent_response:
                agent.hist_add_ai_response(agent_response)
                warning_msg = agent.read_prompt("fw.msg_repeat.md")
                agent.hist_add_warning(message=warning_msg)
                PrintStyle(font_color="orange", padding=True).print(warning_msg)
                continue

            loop_data.last_response = agent_response

            # Process tools if present
            tool_result = await agent.process_tools(agent_response)

            if tool_result is None:
                # No tool call - this is a final response
                return agent_response

            # Tool was called, continue loop

        except Exception as e:
            agent.handle_critical_exception(e)
            break

    return loop_data.last_response


async def process_chain(
    context: "AgentContext", agent: "Agent", msg: Any, user: bool = True
) -> str:
    """Process message chain through agent hierarchy.

    Args:
        context: The agent context
        agent: The current agent
        msg: The message to process
        user: Whether this is a user message

    Returns:
        Final response
    """
    try:
        if user:
            await agent.hist_add_user_message(msg)
        else:
            agent.hist_add_tool_result(tool_name="call_subordinate", tool_result=msg)

        response = await agent.monologue()

        # Check for superior agent
        superior = agent.data.get("_superior", None)
        if superior:
            response = await process_chain(context, superior, response, False)

        return response

    except Exception as e:
        agent.handle_critical_exception(e)
        return ""