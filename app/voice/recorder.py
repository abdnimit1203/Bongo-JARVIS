"""Safe Audio Recorder using sounddevice for Push-to-Talk."""
from typing import Optional, Tuple
import numpy as np


class AudioRecorder:
    """Microphone audio capture for push-to-talk interactions."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    @staticmethod
    def has_input_device() -> bool:
        """Check if an audio input device is available."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            for d in devices:
                if d.get("max_input_channels", 0) > 0:
                    return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_input_device_name() -> Optional[str]:
        """Get the name of the default or first available input device."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            default_in = sd.default.device[0]
            if default_in is not None and default_in >= 0 and default_in < len(devices):
                return devices[default_in].get("name")
            for d in devices:
                if d.get("max_input_channels", 0) > 0:
                    return d.get("name")
            return None
        except Exception:
            return None

    def record(self, duration_seconds: float = 5.0) -> Tuple[bool, Optional[np.ndarray], str]:
        """
        Record audio from the microphone for a fixed duration.
        Returns (success: bool, audio_array: Optional[np.ndarray], message: str).
        """
        if not self.has_input_device():
            return False, None, "No microphone or audio input device detected."

        try:
            import sounddevice as sd
            num_samples = int(duration_seconds * self.sample_rate)
            
            # Record mono audio in float32 format
            audio_buffer = sd.rec(
                num_samples,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32"
            )
            sd.wait()

            audio_data = audio_buffer.squeeze()
            return True, audio_data, f"Recorded {duration_seconds:.1f}s of audio."
        except Exception as e:
            return False, None, f"Audio recording failed: {e}"
