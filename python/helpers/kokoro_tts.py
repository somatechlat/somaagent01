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

from python.helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)
from python.helpers.print_style import PrintStyle
import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

_pipeline = None
_voice = "am_puck,am_onyx"
_speed = 1.1
is_updating_model = False


async def preload():
    try:
        # return await runtime.call_development_function(_preload)
        return await _preload()
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # PrintStyle.standard("RFC failed, falling back to direct execution...")
        # return await _preload()


async def _preload():
    global _pipeline, is_updating_model

    while is_updating_model:
        await asyncio.sleep(0.1)

    try:
        is_updating_model = True
        if not _pipeline:
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Loading Kokoro TTS model...",
                display_time=99,
                group="kokoro-preload",
            )
            PrintStyle.standard("Loading Kokoro TTS model...")
            from kokoro import KPipeline

            _pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Kokoro TTS model loaded.",
                display_time=2,
                group="kokoro-preload",
            )
    finally:
        is_updating_model = False


async def is_downloading():
    try:
        # return await runtime.call_development_function(_is_downloading)
        return _is_downloading()
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # return _is_downloading()


def _is_downloading():
    return is_updating_model


async def is_downloaded():
    try:
        # return await runtime.call_development_function(_is_downloaded)
        return _is_downloaded()
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # return _is_downloaded()


def _is_downloaded():
    return _pipeline is not None


async def synthesize_sentences(sentences: list[str]):
    """Generate audio for multiple sentences and return concatenated base64 audio"""
    try:
        # return await runtime.call_development_function(_synthesize_sentences, sentences)
        return await _synthesize_sentences(sentences)
    except Exception as e:
        # if not runtime.is_development():
        raise e
        # Fallback to direct execution if RFC fails in development
        # return await _synthesize_sentences(sentences)


async def _synthesize_sentences(sentences: list[str]):
    await _preload()

    chunks: List[np.ndarray] = []

    try:
        for sentence in sentences:
            if sentence.strip():
                segments = _pipeline(sentence.strip(), voice=_voice, speed=_speed)  # type: ignore
                for segment in list(segments):
                    audio_tensor = segment.audio
                    audio_numpy = audio_tensor.detach().cpu().numpy()  # type: ignore
                    # Force mono: flatten to 1-D float32 to avoid shape/channel issues with writers
                    arr = np.asarray(audio_numpy, dtype=np.float32).reshape(-1)
                    chunks.append(arr)

        # Concatenate and convert to bytes
        if not _SOUNDFILE_AVAILABLE:
            raise RuntimeError(
                "soundfile is not available in the runtime. Enable audio features or install 'soundfile' and libsndfile."
            )
        if not chunks:
            # Return a short silence (0.2s) to avoid empty file edge cases
            arr = np.zeros(int(0.2 * 24000), dtype=np.float32)
        else:
            arr = np.concatenate(chunks, axis=0)
        buffer = io.BytesIO()
        sf.write(buffer, arr, 24000, format="WAV")
        audio_bytes = buffer.getvalue()

        # Return base64 encoded audio
        return base64.b64encode(audio_bytes).decode("utf-8")

    except Exception as e:
        PrintStyle.error(f"Error in Kokoro TTS synthesis: {e}")
        raise
