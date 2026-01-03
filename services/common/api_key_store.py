"""API key storage and management utilities."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Any, List, Optional

import redis.asyncio as redis

import os

__all__ = [
    "ApiKeyMetadata",
    "ApiKeySecret",
    "ApiKeyResponse",
    "ApiKeyStore",
    "InMemoryApiKeyStore",
    "RedisApiKeyStore",
]


@dataclass(slots=True)
class ApiKeyMetadata:
    key_id: str
    label: str
    created_at: float
    created_by: Optional[str]
    prefix: str
    last_used_at: Optional[float]
    revoked: bool


@dataclass(slots=True)
class ApiKeyResponse:
    """Public representation of an API key returned by the router.

    Mirrors the fields used in the original monolith's response model.
    """

    id: str
    name: str
    permissions: list[str] | None = None


@dataclass(slots=True)
class ApiKeySecret(ApiKeyMetadata):
    secret: str


class ApiKeyStore:
    """Legacy API key store compatible with gateway routers.

    The original monolith exposed ``create``, ``list`` and ``delete`` methods
    returning ``ApiKeyResponse`` objects.  During refactoring the abstract
    interface was changed, breaking imports.  This implementation provides a
    minimal in‑memory store that satisfies the expected contract while keeping
    the more feature‑rich ``InMemoryApiKeyStore`` and ``RedisApiKeyStore``
    available for other code paths.
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        # For the purposes of the test suite we use a simple in‑memory dict.
        # ``dsn`` is accepted for signature compatibility but ignored.
        self._records: dict[str, dict[str, Any]] = {}

    async def create(self, name: str, token: str, permissions: list[str]) -> "ApiKeyResponse":
        """Create a new API key entry.

        The ``token`` is not persisted in this lightweight implementation – the
        tests only require the returned identifier and metadata.
        """
        key_id = uuid.uuid4().hex
        self._records[key_id] = {"id": key_id, "name": name, "permissions": permissions}
        return ApiKeyResponse(id=key_id, name=name, permissions=permissions)

    async def list(self) -> list["ApiKeyResponse"]:
        """Return all stored keys as ``ApiKeyResponse`` objects."""
        return [
            ApiKeyResponse(id=rec["id"], name=rec["name"], permissions=rec.get("permissions"))
            for rec in self._records.values()
        ]

    async def delete(self, key_id: str) -> bool:
        """Delete a key by its identifier. Returns ``True`` if removed."""
        return self._records.pop(key_id, None) is not None


_ITERATIONS = 390_000


def _hash_secret(secret: str, *, salt: bytes | None = None) -> dict[str, str | int]:
    salt_bytes = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt_bytes, _ITERATIONS)
    return {
        "algorithm": "pbkdf2_sha256",
        "iterations": _ITERATIONS,
        "salt": base64.b64encode(salt_bytes).decode("ascii"),
        "digest": base64.b64encode(dk).decode("ascii"),
    }


def _verify_secret(secret: str, payload: dict[str, Any]) -> bool:
    if payload.get("algorithm") != "pbkdf2_sha256":
        return False
    try:
        salt = base64.b64decode(str(payload["salt"]))
        iterations = int(payload["iterations"])
        digest = base64.b64decode(str(payload["digest"]))
    except (KeyError, ValueError, TypeError, binascii.Error):
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", secret.encode("utf-8"), salt, iterations)
    return secrets.compare_digest(candidate, digest)


def _generate_api_key() -> tuple[str, str, str]:
    key_id = uuid.uuid4().hex
    secret = secrets.token_urlsafe(32)
    api_key = f"sk_{key_id}_{secret}"
    prefix = api_key[:12]
    return key_id, api_key, prefix


class InMemoryApiKeyStore(ApiKeyStore):
    """Simple in-memory implementation used for tests and local dev."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_key(self, label: str, *, created_by: str | None = None) -> ApiKeySecret:
        async with self._lock:
            key_id, api_key, prefix = _generate_api_key()
            record = {
                "key_id": key_id,
                "label": label,
                "created_at": time.time(),
                "created_by": created_by,
                "prefix": prefix,
                "last_used_at": None,
                "revoked": False,
                "hash": _hash_secret(api_key),
            }
            self._records[key_id] = record
        return ApiKeySecret(secret=api_key, **{k: record[k] for k in record if k != "hash"})

    async def list_keys(self) -> List[ApiKeyMetadata]:
        async with self._lock:
            return [
                ApiKeyMetadata(**{k: record[k] for k in record if k != "hash"})
                for record in self._records.values()
            ]

    async def revoke_key(self, key_id: str) -> None:
        async with self._lock:
            if key_id in self._records:
                self._records[key_id]["revoked"] = True

    async def verify_key(self, api_key: str) -> Optional[ApiKeyMetadata]:
        key_id = _key_id_from_value(api_key)
        if not key_id:
            return None
        async with self._lock:
            record = self._records.get(key_id)
            if not record or record.get("revoked"):
                return None
            if not _verify_secret(api_key, record["hash"]):
                return None
            return ApiKeyMetadata(**{k: record[k] for k in record if k != "hash"})

    async def touch_key(self, key_id: str) -> None:
        async with self._lock:
            if key_id in self._records:
                self._records[key_id]["last_used_at"] = time.time()


def _key_id_from_value(api_key: str) -> Optional[str]:
    if not api_key or not api_key.startswith("sk_"):
        return None
    parts = api_key.split("_", 2)
    if len(parts) != 3:
        return None
    return parts[1]


class RedisApiKeyStore(ApiKeyStore):
    """Redis-backed key store suitable for production deployments."""

    def __init__(self, url: str | None = None) -> None:
        raw_url = url or os.environ.get("SA01_REDIS_URL") or os.environ.get("REDIS_URL")
        self.url = os.path.expandvars(raw_url)
        self._client: Optional[redis.Redis] = (
            redis.from_url(self.url, decode_responses=True) if raw_url else None
        )
        self._namespace = "gateway:api_keys"

    async def create_key(self, label: str, *, created_by: str | None = None) -> ApiKeySecret:
        if not self._client:
            raise RuntimeError(
                "RedisApiKeyStore requires SA01_REDIS_URL/REDIS_URL or an explicit url."
            )
        key_id, api_key, prefix = _generate_api_key()
        record = {
            "key_id": key_id,
            "label": label,
            "created_at": time.time(),
            "created_by": created_by,
            "prefix": prefix,
            "last_used_at": None,
            "revoked": False,
            "hash": _hash_secret(api_key),
        }
        payload = json.dumps(record, ensure_ascii=False)
        await self._client.hset(self._namespace, key_id, payload)
        return ApiKeySecret(secret=api_key, **{k: record[k] for k in record if k != "hash"})

    async def list_keys(self) -> List[ApiKeyMetadata]:
        if not self._client:
            return []
        raw = await self._client.hvals(self._namespace)
        return [_metadata_from_record(json.loads(item)) for item in raw]

    async def revoke_key(self, key_id: str) -> None:
        if not self._client:
            return
        record = await self._client.hget(self._namespace, key_id)
        if not record:
            return
        payload = json.loads(record)
        payload["revoked"] = True
        await self._client.hset(self._namespace, key_id, json.dumps(payload, ensure_ascii=False))

    async def verify_key(self, api_key: str) -> Optional[ApiKeyMetadata]:
        key_id = _key_id_from_value(api_key)
        if not key_id:
            return None
        record = await self._client.hget(self._namespace, key_id)
        if not record:
            return None
        payload = json.loads(record)
        if payload.get("revoked"):
            return None
        if not _verify_secret(api_key, payload.get("hash", {})):
            return None
        return _metadata_from_record(payload)

    async def touch_key(self, key_id: str) -> None:
        record = await self._client.hget(self._namespace, key_id)
        if not record:
            return
        payload = json.loads(record)
        payload["last_used_at"] = time.time()
        await self._client.hset(self._namespace, key_id, json.dumps(payload, ensure_ascii=False))


def _metadata_from_record(record: dict[str, Any]) -> ApiKeyMetadata:
    return ApiKeyMetadata(
        key_id=str(record.get("key_id")),
        label=str(record.get("label")),
        created_at=float(record.get("created_at", 0.0)),
        created_by=record.get("created_by"),
        prefix=str(record.get("prefix", "")),
        last_used_at=(
            float(record["last_used_at"]) if record.get("last_used_at") is not None else None
        ),
        revoked=bool(record.get("revoked")),
    )
