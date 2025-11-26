"""Tool registry helpers for the SomaAgent 01 tool executor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from services.tool_executor.tools import AVAILABLE_TOOLS, BaseTool
from services.tool_executor.memory_tools import MemorySaveTool, UpdateBehaviorTool


@dataclass(frozen=True)
class ToolDefinition:
    """Metadata describing an executable tool."""

    name: str
    handler: BaseTool
    description: Optional[str] = None

    async def run(self, args: dict[str, object]) -> dict[str, object]:
        return await self.handler.run(args)  # type: ignore[arg-type]


class ToolRegistry:
    """In-memory registry that tracks available tool definitions."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    async def load_all_tools(self) -> None:
        """Load built-in tool implementations."""

        for name, tool in AVAILABLE_TOOLS.items():
            self.register(tool)

        # Register specific memory tools
        self.register(MemorySaveTool())
        self.register(UpdateBehaviorTool())

    def register(self, tool: BaseTool, *, description: Optional[str] = None) -> None:
        definition = ToolDefinition(name=tool.name, handler=tool, description=description)
        self._tools[tool.name] = definition

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list(self) -> Iterable[ToolDefinition]:
        return self._tools.values()
