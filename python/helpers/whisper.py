import asyncio
import base64
import tempfile
import warnings

from python.helpers import files
from python.helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)
from python.helpers.print_style import PrintStyle

# Suppress FutureWarning from torch.load
warnings.filterwarnings("ignore", category=FutureWarning)

# Whisper is required for audio transcription in production
try:
    import whisper  # type: ignore
except ImportError as exc:
    raise ImportError(
        "Whisper library is required for production audio transcription. "
        "Install with: pip install openai-whisper"
    ) from exc

_model = None
_model_name = ""
is_updating_model = False  # Tracks whether the model is currently updating


async def preload(model_name: str):
    try:
        # return await runtime.call_development_function(_preload, model_name)
        return await _preload(model_name)
    except Exception as e:
        # if not runtime.is_development():
        raise e


async def _preload(model_name: str):
    global _model, _model_name, is_updating_model

    while is_updating_model:
        await asyncio.sleep(0.1)

    try:
        is_updating_model = True
        if not _model or _model_name != model_name:
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Loading Whisper model...",
                display_time=99,
                group="whisper-preload",
            )
            PrintStyle.standard(f"Loading Whisper model: {model_name}")
            _model = whisper.load_model(name=model_name, download_root=files.get_abs_path("/tmp/models/whisper"))  # type: ignore
            _model_name = model_name
            NotificationManager.send_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                "Whisper model loaded.",
                display_time=2,
                group="whisper-preload",
            )
    finally:
        is_updating_model = False


async def is_downloading():
    # return await runtime.call_development_function(_is_downloading)
    return _is_downloading()


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
    return _model is not None


async def transcribe(model_name: str, audio_bytes_b64: str):
    # return await runtime.call_development_function(_transcribe, model_name, audio_bytes_b64)
    return await _transcribe(model_name, audio_bytes_b64)


async def _transcribe(model_name: str, audio_bytes_b64: str):
    await _preload(model_name)

    # Decode audio bytes if encoded as a base64 string
    audio_bytes = base64.b64decode(audio_bytes_b64)

    # Create temp audio file
    import os

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
        audio_file.write(audio_bytes)
        temp_path = audio_file.name
    try:
        # Transcribe the audio file
        result = _model.transcribe(temp_path, fp16=False)  # type: ignore
        return result
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass  # ignore errors during cleanup
