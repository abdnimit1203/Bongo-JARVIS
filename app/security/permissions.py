"""Security and Permission Layer for Bongo-JARVIS Tools."""
from enum import Enum
from typing import Callable, Optional
from pydantic import BaseModel


class PermissionLevel(str, Enum):
    """Permission classification for tools."""
    SAFE = "SAFE"                              # Harmless / Read-only action (auto-approved)
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"  # Potentially risky / Modifying action (requires user approval)
    BLOCKED = "BLOCKED"                        # Forbidden action (never executed)


class PermissionDecision(BaseModel):
    """Decision outcome from security guard."""
    allowed: bool
    reason: str


class SecurityGuard:
    """Security validator and confirmation gateway for tool executions."""

    def __init__(self, confirmation_callback: Optional[Callable[[str, str], bool]] = None):
        """
        Args:
            confirmation_callback: A function taking (tool_name, description) -> bool.
                                   If None, default terminal prompt is used.
        """
        self.confirmation_callback = confirmation_callback

    def check_permission(self, tool_name: str, permission_level: PermissionLevel, details: str = "") -> PermissionDecision:
        """Evaluate if a tool execution is allowed under security policy."""
        if permission_level == PermissionLevel.BLOCKED:
            return PermissionDecision(
                allowed=False,
                reason=f"Security Policy: Tool '{tool_name}' is blocked from execution."
            )

        if permission_level == PermissionLevel.SAFE:
            return PermissionDecision(
                allowed=True,
                reason=f"Tool '{tool_name}' is classified as SAFE."
            )

        if permission_level == PermissionLevel.CONFIRMATION_REQUIRED:
            if self.confirmation_callback:
                approved = self.confirmation_callback(tool_name, details)
            else:
                approved = self._default_prompt(tool_name, details)

            if approved:
                return PermissionDecision(
                    allowed=True,
                    reason=f"User manually approved execution of '{tool_name}'."
                )
            else:
                return PermissionDecision(
                    allowed=False,
                    reason=f"User rejected execution of '{tool_name}'."
                )

        return PermissionDecision(allowed=False, reason="Unknown permission level.")

    def _default_prompt(self, tool_name: str, details: str) -> bool:
        """Default fallback terminal confirmation prompt."""
        prompt_text = f"\n[SECURITY CONFIRMATION] Allow tool '{tool_name}' to run? ({details}) [y/N]: "
        try:
            choice = input(prompt_text).strip().lower()
            return choice in ("y", "yes")
        except (KeyboardInterrupt, EOFError):
            return False
