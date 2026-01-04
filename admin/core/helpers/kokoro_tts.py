"""Module kokoro_tts."""

# kokoro_tts.py

import asyncio
import base64
import io
import warnings
from typing import List

try:
    import soundfile as sf

    _SOUNDFILE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency may be missing in images
    sf = None
    _SOUNDFILE_AVAILABLE = False

import numpy as np

from admin.core.helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)
from admin.core.helpers.print_style import PrintStyle

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

_pipeline = None
_voice = "am_puck,am_onyx"
_speed = 1.1
is_updating_model = False


async def preload():
    # return await runtime.call_development_function(_preload)
    """Execute preload.
        """

    return await _preload()


async def _preload():
    """Execute preload.
        """

    global _pipeline, is_updating_model

    while is_updating_model:
        await asyncio.sleep(0.1)

    try:
        is_updating_model = True
        if not _pipeline:
            # Best-effort UX notification; in uvicorn/uvloop contexts the notification bus may not be available
            try:
                NotificationManager.send_notification(
                    NotificationType.INFO,
                    NotificationPriority.NORMAL,
                    "Loading Kokoro TTS model...",
                    display_time=99,
                    group="kokoro-preload",
                )
            except Exception:
                pass
            PrintStyle.standard("Loading Kokoro TTS model...")
            from kokoro import KPipeline

            _pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
            try:
                NotificationManager.send_notification(
                    NotificationType.INFO,
                    NotificationPriority.NORMAL,
                    "Kokoro TTS model loaded.",
                    display_time=2,
                    group="kokoro-preload",
                )
            except Exception:
                pass
    finally:
        is_updating_model = False


async def is_downloading():
    # return await runtime.call_development_function(_is_downloading)
    """Check if downloading.
        """

    return _is_downloading()


def _is_downloading():
    """Execute is downloading.
        """

    return is_updating_model


async def is_downloaded():
    # return await runtime.call_development_function(_is_downloaded)
    """Check if downloaded.
        """

    return _is_downloaded()


def _is_downloaded():
    """Execute is downloaded.
        """

    return _pipeline is not None


async def synthesize_sentences(sentences: list[str]):
    """Generate audio for multiple sentences and return concatenated base64 audio"""
    # return await runtime.call_development_function(_synthesize_sentences, sentences)
    return await _synthesize_sentences(sentences)


async def _synthesize_sentences(sentences: list[str]):
    """Execute synthesize sentences.

        Args:
            sentences: The sentences.
        """

    PrintStyle.standard(f"Kokoro TTS: synthesize start (n_sentences={len(sentences)})")
    await _preload()
    PrintStyle.standard(f"Kokoro TTS: pipeline ready={_pipeline is not None}")

    chunks: List[np.ndarray] = []

    try:
        for sentence in sentences:
            if sentence.strip():
                s = sentence.strip()
                PrintStyle.standard(f"Kokoro TTS: infer len={len(s)} voice={_voice} speed={_speed}")
                segments = _pipeline(s, voice=_voice, speed=_speed)  # type: ignore
                segs = list(segments)
                PrintStyle.standard(f"Kokoro TTS: segments={len(segs)}")
                for segment in segs:
                    audio_tensor = segment.audio
                    audio_numpy = audio_tensor.detach().cpu().numpy()  # type: ignore
                    # Force mono: flatten to 1-D float32 to avoid shape/channel issues with writers
                    arr = np.asarray(audio_numpy, dtype=np.float32).reshape(-1)
                    chunks.append(arr)

        # Concatenate and convert to bytes
        if not chunks:
            # Return a short silence (0.2s) to avoid empty file edge cases
            arr = np.zeros(int(0.2 * 24000), dtype=np.float32)
        else:
            arr = np.concatenate(chunks, axis=0)
        PrintStyle.standard(f"Kokoro TTS: total_chunks={len(chunks)}")
        if not _SOUNDFILE_AVAILABLE:
            raise RuntimeError("soundfile is required for Kokoro TTS audio serialization")

        buffer = io.BytesIO()
        sf.write(buffer, arr, 24000, format="WAV")
        audio_bytes = buffer.getvalue()

        # Return base64 encoded audio
        return base64.b64encode(audio_bytes).decode("utf-8")

    except Exception as e:
        PrintStyle.error(f"Error in Kokoro TTS synthesis: {e}")
        raise