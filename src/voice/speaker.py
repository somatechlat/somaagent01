"""Speaker utilities for the voice subsystem.

The implementation mirrors :mod:`audio_capture` but in the opposite direction –
it plays raw PCM ``bytes`` through the default audio output device using the
``sounddevice`` library.  As with the capture module the import is performed
lazy‑ly so that the package can be installed without the optional dependency.

All playback errors are wrapped in :class:`VoiceProcessingError` to provide a
uniform exception hierarchy for the rest of the service.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import AsyncGenerator

from src.core.config.models import AudioConfig
from .exceptions import VoiceProcessingError


@dataclass
class _OutputWrapper:
    """Container for the sounddevice output stream and an async queue.

    The queue receives raw PCM bytes from the producer (e.g. the TTS client) and
    the background callback consumes them, writing to the audio device.
    """

    stream: "sounddevice.Stream"
    queue: asyncio.Queue[bytes]


class Speaker:
    """Play PCM audio data to the system speaker.

    Parameters
    ----------
    config:
        An :class:`AudioConfig` instance describing the output device and
        sample rate.  The ``chunk_ms`` value is used to calculate the appropriate
        PortAudio blocksize.
    """

    def __init__(self, config: AudioConfig) -> None:
        self._config = config
        self._wrapper: _OutputWrapper | None = None
        try:
            import sounddevice as sd  # type: ignore
        except Exception as exc:  # pragma: no cover – exercised via mock
            raise VoiceProcessingError(
                command="import sounddevice",
                exit_code=1,
                stderr=str(exc),
            ) from exc
        self._sd = sd

    def _callback(self, outdata, frames, time, status):  # pragma: no cover
        """SoundDevice callback – pulls bytes from the async queue.

        The callback runs in a separate thread; we therefore retrieve data from
        the ``asyncio.Queue`` using ``loop.run_in_executor`` to avoid blocking.
        If the queue is empty we output silence.
        """
        if status:
            sys.stderr.write(f"Speaker status: {status}\n")

        loop = asyncio.get_event_loop()
        try:
            # ``get_nowait`` is safe because the callback is called only when
            # the stream needs data; if the queue is empty we fall back to silence.
            raw = self._wrapper.queue.get_nowait()
        except Exception:
            raw = b"\x00" * outdata.nbytes
        # Convert bytes back to a NumPy array matching the stream dtype.
        import numpy as np

        outdata[:] = np.frombuffer(raw, dtype=np.int16).reshape(outdata.shape)

    async def _start_stream(self) -> None:
        if self._wrapper is not None:
            return
        queue: asyncio.Queue[bytes] = asyncio.Queue()
        try:
            stream = self._sd.OutputStream(
                samplerate=self._config.sample_rate,
                device=self._config.output_device_index,
                channels=1,
                dtype="int16",
                blocksize=int(self._config.sample_rate * self._config.chunk_ms / 1000),
                callback=self._callback,
            )
            stream.start()
        except Exception as exc:  # pragma: no cover – exercised via mock
            raise VoiceProcessingError(
                command="sounddevice.OutputStream",
                exit_code=1,
                stderr=str(exc),
            ) from exc
        self._wrapper = _OutputWrapper(stream=stream, queue=queue)

    async def play(self, data: AsyncGenerator[bytes, None]) -> None:
        """Consume an async generator of PCM chunks and feed them to the speaker.

        The method starts the underlying PortAudio stream on first use and
        pushes each incoming chunk onto the internal queue.  When the generator
        finishes the speaker is automatically stopped.
        """
        await self._start_stream()
        assert self._wrapper is not None
        try:
            async for chunk in data:
                await self._wrapper.queue.put(chunk)
        finally:
            self.close()

    def close(self) -> None:
        """Stop playback and release PortAudio resources."""
        if self._wrapper is None:
            return
        try:
            self._wrapper.stream.stop()
            self._wrapper.stream.close()
        finally:
            self._wrapper = None
