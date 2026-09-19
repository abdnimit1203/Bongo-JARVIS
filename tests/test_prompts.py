"""Tests for System Prompts, Dynamic Tool Grounding, and Negative Constraints."""
import pytest
from app.llm.prompts import build_system_prompt, BONGO_JARVIS_BASE_PROMPT


def test_base_prompt_constraints():
    """Verify base prompt contains strict honesty, grounding, and session memory rules."""
    assert "Strict Capability Honesty" in BONGO_JARVIS_BASE_PROMPT
    assert "Strict Tool Grounding" in BONGO_JARVIS_BASE_PROMPT
    assert "session-only" in BONGO_JARVIS_BASE_PROMPT.lower()
    assert "open_url" in BONGO_JARVIS_BASE_PROMPT
    assert "YouTube" in BONGO_JARVIS_BASE_PROMPT
    assert "never offer to bypass" in BONGO_JARVIS_BASE_PROMPT.lower()
    # Verify no hardcoded tool count in base prompt
    assert "5 tools" not in BONGO_JARVIS_BASE_PROMPT
    assert "five tools" not in BONGO_JARVIS_BASE_PROMPT.lower()


def test_build_system_prompt_empty():
    """Verify system prompt behavior when no tools are registered."""
    prompt = build_system_prompt([])
    assert "No tools are currently registered" in prompt
    assert "AI RUNTIME ARCHITECTURE & MODEL IDENTITY" in prompt
    assert "Primary LLM:" in prompt


def test_build_system_prompt_dynamic_tools():
    """Verify system prompt dynamically renders registered tools without fixed numbers."""
    dummy_tools = [
        {"name": "custom_search", "description": "Search custom db", "parameters": {"q": {"type": "string"}}},
        {"name": "custom_calc", "description": "Calculate math", "parameters": {"expr": {"type": "string"}}},
    ]
    prompt = build_system_prompt(dummy_tools)
    assert "custom_search" in prompt
    assert "custom_calc" in prompt
    assert "Source of Truth" in prompt
    assert "AI RUNTIME ARCHITECTURE & MODEL IDENTITY" in prompt

