"""Safe System Tools: System Info, URL Opener, and Allowlisted App Launcher."""
import os
import sys
import platform
import subprocess
import webbrowser
from urllib.parse import urlparse
from typing import Dict, Any, Optional

from app.config import settings
from app.tools.base import BaseTool, ToolResult
from app.security.permissions import PermissionLevel


class GetSystemInfoTool(BaseTool):
    """Retrieve basic non-sensitive system, hardware, and AI model information."""
    name = "get_system_info"
    description = "Get basic OS, CPU architecture, Python version, system platform, and active AI model runtime info."
    permission_level = PermissionLevel.SAFE
    parameters = {}

    def execute(self, **kwargs) -> ToolResult:
        try:
            info = {
                "os": platform.system(),
                "os_release": platform.release(),
                "os_version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
                "python_version": sys.version.split()[0],
                "active_llm_model": settings.default_model,
                "stt_engine": f"faster-whisper ({settings.stt_model}, {settings.stt_compute_type})",
                "tts_engine": f"Windows SAPI5 (enabled={settings.tts_enabled})",
            }
            output_lines = [f"{k}: {v}" for k, v in info.items()]
            return ToolResult.ok("\n".join(output_lines), metadata=info)
        except Exception as e:
            return ToolResult.fail(f"Failed to retrieve system info: {e}")


class OpenUrlTool(BaseTool):
    """Safely open web URLs in default browser without downloading or executing content."""
    name = "open_url"
    description = (
        "Open a web URL (http/https) in the default browser. Use this tool whenever the user wants to "
        "search YouTube, search Google, visit websites, view online videos, or open web services "
        "(e.g., construct 'https://www.youtube.com/results?search_query=...' or 'https://www.google.com/search?q=...')."
    )
    permission_level = PermissionLevel.SAFE
    parameters = {
        "url": {
            "type": "string",
            "description": "The full HTTP or HTTPS URL to open in browser (e.g. 'https://www.youtube.com/results?search_query=mrbeast' or 'https://www.google.com')"
        }
    }

    def execute(self, url: str = "", **kwargs) -> ToolResult:
        url = url.strip()
        if not url:
            return ToolResult.fail("URL cannot be empty.")

        # Parse and validate scheme
        try:
            parsed = urlparse(url)
            if not parsed.scheme or parsed.scheme.lower() not in ("http", "https"):
                return ToolResult.fail(
                    f"Security Block: Only 'http' and 'https' protocols are allowed. Rejected: '{parsed.scheme}'"
                )
            if not parsed.netloc:
                return ToolResult.fail("Invalid URL structure (missing domain name).")

            # Open in system default web browser
            webbrowser.open(url, new=2)
            return ToolResult.ok(f"Successfully requested browser to open: {url}")
        except Exception as e:
            return ToolResult.fail(f"Failed to open URL '{url}': {e}")


class OpenApplicationTool(BaseTool):
    """Open safe allowlisted desktop applications with user confirmation."""
    name = "open_application"
    description = (
        "Launch an approved local desktop executable (notepad, calculator, paint, explorer, vscode). "
        "Do NOT use this tool for websites, web searches, or online media (use open_url instead)."
    )
    permission_level = PermissionLevel.CONFIRMATION_REQUIRED
    parameters = {
        "app_name": {
            "type": "string",
            "description": "Name of the allowlisted local desktop application: 'notepad', 'calc', 'paint', 'explorer', 'vscode'",
            "enum": ["notepad", "calc", "calculator", "paint", "mspaint", "explorer", "vscode", "code"]
        }
    }

    # Strict explicit allowlist mapping alias to executable target
    APP_ALLOWLIST: Dict[str, list[str]] = {
        "notepad": ["notepad.exe"],
        "calc": ["calc.exe"],
        "calculator": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "mspaint": ["mspaint.exe"],
        "explorer": ["explorer.exe"],
        "vscode": ["code"],
        "code": ["code"],
    }

    def execute(self, app_name: str = "", **kwargs) -> ToolResult:
        normalized_name = app_name.strip().lower()
        if not normalized_name:
            return ToolResult.fail("Application name cannot be empty.")

        if normalized_name not in self.APP_ALLOWLIST:
            allowed_list = ", ".join(sorted(self.APP_ALLOWLIST.keys()))
            return ToolResult.fail(
                f"Security Block: Application '{app_name}' is not in the approved allowlist. Allowed applications: {allowed_list}"
            )

        cmd = self.APP_ALLOWLIST[normalized_name]

        try:
            # Safe spawn without shell=True
            subprocess.Popen(cmd, shell=False)
            return ToolResult.ok(f"Successfully launched application '{normalized_name}'.")
        except FileNotFoundError:
            return ToolResult.fail(f"Application executable for '{normalized_name}' was not found on this system.")
        except Exception as e:
            return ToolResult.fail(f"Failed to launch '{normalized_name}': {e}")
