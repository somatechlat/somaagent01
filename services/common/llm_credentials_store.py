"""Redis-backed storage for provider LLM credentials, with optional encryption.

This store is used by the Gateway to persist provider-specific API secrets that
conversation workers can retrieve securely at runtime. Secrets are encrypted at
rest using a symmetric key provided via the `GATEWAY_ENC_KEY` environment
variable (Fernet-compatible urlsafe base64-encoded 32-byte key). If the key is
missing, the Gateway refuses to store credentials.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

import redis.asyncio as redis
from cryptography.fernet import Fernet, InvalidToken


class LlmCredentialsStore:
    def __init__(self, *, redis_url: Optional[str] = None, namespace: str = "gateway:llm_credentials") -> None:
        self._r: redis.Redis = redis.from_url(redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        self._ns = namespace
        self._fernet = self._load_fernet()

    def _load_fernet(self) -> Fernet:
        key = os.getenv("GATEWAY_ENC_KEY")
        if not key:
            raise RuntimeError("GATEWAY_ENC_KEY is required to store LLM credentials securely")
        # Accept raw urlsafe base64 key or plaintext that should be base64 encoded
        try:
            # Validate length by constructing Fernet
            return Fernet(key.encode("utf-8") if not _looks_base64(key) else key.encode("utf-8"))
        except Exception:
            # Try to base64-url encode input bytes if not already
            try:
                k = base64.urlsafe_b64encode(key.encode("utf-8"))
                return Fernet(k)
            except Exception as exc:
                raise RuntimeError("Invalid GATEWAY_ENC_KEY; must be 32-byte urlsafe base64") from exc

    async def set(self, provider: str, secret: str) -> None:
        provider = provider.strip().lower()
        token = self._fernet.encrypt(secret.encode("utf-8")).decode("ascii")
        await self._r.hset(self._ns, provider, token)

    async def get(self, provider: str) -> Optional[str]:
        provider = provider.strip().lower()
        token = await self._r.hget(self._ns, provider)
        if not token:
            return None
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except InvalidToken:
            return None

    async def delete(self, provider: str) -> None:
        provider = provider.strip().lower()
        await self._r.hdel(self._ns, provider)

    async def list_providers(self) -> list[str]:
        try:
            items = await self._r.hkeys(self._ns)
        except Exception:
            return []
        return [str(p) for p in items]

    async def has(self, provider: str) -> bool:
        """Return True if a credential exists for the provider."""
        try:
            return (await self.get(provider)) is not None
        except Exception:
            return False


def _looks_base64(s: str) -> bool:
    try:
        base64.urlsafe_b64decode(s.encode("utf-8"))
        return True
    except Exception:
        return False
