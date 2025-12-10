"""Tool orchestration for conversation worker.

Handles tool execution, result processing, and model-led tool orchestration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from prometheus_client import Counter

LOGGER = logging.getLogger(__name__)

# Metrics
TOOL_EXECUTION_COUNTER = Counter(
    "conversation_worker_tool_executions_total",
    "Total tool executions by conversation worker",
    labelnames=("tool_name", "result"),
)


class ToolOrchestrator:
    """Orchestrate tool execution for conversation worker."""

    def __init__(self, tool_registry: Any, event_bus: Any, publisher: Any):
        """Initialize tool orchestrator.

        Args:
            tool_registry: Registry of available tools
            event_bus: Kafka event bus for tool requests
            publisher: Durable publisher for results
        """
        self.tool_registry = tool_registry
        self.event_bus = event_bus
        self.publisher = publisher
        self._pending_results: Dict[str, Any] = {}

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible tool schemas for all registered tools.

        Returns:
            List of tool schemas in OpenAI function calling format
        """
        tools = []
        for tool_def in self.tool_registry.list_tools():
            schema = {
                "type": "function",
                "function": {
                    "name": tool_def.name,
                    "description": tool_def.description or f"Execute {tool_def.name}",
                    "parameters": tool_def.parameters or {"type": "object", "properties": {}},
                },
            }
            tools.append(schema)
        return tools

    async def execute_tool(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        session_id: str,
        correlation_id: str,
        tenant: str,
    ) -> Dict[str, Any]:
        """Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            session_id: Session ID for context
            correlation_id: Correlation ID for tracking
            tenant: Tenant identifier

        Returns:
            Tool execution result
        """
        try:
            # Check if tool exists
            tool_def = self.tool_registry.get_tool(tool_name)
            if not tool_def:
                TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, result="not_found").inc()
                return {
                    "error": f"Tool '{tool_name}' not found",
                    "tool_name": tool_name,
                }

            # Publish tool execution request
            request_payload = {
                "type": "tool_request",
                "tool_name": tool_name,
                "tool_args": tool_args,
                "session_id": session_id,
                "correlation_id": correlation_id,
                "tenant": tenant,
            }

            await self.publisher.publish(
                topic="tool.requests",
                payload=request_payload,
            )

            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, result="submitted").inc()

            return {
                "status": "submitted",
                "tool_name": tool_name,
                "correlation_id": correlation_id,
            }

        except Exception as e:
            LOGGER.error(f"Tool execution failed: {tool_name} - {e}")
            TOOL_EXECUTION_COUNTER.labels(tool_name=tool_name, result="error").inc()
            return {
                "error": str(e),
                "tool_name": tool_name,
            }

    async def wait_for_result(
        self,
        correlation_id: str,
        timeout: float = 30.0,
    ) -> Optional[Dict[str, Any]]:
        """Wait for a tool execution result.

        Args:
            correlation_id: Correlation ID to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            Tool result or None if timeout
        """
        import asyncio

        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if correlation_id in self._pending_results:
                result = self._pending_results.pop(correlation_id)
                return result
            await asyncio.sleep(0.1)

        LOGGER.warning(f"Timeout waiting for tool result: {correlation_id}")
        return None

    def receive_result(self, correlation_id: str, result: Dict[str, Any]) -> None:
        """Receive a tool execution result.

        Args:
            correlation_id: Correlation ID for the result
            result: The tool execution result
        """
        self._pending_results[correlation_id] = result

    def parse_tool_calls(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response.

        Args:
            response: LLM response potentially containing tool calls

        Returns:
            List of parsed tool calls
        """
        tool_calls = []

        # Handle OpenAI-style tool calls
        if "tool_calls" in response:
            for call in response["tool_calls"]:
                tool_calls.append(
                    {
                        "id": call.get("id"),
                        "name": call.get("function", {}).get("name"),
                        "arguments": call.get("function", {}).get("arguments", {}),
                    }
                )

        # Handle function_call style (legacy)
        elif "function_call" in response:
            fc = response["function_call"]
            tool_calls.append(
                {
                    "id": None,
                    "name": fc.get("name"),
                    "arguments": fc.get("arguments", {}),
                }
            )

        return tool_calls
