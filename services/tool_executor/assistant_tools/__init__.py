"""Assistant file tools package — SOMA-ARCH-TOOLS-001 (W3.1–W3.2).

Import direction is strictly ``services.tool_executor.tools`` → this package.
Nothing here imports ``services.tool_executor.tools`` at module scope, so both
import orders stay acyclic (the tools themselves import ``ToolExecutionError``
lazily inside a call).
"""

from __future__ import annotations

from typing import List, Tuple

from services.tool_executor.assistant_tools.base import SomaAssistantTool, ToolContext
from services.tool_executor.assistant_tools.file_list import FileListTool
from services.tool_executor.assistant_tools.file_patch import FilePatchTool
from services.tool_executor.assistant_tools.file_search import FileSearchTool
from services.tool_executor.assistant_tools.file_write import FileWriteTool

FILE_ASSISTANT_TOOLS: List[SomaAssistantTool] = [
    FileListTool(),
    FileSearchTool(),
    FileWriteTool(),
    FilePatchTool(),
]

ASSISTANT_TOOL_NAMES: Tuple[str, ...] = tuple(tool.name for tool in FILE_ASSISTANT_TOOLS)

__all__ = [
    "ASSISTANT_TOOL_NAMES",
    "FILE_ASSISTANT_TOOLS",
    "FileListTool",
    "FilePatchTool",
    "FileSearchTool",
    "FileWriteTool",
    "SomaAssistantTool",
    "ToolContext",
]
