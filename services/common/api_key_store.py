"""API key storage and management utilities."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import json
import secrets
import time
import uuid
from dataclasses import dataclass
from typing import Any, List, Optional

import redis.asyncio as redis

__all__ = [
    "ApiKeyMetadata",
    "ApiKeySecret",
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
class ApiKeySecret(ApiKeyMetadata):
    secret: str


class ApiKeyStore:
    """Abstract API key store."""

    async def create_key(self, label: str, *, created_by: str | None = None) -> ApiKeySecret:
        raise NotImplementedError

    async def list_keys(self) -> List[ApiKeyMetadata]:
        raise NotImplementedError

    async def revoke_key(self, key_id: str) -> None:
        raise NotImplementedError

    async def verify_key(self, api_key: str) -> Optional[ApiKeyMetadata]:
        raise NotImplementedError

    async def touch_key(self, key_id: str) -> None:
        raise NotImplementedError


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
        raw_url = url or "redis://localhost:6379/0"
        # Expand env placeholders so URLs like redis://localhost:${REDIS_PORT}/0 work in local .env
        self.url = os.path.expandvars(raw_url)
        self._client: redis.Redis = redis.from_url(self.url, decode_responses=True)
        self._namespace = "gateway:api_keys"

    async def create_key(self, label: str, *, created_by: str | None = None) -> ApiKeySecret:
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
        raw = await self._client.hvals(self._namespace)
        return [_metadata_from_record(json.loads(item)) for item in raw]

    async def revoke_key(self, key_id: str) -> None:
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
