"""Tool registry port interface.

This port defines the contract for tool registration and lookup.
The interface matches the existing ToolRegistry methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    services.tool_executor.tool_registry.ToolRegistry
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class ToolDefinitionDTO:
    """Data transfer object for tool definition.

    Mirrors services.tool_executor.tool_registry.ToolDefinition structure.
    """

    name: str
    description: Optional[str] = None


class ToolRegistryPort(ABC):
    """Abstract interface for tool registration and lookup.

    This port wraps the existing ToolRegistry implementation.
    All methods match the production implementation signature exactly.
    """

    @abstractmethod
    async def load_all_tools(self) -> None:
        """Load all built-in tool implementations."""
        ...

    @abstractmethod
    def register(self, name: str, description: Optional[str] = None) -> None:
        """Register a tool definition.

        Args:
            name: Tool name
            description: Optional tool description
        """
        ...

    @abstractmethod
    def get(self, name: str) -> Optional[ToolDefinitionDTO]:
        """Get a tool definition by name.

        Args:
            name: Tool name

        Returns:
            Tool definition or None if not found
        """
        ...

    @abstractmethod
    def list(self) -> Iterable[ToolDefinitionDTO]:
        """List all registered tool definitions.

        Returns:
            Iterable of tool definitions
        """
        ...

    @abstractmethod
    async def execute(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name.

        Args:
            name: Tool name
            args: Tool arguments

        Returns:
            Tool execution result

        Raises:
            KeyError: If tool not found
        """
        ...