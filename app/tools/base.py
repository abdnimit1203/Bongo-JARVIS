"""Base Tool definition and schema specifications."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from app.security.permissions import PermissionLevel


class ToolResult(BaseModel):
    """Structured result returned by tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def ok(cls, output: str, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        return cls(success=True, output=output, metadata=metadata or {})

    @classmethod
    def fail(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        return cls(success=False, output="", error=error, metadata=metadata or {})


class BaseTool(ABC):
    """Abstract Base Class for all JARVIS tools."""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    permission_level: PermissionLevel = PermissionLevel.SAFE

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with validated arguments."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return standardized JSON schema for tool description."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "permission_level": self.permission_level.value,
        }
