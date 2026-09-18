"""Local Text-to-Speech (TTS) using Windows SAPI5 with dynamic voice detection."""
import re
from typing import Optional, List, Dict, Tuple
from app.config import settings


class LocalTTS:
    """Windows SAPI5 TTS wrapper with language and voice availability inspection."""

    def __init__(self, enabled: Optional[bool] = None):
        self.enabled = settings.tts_enabled if enabled is None else enabled
        self._engine = None
        self.is_available = False
        self.english_voice_id: Optional[str] = None
        self.english_voice_name: Optional[str] = None
        self.bangla_voice_id: Optional[str] = None
        self.bangla_voice_name: Optional[str] = None
        self.installed_voices: List[Dict[str, str]] = []

        if self.enabled:
            self._init_engine()

    def _init_engine(self):
        """Initialize pyttsx3 engine and inspect installed voices."""
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 175)  # Standard clear speaking rate
            self._engine.setProperty("volume", 0.9)
            self._scan_voices()
            self.is_available = True
        except Exception as e:
            self.is_available = False
            self._engine = None

    def _scan_voices(self):
        """Detect installed SAPI5 voices and categorize by language."""
        if not self._engine:
            return

        try:
            voices = self._engine.getProperty("voices") or []
            for v in voices:
                v_id = getattr(v, "id", "")
                v_name = getattr(v, "name", "")
                v_lang = str(getattr(v, "languages", "")).lower()

                voice_info = {
                    "id": v_id,
                    "name": v_name,
                    "languages": v_lang,
                }
                self.installed_voices.append(voice_info)

                lower_name = v_name.lower()
                lower_id = v_id.lower()

                # Check for Bangla voice
                if "bangla" in lower_name or "bengali" in lower_name or "bn" in v_lang or "bangla" in lower_id:
                    self.bangla_voice_id = v_id
                    self.bangla_voice_name = v_name
                # Check for English voice
                elif "english" in lower_name or "en" in v_lang or "david" in lower_name or "zira" in lower_name:
                    if not self.english_voice_id:
                        self.english_voice_id = v_id
                        self.english_voice_name = v_name

            # If default voice exists and no specific english selected
            if voices and not self.english_voice_id:
                self.english_voice_id = voices[0].id
                self.english_voice_name = voices[0].name

        except Exception:
            pass

    def has_bangla_voice(self) -> bool:
        """Return True if a verified Bangla SAPI5 voice is installed."""
        return self.bangla_voice_id is not None

    def has_english_voice(self) -> bool:
        """Return True if a verified English SAPI5 voice is installed."""
        return self.english_voice_id is not None

    @staticmethod
    def is_bengali_text(text: str) -> bool:
        """Check if the text contains Bengali unicode characters."""
        return bool(re.search(r"[\u0980-\u09FF]", text))

    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """Clean markdown symbols, code blocks, and formatting before speaking."""
        # Remove code blocks
        clean = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        clean = re.sub(r"`.*?`", "", clean)
        # Remove markdown headers and formatting
        clean = re.sub(r"[#*_~>\[\]\(\)]", " ", clean)
        # Remove urls
        clean = re.sub(r"https?://\S+", "", clean)
        # Clean excess whitespace
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def speak(self, text: str) -> Tuple[bool, str]:
        """
        Speak the provided text if an appropriate voice is available.
        Returns (success: bool, status_message: str).
        """
        if not self.enabled:
            return False, "TTS is disabled."

        if not self.is_available or not self._engine:
            return False, "TTS engine is not initialized."

        clean_text = self.clean_text_for_speech(text)
        if not clean_text:
            return False, "No speakable text found."

        # Check if text is Bengali
        if self.is_bengali_text(clean_text):
            if not self.has_bangla_voice():
                return False, "Bangla voice is not installed in Windows SAPI5. Text displayed without audio."
            else:
                target_voice = self.bangla_voice_id
        else:
            target_voice = self.english_voice_id

        try:
            if target_voice:
                self._engine.setProperty("voice", target_voice)
            self._engine.say(clean_text)
            self._engine.runAndWait()
            return True, "Speech completed."
        except Exception as e:
            return False, f"TTS execution failed: {e}"
