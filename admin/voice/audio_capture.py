"""Audio capture utilities for the voice subsystem.

The implementation uses the :pypi:`sounddevice` library when it is available – it
provides a thin wrapper around PortAudio and works on macOS, Linux and Windows.
If the library cannot be imported (e.g. in a minimal CI environment) the
module raises :class:`VoiceProcessingError` at runtime.  This behaviour satisfies
the VIBE rule **NO OPTIONAL DEPENDENCIES AT IMPORT TIME** – the optional import is
performed lazily inside the ``AudioCapture`` constructor.

The public API consists of a single ``AudioCapture`` class exposing an async
``capture`` method that yields raw PCM ``bytes``.  The method respects the
``AudioConfig`` model defined in ``src.core.config.models`` for sample rate,
device indices and chunk size.  The capture runs in a background thread and
communicates with the async event loop via an ``asyncio.Queue``.

All errors are wrapped in :class:`VoiceProcessingError` to provide a consistent
exception hierarchy for callers.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from typing import AsyncGenerator

# from src.core.config.models import AudioConfig
from .exceptions import VoiceProcessingError


@dataclass
class _StreamWrapper:
    """Thin container for the sounddevice stream and the asyncio queue.

    This helper exists solely to keep the ``AudioCapture`` state tidy and to make
    the ``close`` logic straightforward.
    """

    stream: "sounddevice.Stream"
    queue: asyncio.Queue[bytes]


class AudioCapture:
    """Capture microphone audio as an async byte stream.

    Parameters
    ----------
    config:
        An :class:`AudioConfig` instance that defines the device indices,
        sample rate and the desired chunk duration (in milliseconds).
    """

    def __init__(self, config: AudioConfig) -> None:
        self._config = config
        self._wrapper: _StreamWrapper | None = None

        # Import ``sounddevice`` lazily – this avoids a hard runtime dependency.
        try:
            import sounddevice as sd  # type: ignore
        except Exception as exc:  # pragma: no cover – exercised in CI
            raise VoiceProcessingError(
                command="import sounddevice",
                exit_code=1,
                stderr=str(exc),
            ) from exc
        self._sd = sd

    def _callback(self, indata, frames, time, status):  # pragma: no cover
        """SoundDevice callback – places raw PCM data onto the async queue.

        The callback runs in a separate thread, therefore we use ``call_soon_threadsafe``
        to push data onto the event‑loop queue without blocking.
        """
        if status:
            # Convert any PortAudio status messages into a warning – they do not
            # abort the stream but are useful for debugging.
            sys.stderr.write(f"AudioCapture status: {status}\n")
        # ``indata`` is a NumPy array; we convert it to ``bytes`` preserving the
        # little‑endian PCM layout expected by downstream components.
        raw_bytes = indata.tobytes()
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(self._wrapper.queue.put_nowait, raw_bytes)

    async def _start_stream(self) -> None:
        """Initialise the PortAudio stream and the internal queue.

        This method is separated from ``__init__`` so that the potentially
        blocking ``InputStream`` construction can be awaited in the async
        context.
        """
        if self._wrapper is not None:
            return  # Stream already running.

        queue: asyncio.Queue[bytes] = asyncio.Queue()
        try:
            stream = self._sd.InputStream(
                samplerate=self._config.sample_rate,
                device=self._config.input_device_index,
                channels=1,
                dtype="int16",
                blocksize=int(self._config.sample_rate * self._config.chunk_ms / 1000),
                callback=self._callback,
            )
            stream.start()
        except Exception as exc:  # pragma: no cover – exercised in CI
            raise VoiceProcessingError(
                command="sounddevice.InputStream",
                exit_code=1,
                stderr=str(exc),
            ) from exc

        self._wrapper = _StreamWrapper(stream=stream, queue=queue)

    async def capture(self) -> AsyncGenerator[bytes, None]:
        """Yield audio chunks continuously until the stream is stopped.

        The generator starts the underlying PortAudio stream on first use and
        yields raw PCM ``bytes`` (16‑bit little‑endian) that match the sample rate
        configured in :class:`AudioConfig`.  Consumers should ``await`` each
        iteration; cancellation of the generator will automatically close the
        stream via the ``finally`` block.
        """
        await self._start_stream()
        assert self._wrapper is not None
        try:
            while True:
                chunk = await self._wrapper.queue.get()
                yield chunk
        finally:
            # Ensure resources are released even if the consumer aborts.
            self.close()

    def close(self) -> None:
        """Stop the audio stream and release PortAudio resources."""
        if self._wrapper is None:
            return
        try:
            self._wrapper.stream.stop()
            self._wrapper.stream.close()
        finally:
            self._wrapper = None
