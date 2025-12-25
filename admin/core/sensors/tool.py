"""Tool Sensor.

VIBE COMPLIANT - Django ORM + ZDL pattern.
Captures every tool execution for cognitive learning.

PhD Dev: This IS action. Agent's impact on the world.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from admin.core.sensors.base import BaseSensor

logger = logging.getLogger(__name__)


class ToolSensor(BaseSensor):
    """Sensor for tool operations.
    
    Captures:
    - Tool execution start
    - Tool execution result
    - Tool errors
    - Tool selection decisions
    """
    
    SENSOR_NAME = "tool"
    TARGET_SERVICE = "somabrain"
    
    def on_event(self, event_type: str, data: Any) -> None:
        """Handle tool events."""
        self.capture(event_type, data if isinstance(data, dict) else {"data": data})
    
    def execute_start(
        self,
        tool_name: str,
        tool_input: dict,
        execution_id: str = None,
    ) -> None:
        """Capture tool execution start."""
        self.capture("execute.start", {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "tool_input": tool_input,
        })
    
    def execute_result(
        self,
        tool_name: str,
        tool_output: Any,
        execution_id: str = None,
        latency_ms: float = 0.0,
        success: bool = True,
    ) -> None:
        """Capture tool execution result."""
        self.capture("execute.result", {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "tool_output": str(tool_output)[:2000],  # Truncate
            "latency_ms": latency_ms,
            "success": success,
        })
    
    def execute_error(
        self,
        tool_name: str,
        error_type: str,
        error_message: str,
        execution_id: str = None,
    ) -> None:
        """Capture tool execution error."""
        self.capture("execute.error", {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "error_type": error_type,
            "error_message": error_message,
        })
    
    def selection(
        self,
        available_tools: list,
        selected_tool: str,
        selection_reason: str = "",
    ) -> None:
        """Capture tool selection decision."""
        self.capture("selection", {
            "available_tools": available_tools,
            "selected_tool": selected_tool,
            "selection_reason": selection_reason,
        })
