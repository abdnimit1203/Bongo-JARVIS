"""Tests for Safe System Tools."""
import pytest
from unittest.mock import patch
from app.tools.system_tools import GetSystemInfoTool, OpenUrlTool, OpenApplicationTool


def test_get_system_info():
    """Verify system info tool returns valid OS and environment details."""
    tool = GetSystemInfoTool()
    res = tool.execute()
    assert res.success is True
    assert "os:" in res.output.lower()
    assert "python_version:" in res.output.lower()


def test_open_url_valid():
    """Verify valid http/https URLs are permitted."""
    tool = OpenUrlTool()
    with patch("webbrowser.open") as mock_open:
        res = tool.execute(url="https://www.google.com")
        assert res.success is True
        assert "Successfully requested browser to open" in res.output
        mock_open.assert_called_once_with("https://www.google.com", new=2)


def test_open_url_blocked_schemes():
    """Verify dangerous non-http schemes are blocked."""
    tool = OpenUrlTool()
    
    # 1. file://
    res_file = tool.execute(url="file:///C:/Windows/System32/cmd.exe")
    assert res_file.success is False
    assert "Security Block" in res_file.error

    # 2. javascript:
    res_js = tool.execute(url="javascript:alert(1)")
    assert res_js.success is False
    assert "Security Block" in res_js.error

    # 3. empty
    res_empty = tool.execute(url="")
    assert res_empty.success is False


def test_open_application_allowlist():
    """Verify only allowlisted applications are permitted."""
    tool = OpenApplicationTool()

    # 1. Blocked / unallowlisted application
    res_blocked = tool.execute(app_name="powershell.exe")
    assert res_blocked.success is False
    assert "Security Block" in res_blocked.error
    assert "not in the approved allowlist" in res_blocked.error

    # 2. Approved application alias
    with patch("subprocess.Popen") as mock_popen:
        res_approved = tool.execute(app_name="notepad")
        assert res_approved.success is True
        assert "Successfully launched" in res_approved.output
        mock_popen.assert_called_once_with(["notepad.exe"], shell=False)
