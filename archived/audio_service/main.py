"""Audio ingestion and transcription service for SomaAgent 01."""

from __future__ import annotations

import base64
import io
import logging
import os
import time
import uuid
from typing import Annotated

import numpy as np
import soundfile as sf
from fastapi import Depends, FastAPI, HTTPException
from faster_whisper import WhisperModel
from jsonschema import ValidationError
from pydantic import BaseModel, Field

from services.common.event_bus import KafkaEventBus, KafkaSettings
from services.common.logging_config import setup_logging
from services.common.schema_validator import validate_event
from services.common.settings_sa01 import SA01Settings
from services.common.tracing import setup_tracing

setup_logging()
LOGGER = logging.getLogger(__name__)

APP_SETTINGS = SA01Settings.from_env()
setup_tracing("audio-service", endpoint=APP_SETTINGS.otlp_endpoint)

app = FastAPI(title="SomaAgent 01 Audio Service")


def _kafka_settings() -> KafkaSettings:
    return KafkaSettings(
        bootstrap_servers=os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS", APP_SETTINGS.kafka_bootstrap_servers
        ),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM"),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME"),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD"),
    )


def _topics() -> dict[str, str]:
    defaults = APP_SETTINGS.extra.get(
        "audio_topics",
        {
            "conversation": "conversation.inbound",
            "metrics": "audio.metrics",
        },
    )
    return {
        "conversation": os.getenv(
            "AUDIO_CONVERSATION_TOPIC", defaults.get("conversation", "conversation.inbound")
        ),
        "metrics": os.getenv("AUDIO_METRICS_TOPIC", defaults.get("metrics", "audio.metrics")),
    }


def get_whisper_model() -> WhisperModel:
    model_path = os.getenv("WHISPER_MODEL", "base.en")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE", "int8")
    LOGGER.info("Loading Whisper model", extra={"model": model_path, "device": device})
    return WhisperModel(model_path, device=device, compute_type=compute_type)


def get_event_bus() -> KafkaEventBus:
    return KafkaEventBus(_kafka_settings())


class AudioPayload(BaseModel):
    session_id: str
    persona_id: str | None = None
    audio_b64: str = Field(..., description="Base64 encoded PCM audio (wav)")
    metadata: dict[str, str] = Field(default_factory=dict)


@app.post("/v1/audio/transcribe")
async def transcribe_audio(
    payload: AudioPayload,
    model: Annotated[WhisperModel, Depends(get_whisper_model)],
    bus: Annotated[KafkaEventBus, Depends(get_event_bus)],
) -> dict[str, str]:
    try:
        audio_bytes = base64.b64decode(payload.audio_b64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 audio") from exc

    samples, sample_rate = sf.read(io.BytesIO(audio_bytes))
    if samples.ndim > 1:
        samples = np.mean(samples, axis=1)

    start_time = time.time()
    segments, info = model.transcribe(samples, sample_rate=sample_rate)
    transcript = " ".join(segment.text.strip() for segment in segments).strip()
    latency = time.time() - start_time

    conversation_event = {
        "event_id": str(uuid.uuid4()),
        "session_id": payload.session_id,
        "persona_id": payload.persona_id,
        "message": transcript,
        "metadata": {**payload.metadata, "source": "audio"},
        "role": "user",
    }

    audio_metrics = {
        "event_id": str(uuid.uuid4()),
        "session_id": payload.session_id,
        "duration_seconds": info.duration,
        "language": info.language,
        "latency_seconds": latency,
        "energy": float(np.sqrt(np.mean(np.square(samples)))),
        "metadata": payload.metadata,
    }

    try:
        validate_event(conversation_event, "conversation_event")
    except ValidationError as exc:  # pragma: no cover - validation failure unlikely
        LOGGER.error("Invalid conversation event", extra={"error": exc.message})
        raise HTTPException(status_code=500, detail="Conversation event validation failed") from exc

    topics = _topics()
    await bus.publish(topics["conversation"], conversation_event)
    await bus.publish(topics["metrics"], audio_metrics)

    return {"transcript": transcript, "language": info.language}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8010")))
