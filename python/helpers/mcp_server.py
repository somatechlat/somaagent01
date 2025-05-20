from asyncio import current_task
import os
from typing import Annotated, Literal, Union
from urllib.parse import urlparse
from openai import BaseModel
from pydantic import Field
import uuid
import asyncio
from fastmcp import FastMCP

from agent import AgentContext, AgentContextType, UserMessage
from python.helpers.persist_chat import save_tmp_chat, remove_chat
from initialize import initialize
from python.helpers.print_style import PrintStyle
from python.helpers.task_scheduler import DeferredTask

_PRINTER = PrintStyle(italic=True, font_color="green", padding=False)


mcp_server: FastMCP = FastMCP(
    name="Agent Zero integrated MCP Server",
    instructions="""
    This server connects you to the Agent Zero instance running on the remote server.
    It exposes tools to interact with the remote Agent Zero instance.
    """,
)


class ToolResponse(BaseModel):
    status: Literal["success"] = Field(description="The status of the response", default="success")
    response: str = Field(description="The response from the remote Agent Zero Instance")
    chat_id: str = Field(description="The id of the chat this message belongs to.")


class ToolError(BaseModel):
    status: Literal["error"] = Field(description="The status of the response", default="error")
    error: str = Field(description="The error message from the remote Agent Zero Instance")
    chat_id: str = Field(description="The id of the chat this message belongs to.")


SEND_MESSAGE_DESCRIPTION = """
Send a message to the remote Agent Zero Instance.
This tool is used to send a message to the remote Agent Zero Instance connected remotely via MCP.
"""


@mcp_server.tool(
    name="send_message",
    description=SEND_MESSAGE_DESCRIPTION,
    tags={"agent_zero", "chat", "remote", "communication", "dialogue", "sse", "send", "message", "start", "new", "continue"},
    annotations={
        "remote": True,
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "title": SEND_MESSAGE_DESCRIPTION,
    },
)
async def send_message(
    message: Annotated[str, Field(description="The message to send to the remote Agent Zero Instance", title="message")],
    attachments: Annotated[list[str], Field(
        description="Optional: A list of attachments (file paths or web urls) to send to the remote Agent Zero Instance with the message. Default: Empty list",
        title="attachments",
    )] | None = None,
    chat_id: Annotated[str, Field(
        description="Optional: ID of the chat. Used to continue a chat. This value is returned in response to sending previous message. Default: Empty string",
        title="chat_id",
    )] | None = None,
    persistent_chat: Annotated[bool, Field(
        description="Optional: Whether to use a persistent chat. If true, the chat will be saved and can be continued later. Default: False.",
        title="persistent_chat",
    )] | None = None,
) -> Annotated[Union[ToolResponse, ToolError], Field(description="The response from the remote Agent Zero Instance", title="response")]:
    context: AgentContext | None = None
    if chat_id:
        context = AgentContext.get(chat_id)
        if not context:
            return ToolError(error="Chat not found", chat_id=chat_id)
        else:
            # If the chat is found, we use the persistent chat flag to determine
            # whether we should save the chat or delete it afterwards
            # If we continue a conversation, it must be persistent
            persistent_chat = True
    else:
        config = initialize()
        context = AgentContext(config=config, type=AgentContextType.MCP)

    if not message:
        return ToolError(error="Message is required", chat_id=context.id if persistent_chat else "")

    try:
        response = await _run_chat(context, message, attachments)
        if not persistent_chat:
            context.reset()
            AgentContext.remove(context.id)
            remove_chat(context.id)
        return ToolResponse(response=response, chat_id=context.id if persistent_chat else "")
    except Exception as e:
        return ToolError(error=str(e), chat_id=context.id if persistent_chat else "")


FINISH_CHAT_DESCRIPTION = """
Finish a chat with the remote Agent Zero Instance.
This tool is used to finish a persistent chat (send_message with persistent_chat=True) with the remote Agent Zero Instance connected remotely via MCP.
If you want to continue the chat, use the send_message tool instead.
Always use this tool to finish persistent chat conversations with remote Agent Zero.
"""


@mcp_server.tool(
    name="finish_chat",
    description=FINISH_CHAT_DESCRIPTION,
    tags={"agent_zero", "chat", "remote", "communication", "dialogue", "sse", "finish", "close", "end", "stop"},
    annotations={
        "remote": True,
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
        "title": FINISH_CHAT_DESCRIPTION,
    },
)
async def finish_chat(
    chat_id: Annotated[str, Field(
        description="ID of the chat to be finished. This value is returned in response to sending previous message.",
        title="chat_id",
    )]
) -> Annotated[Union[ToolResponse, ToolError], Field(description="The response from the remote Agent Zero Instance", title="response")]:
    if not chat_id:
        return ToolError(error="Chat ID is required", chat_id="")

    context = AgentContext.get(chat_id)
    if not context:
        return ToolError(error="Chat not found", chat_id=chat_id)
    else:
        context.reset()
        AgentContext.remove(context.id)
        remove_chat(context.id)
        return ToolResponse(response="Chat finished", chat_id=chat_id)


async def _run_chat(context: AgentContext, message: str, attachments: list[str] | None = None):
    async def _run_chat_wrapper(context: AgentContext, message: str, attachments: list[str] | None = None):
        # the agent instance - init in try block
        agent = None

        try:
            _PRINTER.print("MCP Chat message received")

            agent = context.streaming_agent or context.agent0

            # Pcurrent_taskhment filenames for logging
            attachment_filenames = []
            if attachments:
                for attachment in attachments:
                    if os.path.exists(attachment):
                        attachment_filenames.append(attachment)
                    else:
                        try:
                            url = urlparse(attachment)
                            if url.scheme in ["http", "https", "ftp", "ftps", "sftp"]:
                                attachment_filenames.append(attachment)
                            else:
                                _PRINTER.print(f"Skipping attachment: [{attachment}]")
                        except Exception:
                            _PRINTER.print(f"Skipping attachment: [{attachment}]")

            _PRINTER.print("User message:")
            _PRINTER.print(f"> {message}")
            if attachment_filenames:
                _PRINTER.print("Attachments:")
                for filename in attachment_filenames:
                    _PRINTER.print(f"- {filename}")

            # Log the message with message_id and attachments
            context.log.log(
                type="user",
                heading="User message",
                content=message,
                kvps={"attachments": attachment_filenames},
                id=str(uuid.uuid4()),
            )

            agent.hist_add_user_message(
                UserMessage(
                    message=message,
                    system_message=[],
                    attachments=attachment_filenames))

            # Persist after setting up the context but before running the agent
            save_tmp_chat(context)

            result = await agent.monologue()

            # Success
            _PRINTER.print(f"MCP Chat message completed: {result}")
            save_tmp_chat(context)

            return result

        except Exception as e:
            # Error
            _PRINTER.print(f"MCP Chat message failed: {e}")
            if agent:
                agent.handle_critical_exception(e)

            raise RuntimeError(f"MCP Chat message failed: {e}") from e

    deferred_task = DeferredTask(thread_name="mcp_chat_" + context.id)
    deferred_task.start_task(_run_chat_wrapper, context, message, attachments)
    asyncio.create_task(asyncio.sleep(0.1))  # Ensure background execution doesn't exit immediately on async await
    return await deferred_task.result()
