"""Tool Registry for registering, discovering, and executing tools safely."""
from typing import Dict, List, Optional, Any
from app.tools.base import BaseTool, ToolResult
from app.security.permissions import SecurityGuard, PermissionLevel, PermissionDecision


class ToolRegistry:
    """Central registry for managing JARVIS tools."""

    def __init__(self, security_guard: Optional[SecurityGuard] = None):
        self._tools: Dict[str, BaseTool] = {}
        self.security_guard = security_guard or SecurityGuard()

    def register(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        if not tool.name:
            raise ValueError("Tool name cannot be empty.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """Return list of all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Generate JSON schemas for all registered tools."""
        return [tool.get_schema() for tool in self._tools.values()]

    def execute(self, name: str, args: Optional[Dict[str, Any]] = None) -> ToolResult:
        """
        Safely execute a tool through the security permission gate.
        """
        tool = self.get(name)
        if not tool:
            return ToolResult.fail(f"Tool '{name}' is not registered.")

        args = args or {}
        details = f"args={args}"

        # 1. Evaluate permissions
        decision: PermissionDecision = self.security_guard.check_permission(
            tool_name=tool.name,
            permission_level=tool.permission_level,
            details=details,
        )

        if not decision.allowed:
            return ToolResult.fail(f"Permission Denied: {decision.reason}")

        # 2. Execute tool
        try:
            return tool.execute(**args)
        except TypeError as te:
            return ToolResult.fail(f"Invalid arguments for tool '{name}': {te}")
        except Exception as e:
            return ToolResult.fail(f"Execution error in tool '{name}': {e}")
