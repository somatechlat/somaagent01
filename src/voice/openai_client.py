"""Minimal OpenAI Realtime client stub.

The real implementation would open a WebSocket connection to the OpenAI Realtime
endpoint, stream microphone audio, and receive a mixed response of audio chunks
and text.  For the purpose of building the surrounding architecture we provide a
light‑weight stub that conforms to the ``_BaseClient`` protocol defined in
``provider_selector.py``.

The stub simply echoes back the received audio as ``bytes`` wrapped in a simple
``dict`` with a ``type`` field.  This is sufficient for unit tests that verify
the orchestration logic without requiring external network access.

All errors are wrapped in :class:`VoiceProcessingError` so that callers have a
consistent exception type.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from src.core.config.models import OpenAIConfig
from .exceptions import VoiceProcessingError


class OpenAIClient:
    """Stub client for the OpenAI Realtime provider.

    Parameters
    ----------
    config:
        Configuration model containing model name, sample rate and encoding.
    """

    def __init__(self, config: OpenAIConfig) -> None:
        self._config = config
        # In a real implementation we would initialise the WebSocket URL and
        # authentication headers here.

    async def process(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        """Consume ``audio_stream`` and yield dummy response objects.

        The stub reads the incoming audio chunks, pretends to send them to the
        remote service and yields a dictionary containing the original chunk.
        This mimics the shape of a real response where ``type`` indicates the
        payload kind (e.g. ``"audio"`` or ``"text"``).
        """
        try:
            async for chunk in audio_stream:
                # Simulate a tiny processing delay so that the coroutine yields.
                await asyncio.sleep(0)  # pragma: no cover – trivial
                yield {"type": "audio", "data": chunk}
        except Exception as exc:  # pragma: no cover – exercised via mock
            raise VoiceProcessingError(
                command="OpenAIClient.process",
                exit_code=1,
                stderr=str(exc),
            ) from exc
