"""MinIO-backed object storage for exports, backups and audit artefacts.

Real object storage against the MinIO S3 API (``minio`` SDK). Credentials come
from Vault ONLY and the resolution is fail-closed:

    secret/agent/credentials/minio_access_key
    secret/agent/credentials/minio_secret_key

resolved through :class:`UnifiedSecretManager.get_credential`. There is no ENV
fallback, no empty default and no vendor-default credential shim — if either secret is
missing or Vault is unreachable the object store does not start and the raised
error names the missing Vault path.

Endpoint and bucket are non-secret topology (env / Django settings), never
Vault material.
"""

from __future__ import annotations

import io
import logging
import os
from typing import Any, Optional

from services.common.unified_secret_manager import get_secret_manager

LOGGER = logging.getLogger("object_store")

# Vault contract (secret/agent/credentials/{key}) — see SOMA-SETTINGS-MODEL-001.md.
ACCESS_KEY_SECRET = "minio_access_key"
SECRET_KEY_SECRET = "minio_secret_key"
ACCESS_KEY_PATH = f"secret/agent/credentials/{ACCESS_KEY_SECRET}"
SECRET_KEY_PATH = f"secret/agent/credentials/{SECRET_KEY_SECRET}"


class ObjectStoreUnavailable(RuntimeError):
    """Raised when MinIO credentials cannot be resolved from Vault."""


def _topology(name: str, default: str) -> str:
    """Read non-secret topology: Django settings first, then env."""
    try:
        from django.conf import settings

        value = getattr(settings, name, None)
        if value:
            return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


def _normalize_endpoint(raw: str) -> tuple[str, bool]:
    """Split an endpoint into (host:port, secure) for the MinIO SDK.

    Operators may configure either ``minio:9000`` or ``https://minio:9000``;
    the SDK itself wants host:port plus a separate ``secure`` flag.
    """
    from urllib.parse import urlsplit

    value = raw.strip()
    if "://" not in value:
        hostport = value.rstrip("/")
        return hostport, False

    parts = urlsplit(value)
    if not parts.netloc:
        raise ObjectStoreUnavailable(
            f"MINIO_ENDPOINT {raw!r} is not a valid endpoint; expected host:port "
            "or scheme://host:port"
        )
    if parts.path not in ("", "/"):
        raise ObjectStoreUnavailable(
            f"MINIO_ENDPOINT {raw!r} must not contain a path (got {parts.path!r}); "
            "bucket names belong in MINIO_BUCKET"
        )
    return parts.netloc, parts.scheme.lower() == "https"


class MinioObjectStore:
    """Real MinIO object storage: put / get / delete / exists / list."""

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ) -> None:
        from minio import Minio

        self.endpoint = endpoint
        self.bucket = bucket
        self.secure = secure
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._bucket_ready = False

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        if not self._client.bucket_exists(self.bucket):
            self._client.make_bucket(self.bucket)
        self._bucket_ready = True

    def put_bytes(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        self._ensure_bucket()
        self._client.put_object(
            self.bucket, key, io.BytesIO(data), length=len(data), content_type=content_type
        )
        return key

    def get_bytes(self, key: str) -> bytes:
        response = self._client.get_object(self.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> bool:
        self._client.remove_object(self.bucket, key)
        return True

    def exists(self, key: str) -> bool:
        try:
            self._client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False

    def list_keys(self, prefix: str = "") -> list[str]:
        objects = self._client.list_objects(self.bucket, prefix=prefix or "")
        return [obj.object_name for obj in objects]

    def healthcheck(self) -> dict[str, Any]:
        return {"endpoint": self.endpoint, "bucket": self.bucket, "ok": True}


def get_object_store() -> MinioObjectStore:
    """Build the MinIO object store from Vault credentials (fail-closed).

    Raises:
        ObjectStoreUnavailable: naming every Vault path that could not be
            resolved. Never falls back to ENV or default credentials.
    """
    manager = get_secret_manager()
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    vault_error: Optional[Exception] = None

    try:
        access_key = manager.get_credential(ACCESS_KEY_SECRET)
        secret_key = manager.get_credential(SECRET_KEY_SECRET)
    except Exception as exc:  # Vault unreachable / mount missing — fail closed.
        vault_error = exc

    missing = []
    if not access_key:
        missing.append(ACCESS_KEY_PATH)
    if not secret_key:
        missing.append(SECRET_KEY_PATH)

    if missing:
        detail = f" (Vault error: {vault_error})" if vault_error else ""
        LOGGER.error(
            "object store credentials unavailable from Vault; refusing to start",
            extra={"missing": missing},
        )
        raise ObjectStoreUnavailable(
            "MinIO credentials are not available from Vault; refusing to start the "
            f"object store. Missing: {', '.join(missing)}. No ENV fallback and no "
            f"default credentials are permitted.{detail}"
        )

    endpoint, scheme_secure = _normalize_endpoint(_topology("MINIO_ENDPOINT", "http://minio:9000"))
    bucket = _topology("MINIO_BUCKET", "soma-artefacts")
    secure = scheme_secure or os.environ.get("MINIO_SECURE", "").lower() in {"1", "true", "yes"}

    return MinioObjectStore(
        endpoint=endpoint,
        access_key=access_key,  # type: ignore[arg-type]
        secret_key=secret_key,  # type: ignore[arg-type]
        bucket=bucket,
        secure=secure,
    )


__all__ = [
    "ACCESS_KEY_PATH",
    "SECRET_KEY_PATH",
    "MinioObjectStore",
    "ObjectStoreUnavailable",
    "get_object_store",
]
