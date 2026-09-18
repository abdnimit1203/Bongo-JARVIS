"""Configuration management for Bongo-JARVIS."""
import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings(BaseModel):
    """Application settings schema."""
    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "Bongo-JARVIS"))
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
    default_model: str = Field(default_factory=lambda: os.getenv("DEFAULT_MODEL", "qwen2.5:3b"))
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "False").lower() in ("true", "1", "t"))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    
    # Voice Settings (Milestone 4)
    stt_model: str = Field(default_factory=lambda: os.getenv("STT_MODEL", "base"))
    stt_compute_type: str = Field(default_factory=lambda: os.getenv("STT_COMPUTE_TYPE", "int8"))
    tts_enabled: bool = Field(default_factory=lambda: os.getenv("TTS_ENABLED", "True").lower() in ("true", "1", "t"))
    
    root_dir: Path = ROOT_DIR


settings = Settings()
