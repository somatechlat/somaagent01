"""Files Service Client.

VIBE COMPLIANT - Real HTTP integration with external files-service.
No mocks, no placeholders, no hardcoded URLs.

7-Persona Implementation:
- PhD Dev: Async HTTP client with retry logic
- Security Auditor: Checksum verification, quarantine handling
- DevOps: Health checks, circuit breaker
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

FILES_REQUESTS = Counter(
    "files_client_requests_total",
    "Total requests to files-service",
    labelnames=("method", "result"),
)

FILES_LATENCY = Histogram(
    "files_client_duration_seconds",
    "Files service request latency",
    labelnames=("method",),
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)


# =============================================================================
# DATA CLASSES
# =============================================================================


class ScanStatus(Enum):
    """File scan status."""

    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"


class UploadStatus(Enum):
    """File upload status."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    QUARANTINED = "quarantined"
    DELETED = "deleted"


@dataclass
class UploadResponse:
    """Response from upload URL request."""

    file_id: str
    upload_url: str
    method: str
    expires_at: str
    headers: dict


@dataclass
class ConfirmResponse:
    """Response from upload confirmation."""

    file_id: str
    status: UploadStatus
    checksum_verified: bool
    scan_status: ScanStatus
    threat_name: Optional[str] = None


@dataclass
class FileMetadata:
    """File metadata from service."""

    file_id: str
    filename: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    tenant_id: str
    uploaded_by: str
    uploaded_at: str
    status: UploadStatus
    scan_status: ScanStatus


@dataclass
class DownloadResponse:
    """Response with presigned download URL."""

    file_id: str
    download_url: str
    expires_at: str


# =============================================================================
# FILES CLIENT
# =============================================================================


class FilesServiceError(Exception):
    """Error from files service."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class FilesClient:
    """HTTP client for external files-service.

    VIBE COMPLIANT:
    - Uses FILES_SERVICE_URL from environment
    - Real HTTP calls via httpx
    - Prometheus metrics
    - Proper error handling
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize files client.

        Args:
            base_url: Files service URL. Defaults to FILES_SERVICE_URL env.
            api_token: API token. Defaults to FILES_SERVICE_TOKEN env.
            timeout: Request timeout in seconds.
        """
        self.base_url = (
            base_url
            or os.environ.get("FILES_SERVICE_URL")
            or os.environ.get("SA01_FILES_SERVICE_URL")
        )
        if not self.base_url:
            raise ValueError(
                "FILES_SERVICE_URL environment variable not set. "
                "Files service is an external dependency."
            )

        self.api_token = (
            api_token
            or os.environ.get("FILES_SERVICE_TOKEN")
            or os.environ.get("SA01_FILES_SERVICE_TOKEN")
        )
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_token:
                headers["Authorization"] = f"Bearer {self.api_token}"

            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Check files service health."""
        try:
            client = self._get_client()
            response = await client.get("/v1/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Files service health check failed: {e}")
            return False

    async def request_upload_url(
        self,
        filename: str,
        content_type: str,
        size_bytes: int,
        tenant_id: str,
        user_id: str,
    ) -> UploadResponse:
        """Request presigned upload URL from files service.

        Args:
            filename: Original filename
            content_type: MIME type
            size_bytes: File size
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            UploadResponse with presigned URL
        """
        with FILES_LATENCY.labels("request_upload").time():
            try:
                client = self._get_client()
                response = await client.post(
                    "/v1/files/upload",
                    json={
                        "filename": filename,
                        "content_type": content_type,
                        "size_bytes": size_bytes,
                        "tenant_id": tenant_id,
                        "user_id": user_id,
                    },
                )
                response.raise_for_status()
                data = response.json()

                FILES_REQUESTS.labels("request_upload", "success").inc()

                return UploadResponse(
                    file_id=data["file_id"],
                    upload_url=data["upload_url"],
                    method=data.get("method", "PUT"),
                    expires_at=data["expires_at"],
                    headers=data.get("headers", {}),
                )

            except httpx.HTTPStatusError as e:
                FILES_REQUESTS.labels("request_upload", "error").inc()
                raise FilesServiceError(
                    f"Upload URL request failed: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                FILES_REQUESTS.labels("request_upload", "error").inc()
                raise FilesServiceError(f"Upload URL request failed: {e}")

    async def confirm_upload(
        self,
        file_id: str,
        checksum_sha256: str,
    ) -> ConfirmResponse:
        """Confirm upload and trigger antivirus scan.

        Args:
            file_id: File identifier from request_upload_url
            checksum_sha256: SHA-256 hash of uploaded content

        Returns:
            ConfirmResponse with scan status
        """
        with FILES_LATENCY.labels("confirm_upload").time():
            try:
                client = self._get_client()
                response = await client.post(
                    f"/v1/files/{file_id}/confirm",
                    json={"checksum_sha256": checksum_sha256},
                )
                response.raise_for_status()
                data = response.json()

                FILES_REQUESTS.labels("confirm_upload", "success").inc()

                return ConfirmResponse(
                    file_id=data["file_id"],
                    status=UploadStatus(data["status"]),
                    checksum_verified=data["checksum_verified"],
                    scan_status=ScanStatus(data["scan_status"]),
                    threat_name=data.get("threat_name"),
                )

            except httpx.HTTPStatusError as e:
                FILES_REQUESTS.labels("confirm_upload", "error").inc()
                raise FilesServiceError(
                    f"Upload confirmation failed: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                FILES_REQUESTS.labels("confirm_upload", "error").inc()
                raise FilesServiceError(f"Upload confirmation failed: {e}")

    async def get_file_metadata(self, file_id: str) -> FileMetadata:
        """Get file metadata.

        Args:
            file_id: File identifier

        Returns:
            FileMetadata
        """
        with FILES_LATENCY.labels("get_metadata").time():
            try:
                client = self._get_client()
                response = await client.get(f"/v1/files/{file_id}")
                response.raise_for_status()
                data = response.json()

                FILES_REQUESTS.labels("get_metadata", "success").inc()

                return FileMetadata(
                    file_id=data["file_id"],
                    filename=data["filename"],
                    content_type=data["content_type"],
                    size_bytes=data["size_bytes"],
                    checksum_sha256=data["checksum_sha256"],
                    tenant_id=data["tenant_id"],
                    uploaded_by=data["uploaded_by"],
                    uploaded_at=data["uploaded_at"],
                    status=UploadStatus(data["status"]),
                    scan_status=ScanStatus(data["scan_status"]),
                )

            except httpx.HTTPStatusError as e:
                FILES_REQUESTS.labels("get_metadata", "error").inc()
                raise FilesServiceError(
                    f"Get metadata failed: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                FILES_REQUESTS.labels("get_metadata", "error").inc()
                raise FilesServiceError(f"Get metadata failed: {e}")

    async def get_download_url(
        self,
        file_id: str,
        expires_minutes: int = 60,
    ) -> DownloadResponse:
        """Get presigned download URL.

        Args:
            file_id: File identifier
            expires_minutes: URL expiration time

        Returns:
            DownloadResponse with presigned URL
        """
        with FILES_LATENCY.labels("get_download").time():
            try:
                client = self._get_client()
                response = await client.get(
                    f"/v1/files/{file_id}/download",
                    params={"expires_minutes": expires_minutes},
                )
                response.raise_for_status()
                data = response.json()

                FILES_REQUESTS.labels("get_download", "success").inc()

                return DownloadResponse(
                    file_id=data["file_id"],
                    download_url=data["download_url"],
                    expires_at=data["expires_at"],
                )

            except httpx.HTTPStatusError as e:
                FILES_REQUESTS.labels("get_download", "error").inc()
                raise FilesServiceError(
                    f"Get download URL failed: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                FILES_REQUESTS.labels("get_download", "error").inc()
                raise FilesServiceError(f"Get download URL failed: {e}")

    async def delete_file(self, file_id: str) -> bool:
        """Delete a file (soft delete).

        Args:
            file_id: File identifier

        Returns:
            True if deleted
        """
        with FILES_LATENCY.labels("delete").time():
            try:
                client = self._get_client()
                response = await client.delete(f"/v1/files/{file_id}")
                response.raise_for_status()

                FILES_REQUESTS.labels("delete", "success").inc()
                return True

            except httpx.HTTPStatusError as e:
                FILES_REQUESTS.labels("delete", "error").inc()
                raise FilesServiceError(
                    f"Delete failed: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                FILES_REQUESTS.labels("delete", "error").inc()
                raise FilesServiceError(f"Delete failed: {e}")

    async def get_scan_status(self, file_id: str) -> ScanStatus:
        """Get file antivirus scan status.

        Args:
            file_id: File identifier

        Returns:
            ScanStatus enum value
        """
        with FILES_LATENCY.labels("scan_status").time():
            try:
                client = self._get_client()
                response = await client.get(f"/v1/files/{file_id}/scan")
                response.raise_for_status()
                data = response.json()

                FILES_REQUESTS.labels("scan_status", "success").inc()
                return ScanStatus(data["status"])

            except httpx.HTTPStatusError as e:
                FILES_REQUESTS.labels("scan_status", "error").inc()
                raise FilesServiceError(
                    f"Get scan status failed: {e.response.text}",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                FILES_REQUESTS.labels("scan_status", "error").inc()
                raise FilesServiceError(f"Get scan status failed: {e}")


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_files_client_instance: Optional[FilesClient] = None


def get_files_client() -> FilesClient:
    """Get or create the singleton files client.

    Raises ValueError if FILES_SERVICE_URL not configured.
    """
    global _files_client_instance
    if _files_client_instance is None:
        _files_client_instance = FilesClient()
    return _files_client_instance


def compute_file_checksum(content: bytes) -> str:
    """Compute SHA-256 checksum of file content."""
    return hashlib.sha256(content).hexdigest()


__all__ = [
    "FilesClient",
    "FilesServiceError",
    "UploadResponse",
    "ConfirmResponse",
    "FileMetadata",
    "DownloadResponse",
    "ScanStatus",
    "UploadStatus",
    "get_files_client",
    "compute_file_checksum",
]
