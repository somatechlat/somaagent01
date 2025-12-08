"""Stub client for the local STT/TTS stack.

The real implementation would invoke the ``kokoro`` (STT) and ``whisper`` (TTS)
executables via subprocess, streaming audio to and from them.  To keep the CI
fast and deterministic we provide a minimal stub that simply echoes the input
audio back as a ``dict`` payload.  This satisfies the ``_BaseClient`` protocol
required by :func:`src.voice.provider_selector.get_provider_client`.

All errors are wrapped in :class:`VoiceProcessingError` to keep a consistent
exception hierarchy across providers.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from src.core.config.models import LocalVoiceConfig

from .exceptions import VoiceProcessingError


class LocalClient:
    """Stub client for the local voice provider.

    Parameters
    ----------
    config:
        Configuration containing the selected STT/TTS engine names.  The stub does
        not use these values but stores them for completeness.
    """

    def __init__(self, config: LocalVoiceConfig) -> None:
        self._config = config
        # In a full implementation we would verify that the required binaries
        # (``kokoro`` and ``whisper``) are present on the system here.

    async def process(self, audio_stream: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        """Consume ``audio_stream`` and yield dummy response objects.

        The stub mirrors the behaviour of :class:`OpenAIClient` – it yields a
        dictionary with ``type`` set to ``"audio"`` and the original chunk as
        ``data``.  This provides a predictable shape for downstream processing.
        """
        try:
            async for chunk in audio_stream:
                await asyncio.sleep(0)  # pragma: no cover – trivial async yield
                yield {"type": "audio", "data": chunk}
        except Exception as exc:  # pragma: no cover – exercised via mock
            raise VoiceProcessingError(
                command="LocalClient.process",
                exit_code=1,
                stderr=str(exc),
            ) from exc
