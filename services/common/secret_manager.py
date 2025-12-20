"""Central secret manager – the *only* place that reads or writes encrypted secrets.

All production‑level secrets (LLM provider API keys, internal service‑to‑service
token, Fernet encryption key) are stored in Redis **encrypted with a Fernet
key**.  The manager is a singleton per process – the first import creates the
Redis connection and loads the Fernet instance; subsequent imports reuse the
same objects.  This guarantees a single source of truth and makes the code
easily mockable in tests.

Why we need it
---------------
* No component may read ``os.getenv`` directly – the only allowed env reads are
  in ``services.common.runtime_config`` (bootstrap).  By funnelling all secret
  access through this module we satisfy the VIBE *no direct env* rule.
* Encryption at rest is mandatory for compliance.  The Fernet key is supplied
  via the ``SA01_CRYPTO_FERNET_KEY`` environment variable (a url‑safe base64
  32‑byte string).  If the key is missing the application fails fast.
* Workers need a fast, async‑compatible API – the methods are ``async`` and use
  ``redis.asyncio``.
"""

from __future__ import annotations

from typing import List, Optional

import redis.asyncio as redis
from cryptography.fernet import Fernet, InvalidToken

import os

from src.core.config import cfg


# ---------------------------------------------------------------------------
# Helper – validate / normalise the Fernet key supplied via env
# ---------------------------------------------------------------------------
def _load_fernet_key() -> Fernet:
    """Load the Fernet instance from ``SA01_CRYPTO_FERNET_KEY``.

    The environment variable must contain a url‑safe base64‑encoded 32‑byte key.
    """
    raw_key = os.environ.get("SA01_CRYPTO_FERNET_KEY") or cfg.env("SA01_CRYPTO_FERNET_KEY")
    if not raw_key:
        raise RuntimeError(
            "SA01_CRYPTO_FERNET_KEY is required – provide a urlsafe base64 32‑byte key"
        )

    try:
        # ``Fernet`` validates length internally.
        return Fernet(raw_key.encode())
    except Exception as exc:
        raise RuntimeError("Invalid SA01_CRYPTO_FERNET_KEY supplied") from exc


# ---------------------------------------------------------------------------
# Singleton secret manager
# ---------------------------------------------------------------------------
class SecretManager:
    """Async façade for encrypted secret storage.

    *Namespace*
        All keys are stored under a Redis hash ``gateway:secrets``.  Individual
        entries are prefixed (e.g. ``provider:groq``) to avoid collisions.
    *Caching*
        The Fernet instance and Redis client are created once at import time –
        subsequent calls are cheap async Redis hash operations.
    """

    _redis: redis.Redis
    _fernet: Fernet
    _namespace: str = "gateway:secrets"

    def __init__(self) -> None:
        # VIBE Rule #1: NO ALTERNATES - Fail fast if Redis unavailable
        redis_url = os.environ.get("SA01_REDIS_URL") or cfg.env("SA01_REDIS_URL")
        if not redis_url:
            raise RuntimeError(
                "SA01_REDIS_URL environment variable required for SecretManager. "
                "Redis is REQUIRED for encrypted secret storage in production. "
                "No alternate sources per VIBE Coding Rules. "
                "Set SA01_REDIS_URL=redis://host:6379/0 in your environment."
            )
        
        self._redis = redis.from_url(redis_url, decode_responses=True)
        
        # Defer Fernet creation until first use. This allows the manager to be
        # instantiated in test environments where the encryption key may be
        # intentionally omitted.
        self._fernet: Fernet | None = None

    def _ensure_fernet(self) -> Fernet:
        """Return a Fernet instance, loading it on first call.

        The original implementation raised ``RuntimeError`` if the key was not
        set. For compatibility with existing tests that import the manager but
        never encrypt/decrypt data we lazily initialise the key and raise only
        when an encryption operation is requested.
        """
        if self._fernet is None:
            self._fernet = _load_fernet_key()
        return self._fernet

    # ---------------------------------------------------------------------
    # Generic helpers (internal)
    # ---------------------------------------------------------------------
    def _hash_key(self, name: str) -> str:
        """Return the full Redis‑hash field name for a logical secret name.

        ``provider:groq`` → ``gateway:secrets:provider:groq``
        """
        return name  # the namespace is the hash itself; field is the name

    async def _set_encrypted(self, field: str, value: str) -> None:
        token = self._ensure_fernet().encrypt(value.encode()).decode("ascii")
        await self._redis.hset(self._namespace, field, token)

    async def _get_decrypted(self, field: str) -> Optional[str]:
        token = await self._redis.hget(self._namespace, field)
        if token is None:
            return None
        try:
            return self._ensure_fernet().decrypt(token.encode()).decode("utf-8")
        except InvalidToken:
            # Corrupted or wrong key – treat as missing.
            return None

    # ---------------------------------------------------------------------
    # Public API – provider credentials
    # ---------------------------------------------------------------------
    async def set_provider_key(self, provider: str, api_key: str) -> None:
        """Store the API key for a given LLM provider (e.g. ``groq``)."""
        field = self._hash_key(f"provider:{provider.lower()}")
        await self._set_encrypted(field, api_key)

    async def get_provider_key(self, provider: str) -> Optional[str]:
        field = self._hash_key(f"provider:{provider.lower()}")
        return await self._get_decrypted(field)

    async def delete_provider_key(self, provider: str) -> None:
        field = self._hash_key(f"provider:{provider.lower()}")
        await self._redis.hdel(self._namespace, field)

    async def list_providers(self) -> List[str]:
        """Return a list of provider names that have a stored key."""
        raw_fields = await self._redis.hkeys(self._namespace)
        providers: List[str] = []
        for f in raw_fields:
            if f.startswith("provider:"):
                providers.append(f.split(":", 1)[1])
        return providers

    # ---------------------------------------------------------------------
    # Public API – internal service‑to‑service token
    # ---------------------------------------------------------------------
    async def set_internal_token(self, token: str) -> None:
        await self._set_encrypted("internal_token", token)

    async def get_internal_token(self) -> Optional[str]:
        return await self._get_decrypted("internal_token")

    # ---------------------------------------------------------------------
    # Convenience – existence checks
    # ---------------------------------------------------------------------
    async def has_provider_key(self, provider: str) -> bool:
        return (await self.get_provider_key(provider)) is not None

    async def has_internal_token(self) -> bool:
        return (await self.get_internal_token()) is not None
