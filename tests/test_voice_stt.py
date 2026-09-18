"""Unit tests for Local STT (faster-whisper)."""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from app.voice.stt import LocalSTT


def test_stt_initial_state():
    """Verify STT engine starts in lazy state without loading model immediately."""
    stt = LocalSTT(model_name="base")
    assert stt.is_loaded() is False
    assert stt.model_name == "base"


def test_stt_empty_audio_handling():
    """Verify transcribing empty audio returns clean failure without crash."""
    stt = LocalSTT(model_name="base")
    ok, msg = stt.transcribe_audio_array(np.array([], dtype=np.float32))
    assert ok is False
    assert "empty" in msg.lower()


def test_stt_mock_transcription():
    """Verify audio array transcription flow with mock whisper model."""
    stt = LocalSTT(model_name="base")
    
    mock_segment = MagicMock()
    mock_segment.text = "Hello JARVIS"
    mock_info = MagicMock()
    
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    stt._model = mock_model

    dummy_audio = np.zeros(16000, dtype=np.float32)
    ok, text = stt.transcribe_audio_array(dummy_audio)
    
    assert ok is True
    assert text == "Hello JARVIS"
    mock_model.transcribe.assert_called_once()
