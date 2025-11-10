"""Centralized configuration registry abstraction.

This module defines a minimal, runtime-friendly interface for layered config:
defaults → environment → remote dynamic overrides (e.g., from Kafka topic).

Features (scaffold):
- In-memory snapshot with version and checksum.
- JSONSchema validation of incoming documents.
- Subscription mechanism for components to react to updates.
- Acknowledgement publishing hook (no transport coupling here).

Note: Transport (Kafka) wiring intentionally lives in gateway where
`_config_update_listener` can deserialize payloads and call `apply_update`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from jsonschema import Draft202012Validator


def _stable_hash(obj: Any) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(data).hexdigest()


@dataclass
class ConfigSnapshot:
    version: str
    payload: Dict[str, Any]
    checksum: str


class ConfigRegistry:
    """Holds the current configuration snapshot with validation and subscribers."""

    def __init__(self, schema: Dict[str, Any]) -> None:
        self._validator = Draft202012Validator(schema)
        self._snapshot: Optional[ConfigSnapshot] = None
        self._subscribers: List[Callable[[ConfigSnapshot], None]] = []

    def load_defaults(self, payload: Dict[str, Any]) -> ConfigSnapshot:
        """Initialize registry with default config (validated)."""
        self._validator.validate(payload)
        version = str(payload.get("version", "0"))
        snap = ConfigSnapshot(version=version, payload=payload, checksum=_stable_hash(payload))
        self._snapshot = snap
        return snap

    def get(self) -> Optional[ConfigSnapshot]:
        return self._snapshot

    def subscribe(self, callback: Callable[[ConfigSnapshot], None]) -> None:
        self._subscribers.append(callback)

    def apply_update(self, payload: Dict[str, Any]) -> ConfigSnapshot:
        """Validate and apply a new config document.

        Returns the applied snapshot. Raises jsonschema.ValidationError on invalid docs.
        No side effects outside notifying local subscribers.
        """
        self._validator.validate(payload)
        version = str(payload.get("version", "0"))
        snap = ConfigSnapshot(version=version, payload=payload, checksum=_stable_hash(payload))
        self._snapshot = snap
        for cb in list(self._subscribers):
            try:
                cb(snap)
            except Exception:
                # Subscribers must not break the registry; ignore errors here
                pass
        return snap

    def build_ack(self, result: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Construct an acknowledgement payload for external publish by caller.

        result: "ok" | "rejected" | "error"
        error: optional error message when result != ok
        """
        snap = self._snapshot
        return {
            "type": "config.ack",
            "result": result,
            "error": error,
            "version": snap.version if snap else None,
            "checksum": snap.checksum if snap else None,
        }
