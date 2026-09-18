"""Unit tests for VoiceEngine coordinator and graceful degradation."""
import pytest
from unittest.mock import MagicMock
from app.voice.engine import VoiceEngine
from app.voice.stt import LocalSTT
from app.voice.tts import LocalTTS
from app.voice.recorder import AudioRecorder


def test_voice_engine_diagnostics():
    """Verify VoiceEngine provides complete diagnostics dictionary."""
    engine = VoiceEngine()
    diag = engine.get_diagnostics()
    assert "microphone_available" in diag
    assert "stt_model" in diag
    assert "tts_available" in diag
    assert "tts_has_bangla_voice" in diag


def test_voice_engine_recorder_failure_handling():
    """Verify VoiceEngine handles recorder failure gracefully."""
    mock_recorder = MagicMock()
    mock_recorder.record.return_value = (False, None, "Microphone disconnected")
    
    engine = VoiceEngine(recorder=mock_recorder)
    ok, msg = engine.record_and_transcribe()
    
    assert ok is False
    assert "Microphone disconnected" in msg
