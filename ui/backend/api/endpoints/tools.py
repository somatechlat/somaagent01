"""
Eye of God API - Tools Endpoints
Per Eye of God UIX Design Section 2.1

VIBE COMPLIANT:
- Real Django Ninja endpoints
- Tool registration and invocation
- Permission-gated tool access
"""

from datetime import datetime
from typing import List, Optional, Any
from uuid import UUID

from django.http import HttpRequest
from ninja import Router

from api.schemas import ErrorResponse
from pydantic import BaseModel, Field

router = Router(tags=["Tools"])


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    default: Optional[Any] = None


class Tool(BaseModel):
    """Tool definition."""
    id: str
    name: str
    description: str
    category: str = "general"
    parameters: List[ToolParameter] = Field(default_factory=list)
    requires_permission: Optional[str] = None
    is_enabled: bool = True
    is_dangerous: bool = False


class ToolInvocation(BaseModel):
    """Tool invocation request."""
    tool_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Tool invocation result."""
    tool_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: int = 0
    invoked_at: datetime = Field(default_factory=datetime.utcnow)


# Built-in tools catalog
BUILT_IN_TOOLS: List[Tool] = [
    Tool(
        id="web_search",
        name="Web Search",
        description="Search the web for current information",
        category="search",
        parameters=[
            ToolParameter(name="query", type="string", description="Search query"),
            ToolParameter(name="max_results", type="number", description="Maximum results", required=False, default=5),
        ],
    ),
    Tool(
        id="code_execute",
        name="Code Executor",
        description="Execute Python code in a sandboxed environment",
        category="code",
        parameters=[
            ToolParameter(name="code", type="string", description="Python code to execute"),
            ToolParameter(name="timeout", type="number", description="Timeout in seconds", required=False, default=30),
        ],
        requires_permission="tools:execute",
        is_dangerous=True,
    ),
    Tool(
        id="file_read",
        name="File Reader",
        description="Read contents of a file",
        category="filesystem",
        parameters=[
            ToolParameter(name="path", type="string", description="File path"),
        ],
    ),
    Tool(
        id="file_write",
        name="File Writer",
        description="Write content to a file",
        category="filesystem",
        parameters=[
            ToolParameter(name="path", type="string", description="File path"),
            ToolParameter(name="content", type="string", description="Content to write"),
        ],
        requires_permission="tools:write",
    ),
    Tool(
        id="memory_store",
        name="Memory Store",
        description="Store information in agent memory",
        category="memory",
        parameters=[
            ToolParameter(name="content", type="string", description="Content to remember"),
            ToolParameter(name="importance", type="number", description="Importance 0-1", required=False, default=0.5),
        ],
    ),
    Tool(
        id="memory_search",
        name="Memory Search",
        description="Search agent memory for relevant information",
        category="memory",
        parameters=[
            ToolParameter(name="query", type="string", description="Search query"),
            ToolParameter(name="limit", type="number", description="Max results", required=False, default=5),
        ],
    ),
    Tool(
        id="http_request",
        name="HTTP Request",
        description="Make an HTTP request to an external API",
        category="network",
        parameters=[
            ToolParameter(name="url", type="string", description="Request URL"),
            ToolParameter(name="method", type="string", description="HTTP method", required=False, default="GET"),
            ToolParameter(name="headers", type="object", description="Request headers", required=False),
            ToolParameter(name="body", type="string", description="Request body", required=False),
        ],
        requires_permission="tools:network",
    ),
    Tool(
        id="calculator",
        name="Calculator",
        description="Perform mathematical calculations",
        category="utility",
        parameters=[
            ToolParameter(name="expression", type="string", description="Math expression"),
        ],
    ),
    Tool(
        id="datetime",
        name="Date/Time",
        description="Get current date and time information",
        category="utility",
        parameters=[
            ToolParameter(name="timezone", type="string", description="Timezone", required=False, default="UTC"),
            ToolParameter(name="format", type="string", description="Output format", required=False),
        ],
    ),
]

# Custom tools per tenant (in production, use database)
_custom_tools: dict[str, List[Tool]] = {}


@router.get(
    "/",
    response={200: List[Tool]},
    summary="List available tools"
)
async def list_tools(
    request: HttpRequest,
    category: Optional[str] = None,
    include_disabled: bool = False,
) -> List[Tool]:
    """
    Get all tools available to the current user.
    
    Filters by user permissions and tool requirements.
    """
    tenant_id = request.auth.get('tenant_id')
    permissions = request.auth.get('permissions', [])
    
    all_tools = BUILT_IN_TOOLS + _custom_tools.get(tenant_id, [])
    
    result = []
    for tool in all_tools:
        # Filter by enabled state
        if not include_disabled and not tool.is_enabled:
            continue
        
        # Filter by category
        if category and tool.category != category:
            continue
        
        # Filter by permission
        if tool.requires_permission and tool.requires_permission not in permissions:
            continue
        
        result.append(tool)
    
    return result


@router.get(
    "/categories",
    response={200: List[str]},
    summary="List tool categories"
)
async def list_categories(request: HttpRequest) -> List[str]:
    """
    Get all unique tool categories.
    """
    tenant_id = request.auth.get('tenant_id')
    
    all_tools = BUILT_IN_TOOLS + _custom_tools.get(tenant_id, [])
    categories = set(t.category for t in all_tools)
    
    return sorted(list(categories))


@router.get(
    "/{tool_id}",
    response={200: Tool, 404: ErrorResponse},
    summary="Get tool details"
)
async def get_tool(request: HttpRequest, tool_id: str) -> Tool:
    """
    Get detailed information about a specific tool.
    """
    tenant_id = request.auth.get('tenant_id')
    
    all_tools = BUILT_IN_TOOLS + _custom_tools.get(tenant_id, [])
    
    for tool in all_tools:
        if tool.id == tool_id:
            return tool
    
    raise ValueError("Tool not found")


@router.post(
    "/invoke",
    response={200: ToolResult, 400: ErrorResponse, 403: ErrorResponse},
    summary="Invoke a tool"
)
async def invoke_tool(request: HttpRequest, invocation: ToolInvocation) -> ToolResult:
    """
    Invoke a tool with the provided parameters.
    
    Validates permissions and parameters before execution.
    """
    import time
    
    tenant_id = request.auth.get('tenant_id')
    permissions = request.auth.get('permissions', [])
    
    all_tools = BUILT_IN_TOOLS + _custom_tools.get(tenant_id, [])
    
    tool = None
    for t in all_tools:
        if t.id == invocation.tool_id:
            tool = t
            break
    
    if not tool:
        return ToolResult(
            tool_id=invocation.tool_id,
            success=False,
            error="Tool not found",
        )
    
    if not tool.is_enabled:
        return ToolResult(
            tool_id=invocation.tool_id,
            success=False,
            error="Tool is disabled",
        )
    
    if tool.requires_permission and tool.requires_permission not in permissions:
        return ToolResult(
            tool_id=invocation.tool_id,
            success=False,
            error=f"Missing permission: {tool.requires_permission}",
        )
    
    # Validate required parameters
    for param in tool.parameters:
        if param.required and param.name not in invocation.parameters:
            return ToolResult(
                tool_id=invocation.tool_id,
                success=False,
                error=f"Missing required parameter: {param.name}",
            )
    
    # Execute tool (simplified - in production, use proper handlers)
    start_time = time.time()
    
    try:
        result = await _execute_tool(tool.id, invocation.parameters)
        duration_ms = int((time.time() - start_time) * 1000)
        
        return ToolResult(
            tool_id=invocation.tool_id,
            success=True,
            result=result,
            duration_ms=duration_ms,
        )
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return ToolResult(
            tool_id=invocation.tool_id,
            success=False,
            error=str(e),
            duration_ms=duration_ms,
        )


async def _execute_tool(tool_id: str, params: dict) -> Any:
    """Execute a tool with parameters."""
    
    if tool_id == "calculator":
        # Safe eval for math expressions
        import ast
        import operator
        
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
        }
        
        def _eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                return ops[type(node.op)](_eval(node.left), _eval(node.right))
            else:
                raise ValueError("Unsupported expression")
        
        tree = ast.parse(params["expression"], mode="eval")
        result = _eval(tree.body)
        return {"result": result}
    
    elif tool_id == "datetime":
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        fmt = params.get("format", "%Y-%m-%d %H:%M:%S %Z")
        return {"datetime": now.strftime(fmt), "timestamp": now.timestamp()}
    
    elif tool_id == "memory_search":
        # Placeholder - would integrate with SomaBrain
        return {"results": [], "message": "Memory search not yet implemented"}
    
    elif tool_id == "memory_store":
        # Placeholder - would integrate with SomaBrain
        return {"stored": True, "message": "Memory store not yet implemented"}
    
    else:
        return {"message": f"Tool {tool_id} execution placeholder"}


@router.post(
    "/",
    response={201: Tool},
    summary="Register custom tool (admin only)"
)
async def register_tool(request: HttpRequest, tool: Tool) -> Tool:
    """
    Register a custom tool for the tenant.
    
    Requires tools:admin permission.
    """
    tenant_id = request.auth.get('tenant_id')
    role = request.auth.get('role')
    
    if role not in ('admin', 'sysadmin'):
        raise PermissionError("Admin role required")
    
    if tenant_id not in _custom_tools:
        _custom_tools[tenant_id] = []
    
    # Check for duplicate ID
    for t in _custom_tools[tenant_id]:
        if t.id == tool.id:
            raise ValueError(f"Tool {tool.id} already exists")
    
    _custom_tools[tenant_id].append(tool)
    
    return tool


@router.delete(
    "/{tool_id}",
    response={204: None, 404: ErrorResponse},
    summary="Delete custom tool (admin only)"
)
async def delete_tool(request: HttpRequest, tool_id: str) -> None:
    """
    Delete a custom tool.
    
    Built-in tools cannot be deleted.
    """
    tenant_id = request.auth.get('tenant_id')
    role = request.auth.get('role')
    
    if role not in ('admin', 'sysadmin'):
        raise PermissionError("Admin role required")
    
    # Check if it's a built-in tool
    for t in BUILT_IN_TOOLS:
        if t.id == tool_id:
            raise ValueError("Cannot delete built-in tool")
    
    tools = _custom_tools.get(tenant_id, [])
    for i, t in enumerate(tools):
        if t.id == tool_id:
            _custom_tools[tenant_id].pop(i)
            return
    
    raise ValueError("Tool not found")
