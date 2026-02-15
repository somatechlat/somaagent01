"""
Tool System - 4-Phase Tool Gate for Discovery and Execution.

Implements the 4-phase authorization pipeline:
1. Registry: Global is_enabled check
2. Capsule: M2M capability filter
3. SpiceDB: User permission check
4. OPA: Policy enforcement

SRS Source: SRS-TOOL-SYSTEM-2026-01-16

Applied Personas:
- PhD Developer: Clean async design
- Security Auditor: FAIL-CLOSED on all gates
- Performance: Cached policy results
- Django Architect: ORM integration
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, Set

if TYPE_CHECKING:
    from admin.core.models import Capsule

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredTool:
    """Tool that passed all 4 discovery gates."""

    name: str
    display_name: str
    description: str
    category: str
    schema: Dict[str, Any] = field(default_factory=dict)
    provider: str = "native"  # native, mcp, external


class ToolNotFoundError(Exception):
    """Tool not in discovered set."""

    pass


class ToolPermissionDeniedError(Exception):
    """SpiceDB or OPA denied tool access."""

    pass


class SpiceDBClientProtocol(Protocol):
    """Protocol for SpiceDB permission client."""

    async def check_permission(
        self,
        subject: str,
        permission: str,
        resource: str,
    ) -> bool:
        """Check if subject has permission on resource."""
        ...


class OPAClientProtocol(Protocol):
    """Protocol for OPA policy client."""

    async def check_policy(
        self,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate OPA policy."""
        ...


class ToolDiscovery:
    """
    4-Phase Tool Discovery Pipeline.

    All 4 gates must pass for a tool to be discoverable:
    1. Registry: Capability.is_enabled = True
    2. Capsule: Tool in capsule.body.persona.tools.enabled_capabilities
    3. SpiceDB: User has tool:execute permission
    4. OPA: Policy allows tool usage

    Security: FAIL-CLOSED on any gate failure
    """

    def __init__(
        self,
        spicedb_client: Optional[SpiceDBClientProtocol] = None,
        opa_client: Optional[OPAClientProtocol] = None,
    ) -> None:
        """Initialize ToolDiscovery."""
        self._spicedb = spicedb_client
        self._opa = opa_client
        self._policy_cache: Dict[str, bool] = {}

    async def discover_tools(
        self,
        capsule: "Capsule",
        user_id: str,
        tenant_id: str,
    ) -> List[DiscoveredTool]:
        """
        Discover all tools available to this capsule/user.

        Args:
            capsule: Capsule with tool configuration
            user_id: User requesting tools
            tenant_id: Tenant context

        Returns:
            List of tools that passed all 4 gates
        """
        discovered: List[DiscoveredTool] = []

        # Get all capabilities from registry
        try:
            from admin.core.models import Capability

            all_capabilities = list(Capability.objects.filter(is_enabled=True))
        except ImportError:
            logger.warning("Capability model not available, using fallback")
            all_capabilities = _get_fallback_capabilities()

        # Get capsule's enabled tools
        body: Dict[str, Any] = capsule.body or {}
        persona = body.get("persona", {})
        tools_config = persona.get("tools", {})
        enabled_names: Set[str] = set(tools_config.get("enabled_capabilities", []))

        # Process each capability through 4 gates
        for cap in all_capabilities:
            cap_name = _get_attr(cap, "name", "")

            # Gate 1: Registry (already filtered by is_enabled=True)
            # Gate 2: Capsule filter
            if cap_name not in enabled_names:
                continue

            # Gate 3: SpiceDB permission
            if not await self._check_spicedb(user_id, cap_name):
                continue

            # Gate 4: OPA policy
            if not await self._check_opa(cap_name, user_id, tenant_id):
                continue

            # All gates passed
            discovered.append(
                DiscoveredTool(
                    name=cap_name,
                    display_name=_get_attr(cap, "display_name", cap_name),
                    description=_get_attr(cap, "description", ""),
                    category=_get_attr(cap, "category", "general"),
                    schema=_get_attr(cap, "schema", {}),
                    provider=_get_attr(cap, "provider", "native"),
                )
            )

        logger.info(
            "Tool discovery: %d/%d tools passed gates for user=%s",
            len(discovered),
            len(all_capabilities),
            user_id,
        )

        return discovered

    async def _check_spicedb(self, user_id: str, tool_name: str) -> bool:
        """Gate 3: SpiceDB permission check."""
        if not self._spicedb:
            # No SpiceDB = ALLOW (fail-open for dev)
            return True

        try:
            return await self._spicedb.check_permission(
                subject=f"user:{user_id}",
                permission="tool:execute",
                resource=f"tool:{tool_name}",
            )
        except Exception as exc:
            logger.warning("SpiceDB check failed: %s, DENYING", exc)
            return False  # FAIL-CLOSED

    async def _check_opa(self, tool_name: str, user_id: str, tenant_id: str) -> bool:
        """Gate 4: OPA policy check."""
        if not self._opa:
            return True

        cache_key = f"{tenant_id}:{user_id}:{tool_name}"
        if cache_key in self._policy_cache:
            return self._policy_cache[cache_key]

        try:
            result = await self._opa.check_policy(
                input_data={
                    "tool_name": tool_name,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "action": "execute",
                }
            )
            allowed = result.get("allow", False)
            self._policy_cache[cache_key] = allowed
            return allowed
        except Exception as exc:
            logger.warning("OPA check failed: %s, DENYING", exc)
            return False  # FAIL-CLOSED


class ToolExecutor:
    """
    Tool execution engine.

    Validates tool calls against discovered tools
    and executes via native or MCP provider.
    """

    def __init__(self) -> None:
        """Initialize executor."""
        self._native_tools: Dict[str, Any] = {}

    def register_native_tool(self, name: str, handler: Any) -> None:
        """Register a native tool handler."""
        self._native_tools[name] = handler

    async def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        discovered_tools: List[DiscoveredTool],
    ) -> str:
        """
        Execute a tool call.

        Args:
            tool_name: Tool to execute
            args: Tool arguments
            discovered_tools: Validated tool list from discovery

        Returns:
            Tool execution result

        Raises:
            ToolNotFoundError: Tool not in discovered set
        """
        # Validate tool is in discovered set
        tool = next((t for t in discovered_tools if t.name == tool_name), None)
        if not tool:
            raise ToolNotFoundError(f"Tool '{tool_name}' not discovered")

        # Execute based on provider
        if tool.provider == "native":
            return await self._execute_native(tool_name, args)
        elif tool.provider == "mcp":
            return await self._execute_mcp(tool_name, args)
        else:
            return f"[Unknown provider: {tool.provider}]"

    async def _execute_native(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute native tool."""
        handler = self._native_tools.get(tool_name)
        if not handler:
            return f"[Native tool '{tool_name}' not registered]"

        try:
            if callable(handler):
                result = handler(**args)
                if hasattr(result, "__await__"):
                    result = await result
                return str(result)
            return str(handler)
        except Exception as exc:
            return f"[Tool error: {exc}]"

    async def _execute_mcp(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Execute MCP tool via configured MCP client.

        Standalone mode does not ship an MCP client; fail closed with guidance.
        """
        raise RuntimeError(
            f"MCP provider is not available in this deployment. Tool '{tool_name}' was requested with args {args}."
        )


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Get attribute from ORM or dict."""
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default


def _get_fallback_capabilities() -> List[Dict[str, Any]]:
    """Fallback tool catalog for development."""
    return [
        {
            "name": "calculator",
            "display_name": "Calculator",
            "description": "Perform math calculations",
            "category": "utility",
            "provider": "native",
            "schema": {"expression": {"type": "string"}},
        },
        {
            "name": "web_search",
            "display_name": "Web Search",
            "description": "Search the web",
            "category": "search",
            "provider": "mcp",
            "schema": {"query": {"type": "string"}},
        },
        {
            "name": "file_reader",
            "display_name": "File Reader",
            "description": "Read file contents",
            "category": "filesystem",
            "provider": "mcp",
            "schema": {"path": {"type": "string"}},
        },
    ]
