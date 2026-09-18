# 🤖 Bongo-JARVIS

> **A Privacy-First, Local Desktop AI Assistant tailored for Windows**  
> *Developed by ABD NIMIT*

---

## 🌟 Overview

**Bongo-JARVIS** is a local-first, modular desktop AI assistant built to operate directly on your PC without relying on third-party cloud APIs. It combines local LLM reasoning with controlled tool execution, structured security guardrails, and offline voice capabilities.

---

## 🎯 Purpose & Core Vision

- **100% Local & Private:** Runs entirely on-device with zero telemetry or external API dependencies.
- **Bilingual Interaction:** Native support for conversational English and standard Bengali (বাংলা).
- **Safe & Controlled Automation:** All desktop interactions pass through explicit permission boundaries and allowlists.
- **Hardware Optimized:** Engineered to run smoothly on standard consumer hardware without requiring dedicated high-end GPUs.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Language & Runtime** | Python 3.12+ | Core application backend and orchestration |
| **Local LLM Engine** | Ollama (`qwen2.5:3b`) | Quantized local language model reasoning |
| **Speech-to-Text (STT)** | `faster-whisper` | CPU int8 quantized offline speech recognition |
| **Text-to-Speech (TTS)** | `pyttsx3` (Windows SAPI5) | Zero-latency offline speech synthesis |
| **Audio Processing** | `sounddevice` & `numpy` | Push-to-Talk microphone capture and audio buffers |
| **CLI & Terminal UI** | `rich` | Beautiful formatted terminal output and status banners |

---

## ✨ Key Features

- 💬 **Interactive Local Chat:** Real-time token streaming with contextual conversation memory.
- 🛡️ **Security Guard & Confirmation Gate:** Risky actions require explicit user approval (`y/N`) before running.
- ⚙️ **Modular Safe Tools:**
  - 🖥️ **System Information:** View non-sensitive OS and CPU hardware specs.
  - 🌐 **Web URL Opener:** Launch verified HTTP/HTTPS links in default browser.
  - 🚀 **Allowlisted App Launcher:** Open pre-approved tools (`notepad`, `calc`, `vscode`, etc.) with user confirmation.
  - 📁 **Restricted File Tools:** Safe file read and search confined strictly to project boundaries with path-traversal protection.
- 🎙️ **Push-to-Talk Voice Mode:** Capture voice with `/voice`, transcribe offline, process with the agent, and speak the reply.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Windows 10/11 (64-bit)**
- **Python 3.12+**
- **[Ollama](https://ollama.com/)** installed and running with a local model:
  ```powershell
  ollama pull qwen2.5:3b
  ```

### 2. Setup & Installation
```powershell
# Clone the repository
git clone https://github.com/abdnimit1203/Bongo-JARVIS.git
cd Bongo-JARVIS

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install lightweight dependencies
pip install -r requirements.txt
```

### 3. Launch Bongo-JARVIS
```powershell
python -m app.main
```

---

## 💡 CLI Commands

| Command | Action |
|---|---|
| `/voice` | Trigger Push-to-Talk recording (5s audio input) |
| `/voice_info` | View microphone and TTS voice diagnostics |
| `/tts_toggle` | Toggle speech audio output On / Off |
| `/tools` | List registered tools and their security levels |
| `/models` | List installed Ollama models |
| `/clear` | Clear terminal and session history |
| `/exit` | Exit the assistant |

---

## 📜 License & Acknowledgments

This project is built for personal desktop assistance and research into efficient local agent architectures.
