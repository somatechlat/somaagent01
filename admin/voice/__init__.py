"""Voice subsystem public façade.

The :class:`VoiceService` class provides a high‑level orchestration API that
coordinates microphone capture, provider selection, speech‑to‑text, LLM response
normalisation, text‑to‑speech synthesis and speaker playback.  All heavy‑weight
logic lives in the sub‑modules of this package; the ``__init__`` file merely
exposes the public entry point.

This module follows the 
single place for all audio‑related code.
"""

from __future__ import annotations

from .service import VoiceService

__all__ = ["VoiceService"]
