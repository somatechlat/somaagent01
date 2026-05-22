"""Tool registry helpers for the SomaAgent 01 tool executor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from services.tool_executor.tools import AVAILABLE_TOOLS, BaseTool


@dataclass(frozen=True)
class ToolDefinition:
    """Metadata describing an executable tool."""

    name: str
    handler: BaseTool
    description: Optional[str] = None

    async def run(self, args: dict[str, object]) -> dict[str, object]:
        """Execute run.

        Args:
            args: The args.
        """

        return await self.handler.run(args)  # type: ignore[arg-type]


class ToolRegistry:
    """In-memory registry that tracks available tool definitions."""

    def __init__(self) -> None:
        """Initialize the instance."""

        self._tools: Dict[str, ToolDefinition] = {}

    async def load_all_tools(self) -> None:
        """Load built-in tool implementations."""

        for name, tool in AVAILABLE_TOOLS.items():
            self.register(tool)

    def load_from_capsule(self, capsule: Any) -> None:
        """Load tool definitions from a Capsule's tool registry snapshot.

        Each Capsule carries its own tool schemas and policies.
        This creates a per-capsule ToolRegistry that snapshots the
        capabilities at certification time.
        """
        from admin.core.models import Capsule

        if not isinstance(capsule, Capsule):
            return

        body = capsule.body or {}
        persona = body.get("persona", {})
        tools_config = persona.get("tools", {})
        tool_registry = tools_config.get("tool_registry", {})

        for name, definition in tool_registry.items():
            # Look up the system tool implementation
            handler = AVAILABLE_TOOLS.get(name)
            if handler:
                self.register(
                    handler,
                    description=definition.get("description", name),
                )

    def register(self, tool: BaseTool, *, description: Optional[str] = None) -> None:
        """Execute register.

        Args:
            tool: The tool.
        """

        definition = ToolDefinition(name=tool.name, handler=tool, description=description)
        self._tools[tool.name] = definition

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Execute get.

        Args:
            name: The name.
        """

        return self._tools.get(name)

    def list(self) -> Iterable[ToolDefinition]:
        """Execute list."""

        return self._tools.values()
