"""Local Speech-to-Text (STT) using faster-whisper with lazy CPU loading."""
from typing import Optional, Tuple
import numpy as np
from app.config import settings


class LocalSTT:
    """Offline STT engine wrapping faster-whisper on CPU."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        compute_type: Optional[str] = None,
        device: str = "cpu",
    ):
        self.model_name = model_name or settings.stt_model
        self.compute_type = compute_type or settings.stt_compute_type
        self.device = device
        self._model = None
        self.is_available = True

    def is_loaded(self) -> bool:
        """Return True if the whisper model is already loaded in memory."""
        return self._model is not None

    def load_model(self) -> Tuple[bool, str]:
        """Explicitly load the faster-whisper model."""
        if self._model is not None:
            return True, f"Model '{self.model_name}' already loaded."

        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                model_size_or_path=self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=4,
            )
            return True, f"Successfully loaded faster-whisper model '{self.model_name}' (device={self.device}, compute={self.compute_type})."
        except Exception as e:
            self._model = None
            self.is_available = False
            return False, f"Failed to load faster-whisper model '{self.model_name}': {e}"

    def transcribe_audio_array(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Transcribe audio data from a 1D float32 numpy array.
        Returns (success: bool, transcription_or_error: str).
        """
        if audio_data is None or len(audio_data) == 0:
            return False, "Audio buffer is empty."

        # Ensure model is loaded
        if not self.is_loaded():
            ok, msg = self.load_model()
            if not ok:
                return False, msg

        try:
            # Ensure float32 1D array
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            if audio_data.ndim > 1:
                audio_data = audio_data.squeeze()

            segments, info = self._model.transcribe(
                audio_data,
                beam_size=3,
                language=language,
                vad_filter=True,
            )

            text_parts = [segment.text.strip() for segment in segments]
            full_text = " ".join(text_parts).strip()
            return True, full_text
        except Exception as e:
            return False, f"Transcription error: {e}"

    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> Tuple[bool, str]:
        """Transcribe an audio file from disk."""
        if not self.is_loaded():
            ok, msg = self.load_model()
            if not ok:
                return False, msg

        try:
            segments, info = self._model.transcribe(
                file_path,
                beam_size=3,
                language=language,
                vad_filter=True,
            )
            text_parts = [segment.text.strip() for segment in segments]
            full_text = " ".join(text_parts).strip()
            return True, full_text
        except Exception as e:
            return False, f"File transcription error: {e}"
