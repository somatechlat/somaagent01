"""Logging redaction filter for sensitive values.

Replaces occurrences of configured sensitive keys and bearer tokens in
log record messages and selected extra fields with the placeholder
"[REDACTED]".  This operates at the logging layer so callers do not need
to proactively scrub every value.

Design goals:
  - Minimal overhead: simple string scans, no heavy regex on every record.
  - Configurable via environment variables (LOG_REDACT_KEYS, LOG_REDACT_TOKEN_PREFIXES)
  - Safe defaults covering common secret field names.

Limitations:
  - Only scrubs simple key=value or JSON-ish patterns already rendered in
    the message; deeply nested objects logged via %r may still leak if the
    formatter bypasses message construction. Structured logging in this
    repo ensures JSONFormatter builds from `record.getMessage()` so this
    approach is effective.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Iterable

DEFAULT_KEYS = {
    "authorization",
    "auth",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "password",
    "credentials",
}


def _env_key_set(name: str, base: set[str]) -> set[str]:
    """Execute env key set.

        Args:
            name: The name.
            base: The base.
        """

    raw = os.environ.get(name, "").strip()
    if not raw:
        return base
    extra = {p.strip().lower() for p in raw.split(",") if p.strip()}
    return base | extra


def _compile_patterns(keys: Iterable[str]) -> list[re.Pattern]:
    """Execute compile patterns.

        Args:
            keys: The keys.
        """

    patterns: list[re.Pattern] = []
    for k in keys:
        # Match key": "value", key=value, key':'value', case-insensitive
        pat = re.compile(rf"(\b{k}\b\s*[=:]\s*)([A-Za-z0-9_\-\.\+/=]{{4,}})", re.IGNORECASE)
        patterns.append(pat)
    return patterns


class RedactionFilter(logging.Filter):
    """Redactionfilter class implementation."""

    def __init__(self) -> None:
        """Initialize the instance."""

        super().__init__(name="redaction")
        self.keys = _env_key_set("LOG_REDACT_KEYS", DEFAULT_KEYS)
        self.patterns = _compile_patterns(self.keys)
        # Token prefixes (e.g., sk-, xoxb-, ghp_) redacted when followed by token chars
        raw_prefixes = os.environ.get("LOG_REDACT_TOKEN_PREFIXES", "sk-,xoxb-,xoxp-,ghp_")
        self.prefixes = [p.strip() for p in raw_prefixes.split(",") if p.strip()]
        if self.prefixes:
            pref_alt = "|".join(re.escape(p) for p in self.prefixes)
            self.token_pattern = re.compile(rf"({pref_alt})([A-Za-z0-9]{{8,}})")
        else:
            self.token_pattern = None

    def _redact(self, text: str) -> str:
        """Execute redact.

            Args:
                text: The text.
            """

        if not text:
            return text
        out = text
        for pat in self.patterns:
            out = pat.sub(r"\1[REDACTED]", out)
        if self.token_pattern:
            out = self.token_pattern.sub(r"\1[REDACTED]", out)
        return out

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        """Execute filter.

            Args:
                record: The record.
            """

        try:
            # Redact the formatted message (getMessage executed later by formatter)
            if isinstance(record.msg, str):
                record.msg = self._redact(record.msg)
            # Redact common extra fields if present
            for attr in ("payload", "payload_preview", "authorization", "token"):
                if hasattr(record, attr):
                    val = getattr(record, attr)
                    if isinstance(val, str):
                        setattr(record, attr, self._redact(val))
        except Exception:
            # Never block logging on filter errors
            return True
        return True


def install_redaction_filter(root: logging.Logger | None = None) -> None:
    """Execute install redaction filter.

        Args:
            root: The root.
        """

    logger = root or logging.getLogger()
    flt = RedactionFilter()
    for handler in logger.handlers:
        handler.addFilter(flt)


__all__ = ["install_redaction_filter", "RedactionFilter"]