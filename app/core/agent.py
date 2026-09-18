"""Agent Orchestrator coordinating LLM reasoning, tools, and security."""
import json
import re
from typing import Generator, List, Optional, Tuple, Dict, Any

from app.llm.client import OllamaClient, ChatMessage
from app.llm.prompts import build_system_prompt
from app.tools.registry import ToolRegistry
from app.tools.base import ToolResult
from app.security.permissions import SecurityGuard


class Agent:
    """Core Agent coordinating reasoning, tool calling loop, and security."""

    def __init__(
        self,
        llm_client: Optional[OllamaClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        security_guard: Optional[SecurityGuard] = None,
    ):
        self.client = llm_client or OllamaClient()
        self.security_guard = security_guard or SecurityGuard()
        self.registry = tool_registry or ToolRegistry(security_guard=self.security_guard)

    def _parse_tool_call(self, text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Extract structured tool call from LLM response text if present.
        Handles markdown blocks, raw JSON strings, and embedded JSON with nested objects.
        """
        clean_text = text.strip()

        # 1. Try markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, dict) and "tool" in data:
                    tool_name = data.get("tool", "")
                    tool_args = data.get("arguments", {})
                    if tool_name and isinstance(tool_args, dict):
                        return tool_name, tool_args
            except Exception:
                pass

        # 2. Try parsing the entire clean_text directly as JSON
        try:
            data = json.loads(clean_text)
            if isinstance(data, dict) and "tool" in data:
                tool_name = data.get("tool", "")
                tool_args = data.get("arguments", {})
                if tool_name and isinstance(tool_args, dict):
                    return tool_name, tool_args
        except Exception:
            pass

        # 3. Find balanced JSON structures within text
        start_idx = clean_text.find("{")
        while start_idx != -1:
            brace_count = 0
            in_string = False
            escape = False
            end_idx = -1

            for i in range(start_idx, len(clean_text)):
                char = clean_text[i]
                if escape:
                    escape = False
                    continue
                if char == "\\":
                    escape = True
                    continue
                if char == '"':
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break

            if end_idx != -1:
                candidate = clean_text[start_idx:end_idx]
                try:
                    data = json.loads(candidate)
                    if isinstance(data, dict) and "tool" in data:
                        tool_name = data.get("tool", "")
                        tool_args = data.get("arguments", {})
                        if tool_name and isinstance(tool_args, dict):
                            return tool_name, tool_args
                except Exception:
                    pass

            start_idx = clean_text.find("{", start_idx + 1)

        return None

    def process_turn(
        self,
        user_input: str,
        conversation_history: List[ChatMessage],
    ) -> Generator[str, None, None]:
        """
        Execute one conversational/agent turn.
        Yields tokens/chunks for real-time streaming output to the UI.
        """
        tool_schemas = self.registry.get_schemas()
        system_prompt = build_system_prompt(tool_schemas)

        # Build working context for LLM
        working_messages = [ChatMessage(role="system", content=system_prompt)]
        
        # Add past history (skipping previous system prompt)
        for msg in conversation_history:
            if msg.role != "system":
                working_messages.append(msg)

        # Add current user input
        working_messages.append(ChatMessage(role="user", content=user_input))

        # First pass: Ask LLM (non-streaming to check for tool invocation quickly)
        first_pass_reply = self.client.chat(messages=working_messages, temperature=0.2)
        tool_call = self._parse_tool_call(first_pass_reply)

        if tool_call:
            tool_name, tool_args = tool_call
            yield f"[dim]⚙ Tool call requested: {tool_name}({tool_args})[/dim]\n"

            # Execute tool through security layer
            result: ToolResult = self.registry.execute(tool_name, tool_args)

            if result.success:
                yield f"[dim]✓ Tool '{tool_name}' executed successfully.[/dim]\n\n"
                tool_feedback = f"[Tool '{tool_name}' Result]:\n{result.output}"
            else:
                yield f"[dim]✗ Tool '{tool_name}' failed or was denied: {result.error}[/dim]\n\n"
                tool_feedback = f"[Tool '{tool_name}' Execution Failed]:\n{result.error}"

            # Append tool execution feedback into messages with strict grounding constraint
            working_messages.append(ChatMessage(role="assistant", content=first_pass_reply))
            grounding_instruction = (
                f"{tool_feedback}\n\n"
                "Please provide a final concise answer to the user based STRICTLY and ONLY on the tool result above. "
                "Do NOT assume, fabricate, or extrapolate unmentioned metrics (such as disk storage, battery level, or hardware temperatures)."
            )
            working_messages.append(ChatMessage(role="user", content=grounding_instruction))

            # Stream final conversational response to user
            for chunk in self.client.stream_chat(messages=working_messages, temperature=0.7):
                yield chunk

        else:
            # No tool needed: yield the first-pass response directly
            yield first_pass_reply
