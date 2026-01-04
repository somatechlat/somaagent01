"""MCP Client implementations for local and remote connections.

This module contains the client classes that handle MCP protocol communication.
"""

from __future__ import annotations

import tempfile
import threading
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from datetime import timedelta
from shutil import which
from typing import (
    Any,
    Awaitable,
    Callable,
    cast,
    ClassVar,
    Dict,
    List,
    Optional,
    TextIO,
    TypeVar,
)

import httpx
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.message import SessionMessage
from mcp.types import CallToolResult, ListToolsResult

from admin.core.helpers import errors, settings
from admin.core.helpers.print_style import PrintStyle

T = TypeVar("T")


def _is_streaming_http_type(server_type: str) -> bool:
    """Check if the server type is a streaming HTTP variant."""
    return server_type.lower() in [
        "http-stream",
        "streaming-http",
        "streamable-http",
        "http-streaming",
    ]


class MCPClientBase(ABC):
    """Abstract base class for MCP clients."""

    __lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self, server: Any):
        """Initialize the instance."""

        self.server = server
        self.tools: List[dict[str, Any]] = []
        self.error: str = ""
        self.log: List[str] = []
        self.log_file: Optional[TextIO] = None

    @abstractmethod
    async def _create_stdio_transport(
        self, current_exit_stack: AsyncExitStack
    ) -> tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]:
        """Create stdio/write streams using the provided exit_stack."""
        ...

    async def _execute_with_session(
        self,
        coro_func: Callable[[ClientSession], Awaitable[T]],
        read_timeout_seconds=60,
    ) -> T:
        """Manages the lifecycle of an MCP session for a single operation."""
        operation_name = coro_func.__name__
        original_exception = None
        try:
            async with AsyncExitStack() as temp_stack:
                try:
                    stdio, write = await self._create_stdio_transport(temp_stack)
                    session = await temp_stack.enter_async_context(
                        ClientSession(
                            stdio,
                            write,
                            read_timeout_seconds=timedelta(seconds=read_timeout_seconds),
                        )
                    )
                    await session.initialize()
                    return await coro_func(session)
                except Exception as e:
                    excs = getattr(e, "exceptions", None)
                    original_exception = excs[0] if excs else e
                    raise RuntimeError("Dummy exception to break out of async block")
        except Exception:
            if original_exception is not None:
                e = original_exception
            PrintStyle(background_color="#AA4455", font_color="white", padding=False).print(
                f"MCPClientBase ({self.server.name} - {operation_name}): Error: {type(e).__name__}: {e}"
            )
            raise e
        raise RuntimeError(f"MCPClientBase ({self.server.name}): Unexpected exit")

    async def update_tools(self) -> "MCPClientBase":
        """Fetch and cache tools from the server."""

        async def list_tools_op(current_session: ClientSession):
            """Execute list tools op.

            Args:
                current_session: The current_session.
            """

            response: ListToolsResult = await current_session.list_tools()
            with self.__lock:
                self.tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in response.tools
                ]
            PrintStyle(font_color="green").print(
                f"MCPClientBase ({self.server.name}): Found {len(self.tools)} tools."
            )

        try:
            set = settings.get_settings()
            await self._execute_with_session(
                list_tools_op,
                read_timeout_seconds=self.server.init_timeout or set["mcp_client_init_timeout"],
            )
        except Exception as e:
            error_text = errors.format_error(e, 0, 0)
            PrintStyle(
                background_color="#CC34C3", font_color="white", bold=True, padding=True
            ).print(f"MCPClientBase ({self.server.name}): 'update_tools' failed: {error_text}")
            with self.__lock:
                self.tools = []
                self.error = f"Failed to initialize. {error_text[:200]}{'...' if len(error_text) > 200 else ''}"
        return self

    def has_tool(self, tool_name: str) -> bool:
        """Check if tool.

        Args:
            tool_name: The tool_name.
        """

        with self.__lock:
            return any(tool["name"] == tool_name for tool in self.tools)

    def get_tools(self) -> List[dict[str, Any]]:
        """Retrieve tools."""

        with self.__lock:
            return self.tools

    async def call_tool(self, tool_name: str, input_data: Dict[str, Any]) -> CallToolResult:
        """Execute call tool.

        Args:
            tool_name: The tool_name.
            input_data: The input_data.
        """

        if not self.has_tool(tool_name):
            await self.update_tools()
            if not self.has_tool(tool_name):
                raise ValueError(f"Tool {tool_name} not found on server {self.server.name}")

        async def call_tool_op(current_session: ClientSession):
            """Execute call tool op.

            Args:
                current_session: The current_session.
            """

            set = settings.get_settings()
            return await current_session.call_tool(
                tool_name,
                input_data,
                read_timeout_seconds=timedelta(seconds=set["mcp_client_tool_timeout"]),
            )

        try:
            return await self._execute_with_session(call_tool_op)
        except Exception as e:
            raise ConnectionError(f"Failed to call tool '{tool_name}' on '{self.server.name}': {e}")

    def get_log(self):
        """Retrieve log."""

        if not hasattr(self, "log_file") or self.log_file is None:
            return ""
        self.log_file.seek(0)
        try:
            return self.log_file.read()
        except Exception:
            return ""


class MCPClientLocal(MCPClientBase):
    """Local MCP client using stdio transport."""

    def __del__(self):
        """Execute del  ."""

        if hasattr(self, "log_file") and self.log_file is not None:
            try:
                self.log_file.close()
            except Exception:
                pass
            self.log_file = None

    async def _create_stdio_transport(
        self, current_exit_stack: AsyncExitStack
    ) -> tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]:
        """Execute create stdio transport.

        Args:
            current_exit_stack: The current_exit_stack.
        """

        from admin.core.helpers.mcp_servers import MCPServerLocal

        server: MCPServerLocal = cast(MCPServerLocal, self.server)

        if not server.command:
            raise ValueError("Command not specified")
        if not which(server.command):
            raise ValueError(f"Command '{server.command}' not found")

        server_params = StdioServerParameters(
            command=server.command,
            args=server.args,
            env=server.env,
            encoding=server.encoding,
            encoding_error_handler=server.encoding_error_handler,
        )

        if not hasattr(self, "log_file") or self.log_file is None:
            self.log_file = tempfile.TemporaryFile(mode="w+", encoding="utf-8")

        return await current_exit_stack.enter_async_context(
            stdio_client(server_params, errlog=self.log_file)
        )


class CustomHTTPClientFactory:
    """Factory for creating httpx clients with custom settings."""

    def __init__(self, verify: bool = True):
        """Initialize the instance."""

        self.verify = verify

    def __call__(
        self,
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
    ) -> httpx.AsyncClient:
        """Execute call  .

        Args:
            headers: The headers.
            timeout: The timeout.
            auth: The auth.
        """

        kwargs: dict[str, Any] = {"follow_redirects": True}
        kwargs["timeout"] = timeout if timeout else httpx.Timeout(30.0)
        if headers:
            kwargs["headers"] = headers
        if auth:
            kwargs["auth"] = auth
        return httpx.AsyncClient(**kwargs, verify=self.verify)


class MCPClientRemote(MCPClientBase):
    """Remote MCP client using SSE or streaming HTTP transport."""

    def __init__(self, server: Any):
        """Initialize the instance."""

        super().__init__(server)
        self.session_id: Optional[str] = None
        self.session_id_callback: Optional[Callable[[], Optional[str]]] = None

    async def _create_stdio_transport(
        self, current_exit_stack: AsyncExitStack
    ) -> tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]:
        """Execute create stdio transport.

        Args:
            current_exit_stack: The current_exit_stack.
        """

        from admin.core.helpers.mcp_servers import MCPServerRemote

        server: MCPServerRemote = cast(MCPServerRemote, self.server)
        set = settings.get_settings()

        init_timeout = min(server.init_timeout or set["mcp_client_init_timeout"], 5)
        tool_timeout = min(server.tool_timeout or set["mcp_client_tool_timeout"], 10)

        client_factory = CustomHTTPClientFactory(verify=server.verify)

        if _is_streaming_http_type(server.type):
            transport_result = await current_exit_stack.enter_async_context(
                streamablehttp_client(
                    url=server.url,
                    headers=server.headers,
                    timeout=timedelta(seconds=init_timeout),
                    sse_read_timeout=timedelta(seconds=tool_timeout),
                    httpx_client_factory=client_factory,
                )
            )
            read_stream, write_stream, get_session_id_callback = transport_result
            self.session_id_callback = get_session_id_callback
            return read_stream, write_stream
        else:
            return await current_exit_stack.enter_async_context(
                sse_client(
                    url=server.url,
                    headers=server.headers,
                    timeout=init_timeout,
                    sse_read_timeout=tool_timeout,
                    httpx_client_factory=client_factory,
                )
            )

    def get_session_id(self) -> Optional[str]:
        """Retrieve session id."""

        if self.session_id_callback is not None:
            return self.session_id_callback()
        return None
