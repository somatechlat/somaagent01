"""Deterministic environment snapshot utilities.

All legacy accesses to environment variables flow through this module so that
the Zero-Legacy roadmap maintains a single point of entry.  The snapshot can be
refreshed (e.g., in tests) via ``refresh()`` to pick up mutations to
``os.environ`` when required.
"""

from __future__ import annotations

import os
import re
from typing import Optional


_VAR_PATTERN = re.compile(r"\$(\w+)|\${(\w+)}")


class _EnvSnapshot:
    def __init__(self) -> None:
        self._data: dict[str, str] = dict(os.environ)

    def refresh(self) -> None:
        self._data = dict(os.environ)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self._data.get(key, default)

    def expand(self, value: str) -> str:
        if not value:
            return value

        def _replace(match: re.Match[str]) -> str:
            key = match.group(1) or match.group(2)
            return self._data.get(key.strip(), "")

        return _VAR_PATTERN.sub(_replace, value)


_SNAPSHOT = _EnvSnapshot()


def refresh() -> None:
    """Refresh the cached environment snapshot (used by tests)."""
    _SNAPSHOT.refresh()


def get(key: str, default: Optional[str] = None) -> Optional[str]:
    return _SNAPSHOT.get(key, default)


def get_bool(key: str, default: bool = False) -> bool:
    raw = get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_int(key: str, default: int) -> int:
    raw = get(key)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def expand(value: str) -> str:
    return _SNAPSHOT.expand(value)
