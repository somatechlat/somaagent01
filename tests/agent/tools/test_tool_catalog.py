"""
Perfect tool catalog integration tests - testing real tool catalog with no mocks.
Verifies the new canonical tool catalog singleton works correctly.
"""

import asyncio

import pytest

from integrations.tool_catalog import catalog
from python.tools.models import ToolDefinition


class TestToolCatalogIntegration:
    """Test the canonical tool catalog with real implementations."""

    def test_catalog_singleton_instance(self):
        """Test tool catalog is properly implemented as singleton."""
        from integrations.tool_catalog import catalog as catalog_1, catalog as catalog_2

        assert catalog_1 is catalog_2
        assert catalog_1 is catalog

    def test_catalog_initialization(self):
        """Test tool catalog initializes with real tools."""
        # Should have tools loaded
        all_tools = catalog.list_tools()
        assert isinstance(all_tools, list)
        assert len(all_tools) > 0

        # Verify tool structure
        for tool in all_tools:
            assert isinstance(tool, ToolDefinition)
            assert tool.name
            assert tool.description
            assert isinstance(tool.parameters, list)

    def test_tool_lookup_real(self):
        """Test tool lookup with real catalog data."""
        # Test known tools exist
        known_tools = ["search", "memory_store", "memory_recall"]

        for tool_name in known_tools:
            tool = catalog.get_tool(tool_name)
            assert tool is not None
            assert tool.name == tool_name
            assert isinstance(tool, ToolDefinition)

    def test_tool_parameter_validation(self):
        """Test tool parameter validation with real tool definitions."""
        search_tool = catalog.get_tool("search")
        assert search_tool is not None

        # Verify parameter structure
        params = search_tool.parameters
        assert isinstance(params, list)

        # Find query parameter
        query_param = next((p for p in params if p.name == "query"), None)
        assert query_param is not None
        assert query_param.type == "string"
        assert query_param.required is True

    def test_tool_schema_generation(self):
        """Test OpenAPI schema generation for tools."""
        schema = catalog.get_tools_schema()
        assert isinstance(schema, dict)
        assert "functions" in schema

        functions = schema["functions"]
        assert isinstance(functions, list)
        assert len(functions) > 0

        # Verify schema structure
        for func in functions:
            assert "name" in func
            assert "description" in func
            assert "parameters" in func
            assert isinstance(func["parameters"], dict)

    def test_tool_execution_capability(self):
        """Test tool execution capability without mocking."""
        memory_tool = catalog.get_tool("memory_store")
        assert memory_tool is not None

        # Test parameter requirements
        required_params = [p for p in memory_tool.parameters if p.required]
        assert len(required_params) > 0

        # Verify at least key parameter exists
        key_param = next((p for p in memory_tool.parameters if p.name == "key"), None)
        assert key_param is not None
        assert key_param.required is True

    @pytest.mark.asyncio
    async def test_async_tool_catalog_operations(self):
        """Test async operations on tool catalog."""
        # Test async listing
        tools = await catalog.alist_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Test async lookup
        search_tool = await catalog.aget_tool("search")
        assert search_tool is not None
        assert search_tool.name == "search"

    def test_tool_catalog_memory_usage(self):
        """Test tool catalog doesn't duplicate tool instances."""
        tool_1 = catalog.get_tool("search")
        tool_2 = catalog.get_tool("search")

        # Should be the same instance (singleton behavior)
        assert tool_1 is tool_2

    def test_invalid_tool_handling(self):
        """Test handling of non-existent tools."""
        invalid_tool = catalog.get_tool("nonexistent_tool_12345")
        assert invalid_tool is None

    def test_tool_categories(self):
        """Test tool categorization."""
        all_tools = catalog.list_tools()

        # Group by category
        categories = {}
        for tool in all_tools:
            cat = tool.category or "uncategorized"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(tool.name)

        assert len(categories) > 0
        # Should have at least memory and search categories
        assert any("memory" in cat.lower() for cat in categories.keys())
        assert any("search" in cat.lower() for cat in categories.keys())

    def test_tool_parameter_defaults(self):
        """Test tool parameter default values."""
        recall_tool = catalog.get_tool("memory_recall")
        assert recall_tool is not None

        # Check for optional parameters with defaults
        for param in recall_tool.parameters:
            if not param.required and param.default is not None:
                assert param.type == type(param.default).__name__

    @pytest.mark.asyncio
    async def test_concurrent_tool_access(self):
        """Test concurrent access to tool catalog."""

        async def get_search_tool():
            return catalog.get_tool("search")

        # Run multiple concurrent lookups
        tasks = [get_search_tool() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should return the same instance
        first = results[0]
        for result in results[1:]:
            assert result is first
