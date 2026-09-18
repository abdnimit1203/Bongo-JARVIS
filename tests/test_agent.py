"""Tests for Agent Core Orchestrator."""
import pytest
from app.core.agent import Agent
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import ToolRegistry
from app.security.permissions import SecurityGuard, PermissionLevel
from app.llm.client import ChatMessage


class MockEchoTool(BaseTool):
    name = "mock_echo"
    description = "Echoes back the message."
    permission_level = PermissionLevel.SAFE
    parameters = {"msg": {"type": "string", "description": "Message to echo"}}

    def execute(self, msg: str = "") -> ToolResult:
        return ToolResult.ok(f"ECHO: {msg}")


def test_agent_tool_parsing():
    """Verify agent can parse tool JSON from markdown blocks and raw text."""
    agent = Agent()
    
    # 1. Markdown block test
    json_block = """Here is the tool call:
```json
{
  "tool": "mock_echo",
  "arguments": {
    "msg": "Hello world"
  }
}
```"""
    parsed = agent._parse_tool_call(json_block)
    assert parsed is not None
    assert parsed[0] == "mock_echo"
    assert parsed[1] == {"msg": "Hello world"}

    # 2. Raw JSON test
    raw_json = '{"tool": "mock_echo", "arguments": {"msg": "Test"}}'
    parsed_raw = agent._parse_tool_call(raw_json)
    assert parsed_raw is not None
    assert parsed_raw[0] == "mock_echo"
    assert parsed_raw[1] == {"msg": "Test"}

    # 3. Regular conversational text (no tool call)
    plain_text = "I am JARVIS, how can I assist you today?"
    assert agent._parse_tool_call(plain_text) is None


def test_agent_with_tool_loop():
    """Verify full agent execution turn with dummy tool registered."""
    guard = SecurityGuard()
    registry = ToolRegistry(security_guard=guard)
    registry.register(MockEchoTool())

    agent = Agent(tool_registry=registry, security_guard=guard)
    history = []

    # Send a conversational query where no tool is triggered
    chunks = list(agent.process_turn(user_input="Hi, who are you?", conversation_history=history))
    reply = "".join(chunks)
    assert len(reply.strip()) > 0
