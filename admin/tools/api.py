"""Tools API - Agent tool management.


Tool registration and execution for agents.

- PhD Dev: Tool architecture, MCP
- Security Auditor: Tool sandboxing
- DevOps: Tool execution limits
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["tools"])
logger = logging.getLogger(__name__)


async def _load_registry():
    """Build a ToolRegistry populated with the real built-in tools."""
    from services.tool_executor.tool_registry import ToolRegistry

    registry = ToolRegistry()
    await registry.load_all_tools()
    return registry


# =============================================================================
# SCHEMAS
# =============================================================================


class Tool(BaseModel):
    """Tool definition."""

    tool_id: str
    name: str
    description: str
    category: str  # web, code, file, api, custom
    provider: str  # system, mcp, custom
    parameters: dict
    is_enabled: bool = True
    requires_approval: bool = False


class ToolExecution(BaseModel):
    """Tool execution record."""

    execution_id: str
    tool_id: str
    agent_id: str
    conversation_id: str
    status: str  # pending, approved, running, success, failed
    input_params: dict
    output: Optional[dict] = None
    started_at: str
    completed_at: Optional[str] = None


# =============================================================================
# ENDPOINTS - Tool Registry
# =============================================================================


@router.get(
    "",
    summary="List tools",
    auth=AuthBearer(),
)
async def list_tools(
    request,
    category: Optional[str] = None,
    provider: Optional[str] = None,
    enabled_only: bool = True,
) -> dict:
    """List available tools.

    PhD Dev: Tool catalog.
    """
    registry = await _load_registry()
    tools = []
    for definition in registry.list():
        schema = definition.handler.input_schema() or {}
        tools.append(
            Tool(
                tool_id=definition.name,
                name=definition.name,
                description=definition.description or "",
                category="custom",
                provider="system",
                parameters=schema,
                requires_approval=False,
            ).dict()
        )

    return {
        "tools": tools,
        "total": len(tools),
    }


@router.post(
    "",
    response=Tool,
    summary="Register tool",
    auth=AuthBearer(),
)
async def register_tool(
    request,
    name: str,
    description: str,
    category: str,
    parameters: dict,
    provider: str = "custom",
    requires_approval: bool = False,
) -> Tool:
    """Register a custom tool.

    PhD Dev: Custom tool creation.
    """
    raise HttpError(501, "Custom tool registration is not implemented: no persistent tool store.")


@router.get(
    "/{tool_id}",
    response=Tool,
    summary="Get tool",
    auth=AuthBearer(),
)
async def get_tool(request, tool_id: str) -> Tool:
    """Get tool details."""
    registry = await _load_registry()
    definition = registry.get(tool_id)
    if definition is None:
        raise HttpError(404, f"Tool '{tool_id}' not found")

    schema = definition.handler.input_schema() or {}
    return Tool(
        tool_id=definition.name,
        name=definition.name,
        description=definition.description or "",
        category="custom",
        provider="system",
        parameters=schema,
    )


@router.patch(
    "/{tool_id}",
    summary="Update tool",
    auth=AuthBearer(),
)
async def update_tool(
    request,
    tool_id: str,
    is_enabled: Optional[bool] = None,
    requires_approval: Optional[bool] = None,
) -> dict:
    """Update tool settings."""
    raise HttpError(501, "Tool settings update is not implemented: no persistent tool store.")


@router.delete(
    "/{tool_id}",
    summary="Delete tool",
    auth=AuthBearer(),
)
async def delete_tool(request, tool_id: str) -> dict:
    """Delete a custom tool."""
    raise HttpError(501, "Tool deletion is not implemented: no persistent tool store.")


# =============================================================================
# ENDPOINTS - Tool Execution
# =============================================================================


@router.post(
    "/{tool_id}/execute",
    summary="Execute tool",
    auth=AuthBearer(),
)
async def execute_tool(
    request,
    tool_id: str,
    agent_id: str,
    conversation_id: str,
    parameters: dict,
) -> dict:
    """Execute a tool.

    PhD Dev: Tool invocation.
    DevOps: Execution limits.
    """
    registry = await _load_registry()
    definition = registry.get(tool_id)
    if definition is None:
        raise HttpError(404, f"Tool '{tool_id}' not found")

    result = await definition.run(parameters)
    return {
        "execution_id": f"{tool_id}:{agent_id}:{conversation_id}",
        "tool_id": tool_id,
        "status": "success",
        "output": result,
    }


@router.get(
    "/executions/{execution_id}",
    response=ToolExecution,
    summary="Get execution",
    auth=AuthBearer(),
)
async def get_execution(
    request,
    execution_id: str,
) -> ToolExecution:
    """Get execution status."""
    raise HttpError(501, "Execution history is not implemented: no execution store.")


@router.post(
    "/executions/{execution_id}/approve",
    summary="Approve execution",
    auth=AuthBearer(),
)
async def approve_execution(
    request,
    execution_id: str,
) -> dict:
    """Approve a pending execution.

    Security Auditor: Human-in-the-loop.
    """
    raise HttpError(501, "Execution approval is not implemented: no execution store.")


@router.post(
    "/executions/{execution_id}/reject",
    summary="Reject execution",
    auth=AuthBearer(),
)
async def reject_execution(
    request,
    execution_id: str,
    reason: str,
) -> dict:
    """Reject a pending execution."""
    raise HttpError(501, "Execution rejection is not implemented: no execution store.")


# =============================================================================
# ENDPOINTS - MCP Servers
# =============================================================================


@router.get(
    "/mcp/servers",
    summary="List MCP servers",
    auth=AuthBearer(),
)
async def list_mcp_servers(request) -> dict:
    """List connected MCP servers.

    PhD Dev: MCP integration.
    """
    return {
        "servers": [],
        "total": 0,
    }


@router.post(
    "/mcp/servers",
    summary="Register MCP server",
    auth=AuthBearer(),
)
async def register_mcp_server(
    request,
    name: str,
    transport: str,  # stdio, sse
    command: Optional[str] = None,
    url: Optional[str] = None,
) -> dict:
    """Register an MCP server."""
    raise HttpError(501, "MCP server registration is not implemented: no MCP client host.")


@router.get(
    "/mcp/servers/{server_id}/tools",
    summary="List MCP tools",
    auth=AuthBearer(),
)
async def list_mcp_tools(
    request,
    server_id: str,
) -> dict:
    """List tools from an MCP server."""
    return {
        "server_id": server_id,
        "tools": [],
        "total": 0,
    }
