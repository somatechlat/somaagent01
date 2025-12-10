"""Adapter that wires together audio capture, a provider client and the speaker.

The adapter is deliberately thin – it does not perform any speech‑to‑text or
text‑to‑speech logic itself.  Instead it forwards raw microphone PCM bytes to the
selected provider client (OpenAI or local) and streams any returned audio chunks
to the :class:`~src.voice.speaker.Speaker` for playback.

All components are injected via the constructor which makes the class easy to
unit‑test (dependencies can be replaced with mocks).  Errors from any stage are
propagated as :class:`~src.voice.exceptions.VoiceProcessingError` which is a
common base class for the whole voice subsystem.
"""

from __future__ import annotations

from typing import AsyncGenerator

from .audio_capture import AudioCapture
from .exceptions import VoiceProcessingError
from .provider_selector import _BaseClient
from .speaker import Speaker


class VoiceAdapter:
    """High‑level orchestrator for a single voice interaction session.

    Parameters
    ----------
    capture:
        Instance of :class:`AudioCapture` that yields raw PCM audio.
    client:
        Provider client implementing the ``_BaseClient`` protocol (e.g.
        :class:`OpenAIClient` or :class:`LocalClient`).
    speaker:
        Instance of :class:`Speaker` that plays back audio chunks.
    """

    def __init__(self, capture: AudioCapture, client: _BaseClient, speaker: Speaker) -> None:
        self._capture = capture
        self._client = client
        self._speaker = speaker

    async def _audio_responses(
        self, audio_stream: AsyncGenerator[bytes, None]
    ) -> AsyncGenerator[bytes, None]:
        """Transform provider responses into a pure audio byte stream.

        The concrete client returns dictionaries with a ``type`` field.
        The adapter filters for ``"audio"`` type and yields the ``data`` payload.
        """
        try:
            async for resp in self._client.process(audio_stream):
                if isinstance(resp, dict) and resp.get("type") == "audio":
                    data = resp.get("data")
                    if isinstance(data, (bytes, bytearray)):
                        yield bytes(data)
        except VoiceProcessingError:
            # Re‑raise known voice errors unchanged.
            raise
        except Exception as exc:  # pragma: no cover – defensive
            raise VoiceProcessingError(
                command="VoiceAdapter._audio_responses",
                exit_code=1,
                stderr=str(exc),
            ) from exc

    async def run(self) -> None:
        """Execute the end‑to‑end audio pipeline.

        The method starts the capture generator, feeds it into the provider
        client, extracts audio responses and streams them to the speaker.  It
        returns when the capture generator is exhausted (e.g. the client closes
        the connection) or when the caller cancels the coroutine.
        """
        # The capture generator is an async iterator; we pass it directly to the
        # client and then pipe the resulting audio to the speaker.
        audio_stream = self._capture.capture()
        audio_responder = self._audio_responses(audio_stream)
        # ``Speaker.play`` consumes the async generator until exhaustion.
        await self._speaker.play(audio_responder)
