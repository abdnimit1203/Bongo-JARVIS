"""VoiceEngine coordinating STT, TTS, and Audio Capture."""
from typing import Optional, Tuple, Dict, Any

from app.voice.stt import LocalSTT
from app.voice.tts import LocalTTS
from app.voice.recorder import AudioRecorder


class VoiceEngine:
    """Modular coordinator for offline voice input and output."""

    def __init__(
        self,
        stt: Optional[LocalSTT] = None,
        tts: Optional[LocalTTS] = None,
        recorder: Optional[AudioRecorder] = None,
    ):
        self.stt = stt or LocalSTT()
        self.tts = tts or LocalTTS()
        self.recorder = recorder or AudioRecorder()

    def record_and_transcribe(
        self,
        duration_seconds: float = 5.0,
        language: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Capture microphone audio via Push-to-Talk and transcribe it.
        Returns (success: bool, text_or_error: str).
        """
        ok, audio_data, msg = self.recorder.record(duration_seconds=duration_seconds)
        if not ok or audio_data is None:
            return False, msg

        # Transcribe captured audio
        stt_ok, text = self.stt.transcribe_audio_array(
            audio_data=audio_data,
            sample_rate=self.recorder.sample_rate,
            language=language,
        )
        if not stt_ok or not text.strip():
            return False, text or "No audible speech detected."

        return True, text.strip()

    def speak(self, text: str) -> Tuple[bool, str]:
        """Convert text to speech."""
        return self.tts.speak(text)

    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic status of voice components."""
        return {
            "microphone_available": self.recorder.has_input_device(),
            "microphone_name": self.recorder.get_input_device_name() or "None",
            "stt_model": self.stt.model_name,
            "stt_compute_type": self.stt.compute_type,
            "stt_loaded": self.stt.is_loaded(),
            "tts_enabled": self.tts.enabled,
            "tts_available": self.tts.is_available,
            "tts_english_voice": self.tts.english_voice_name or "None",
            "tts_has_bangla_voice": self.tts.has_bangla_voice(),
            "tts_bangla_voice": self.tts.bangla_voice_name or "None",
        }
