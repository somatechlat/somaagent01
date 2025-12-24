"""High‑level orchestration service for the voice subsystem.

The :class:`VoiceService` class glues together the capture, provider client,
adapter and speaker components.  It also records metrics and tracing spans.
All heavy‑weight objects are created lazily in ``__init__`` so that importing the
module has no side effects (VIBE rule **NO SIDE‑EFFECTS AT IMPORT**).

Typical usage inside a Django Ninja endpoint::

    async def voice_endpoint():
        service = VoiceService(config)
        await service.start()
        # ``run`` blocks until the capture generator finishes (e.g., client
        # disconnects).  In a real implementation the endpoint would stream
        # data back to the client.
        await service.run()

The implementation below is intentionally minimal – it provides the required
public API while delegating the actual audio handling to the previously defined
modules.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable

from src.core.config.models import Config
from .audio_capture import AudioCapture
from .speaker import Speaker
from .provider_selector import get_provider_client, _BaseClient
from .voice_adapter import VoiceAdapter
from .metrics import VOICE_SESSIONS_TOTAL, VOICE_SESSION_DURATION_SECONDS, record_error
from .tracing import span


class VoiceService:
    """Orchestrates a single voice interaction session.

    Parameters
    ----------
    config:
        Global configuration object from which the voice settings are derived.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._capture: AudioCapture | None = None
        self._speaker: Speaker | None = None
        self._client: _BaseClient | None = None
        self._adapter: VoiceAdapter | None = None
        self._session_task: Awaitable[None] | None = None

    def _setup_components(self) -> None:
        """Instantiate all low‑level components.

        This method is called lazily the first time the service is started.
        """
        voice_cfg = self._config.voice
        self._capture = AudioCapture(voice_cfg.audio)
        self._speaker = Speaker(voice_cfg.audio)
        self._client = get_provider_client(self._config)
        assert self._capture and self._speaker and self._client  # for mypy
        self._adapter = VoiceAdapter(self._capture, self._client, self._speaker)

    async def start(self) -> None:
        """Prepare the service and record metrics.

        This method must be called before ``run``.  It increments the session
        counter and creates the component instances.
        """
        VOICE_SESSIONS_TOTAL.inc()
        self._setup_components()

    async def run(self) -> None:
        """Execute the full audio pipeline.

        The method records a duration histogram and ensures any raised errors are
        accounted for in the ``VOICE_ERRORS_TOTAL`` metric.
        """
        if not self._adapter:
            raise RuntimeError("VoiceService.start() must be called before run()")
        with span("voice_session") as end_span:
            with VOICE_SESSION_DURATION_SECONDS.time():
                try:
                    await self._adapter.run()
                except Exception as exc:  # pragma: no cover – defensive
                    record_error("adapter")
                    raise
                finally:
                    # Ensure the span is closed even on error.
                    end_span()
