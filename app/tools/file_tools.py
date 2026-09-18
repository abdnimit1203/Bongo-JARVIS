"""Safe File Tools: Read and Search within restricted safe directory boundaries."""
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from app.tools.base import BaseTool, ToolResult
from app.security.permissions import PermissionLevel
from app.config import settings

# Default allowed directories: Project Root
DEFAULT_ALLOWED_ROOTS = [settings.root_dir.resolve()]

# Explicitly blocked sensitive filenames and directories
BLOCKED_PATTERNS = {
    ".env",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "id_rsa",
    "id_ed25519",
    ".ssh",
}


def validate_safe_path(
    raw_path: str,
    allowed_roots: Optional[List[Path]] = None,
) -> Tuple[bool, Optional[Path], Optional[str]]:
    """
    Validate that a path is safe and strictly resides within allowed roots.
    Blocks directory traversal, sensitive files, and unapproved directories.
    """
    if not raw_path or not raw_path.strip():
        return False, None, "File path cannot be empty."

    roots = allowed_roots or DEFAULT_ALLOWED_ROOTS
    clean_raw = raw_path.strip()

    try:
        # If relative, resolve against project root
        p = Path(clean_raw)
        if not p.is_absolute():
            candidate = (settings.root_dir / p).resolve()
        else:
            candidate = p.resolve()

        # 1. Verify path is inside at least one allowed root
        is_inside = any(
            candidate == root or candidate.is_relative_to(root)
            for root in roots
        )

        if not is_inside:
            roots_str = ", ".join(str(r) for r in roots)
            return False, None, f"Security Block: Access denied outside allowed directory boundaries ({roots_str}). Target: '{candidate}'"

        # 2. Block sensitive files or folders in the path parts
        for part in candidate.parts:
            if part.lower() in BLOCKED_PATTERNS or part.endswith(".key") or part.endswith(".pem"):
                return False, None, f"Security Block: Access to sensitive file/directory '{part}' is restricted."

        return True, candidate, None

    except Exception as e:
        return False, None, f"Path validation error: {e}"


class ReadFileTool(BaseTool):
    """Safely read content from allowed text files."""
    name = "read_file"
    description = "Read text content of a file within the allowed project workspace."
    permission_level = PermissionLevel.SAFE
    parameters = {
        "file_path": {
            "type": "string",
            "description": "Relative or absolute path of the file to read within project boundaries."
        },
        "max_lines": {
            "type": "integer",
            "description": "Maximum number of lines to return (default 200, max 500)."
        }
    }

    MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB limit

    def execute(self, file_path: str = "", max_lines: int = 200, **kwargs) -> ToolResult:
        is_safe, valid_path, error_msg = validate_safe_path(file_path)
        if not is_safe or valid_path is None:
            return ToolResult.fail(error_msg or "Invalid file path.")

        if not valid_path.exists():
            return ToolResult.fail(f"File not found: '{valid_path}'")

        if not valid_path.is_file():
            return ToolResult.fail(f"Path is not a regular file: '{valid_path}'")

        # Check file size limit
        file_size = valid_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE_BYTES:
            return ToolResult.fail(
                f"File size ({file_size / 1024:.1f} KB) exceeds safety limit of 1 MB."
            )

        try:
            max_l = min(max(1, max_lines), 500)
            lines = []
            with open(valid_path, "r", encoding="utf-8", errors="replace") as f:
                for idx, line in enumerate(f):
                    if idx >= max_l:
                        lines.append(f"\n... [Truncated after {max_l} lines]")
                        break
                    lines.append(line)

            content = "".join(lines)
            return ToolResult.ok(content, metadata={"path": str(valid_path), "size_bytes": file_size})
        except Exception as e:
            return ToolResult.fail(f"Failed to read file '{valid_path}': {e}")


class SearchFilesTool(BaseTool):
    """Safely search for files matching a pattern in allowed directories."""
    name = "search_files"
    description = "Search for files matching a glob pattern (e.g. '*.py', '*.md') within project workspace."
    permission_level = PermissionLevel.SAFE
    parameters = {
        "pattern": {
            "type": "string",
            "description": "Glob search pattern, e.g. '*.py' or '*config*'"
        },
        "subfolder": {
            "type": "string",
            "description": "Optional subfolder to search within (e.g. 'app' or 'tests')."
        }
    }

    MAX_RESULTS = 50

    def execute(self, pattern: str = "*", subfolder: str = "", **kwargs) -> ToolResult:
        target_dir = subfolder.strip() if subfolder else "."
        is_safe, search_path, error_msg = validate_safe_path(target_dir)
        if not is_safe or search_path is None:
            return ToolResult.fail(error_msg or "Invalid search directory.")

        if not search_path.exists() or not search_path.is_dir():
            return ToolResult.fail(f"Search path is not a valid directory: '{search_path}'")

        try:
            matches: List[str] = []
            for item in search_path.rglob(pattern or "*"):
                # Filter out blocked patterns
                if any(part.lower() in BLOCKED_PATTERNS for part in item.parts):
                    continue

                if item.is_file():
                    try:
                        rel_path = item.relative_to(settings.root_dir)
                        matches.append(str(rel_path))
                    except ValueError:
                        matches.append(str(item))

                if len(matches) >= self.MAX_RESULTS:
                    matches.append(f"... [Capped at {self.MAX_RESULTS} results]")
                    break

            if not matches:
                return ToolResult.ok(f"No files found matching pattern '{pattern}' in '{target_dir}'.")

            output = f"Found {len(matches)} matching file(s):\n" + "\n".join(f"- {m}" for m in matches)
            return ToolResult.ok(output, metadata={"count": len(matches)})
        except Exception as e:
            return ToolResult.fail(f"File search failed: {e}")
