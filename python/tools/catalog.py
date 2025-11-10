from __future__ import annotations

from typing import Dict, List, Optional

from .models import ToolDefinition, ToolParameter


class ToolCatalog:
    """Minimal Tool Catalog singleton used by tests.

    Provides lookup, listing, and schema generation for a handful of built-in tools.
    """

    _instance: "ToolCatalog | None" = None

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._load_defaults()

    @classmethod
    def get(cls) -> "ToolCatalog":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # Public API expected in tests
    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    async def alist_tools(self) -> List[ToolDefinition]:
        return self.list_tools()

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    async def aget_tool(self, name: str) -> Optional[ToolDefinition]:
        return self.get_tool(name)

    def get_tools_schema(self) -> Dict[str, List[dict]]:
        return {
            "functions": [t.to_openapi_function() for t in self._tools.values()],
        }

    # Internal helpers
    def _load_defaults(self) -> None:
        # Search tool
        self._tools["search"] = ToolDefinition(
            name="search",
            description="Search indexed content and knowledge bases",
            category="search",
            parameters=[
                ToolParameter(
                    name="query", type="string", description="Search query", required=True
                ),
                ToolParameter(
                    name="top_k", type="int", description="Max results", required=False, default=5
                ),
            ],
        )
        # Memory store (alias expected by tests)
        self._tools["memory_store"] = ToolDefinition(
            name="memory_store",
            description="Store a memory item",
            category="memory",
            parameters=[
                ToolParameter(name="key", type="string", description="Memory key", required=True),
                ToolParameter(
                    name="value", type="string", description="Value to store", required=True
                ),
                ToolParameter(
                    name="namespace",
                    type="string",
                    description="Memory namespace",
                    required=False,
                    default="wm",
                ),
            ],
        )
        # Memory recall
        self._tools["memory_recall"] = ToolDefinition(
            name="memory_recall",
            description="Recall memories for a query",
            category="memory",
            parameters=[
                ToolParameter(
                    name="query", type="string", description="Recall query", required=True
                ),
                ToolParameter(
                    name="top_k",
                    type="int",
                    description="Number of results",
                    required=False,
                    default=3,
                ),
            ],
        )


# Export a module-level singleton for convenience
catalog = ToolCatalog.get()

__all__ = ["ToolCatalog", "catalog"]
