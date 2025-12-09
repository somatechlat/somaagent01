"""MCP Server models for local and remote connections.

This module contains the server configuration models that wrap MCP clients.
"""

from __future__ import annotations

import asyncio
import re
import threading
from typing import Any, ClassVar, Dict, List, Literal, Optional

from mcp.types import CallToolResult
from pydantic import BaseModel, Field, PrivateAttr


def normalize_name(name: str) -> str:
    """Normalize server/tool names to lowercase with underscores."""
    name = name.strip().lower()
    name = re.sub(r"[^\w]", "_", name, flags=re.UNICODE)
    return name


class MCPServerRemote(BaseModel):
    """Remote MCP server configuration (SSE/HTTP)."""

    name: str = Field(default_factory=str)
    description: Optional[str] = Field(default="Remote SSE Server")
    type: str = Field(default="sse", description="Server connection type")
    url: str = Field(default_factory=str)
    headers: dict[str, Any] | None = Field(default_factory=dict[str, Any])
    init_timeout: int = Field(default=0)
    tool_timeout: int = Field(default=0)
    verify: bool = Field(default=True, description="Verify SSL certificates")
    disabled: bool = Field(default=False)

    __lock: ClassVar[threading.Lock] = PrivateAttr(default=threading.Lock())
    __client: Optional[Any] = PrivateAttr(default=None)

    def __init__(self, config: dict[str, Any]):
        super().__init__()
        from python.helpers.mcp_clients import MCPClientRemote
        self.__client = MCPClientRemote(self)
        self.update(config)

    def get_error(self) -> str:
        with self.__lock:
            return self.__client.error

    def get_log(self) -> str:
        with self.__lock:
            return self.__client.get_log()

    def get_tools(self) -> List[dict[str, Any]]:
        with self.__lock:
            return self.__client.tools

    def has_tool(self, tool_name: str) -> bool:
        with self.__lock:
            return self.__client.has_tool(tool_name)

    async def call_tool(self, tool_name: str, input_data: Dict[str, Any]) -> CallToolResult:
        with self.__lock:
            return await self.__client.call_tool(tool_name, input_data)

    def update(self, config: dict[str, Any]) -> "MCPServerRemote":
        with self.__lock:
            for key, value in config.items():
                if key in ["name", "description", "type", "url", "serverUrl", "headers",
                           "init_timeout", "tool_timeout", "disabled", "verify"]:
                    if key == "name":
                        value = normalize_name(value)
                    if key == "serverUrl":
                        key = "url"
                    setattr(self, key, value)
            return asyncio.run(self.__on_update())

    async def __on_update(self) -> "MCPServerRemote":
        await self.__client.update_tools()
        return self


class MCPServerLocal(BaseModel):
    """Local MCP server configuration (stdio)."""

    name: str = Field(default_factory=str)
    description: Optional[str] = Field(default="Local StdIO Server")
    type: str = Field(default="stdio", description="Server connection type")
    command: str = Field(default_factory=str)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = Field(default_factory=dict[str, str])
    encoding: str = Field(default="utf-8")
    encoding_error_handler: Literal["strict", "ignore", "replace"] = Field(default="strict")
    init_timeout: int = Field(default=0)
    tool_timeout: int = Field(default=0)
    verify: bool = Field(default=True, description="Verify SSL certificates")
    disabled: bool = Field(default=False)

    __lock: ClassVar[threading.Lock] = PrivateAttr(default=threading.Lock())
    __client: Optional[Any] = PrivateAttr(default=None)

    def __init__(self, config: dict[str, Any]):
        super().__init__()
        from python.helpers.mcp_clients import MCPClientLocal
        self.__client = MCPClientLocal(self)
        self.update(config)

    def get_error(self) -> str:
        with self.__lock:
            return self.__client.error

    def get_log(self) -> str:
        with self.__lock:
            return self.__client.get_log()

    def get_tools(self) -> List[dict[str, Any]]:
        with self.__lock:
            return self.__client.tools

    def has_tool(self, tool_name: str) -> bool:
        with self.__lock:
            return self.__client.has_tool(tool_name)

    async def call_tool(self, tool_name: str, input_data: Dict[str, Any]) -> CallToolResult:
        with self.__lock:
            return await self.__client.call_tool(tool_name, input_data)

    def update(self, config: dict[str, Any]) -> "MCPServerLocal":
        with self.__lock:
            for key, value in config.items():
                if key in ["name", "description", "type", "command", "args", "env",
                           "encoding", "encoding_error_handler", "init_timeout",
                           "tool_timeout", "disabled"]:
                    if key == "name":
                        value = normalize_name(value)
                    setattr(self, key, value)
            return asyncio.run(self.__on_update())

    async def __on_update(self) -> "MCPServerLocal":
        await self.__client.update_tools()
        return self
