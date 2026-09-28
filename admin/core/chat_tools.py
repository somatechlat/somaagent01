"""Chat tool discovery, extraction, and execution."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def discover_tools(tool_registry: Optional[Any]) -> List[Dict[str, Any]]:
    """Build the list of tool definitions to pass to the LLM."""
    tools_for_llm: List[Dict[str, Any]] = []
    if tool_registry:
        for tool_def in tool_registry.list():
            handler = tool_def.handler
            schema = handler.input_schema() if handler else None
            if schema:
                tools_for_llm.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool_def.name,
                            "description": tool_def.description or tool_def.name,
                            "parameters": schema,
                        },
                    }
                )
    return tools_for_llm


def extract_tool_calls(response_text: str) -> List[Dict[str, str]]:
    """Extract tool calls from LLM response.

    This is a simple parser for tool call patterns in the response.
    Full implementation should use the LLM's native tool_call format
    (e.g., OpenAI's message.tool_calls).

    Supports two formats:
    1. Markdown code block: ```tool:{name}\n{json_args}\n```
    2. XML tag: <tool name="{name}">{json_args}</tool>
    """
    tool_calls: List[Dict[str, str]] = []

    # Format 1: Markdown code blocks with tool: prefix
    pattern1 = r"```tool:(\w+)\s*\n(.*?)\n```"
    for match in re.finditer(pattern1, response_text, re.DOTALL):
        name = match.group(1)
        args_raw = match.group(2).strip()
        try:
            # Validate it's valid JSON
            json.loads(args_raw)
            tool_calls.append({"name": name, "arguments": args_raw})
        except json.JSONDecodeError:
            tool_calls.append({"name": name, "arguments": json.dumps({"raw": args_raw})})

    # Format 2: XML-style tool tags
    pattern2 = r'<tool\s+name="(\w+)">\s*(.*?)\s*</tool>'
    for match in re.finditer(pattern2, response_text, re.DOTALL):
        name = match.group(1)
        args_raw = match.group(2).strip()
        try:
            json.loads(args_raw)
            tool_calls.append({"name": name, "arguments": args_raw})
        except json.JSONDecodeError:
            tool_calls.append({"name": name, "arguments": json.dumps({"raw": args_raw})})

    return tool_calls


async def execute_tools(
    tool_calls: List[Dict[str, str]],
    tool_registry: Optional[Any],
) -> Tuple[List[str], List[str]]:
    """Execute extracted tool calls against the registry.

    Returns a tuple of (tools_called_names, error_messages).
    """
    tools_called: List[str] = []
    errors: List[str] = []
    if not tool_registry:
        return tools_called, errors

    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        tool_def = tool_registry.get(tool_name)
        if tool_def:
            try:
                args = json.loads(tool_call.get("arguments", "{}"))
                tool_result = await tool_def.run(args)
                tools_called.append(tool_name)
                logger.info("Tool executed: %s → %s", tool_name, tool_result.get("status", "ok"))
            except Exception as tool_exc:
                logger.error("Tool execution failed: %s", tool_exc)
                errors.append(f"Tool {tool_name} failed: {tool_exc}")

    return tools_called, errors


class ChatToolManager:
    """Manages tool discovery, extraction, and execution for a chat turn."""

    def __init__(self, tool_registry: Optional[Any] = None) -> None:
        self._tool_registry = tool_registry

    def list_for_llm(self) -> List[Dict[str, Any]]:
        """Return tools formatted for the LLM API."""
        return discover_tools(self._tool_registry)

    def extract_from_response(self, response_text: str) -> List[Dict[str, str]]:
        """Extract tool calls from an LLM response."""
        return extract_tool_calls(response_text)

    async def run_extracted(self, response_text: str) -> Tuple[List[str], List[str]]:
        """Extract and execute any tool calls found in the response."""
        tool_calls = self.extract_from_response(response_text)
        return await execute_tools(tool_calls, self._tool_registry)


__all__ = [
    "ChatToolManager",
    "discover_tools",
    "extract_tool_calls",
    "execute_tools",
]
