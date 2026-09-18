"""Tests for Ollama LLM Client."""
import pytest
from app.llm.client import OllamaClient, ChatMessage
from app.llm.prompts import BONGO_JARVIS_SYSTEM_PROMPT


def test_ollama_health():
    """Verify Ollama server is running and healthy."""
    client = OllamaClient()
    assert client.check_health() is True


def test_ollama_list_models():
    """Verify downloaded model is listed in Ollama."""
    client = OllamaClient()
    models = client.list_models()
    assert len(models) > 0
    assert any("qwen2.5:3b" in m for m in models)


def test_ollama_short_generation():
    """Verify quick non-streaming generation."""
    client = OllamaClient()
    messages = [
        ChatMessage(role="system", content=BONGO_JARVIS_SYSTEM_PROMPT),
        ChatMessage(role="user", content="Reply with only the word 'ACTIVE'."),
    ]
    response = client.chat(messages=messages)
    assert response is not None
    assert len(response.strip()) > 0
