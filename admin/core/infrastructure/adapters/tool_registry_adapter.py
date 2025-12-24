"""Tool registry adapter wrapping ToolRegistry.

This adapter implements ToolRegistryPort by delegating ALL operations
to the existing production ToolRegistry implementation.
"""

from typing import Any, Dict, Iterable, Optional

from services.tool_executor.tool_registry import ToolRegistry
# from src.core.domain.ports.adapters.tool_registry import (
    ToolDefinitionDTO,
    ToolRegistryPort,
)


class ToolRegistryAdapter(ToolRegistryPort):
    """Implements ToolRegistryPort using existing ToolRegistry.

    Delegates ALL operations to services.tool_executor.tool_registry.ToolRegistry.
    """

    def __init__(self, registry: Optional[ToolRegistry] = None):
        """Initialize adapter with existing registry or create new one.

        Args:
            registry: Existing ToolRegistry instance (preferred)
        """
        self._registry = registry or ToolRegistry()

    async def load_all_tools(self) -> None:
        await self._registry.load_all_tools()

    def register(self, name: str, description: Optional[str] = None) -> None:
        # Note: The original register takes a BaseTool, but for the port
        # we simplify to just name/description. Full registration should
        # go through the underlying registry directly.
        pass  # Registration handled by load_all_tools

    def get(self, name: str) -> Optional[ToolDefinitionDTO]:
        tool_def = self._registry.get(name)
        if tool_def is None:
            return None
        return ToolDefinitionDTO(
            name=tool_def.name,
            description=tool_def.description,
        )

    def list(self) -> Iterable[ToolDefinitionDTO]:
        return [
            ToolDefinitionDTO(name=t.name, description=t.description) for t in self._registry.list()
        ]

    async def execute(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tool_def = self._registry.get(name)
        if tool_def is None:
            raise KeyError(f"Tool not found: {name}")
        return await tool_def.run(args)
