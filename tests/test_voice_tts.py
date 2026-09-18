"""Unit tests for Local TTS (Windows SAPI5 voice inspection & speech)."""
import pytest
from unittest.mock import MagicMock, patch
from app.voice.tts import LocalTTS


def test_tts_text_cleaning():
    """Verify markdown and code removal for spoken audio."""
    raw = "Here is the code: ```python\nprint('hello')\n``` And a link [Google](https://google.com)"
    cleaned = LocalTTS.clean_text_for_speech(raw)
    assert "print('hello')" not in cleaned
    assert "https://google.com" not in cleaned
    assert "Here is the code" in cleaned


def test_tts_bengali_detection():
    """Verify detection of Bengali unicode text."""
    assert LocalTTS.is_bengali_text("আমি ভালো আছি") is True
    assert LocalTTS.is_bengali_text("Hello, how are you?") is False
    assert LocalTTS.is_bengali_text("Mixed: Hello বাংলা") is True


def test_tts_voice_scanning():
    """Verify TTS engine initializes and detects voices."""
    tts = LocalTTS(enabled=True)
    assert isinstance(tts.installed_voices, list)
    # On Windows test runner, English voice should exist
    assert tts.has_english_voice() is True


def test_tts_bangla_voice_handling_when_missing():
    """Verify graceful handling when Bangla SAPI5 voice is not installed."""
    tts = LocalTTS(enabled=True)
    # Ensure Bangla voice is None for test
    tts.bangla_voice_id = None
    
    ok, msg = tts.speak("আজকে আবহাওয়া কেমন?")
    assert ok is False
    assert "Bangla voice is not installed" in msg


def test_tts_english_speech_mock():
    """Verify English speech dispatch."""
    tts = LocalTTS(enabled=True)
    if tts._engine:
        with patch.object(tts._engine, "say") as mock_say, patch.object(tts._engine, "runAndWait"):
            ok, msg = tts.speak("Hello, sir. All systems are operational.")
            assert ok is True
            mock_say.assert_called_once()
