"""Tests for Tool Infrastructure and Security Permissions."""
import pytest
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry
from app.security.permissions import SecurityGuard, PermissionLevel


class DummySafeTool(BaseTool):
    name = "dummy_safe"
    description = "A safe dummy tool for testing."
    permission_level = PermissionLevel.SAFE
    parameters = {"query": {"type": "string", "description": "A query string"}}

    def execute(self, query: str = "") -> ToolResult:
        return ToolResult.ok(f"Safe query processed: {query}")


class DummyRiskyTool(BaseTool):
    name = "dummy_risky"
    description = "A risky dummy tool requiring confirmation."
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED
    parameters = {"target": {"type": "string"}}

    def execute(self, target: str = "") -> ToolResult:
        return ToolResult.ok(f"Risky action executed on {target}")


class DummyBlockedTool(BaseTool):
    name = "dummy_blocked"
    description = "A blocked tool."
    permission_level = PermissionLevel.BLOCKED

    def execute(self, **kwargs) -> ToolResult:
        return ToolResult.ok("Should never run")


def test_tool_schema():
    """Verify tool schema generation."""
    tool = DummySafeTool()
    schema = tool.get_schema()
    assert schema["name"] == "dummy_safe"
    assert schema["permission_level"] == "SAFE"
    assert "query" in schema["parameters"]


def test_safe_tool_execution():
    """Verify SAFE tools execute automatically."""
    guard = SecurityGuard()
    registry = ToolRegistry(security_guard=guard)
    registry.register(DummySafeTool())

    res = registry.execute("dummy_safe", {"query": "hello"})
    assert res.success is True
    assert "Safe query processed: hello" in res.output


def test_blocked_tool_execution():
    """Verify BLOCKED tools are rejected by SecurityGuard."""
    guard = SecurityGuard()
    registry = ToolRegistry(security_guard=guard)
    registry.register(DummyBlockedTool())

    res = registry.execute("dummy_blocked", {})
    assert res.success is False
    assert "Permission Denied" in res.error


def test_confirmation_required_tool_rejected():
    """Verify CONFIRMATION_REQUIRED tool is rejected if user declines."""
    guard = SecurityGuard(confirmation_callback=lambda tool, details: False)
    registry = ToolRegistry(security_guard=guard)
    registry.register(DummyRiskyTool())

    res = registry.execute("dummy_risky", {"target": "test_target"})
    assert res.success is False
    assert "rejected execution" in res.error


def test_confirmation_required_tool_approved():
    """Verify CONFIRMATION_REQUIRED tool executes if user approves."""
    guard = SecurityGuard(confirmation_callback=lambda tool, details: True)
    registry = ToolRegistry(security_guard=guard)
    registry.register(DummyRiskyTool())

    res = registry.execute("dummy_risky", {"target": "test_target"})
    assert res.success is True
    assert "Risky action executed on test_target" in res.output
