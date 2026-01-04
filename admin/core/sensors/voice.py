"""Voice Sensor - ZDL Pattern.


Tracks: voice input, TTS output, transcription, speaker changes.

Usage:
    sensor = VoiceSensor(tenant_id="tenant-123")
    sensor.capture_voice_input(audio_data=bytes, session_id="...")
    sensor.capture_tts_output(text="Hello", session_id="...")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from admin.core.sensors.base import BaseSensor

logger = logging.getLogger(__name__)


class VoiceSensor(BaseSensor):
    """Voice sensor for Zero Data Loss.

    Captures:
    - Voice input (audio received)
    - Transcription results
    - TTS output (text-to-speech)
    - Speaker changes
    - Voice errors
    """

    sensor_name = "voice"
    target_service = "somabrain"

    def capture_voice_input(
        self,
        session_id: str,
        audio_format: str = "wav",
        duration_ms: int = 0,
        sample_rate: int = 16000,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Capture voice input received."""
        return self.capture(
            event_type="voice.input",
            data={
                "session_id": session_id,
                "audio_format": audio_format,
                "duration_ms": duration_ms,
                "sample_rate": sample_rate,
                "metadata": metadata or {},
            },
        )

    def capture_transcription(
        self,
        session_id: str,
        text: str,
        confidence: float = 1.0,
        language: str = "en",
        provider: str = "whisper",
        duration_ms: int = 0,
    ) -> str:
        """Capture transcription result."""
        return self.capture(
            event_type="voice.transcription",
            data={
                "session_id": session_id,
                "text": text,
                "confidence": confidence,
                "language": language,
                "provider": provider,
                "duration_ms": duration_ms,
            },
        )

    def capture_tts_output(
        self,
        session_id: str,
        text: str,
        voice_id: str = "default",
        provider: str = "kokoro",
        duration_ms: int = 0,
    ) -> str:
        """Capture TTS output generated."""
        return self.capture(
            event_type="voice.tts",
            data={
                "session_id": session_id,
                "text": text,
                "voice_id": voice_id,
                "provider": provider,
                "duration_ms": duration_ms,
            },
        )

    def capture_speaker_change(
        self,
        session_id: str,
        speaker_id: str,
        speaker_name: str = None,
    ) -> str:
        """Capture speaker change event."""
        return self.capture(
            event_type="voice.speaker_change",
            data={
                "session_id": session_id,
                "speaker_id": speaker_id,
                "speaker_name": speaker_name,
            },
        )

    def capture_voice_error(
        self,
        session_id: str,
        error: str,
        error_type: str = "transcription",
    ) -> str:
        """Capture voice processing error."""
        return self.capture(
            event_type="voice.error",
            data={
                "session_id": session_id,
                "error": error,
                "error_type": error_type,
            },
        )
