"""Utility to normalize provider responses into a common schema.

Both the OpenAI and local client stubs emit dictionaries with a ``type`` key –
currently only ``"audio"`` is used.  In a full implementation the provider may
also return ``"text"`` (transcriptions) or ``"event"`` messages.  The
``ResponseNormalizer`` centralises this transformation so that downstream code
does not need to branch on the provider implementation.

The normaliser is deliberately lightweight: it validates the expected keys and
produces a ``dict`` with ``kind`` (the normalized type) and ``payload`` (the
raw data).  Errors are raised as :class:`VoiceProcessingError` to keep a
consistent exception hierarchy.
"""

from __future__ import annotations

from typing import Any, Mapping

from .exceptions import VoiceProcessingError


class ResponseNormalizer:
    """Convert raw provider responses to a unified format.

    The public ``normalize`` method accepts any mapping (typically the dict
    produced by a client) and returns a dictionary with the keys:

    - ``kind``: a string such as ``"audio"`` or ``"text"``
    - ``payload``: the raw data associated with the kind
    """

    @staticmethod
    def normalize(raw: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(raw, Mapping):
            raise VoiceProcessingError(
                command="ResponseNormalizer.normalize",
                exit_code=1,
                stderr="Response is not a mapping",
            )
        kind = raw.get("type")
        if kind not in {"audio", "text", "event"}:
            raise VoiceProcessingError(
                command="ResponseNormalizer.normalize",
                exit_code=1,
                stderr=f"Unsupported response type: {kind}",
            )
        payload = raw.get("data")
        return {"kind": kind, "payload": payload}
