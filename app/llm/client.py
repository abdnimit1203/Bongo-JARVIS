"""Lightweight Ollama REST API Client."""
from typing import Generator, List, Optional
import json
import httpx
from pydantic import BaseModel, Field

from app.config import settings


class ChatMessage(BaseModel):
    """Structure for a single chat message."""
    role: str  # "system", "user", "assistant", "tool"
    content: str


class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaClientError):
    """Raised when unable to connect to Ollama server."""
    pass


class OllamaClient:
    """Client for interacting with local Ollama server."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout

    def check_health(self) -> bool:
        """Check if Ollama server is accessible."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Fetch list of all installed local models."""
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    return [m.get("name") for m in data.get("models", [])]
                return []
        except Exception as e:
            raise OllamaConnectionError(f"Failed to connect to Ollama at {self.base_url}: {e}") from e

    def stream_chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        """
        Stream chat completion response chunk by chunk from Ollama.
        Yields text deltas as strings.
        """
        target_model = model or settings.default_model
        payload = {
            "model": target_model,
            "messages": [msg.model_dump() for msg in messages],
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        error_body = response.read().decode("utf-8", errors="replace")
                        raise OllamaClientError(f"Ollama API returned HTTP {response.status_code}: {error_body}")

                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                            if data.get("done", False):
                                break
        except httpx.ConnectError as e:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is running.") from e
        except httpx.TimeoutException as e:
            raise OllamaClientError("Request to Ollama timed out.") from e
        except json.JSONDecodeError as e:
            raise OllamaClientError(f"Invalid JSON received from Ollama: {e}") from e

    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Non-streaming chat completion request.
        Returns the complete assistant message content.
        """
        chunks = []
        for chunk in self.stream_chat(messages, model=model, temperature=temperature):
            chunks.append(chunk)
        return "".join(chunks)
