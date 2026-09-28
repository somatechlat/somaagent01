"""HTTP client timeouts — Django settings is the authority.

Every outbound HTTP client must build its timeout here. No inline literals.
Reads ``HTTP_CONNECT_TIMEOUT_S`` / ``HTTP_READ_TIMEOUT_S`` /
``HTTP_SLOW_READ_TIMEOUT_S`` from Django settings (env-backed).
"""

from __future__ import annotations

from typing import Any


def _setting(name: str, default: float) -> float:
    try:
        from django.conf import settings

        value = getattr(settings, name, None)
        if value is not None:
            return float(value)
    except Exception:
        pass
    return float(default)


def connect_timeout() -> float:
    return _setting("HTTP_CONNECT_TIMEOUT_S", 5.0)


def read_timeout() -> float:
    return _setting("HTTP_READ_TIMEOUT_S", 10.0)


def slow_read_timeout() -> float:
    return _setting("HTTP_SLOW_READ_TIMEOUT_S", 30.0)


def httpx_timeout(slow: bool = False) -> Any:
    """Build an httpx.Timeout from Django settings."""
    import httpx

    connect = connect_timeout()
    read = slow_read_timeout() if slow else read_timeout()
    return httpx.Timeout(connect=connect, read=read, write=read, pool=connect)


def slow_httpx_timeout() -> Any:
    """httpx.Timeout with the slow-read budget from Django settings."""
    return httpx_timeout(slow=True)


__all__ = [
    "connect_timeout",
    "read_timeout",
    "slow_read_timeout",
    "httpx_timeout",
    "slow_httpx_timeout",
]
