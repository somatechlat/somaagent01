"""Constitution + Persona aware prompt providers (in-memory, fail-closed)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from python.integrations.soma_client import (
    SomaClient,  # type: ignore
    SomaClientError,
)
import os


@dataclass
class ConstitutionPayload:
    version: str
    text: str


@dataclass
class PersonaPayload:
    version: Optional[str]
    text: str


class ConstitutionPromptProvider:
    """Fetches and caches the signed Constitution. Fail-closed on errors."""

    def __init__(self, client: SomaClient, ttl_seconds: int = 300) -> None:
        self.client = client
        self.ttl = ttl_seconds
        self._cached: Optional[ConstitutionPayload] = None
        self._expires_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get(self) -> ConstitutionPayload:
        now = time.time()
        if self._cached and now < self._expires_at:
            return self._cached
        async with self._lock:
            if self._cached and now < self._expires_at:
                return self._cached
            payload = await self._fetch()
            self._cached = payload
            self._expires_at = time.time() + self.ttl
            return payload

    async def reload(self) -> ConstitutionPayload:
        async with self._lock:
            payload = await self._fetch()
            self._cached = payload
            self._expires_at = time.time() + self.ttl
            return payload

    async def _fetch(self) -> ConstitutionPayload:
        try:
            resp = await self.client.constitution_version()
        except Exception as exc:
            raise RuntimeError(f"constitution_unavailable: {exc}") from exc
        version = str(resp.get("version") or resp.get("etag") or "")
        text = resp.get("text") or resp.get("body") or resp.get("constitution")
        if not version or not text:
            raise RuntimeError("constitution_invalid: missing version/text")
        return ConstitutionPayload(version=version, text=text)


class PersonaProvider:
    """Returns persona prompt fragment for tenant/persona; cached with TTL."""

    def __init__(self, client: SomaClient, ttl_seconds: int = 300) -> None:
        self.client = client
        self.ttl = ttl_seconds
        self._cache: dict[Tuple[str, str], Tuple[PersonaPayload, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, tenant_id: str, persona_id: Optional[str]) -> PersonaPayload:
        key = (tenant_id, persona_id or "")
        now = time.time()
        cached = self._cache.get(key)
        if cached and now < cached[1]:
            return cached[0]
        async with self._lock:
            cached = self._cache.get(key)
            if cached and now < cached[1]:
                return cached[0]
            payload = await self._fetch(tenant_id, persona_id)
            self._cache[key] = (payload, time.time() + self.ttl)
            return payload

    async def _fetch(self, tenant_id: str, persona_id: Optional[str]) -> PersonaPayload:
        if not persona_id:
            return PersonaPayload(version=None, text="")
        try:
            resp = await self.client.get_persona(persona_id)
        except SomaClientError as exc:
            raise RuntimeError(f"persona_unavailable: {exc}") from exc
        version = resp.get("version") or resp.get("etag") or resp.get("id")
        text = resp.get("prompt") or resp.get("system_prompt") or ""
        return PersonaPayload(version=str(version) if version else None, text=text)


def ttl_from_env(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)) or default)
    except Exception:
        return default
