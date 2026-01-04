"""Upload Sensor - ZDL Pattern.


Tracks: file uploads, processing status, storage location, deletions.

Usage:
    sensor = UploadSensor(tenant_id="tenant-123")
    sensor.capture_upload_start(filename="doc.pdf", session_id="...")
    sensor.capture_upload_complete(file_id="...", storage_url="...")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from admin.core.sensors.base import BaseSensor

logger = logging.getLogger(__name__)


class UploadSensor(BaseSensor):
    """Upload sensor for Zero Data Loss.

    Captures:
    - Upload start
    - Upload complete
    - Upload processing (e.g., embedding generation)
    - Upload deletion
    - Upload errors
    """

    sensor_name = "upload"
    target_service = "somabrain"

    def capture_upload_start(
        self,
        session_id: str,
        filename: str,
        content_type: str,
        size_bytes: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Capture upload start event."""
        return self.capture(
            event_type="upload.start",
            data={
                "session_id": session_id,
                "filename": filename,
                "content_type": content_type,
                "size_bytes": size_bytes,
                "metadata": metadata or {},
            },
        )

    def capture_upload_complete(
        self,
        session_id: str,
        file_id: str,
        filename: str,
        storage_url: str,
        size_bytes: int,
        content_type: str,
    ) -> str:
        """Capture upload complete event."""
        return self.capture(
            event_type="upload.complete",
            data={
                "session_id": session_id,
                "file_id": file_id,
                "filename": filename,
                "storage_url": storage_url,
                "size_bytes": size_bytes,
                "content_type": content_type,
            },
        )

    def capture_upload_processing(
        self,
        file_id: str,
        processing_type: str,  # e.g., "embedding", "ocr", "thumbnail"
        status: str,  # e.g., "started", "completed", "failed"
        result: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Capture upload processing event."""
        return self.capture(
            event_type="upload.processing",
            data={
                "file_id": file_id,
                "processing_type": processing_type,
                "status": status,
                "result": result or {},
            },
        )

    def capture_upload_deletion(
        self,
        file_id: str,
        filename: str,
        deleted_by: str = None,
    ) -> str:
        """Capture upload deletion event."""
        return self.capture(
            event_type="upload.deletion",
            data={
                "file_id": file_id,
                "filename": filename,
                "deleted_by": deleted_by,
            },
        )

    def capture_upload_error(
        self,
        session_id: str,
        filename: str,
        error: str,
        error_type: str = "upload",
    ) -> str:
        """Capture upload error event."""
        return self.capture(
            event_type="upload.error",
            data={
                "session_id": session_id,
                "filename": filename,
                "error": error,
                "error_type": error_type,
            },
        )
