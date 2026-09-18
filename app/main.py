"""Bongo-JARVIS Interactive Terminal CLI."""
import sys
from typing import List, Optional

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.config import settings
from app.llm.client import OllamaClient, ChatMessage, OllamaClientError
from app.core.agent import Agent
from app.tools.registry import ToolRegistry
from app.security.permissions import SecurityGuard
from app.tools.system_tools import GetSystemInfoTool, OpenUrlTool, OpenApplicationTool
from app.tools.file_tools import ReadFileTool, SearchFilesTool
from app.voice import VoiceEngine

console = Console(force_terminal=True, legacy_windows=False)


def create_default_registry(guard: SecurityGuard) -> ToolRegistry:
    """Create and register all approved safe tools."""
    registry = ToolRegistry(security_guard=guard)
    registry.register(GetSystemInfoTool())
    registry.register(OpenUrlTool())
    registry.register(OpenApplicationTool())
    registry.register(ReadFileTool())
    registry.register(SearchFilesTool())
    return registry


def print_banner(client: OllamaClient, registry: ToolRegistry, voice_engine: Optional[VoiceEngine] = None):
    """Display startup banner, models, tools, and voice info."""
    ollama_ok = client.check_health()
    models = []
    if ollama_ok:
        try:
            models = client.list_models()
        except Exception:
            pass

    tools = registry.list_tools()

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Version:", "0.5.0 (Milestone 4: Voice & Tools)")
    table.add_row("Python:", sys.version.split()[0])
    table.add_row("Ollama URL:", settings.ollama_base_url)
    table.add_row("Active Model:", f"[bold green]{settings.default_model}[/bold green]")
    table.add_row(
        "Ollama Status:",
        f"[green]Online ({len(models)} model{'s' if len(models) != 1 else ''} available)[/green]"
        if ollama_ok
        else "[bold red]Offline (Ollama server not responding)[/bold red]"
    )
    table.add_row("Active Tools:", f"[cyan]{len(tools)} registered[/cyan]")

    if voice_engine:
        diag = voice_engine.get_diagnostics()
        mic_status = f"[green]Available ({diag['microphone_name']})[/green]" if diag["microphone_available"] else "[yellow]No mic detected[/yellow]"
        tts_status = f"[green]Active ({diag['tts_english_voice']})[/green]" if diag["tts_available"] else "[yellow]Disabled[/yellow]"
        table.add_row("Microphone:", mic_status)
        table.add_row("STT Model:", f"faster-whisper ({diag['stt_model']}, {diag['stt_compute_type']})")
        table.add_row("TTS Status:", tts_status)

    panel = Panel(
        table,
        title="[bold blue]Bongo-JARVIS Local AI Assistant[/bold blue]",
        subtitle="[dim]Commands: /voice, /voice_info, /tools, /models, /clear, /exit, /help[/dim]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def print_help():
    """Display available CLI commands."""
    table = Table(title="Available Commands", box=None, padding=(0, 2))
    table.add_column("Command", style="bold cyan")
    table.add_column("Description", style="white")
    table.add_row("/voice", "Trigger Push-to-Talk (records 5s audio -> transcribes -> processes)")
    table.add_row("/voice_info", "Display microphone, STT model, and SAPI5 TTS voice status")
    table.add_row("/tts_toggle", "Toggle TTS speech output On / Off")
    table.add_row("/tools", "List registered tools and permissions")
    table.add_row("/models", "List installed local Ollama models")
    table.add_row("/clear", "Clear terminal screen and conversation history")
    table.add_row("/exit, /quit", "Exit the assistant")
    table.add_row("/help", "Show this help table")
    console.print(table)


def print_tools(registry: ToolRegistry):
    """Display registered tools."""
    tools = registry.list_tools()
    if not tools:
        console.print("[dim]No tools currently registered.[/dim]\n")
        return

    table = Table(title="Registered Tools", box=None, padding=(0, 2))
    table.add_column("Tool Name", style="bold cyan")
    table.add_column("Permission Level", style="yellow")
    table.add_column("Description", style="white")

    for t in tools:
        table.add_row(t.name, t.permission_level.value, t.description)
    console.print(table)
    console.print()


def print_voice_diagnostics(voice_engine: VoiceEngine):
    """Display detailed voice diagnostics."""
    diag = voice_engine.get_diagnostics()
    table = Table(title="Voice Subsystem Diagnostics", box=None, padding=(0, 2))
    table.add_column("Component", style="bold cyan")
    table.add_column("Status / Details", style="white")

    table.add_row("Microphone Available:", "Yes" if diag["microphone_available"] else "[yellow]No[/yellow]")
    table.add_row("Microphone Device:", str(diag["microphone_name"]))
    table.add_row("STT Engine:", "faster-whisper (CPU / int8)")
    table.add_row("STT Model:", str(diag["stt_model"]))
    table.add_row("STT Model Loaded:", "Yes" if diag["stt_loaded"] else "No (Loads lazily on first recording)")
    table.add_row("TTS Engine:", "Windows SAPI5")
    table.add_row("TTS Enabled:", "Yes" if diag["tts_enabled"] else "No")
    table.add_row("TTS English Voice:", str(diag["tts_english_voice"]))
    table.add_row("TTS Bangla Voice Installed:", "[green]Yes[/green]" if diag["tts_has_bangla_voice"] else "[yellow]No (Bangla responses will display text without speech)[/yellow]")
    
    console.print(table)
    console.print()


def handle_agent_turn(agent: Agent, user_input: str, history: List[ChatMessage], voice_engine: Optional[VoiceEngine] = None):
    """Process a user query through the agent and optionally speak the response."""
    console.print("[bold green]JARVIS > [/bold green]", end="")
    full_response = []

    try:
        for chunk in agent.process_turn(user_input=user_input, conversation_history=history):
            print(chunk, end="", flush=True)
            full_response.append(chunk)
        print("\n")

        assistant_reply = "".join(full_response).strip()
        
        # Update conversation history
        history.append(ChatMessage(role="user", content=user_input))
        history.append(ChatMessage(role="assistant", content=assistant_reply))

        # Speak response via TTS if voice engine is enabled
        if voice_engine and voice_engine.tts.enabled:
            spk_ok, spk_msg = voice_engine.speak(assistant_reply)
            if not spk_ok and "Bangla voice is not installed" in spk_msg:
                console.print(f"[dim]ℹ {spk_msg}[/dim]\n")

    except OllamaClientError as err:
        console.print(f"\n[bold red]Error generating response:[/] {err}\n")
    except KeyboardInterrupt:
        console.print("\n[yellow][Generation interrupted by user][/yellow]\n")


def run_chat_loop():
    """Interactive agent loop with Push-to-Talk voice integration."""
    client = OllamaClient()
    guard = SecurityGuard()
    registry = create_default_registry(guard)
    agent = Agent(llm_client=client, tool_registry=registry, security_guard=guard)

    # Initialize Voice Engine with graceful fallback
    voice_engine: Optional[VoiceEngine] = None
    try:
        voice_engine = VoiceEngine()
    except Exception as e:
        console.print(f"[yellow]Warning: Voice initialization notice: {e}. Text mode active.[/yellow]")

    print_banner(client, registry, voice_engine)

    if not client.check_health():
        console.print("[bold red]Error:[/] Cannot connect to Ollama. Please make sure Ollama is running and retry.")
        return

    history: List[ChatMessage] = []

    console.print("[bold green]JARVIS is ready.[/bold green] Type your message or enter [bold cyan]/voice[/bold cyan] to speak.\n")

    while True:
        try:
            user_input = console.input("[bold cyan]You > [/bold cyan]").strip()

            if not user_input:
                continue

            # Command Handling
            if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
                console.print("\n[bold yellow]JARVIS:[/] Goodbye, sir. Shutting down.\n")
                break

            if user_input.lower() == "/clear":
                console.clear()
                history = []
                print_banner(client, registry, voice_engine)
                console.print("[dim]Conversation history cleared.[/dim]\n")
                continue

            if user_input.lower() == "/help":
                print_help()
                console.print()
                continue

            if user_input.lower() == "/tools":
                print_tools(registry)
                continue

            if user_input.lower() == "/voice_info":
                if voice_engine:
                    print_voice_diagnostics(voice_engine)
                else:
                    console.print("[yellow]Voice engine is not initialized.[/yellow]\n")
                continue

            if user_input.lower() == "/tts_toggle":
                if voice_engine:
                    voice_engine.tts.enabled = not voice_engine.tts.enabled
                    console.print(f"[cyan]TTS Speech output is now {'ENABLED' if voice_engine.tts.enabled else 'DISABLED'}.[/cyan]\n")
                continue

            if user_input.lower() == "/models":
                try:
                    models = client.list_models()
                    console.print(f"[bold cyan]Installed Models:[/] {', '.join(models) if models else 'None'}\n")
                except Exception as e:
                    console.print(f"[bold red]Failed to fetch models:[/] {e}\n")
                continue

            # Push-to-Talk Voice Trigger
            if user_input.lower() in ("/voice", "/talk"):
                if not voice_engine:
                    console.print("[yellow]Voice engine is unavailable. Please use text mode.[/yellow]\n")
                    continue

                if not voice_engine.recorder.has_input_device():
                    console.print("[yellow]No microphone detected. Please connect a microphone or use text mode.[/yellow]\n")
                    continue

                console.print("[bold red]🎙 Recording... Speak now (5 seconds)[/bold red]")
                ok, text = voice_engine.record_and_transcribe(duration_seconds=5.0)
                
                if not ok:
                    console.print(f"[yellow]Voice recognition note:[/] {text}\n")
                    continue

                console.print(f"[bold cyan]You (Voice) > [/bold cyan]{text}")
                handle_agent_turn(agent=agent, user_input=text, history=history, voice_engine=voice_engine)
                continue

            # Standard Text Mode
            handle_agent_turn(agent=agent, user_input=user_input, history=history, voice_engine=voice_engine)

        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]JARVIS:[/] Session terminated. Goodbye!\n")
            break
        except EOFError:
            break


def main():
    """Main execution function."""
    run_chat_loop()


if __name__ == "__main__":
    main()
