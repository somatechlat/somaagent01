import asyncio
import base64
import logging
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

# Whisper is optional in lightweight developer builds – only require the
# package when audio support is explicitly enabled.
LOGGER = logging.getLogger(__name__)
try:
    from services.common import runtime_config as _cfg

    _feature_audio_enabled = bool(_cfg.flag("audio_support"))
except Exception:
    # No legacy env fallback – treat as disabled when cfg unavailable
    _feature_audio_enabled = False

import os as _os

try:
    if not _feature_audio_enabled:
        raise ImportError("audio features disabled")
    import whisper  # type: ignore
except ImportError as exc:  # pragma: no cover - exercised in developer & CI builds
    _testing_mode = _os.getenv("TESTING") == "1" or _os.getenv("PYTEST_CURRENT_TEST") is not None
    _require_whisper = _os.getenv("SA01_REQUIRE_WHISPER") in {"1", "true", "yes"}
    # In normal (non-test) operation with the feature enabled OR when explicitly required, fail fast.
    if (_feature_audio_enabled and not _testing_mode) or _require_whisper:
        raise ImportError(
            "Whisper library is required for production audio transcription. "
            "Install with: pip install openai-whisper"
        ) from exc
    # Otherwise degrade gracefully for tests / lightweight dev builds.
    whisper = None  # type: ignore
    LOGGER.info(
        "Skipping Whisper preload – audio support disabled, package missing, or test mode graceful fallback"
    )

_model = None
_model_name = ""
is_updating_model = False  # Tracks whether the model is currently updating


async def preload(model_name: str):
    if whisper is None:
        LOGGER.debug("Whisper preload skipped – audio support disabled")
        return None
    try:
        # return await runtime.call_development_function(_preload, model_name)
        return await _preload(model_name)
    except Exception as e:
        # if not runtime.is_development():
        raise e


async def _preload(model_name: str):
    if whisper is None:
        return None

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
    if whisper is None:
        return False
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
    if whisper is None:
        raise RuntimeError("Audio transcription is disabled (audio_support feature off).")
    # return await runtime.call_development_function(_transcribe, model_name, audio_bytes_b64)
    return await _transcribe(model_name, audio_bytes_b64)


async def _transcribe(model_name: str, audio_bytes_b64: str):
    if whisper is None:
        raise RuntimeError("Audio transcription is disabled (audio_support feature off).")
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
