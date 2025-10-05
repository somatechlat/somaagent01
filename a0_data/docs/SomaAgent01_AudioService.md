⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Audio Service

## Overview
The audio service (`services/audio_service/main.py`) ingests base64-encoded audio, transcribes it using the OSS Faster-Whisper model, and publishes both conversation events and audio metrics to Kafka. It enables full duplex speech interactions without any proprietary components.

## Endpoint
`POST /v1/audio/transcribe`
```json
{
  "session_id": "uuid",
  "persona_id": "optional persona",
  "audio_b64": "...",
  "metadata": {"tenant": "acme"}
}
```
Response:
```json
{
  "transcript": "recognized text",
  "language": "en"
}
```

## Pipeline
1. Decode base64 PCM audio (wav) and load via `soundfile`.
2. Run `WhisperModel.transcribe()` (device determined by `WHISPER_DEVICE`).
3. Emit conversation event to `conversation.inbound` with transcript marked as `source: audio`.
4. Emit metrics to `audio.metrics` capturing duration, language, latency, RMS energy.

## Configuration
- `WHISPER_MODEL`: e.g., `base.en`, `medium.en`, or a path to a local `.pt` file.
- `WHISPER_DEVICE`: `cpu` or `cuda`.
- `WHISPER_COMPUTE`: compute precision (`int8`, `float16`, etc.).
- `PORT`: HTTP port (default 8010).

## Kafka Topics
- `conversation.inbound`: transcript forwarded for standard conversation processing.
- `audio.metrics`: structured metrics consumed by analytics/ClickHouse.

## Future Enhancements
- WebSocket streaming ingest for partial transcripts.
- MOS estimation using open-source libraries.
- Persona tone shaping integration (TTS) in Sprint 2A continuation.
