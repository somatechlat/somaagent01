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
from pydantic import BaseModel, Field

from jsonschema import ValidationError

from services.common.event_bus import KafkaEventBus
from services.common.schema_validator import validate_event

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

app = FastAPI(title="SomaAgent 01 Audio Service")


def get_whisper_model() -> WhisperModel:
    model_path = os.getenv("WHISPER_MODEL", "base.en")
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute_type = os.getenv("WHISPER_COMPUTE", "int8")
    LOGGER.info("Loading Whisper model", extra={"model": model_path, "device": device})
    return WhisperModel(model_path, device=device, compute_type=compute_type)


def get_event_bus() -> KafkaEventBus:
    return KafkaEventBus()


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

    await bus.publish("conversation.inbound", conversation_event)
    await bus.publish("audio.metrics", audio_metrics)

    return {"transcript": transcript, "language": info.language}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8010")))
