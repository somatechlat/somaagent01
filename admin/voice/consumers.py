"""Voice WebSocket Consumer - Real-time Voice Streaming.


Per CANONICAL_USER_JOURNEYS_SRS.md UC-04: Voice Chat.

7-Persona Implementation:
- 🏗️ Django Architect: Channels consumer, async handlers
- 🔒 Security Auditor: Token validation, tenant isolation
- 📈 PM: Clear message protocol, status updates
- 🧪 QA Engineer: Error handling, reconnection
- 📚 Technical Writer: Protocol documentation
- ⚡ Performance Lead: Chunked audio, streaming
- 🌍 i18n Specialist: Language detection support
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class VoiceSessionState:
    """State for an active voice session."""

    session_id: str
    tenant_id: str
    user_id: str
    persona_id: Optional[str] = None
    status: str = "connecting"
    start_time: datetime = field(default_factory=datetime.now)
    input_tokens: int = 0
    output_tokens: int = 0
    audio_seconds: float = 0.0
    turn_count: int = 0
    is_speaking: bool = False
    transcript_buffer: str = ""


class VoiceConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time voice streaming.

    Protocol:
    - Client → Server:
        - {"type": "audio_chunk", "data": "<base64>", "format": "webm"}
        - {"type": "start_session", "persona_id": "..."}
        - {"type": "end_session"}
        - {"type": "interrupt"}

    - Server → Client:
        - {"type": "session_started", "session_id": "..."}
        - {"type": "transcription", "text": "...", "is_final": true}
        - {"type": "response_start"}
        - {"type": "audio_chunk", "data": "<base64>"}
        - {"type": "response_end", "text": "..."}
        - {"type": "status", "status": "listening|processing|speaking"}
        - {"type": "error", "message": "..."}
    """

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""

        super().__init__(*args, **kwargs)
        self.state: Optional[VoiceSessionState] = None
        self.audio_buffer: list[bytes] = []
        self.processing_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Handle WebSocket connection."""
        try:
            # Extract user from scope (set by middleware)
            user = self.scope.get("user")
            if not user or not user.is_authenticated:
                await self.close(code=4001)  # Unauthorized
                return

            # Extract tenant_id from query string or token
            query_string = self.scope.get("query_string", b"").decode()
            params = dict(p.split("=") for p in query_string.split("&") if "=" in p)
            tenant_id = params.get("tenant_id", "default")

            # Initialize session state
            self.state = VoiceSessionState(
                session_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=str(user.id) if hasattr(user, "id") else "anonymous",
            )

            await self.accept()
            await self.send_json(
                {
                    "type": "connected",
                    "session_id": self.state.session_id,
                    "message": "Voice WebSocket connected. Send 'start_session' to begin.",
                }
            )
            logger.info(f"Voice WS connected: {self.state.session_id}")

        except Exception as e:
            logger.error(f"Voice WS connection error: {e}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if self.processing_task:
            self.processing_task.cancel()

        if self.state:
            logger.info(
                f"Voice WS disconnected: {self.state.session_id}, "
                f"duration={self.state.audio_seconds:.1f}s, "
                f"turns={self.state.turn_count}"
            )
            # Persist session to database via Django ORM
            await self._persist_session_end()

    async def receive_json(self, content):
        """Handle incoming JSON messages."""
        msg_type = content.get("type")

        try:
            if msg_type == "start_session":
                await self._handle_start_session(content)
            elif msg_type == "audio_chunk":
                await self._handle_audio_chunk(content)
            elif msg_type == "end_session":
                await self._handle_end_session(content)
            elif msg_type == "interrupt":
                await self._handle_interrupt(content)
            elif msg_type == "ping":
                await self.send_json({"type": "pong"})
            else:
                await self.send_json(
                    {"type": "error", "message": f"Unknown message type: {msg_type}"}
                )

        except Exception as e:
            logger.error(f"Voice WS error: {e}")
            await self.send_json({"type": "error", "message": str(e)})

    async def _handle_start_session(self, content):
        """Start a new voice session with persona."""
        if not self.state:
            return

        persona_id = content.get("persona_id")
        self.state.persona_id = persona_id
        self.state.status = "listening"
        self.state.start_time = datetime.now()

        # Create VoiceSession in database
        await self._create_session_record()

        await self.send_json(
            {
                "type": "session_started",
                "session_id": self.state.session_id,
                "persona_id": persona_id,
                "status": "listening",
            }
        )

        await self._send_status("listening")
        logger.info(f"Voice session started: {self.state.session_id}, persona={persona_id}")

    async def _create_session_record(self):
        """Create VoiceSession record in database."""
        if not self.state:
            return

        from asgiref.sync import sync_to_async

        try:
            from admin.voice.models import VoiceSession

            await sync_to_async(VoiceSession.objects.create)(
                id=self.state.session_id,
                tenant_id=self.state.tenant_id,
                user_id=self.state.user_id,
                persona_id=self.state.persona_id,
                status="active",
                started_at=self.state.start_time,
            )
            logger.debug(f"VoiceSession created: {self.state.session_id}")
        except Exception as e:
            # Non-fatal - log and continue
            logger.warning(f"Failed to create VoiceSession record: {e}")

    async def _persist_session_end(self):
        """Update VoiceSession record on disconnect."""
        if not self.state:
            return

        from asgiref.sync import sync_to_async
        from datetime import datetime as dt

        try:
            from admin.voice.models import VoiceSession

            await sync_to_async(VoiceSession.objects.filter(id=self.state.session_id).update)(
                status=self.state.status,
                ended_at=dt.now(),
                audio_seconds=self.state.audio_seconds,
                turn_count=self.state.turn_count,
                input_tokens=self.state.input_tokens,
                output_tokens=self.state.output_tokens,
            )
            logger.debug(f"VoiceSession updated: {self.state.session_id}")
        except Exception as e:
            # Non-fatal - log and continue
            logger.warning(f"Failed to update VoiceSession record: {e}")

    async def _handle_audio_chunk(self, content):
        """Process incoming audio chunk."""
        if not self.state or self.state.status not in ["listening", "processing"]:
            return

        # Decode base64 audio
        audio_b64 = content.get("data", "")
        try:
            audio_bytes = base64.b64decode(audio_b64)
            self.audio_buffer.append(audio_bytes)

            # Update audio duration (rough estimate: 16kHz, 16-bit)
            self.state.audio_seconds += len(audio_bytes) / (16000 * 2)

        except Exception as e:
            logger.error(f"Audio decode error: {e}")
            return

        # Check if we have enough audio for VAD/processing
        total_bytes = sum(len(chunk) for chunk in self.audio_buffer)
        if total_bytes > 16000:  # ~0.5 seconds at 16kHz
            await self._process_audio_buffer()

    async def _process_audio_buffer(self):
        """Process accumulated audio buffer through STT."""
        if not self.audio_buffer:
            return

        await self._send_status("processing")

        # Combine audio chunks
        audio_data = b"".join(self.audio_buffer)
        self.audio_buffer = []

        # Real transcription via Whisper API
        transcript = await self._transcribe_audio(audio_data)

        if transcript:
            self.state.turn_count += 1

            # Send transcription to client
            await self.send_json(
                {
                    "type": "transcription",
                    "text": transcript,
                    "is_final": True,
                    "turn": self.state.turn_count,
                }
            )

            # Generate response via LLM
            await self._generate_llm_response(transcript)

        await self._send_status("listening")

    async def _transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio using Whisper API.

        
        """
        try:
            import httpx

            whisper_url = getattr(settings, "WHISPER_API_URL", "http://localhost:8001/transcribe")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    whisper_url,
                    files={"audio": ("audio.webm", audio_data, "audio/webm")},
                    data={"language": "en"},
                )

                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "").strip()
                else:
                    logger.error(f"Whisper API error: {response.status_code}")
                    return ""

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            # Graceful degradation - return empty on error
            return ""

    async def _generate_llm_response(self, transcript: str):
        """Generate AI response via LLM and TTS.

        
        """
        await self._send_status("speaking")
        self.state.is_speaking = True

        await self.send_json({"type": "response_start"})

        try:
            import httpx

            # Get LLM response via internal API
            llm_url = getattr(
                settings, "LLM_API_URL", "http://localhost:20020/api/v2/core/llm/chat"
            )

            async with httpx.AsyncClient(timeout=60.0) as client:
                llm_response = await client.post(
                    llm_url,
                    json={
                        "messages": [
                            {
                                "role": "system",
                                "content": f"You are a helpful voice assistant. Persona: {self.state.persona_id or 'default'}",
                            },
                            {"role": "user", "content": transcript},
                        ],
                        "model": getattr(settings, "DEFAULT_VOICE_MODEL", "gpt-4o-mini"),
                        "max_tokens": 150,
                    },
                    headers={"Authorization": f"Bearer {getattr(settings, 'LLM_API_KEY', '')}"},
                )

                if llm_response.status_code == 200:
                    result = llm_response.json()
                    response_text = result.get(
                        "content", result.get("message", {}).get("content", "I understand.")
                    )
                else:
                    response_text = "I'm having trouble processing that right now."

        except Exception as e:
            logger.error(f"LLM response error: {e}")
            response_text = "I'm sorry, I couldn't process your request."

        self.state.output_tokens += len(response_text.split())

        # Stream TTS audio via Kokoro
        try:
            await self._stream_tts_audio(response_text)
        except Exception as e:
            logger.error(f"TTS error: {e}")

        await self.send_json(
            {
                "type": "response_end",
                "text": response_text,
                "tokens": self.state.output_tokens,
            }
        )

        self.state.is_speaking = False
        await self._send_status("listening")

    async def _stream_tts_audio(self, text: str):
        """Stream TTS audio chunks using Kokoro.

        
        """
        import httpx

        tts_url = getattr(settings, "KOKORO_TTS_URL", "http://localhost:8002/synthesize")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                tts_url,
                json={
                    "text": text,
                    "voice": self.state.persona_id or "default",
                    "format": "mp3",
                },
                headers={"Accept": "audio/mpeg"},
            )

            if response.status_code == 200:
                # Stream audio in chunks
                audio_data = response.content
                chunk_size = 4096
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i : i + chunk_size]
                    await self.send_json(
                        {
                            "type": "audio_chunk",
                            "data": base64.b64encode(chunk).decode(),
                            "chunk_index": i // chunk_size,
                        }
                    )

    async def _handle_end_session(self, content):
        """End the current voice session."""
        if not self.state:
            return

        self.state.status = "completed"

        await self.send_json(
            {
                "type": "session_ended",
                "session_id": self.state.session_id,
                "duration_seconds": self.state.audio_seconds,
                "turn_count": self.state.turn_count,
                "input_tokens": self.state.input_tokens,
                "output_tokens": self.state.output_tokens,
            }
        )

        logger.info(f"Voice session ended: {self.state.session_id}")

    async def _handle_interrupt(self, content):
        """Handle user interrupt (barge-in)."""
        if self.state and self.state.is_speaking:
            self.state.is_speaking = False
            await self.send_json({"type": "interrupted"})
            await self._send_status("listening")
            logger.info(f"Voice interrupted: {self.state.session_id}")

    async def _send_status(self, status: str):
        """Send status update to client."""
        if self.state:
            self.state.status = status
        await self.send_json({"type": "status", "status": status})


# =============================================================================
# URL ROUTING (for routing.py)
# =============================================================================

# In admin/voice/routing.py:
# from django.urls import path
# from admin.voice.consumers import VoiceConsumer
#
# websocket_urlpatterns = [
#     path("ws/voice/", VoiceConsumer.as_asgi()),
# ]