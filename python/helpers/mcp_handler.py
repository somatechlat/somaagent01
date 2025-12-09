"""MCP Handler - Main entry point for MCP server management.

This module provides the MCPConfig singleton and MCPTool wrapper.
Server and client implementations are in separate modules.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterable, Mapping
from typing import Annotated, Any, ClassVar, Dict, List, Optional, Union

from mcp.types import CallToolResult
from pydantic import BaseModel, Discriminator, Field, PrivateAttr, Tag

from python.helpers import dirty_json
from python.helpers.print_style import PrintStyle
from python.helpers.tool import Response, Tool

# Re-export from extracted modules
from python.helpers.mcp_servers import (
    MCPServerLocal,
    MCPServerRemote,
    normalize_name,
)
from python.helpers.mcp_clients import (
    MCPClientBase,
    MCPClientLocal,
    MCPClientRemote,
    _is_streaming_http_type,
)


def _determine_server_type(config_dict: dict) -> str:
    """Determine the server type based on configuration."""
    if "type" in config_dict:
        server_type = config_dict["type"].lower()
        if server_type in ["sse", "http-stream", "streaming-http", "streamable-http", "http-streaming"]:
            return "MCPServerRemote"
        elif server_type == "stdio":
            return "MCPServerLocal"
    if "url" in config_dict or "serverUrl" in config_dict:
        return "MCPServerRemote"
    return "MCPServerLocal"


def initialize_mcp(mcp_servers_config: str):
    """Initialize MCP configuration from JSON string."""
    if not MCPConfig.get_instance().is_initialized():
        try:
            MCPConfig.update(mcp_servers_config)
        except Exception as e:
            from agent import AgentContext
            AgentContext.log_to_all(type="warning", content=f"Failed to update MCP settings: {e}", temp=False)
            PrintStyle(background_color="black", font_color="red", padding=True).print(f"Failed to update MCP settings: {e}")


class MCPTool(Tool):
    """MCP Tool wrapper for agent integration."""

    async def execute(self, **kwargs: Any):
        error = ""
        try:
            response: CallToolResult = await MCPConfig.get_instance().call_tool(self.name, kwargs)
            message = "\n\n".join([item.text for item in response.content if item.type == "text"])
            if response.isError:
                error = message
        except Exception as e:
            error = f"MCP Tool Exception: {str(e)}"
            message = f"ERROR: {str(e)}"

        if error:
            PrintStyle(background_color="#CC34C3", font_color="white", bold=True, padding=True).print(
                f"MCPTool::Failed to call mcp tool {self.name}:"
            )
            PrintStyle(background_color="#AA4455", font_color="white", padding=False).print(error)
            self.agent.context.log.log(type="warning", content=f"{self.name}: {error}")

        return Response(message=message, break_loop=False)

    async def before_execution(self, **kwargs: Any):
        PrintStyle(font_color="#1B4F72", padding=True, background_color="white", bold=True).print(
            f"{self.agent.agent_name}: Using tool '{self.name}'"
        )
        self.log = self.get_log_object()
        for key, value in self.args.items():
            PrintStyle(font_color="#85C1E9", bold=True).stream(self.nice_key(key) + ": ")
            PrintStyle(font_color="#85C1E9", padding=isinstance(value, str) and "\n" in value).stream(value)
            PrintStyle().print()

    async def after_execution(self, response: Response, **kwargs: Any):
        raw_tool_response = response.message.strip() if response.message else ""
        if not raw_tool_response:
            PrintStyle(font_color="red").print(f"Warning: Tool '{self.name}' returned an empty message.")
            raw_tool_response = "[Tool returned no textual content]"

        self.agent.hist_add_tool_result(self.name, raw_tool_response)
        PrintStyle(font_color="#1B4F72", background_color="white", padding=True, bold=True).print(
            f"{self.agent.agent_name}: Response from tool '{self.name}'"
        )
        PrintStyle(font_color="#85C1E9").print(raw_tool_response or "[No direct textual output from tool]")
        if self.log:
            self.log.update(content=raw_tool_response)


MCPServer = Annotated[
    Union[
        Annotated[MCPServerRemote, Tag("MCPServerRemote")],
        Annotated[MCPServerLocal, Tag("MCPServerLocal")],
    ],
    Discriminator(_determine_server_type),
]



class MCPConfig(BaseModel):
    """Singleton configuration manager for MCP servers."""

    servers: list[MCPServer] = Field(default_factory=list)
    disconnected_servers: list[dict[str, Any]] = Field(default_factory=list)
    __lock: ClassVar[threading.Lock] = PrivateAttr(default=threading.Lock())
    __instance: ClassVar[Any] = PrivateAttr(default=None)
    __initialized: ClassVar[bool] = PrivateAttr(default=False)

    @classmethod
    def get_instance(cls) -> "MCPConfig":
        if cls.__instance is None:
            cls.__instance = cls(servers_list=[])
        return cls.__instance

    @classmethod
    def wait_for_lock(cls):
        with cls.__lock:
            return

    @classmethod
    def update(cls, config_str: str) -> Any:
        with cls.__lock:
            servers_data: List[Dict[str, Any]] = []
            if config_str and config_str.strip():
                try:
                    parsed_value = dirty_json.try_parse(config_str)
                    normalized = cls.normalize_config(parsed_value)
                    if isinstance(normalized, list):
                        servers_data = [item for item in normalized if isinstance(item, dict)]
                except Exception as e:
                    PrintStyle.error(f"Error parsing MCP config: {e}")

            instance = cls.get_instance()
            instance.__init__(servers_list=servers_data)
            cls.__initialized = True
            return instance

    @classmethod
    def normalize_config(cls, servers: Any):
        normalized = []
        if isinstance(servers, list):
            normalized = [s for s in servers if isinstance(s, dict)]
        elif isinstance(servers, dict):
            if "mcpServers" in servers:
                mcp_servers = servers["mcpServers"]
                if isinstance(mcp_servers, dict):
                    for key, value in mcp_servers.items():
                        if isinstance(value, dict):
                            value["name"] = key
                            normalized.append(value)
                elif isinstance(mcp_servers, list):
                    normalized = [s for s in mcp_servers if isinstance(s, dict)]
            else:
                normalized.append(servers)
        return normalized

    def __init__(self, servers_list: List[Dict[str, Any]]):
        super().__init__()
        self.servers = []
        self.disconnected_servers = []

        if not isinstance(servers_list, Iterable):
            PrintStyle(background_color="grey", font_color="red", padding=True).print(
                "MCPConfig::__init__::servers_list must be a list"
            )
            return

        for server_item in servers_list:
            if not isinstance(server_item, Mapping):
                self.disconnected_servers.append({
                    "config": server_item if isinstance(server_item, dict) else {"raw": str(server_item)},
                    "error": "server_item must be a mapping",
                    "name": "invalid_server_config",
                })
                continue

            if server_item.get("disabled", False):
                server_name = normalize_name(server_item.get("name", "unnamed_server"))
                self.disconnected_servers.append({
                    "config": server_item, "error": "Disabled in config", "name": server_name
                })
                continue

            server_name = server_item.get("name", "__not__found__")
            if server_name == "__not__found__":
                self.disconnected_servers.append({
                    "config": server_item, "error": "server_name is required", "name": "unnamed_server"
                })
                continue

            try:
                if server_item.get("url") or server_item.get("serverUrl"):
                    self.servers.append(MCPServerRemote(server_item))
                else:
                    self.servers.append(MCPServerLocal(server_item))
            except Exception as e:
                self.disconnected_servers.append({
                    "config": server_item, "error": str(e), "name": server_name
                })

    def get_server_log(self, server_name: str) -> str:
        with self.__lock:
            for server in self.servers:
                if server.name == server_name:
                    return server.get_log()
            return ""

    def get_servers_status(self) -> list[dict[str, Any]]:
        result = []
        with self.__lock:
            for server in self.servers:
                result.append({
                    "name": server.name,
                    "connected": True,
                    "error": server.get_error(),
                    "tool_count": len(server.get_tools()),
                    "has_log": server.get_log() != "",
                })
            for disconnected in self.disconnected_servers:
                result.append({
                    "name": disconnected["name"],
                    "connected": False,
                    "error": disconnected["error"],
                    "tool_count": 0,
                    "has_log": False,
                })
        return result

    def get_server_detail(self, server_name: str) -> dict[str, Any]:
        with self.__lock:
            for server in self.servers:
                if server.name == server_name:
                    try:
                        tools = server.get_tools()
                    except Exception:
                        tools = []
                    return {"name": server.name, "description": server.description, "tools": tools}
            return {}

    def is_initialized(self) -> bool:
        with self.__lock:
            return self.__initialized

    def get_tools(self) -> List[dict[str, dict[str, Any]]]:
        with self.__lock:
            tools = []
            for server in self.servers:
                for tool in server.get_tools():
                    tool_copy = tool.copy()
                    tool_copy["server"] = server.name
                    tools.append({f"{server.name}.{tool['name']}": tool_copy})
            return tools

    def get_tools_prompt(self, server_name: str = "") -> str:
        with self.__lock:
            pass

        prompt = '## "Remote (MCP Server) Agent Tools" available:\n\n'
        server_names = [s.name for s in self.servers if not server_name or s.name == server_name]

        if server_name and server_name not in server_names:
            raise ValueError(f"Server {server_name} not found")

        for server in self.servers:
            if server.name in server_names:
                prompt += f"### {server.name}\n{server.description}\n"
                for tool in server.get_tools():
                    input_schema = json.dumps(tool["input_schema"]) if tool["input_schema"] else ""
                    prompt += (
                        f"\n### {server.name}.{tool['name']}:\n{tool['description']}\n\n"
                        f"#### Input schema for tool_args:\n{input_schema}\n\n"
                        f"#### Usage:\n{{\n"
                        f'    "thoughts": ["..."],\n'
                        f'    "tool_name": "{server.name}.{tool["name"]}",\n'
                        f'    "tool_args": !follow schema above\n}}\n'
                    )
        return prompt

    def has_tool(self, tool_name: str) -> bool:
        if "." not in tool_name:
            return False
        server_name_part, tool_name_part = tool_name.split(".")
        with self.__lock:
            for server in self.servers:
                if server.name == server_name_part:
                    return server.has_tool(tool_name_part)
            return False

    def get_tool(self, agent: Any, tool_name: str) -> MCPTool | None:
        if not self.has_tool(tool_name):
            return None
        return MCPTool(agent=agent, name=tool_name, method=None, args={}, message="", loop_data=None)

    async def call_tool(self, tool_name: str, input_data: Dict[str, Any]) -> CallToolResult:
        if "." not in tool_name:
            raise ValueError(f"Tool {tool_name} not found")
        server_name_part, tool_name_part = tool_name.split(".")
        with self.__lock:
            for server in self.servers:
                if server.name == server_name_part and server.has_tool(tool_name_part):
                    return await server.call_tool(tool_name_part, input_data)
            raise ValueError(f"Tool {tool_name} not found")
