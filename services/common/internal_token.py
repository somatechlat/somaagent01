"""Thin wrapper around :class:`SecretManager` for the internal service‑to‑service token.

Only the minimal async ``get``/``set`` helpers are exported – the underlying
manager handles encryption and Redis storage.
"""

from __future__ import annotations

from typing import Optional

from .secret_manager import SecretManager

# A single shared instance – constructing ``SecretManager`` is cheap after the
# first import because the Redis client and Fernet key are cached.
_manager = SecretManager()


async def set_token(token: str) -> None:
    """Persist the internal JWT or opaque token used for service‑to‑service auth."""
    await manager.set_internal_token(token)


async def get_token() -> Optional[str]:
    """Retrieve the stored internal token, or ``None`` if it has not been set."""
    return await manager.get_internal_token()


async def has_token() -> bool:
    """Convenient boolean check for the presence of a stored token."""
    return await manager.has_internal_token()
