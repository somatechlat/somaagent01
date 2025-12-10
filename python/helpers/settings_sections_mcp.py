"""Settings section builders for MCP and A2A configurations."""

from typing import Any

from python.helpers.settings_types import SettingsSection


def build_mcp_client_section(settings: Any) -> SettingsSection:
    """Build the MCP client settings section."""
    return {
        "id": "mcp_client",
        "title": "External MCP Servers",
        "description": "Agent Zero can use external MCP servers as tools.",
        "fields": [
            {
                "id": "mcp_servers_config",
                "title": "MCP Servers Configuration",
                "type": "button",
                "value": "Open",
            },
            {
                "id": "mcp_servers",
                "title": "MCP Servers",
                "description": "JSON list of MCP server configurations.",
                "type": "textarea",
                "value": settings["mcp_servers"],
                "hidden": True,
            },
            {
                "id": "mcp_client_init_timeout",
                "title": "MCP Client Init Timeout",
                "description": "Timeout for initialization (seconds).",
                "type": "number",
                "value": settings["mcp_client_init_timeout"],
            },
            {
                "id": "mcp_client_tool_timeout",
                "title": "MCP Client Tool Timeout",
                "description": "Timeout for tool execution.",
                "type": "number",
                "value": settings["mcp_client_tool_timeout"],
            },
        ],
        "tab": "mcp",
    }


def build_mcp_server_section(settings: Any) -> SettingsSection:
    """Build the MCP server settings section."""
    return {
        "id": "mcp_server",
        "title": "A0 MCP Server",
        "description": "Expose Agent Zero as an SSE MCP server.",
        "fields": [
            {
                "id": "mcp_server_enabled",
                "title": "Enable A0 MCP Server",
                "type": "switch",
                "value": settings["mcp_server_enabled"],
            },
            {
                "id": "mcp_server_token",
                "title": "MCP Server Token",
                "type": "text",
                "hidden": True,
                "value": settings["mcp_server_token"],
            },
        ],
        "tab": "mcp",
    }


def build_a2a_section(settings: Any) -> SettingsSection:
    """Build the A2A server settings section."""
    return {
        "id": "a2a_server",
        "title": "A0 A2A Server",
        "description": "Expose Agent Zero as an A2A server.",
        "fields": [
            {
                "id": "a2a_server_enabled",
                "title": "Enable A2A server",
                "type": "switch",
                "value": settings["a2a_server_enabled"],
            },
        ],
        "tab": "mcp",
    }
