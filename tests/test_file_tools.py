"""Tests for Safe File Tools (Read and Search with Path Traversal Guards)."""
import pytest
from pathlib import Path
from app.tools.file_tools import ReadFileTool, SearchFilesTool, validate_safe_path
from app.config import settings


def test_validate_safe_path_valid():
    """Verify paths within project root are allowed."""
    is_safe, p, err = validate_safe_path("requirements.txt")
    assert is_safe is True
    assert p is not None
    assert p.exists()


def test_validate_safe_path_traversal_blocked():
    """Verify path traversal (..) attempting to escape project root is blocked."""
    is_safe, p, err = validate_safe_path("../../../../Windows/System32/drivers/etc/hosts")
    assert is_safe is False
    assert "Security Block" in err


def test_validate_safe_path_sensitive_blocked():
    """Verify sensitive files like .env and .git are blocked from reading."""
    # .env
    is_safe_env, _, err_env = validate_safe_path(".env")
    assert is_safe_env is False
    assert "sensitive file" in err_env.lower()

    # .git/config
    is_safe_git, _, err_git = validate_safe_path(".git/config")
    assert is_safe_git is False
    assert "sensitive file" in err_git.lower()


def test_read_file_tool_success():
    """Verify reading an approved file in project workspace."""
    tool = ReadFileTool()
    res = tool.execute(file_path="requirements.txt")
    assert res.success is True
    assert "httpx" in res.output


def test_read_file_tool_blocked():
    """Verify reading blocked paths fails cleanly."""
    tool = ReadFileTool()
    res = tool.execute(file_path=".env")
    assert res.success is False
    assert "Security Block" in res.error


def test_search_files_tool():
    """Verify search tool finds matching files in project directory."""
    tool = SearchFilesTool()
    res = tool.execute(pattern="*.py", subfolder="app")
    assert res.success is True
    assert "main.py" in res.output
    assert "config.py" in res.output
