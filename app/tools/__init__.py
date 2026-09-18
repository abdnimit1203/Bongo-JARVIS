"""Modular tool registry and tools implementation."""
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry
from app.tools.system_tools import GetSystemInfoTool, OpenUrlTool, OpenApplicationTool
from app.tools.file_tools import ReadFileTool, SearchFilesTool

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "GetSystemInfoTool",
    "OpenUrlTool",
    "OpenApplicationTool",
    "ReadFileTool",
    "SearchFilesTool",
]
