"""Tool selection and execution for agent."""
from __future__ import annotations

import importlib
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent import Agent

from python.helpers import extract_tools
from python.helpers.print_style import PrintStyle


def get_tool(agent: "Agent", name: str, args: dict, message: str):
    """Get a tool instance by name.
    
    Note: This function is provided for external use. The Agent class has its own
    get_tool() method that includes profile-specific tool loading.
    
    Args:
        agent: The agent instance
        name: Tool name
        args: Tool arguments
        message: Original message containing tool request
        
    Returns:
        Tool instance or None if not found
        
    Raises:
        ImportError: If tool module cannot be loaded (logged, not raised)
    """
    from python.tools.base_tool import BaseTool
    
    # Try to import the tool module
    try:
        module = importlib.import_module(f"python.tools.{name}")
        tool_class = getattr(module, name.title().replace("_", ""), None)
        if tool_class and issubclass(tool_class, BaseTool):
            return tool_class(agent=agent, name=name, args=args, message=message)
        else:
            PrintStyle(font_color="orange", padding=False).print(
                f"Tool '{name}' found but class not valid BaseTool subclass"
            )
    except ImportError as e:
        PrintStyle(font_color="orange", padding=False).print(f"Tool module '{name}' not found: {e}")
    except AttributeError as e:
        PrintStyle(font_color="orange", padding=False).print(f"Tool class in '{name}' not accessible: {e}")
    
    return None


async def process_tool_request(agent: "Agent", msg: str) -> Optional[dict[str, Any]]:
    """Process tool requests from agent message.
    
    Args:
        agent: The agent instance
        msg: The message potentially containing tool requests
        
    Returns:
        Tool result dict or None if no tools found
    """
    # Parse tool request from message
    tool_request = extract_tools.json_parse_dirty(msg)
    
    if not tool_request:
        return None
    
    tool_name = tool_request.get("tool_name", "")
    tool_args = tool_request.get("tool_args", {})
    
    if not tool_name:
        return None
    
    # Get and execute tool
    tool = get_tool(agent, tool_name, tool_args, msg)
    
    if not tool:
        PrintStyle(font_color="red", padding=True).print(f"Tool not found: {tool_name}")
        return {"error": f"Tool '{tool_name}' not found"}
    
    try:
        result = await tool.execute()
        return {"tool_name": tool_name, "result": result}
    except Exception as e:
        PrintStyle(font_color="red", padding=True).print(f"Tool error: {e}")
        return {"tool_name": tool_name, "error": str(e)}


def extract_tool_from_response(response: str) -> Optional[dict[str, Any]]:
    """Extract tool request from LLM response.
    
    Args:
        response: The LLM response text
        
    Returns:
        Parsed tool request or None
    """
    return extract_tools.json_parse_dirty(response)
