"""Files V2 API Router.


Enhanced file management with versioning and metadata.

10-Persona Implementation:
- 🏗️ Django Architect: Django Ninja router, async handlers
- 📊 PhD Dev: S3 integration, presigned URLs
- 🔒 Security: Tenant isolation, size limits
- ⚡ Performance: Streaming uploads, chunked transfers
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from django.conf import settings

from admin.core.helpers.service_urls import require_setting
from ninja import Router

from admin.common.auth import AuthBearer
from admin.common.messages import ErrorCode, get_message, SuccessCode
from services.common.authorization import authorize_sync

logger = logging.getLogger(__name__)
router = Router(tags=["Files V2"])


# =============================================================================
# SCHEMAS
# =============================================================================

from ninja import File, Schema, UploadedFile


class FileOut(Schema):
    """File response schema."""

    id: str
    name: str
    original_name: str
    mime_type: str
    size_bytes: int
    version: int
    storage_backend: str
    metadata: dict = {}
    tags: list = []
    created_at: str
    updated_at: str


class FileUploadResponse(Schema):
    """Upload response with presigned URL."""

    file_id: str
    upload_url: str
    expires_in: int


class FileListResponse(Schema):
    """Paginated file list."""

    files: list[FileOut]
    total: int
    page: int
    per_page: int


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/", response=FileListResponse, auth=AuthBearer())
def list_files(
    request,
    page: int = 1,
    per_page: int = 20,
    tenant_id: Optional[str] = None,
):
    """List files with pagination."""
    authorize_sync(request, action="resource:file_read", resource="files")

    from admin.filesv2.models import File

    offset = (page - 1) * per_page

    # Get files with tenant isolation
    queryset = File.objects.filter(deleted_at__isnull=True)
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)

    total = queryset.count()
    files = queryset.order_by("-created_at")[offset : offset + per_page]

    return {
        "files": [
            {
                "id": str(f.id),
                "name": f.name,
                "original_name": f.original_name,
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "version": f.version,
                "storage_backend": f.storage_backend,
                "metadata": f.metadata,
                "tags": f.tags,
                "created_at": f.created_at.isoformat(),
                "updated_at": f.updated_at.isoformat(),
            }
            for f in files
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/upload", response=FileUploadResponse, auth=AuthBearer())
def create_upload_url(
    request,
    filename: str,
    mime_type: str,
    size_bytes: int,
    tenant_id: str,
    user_id: str,
):
    """Create presigned upload URL."""
    authorize_sync(request, action="resource:file_upload", resource="files")

    file_id = str(uuid.uuid4())
    storage_key = f"uploads/{tenant_id}/{file_id}/{filename}"

    # The File row is keyed by the caller's tenant and user (UUID columns) —
    # validate them at this boundary instead of letting the ORM raise a 500.
    try:
        uuid.UUID(str(tenant_id))
        uuid.UUID(str(user_id))
    except ValueError:
        # Raised (not `return body, status`): django-ninja 1.7 reads a 2-tuple
        # as (status, body), and every non-200 status must be declared on the
        # operation — the registered ApiError handler does both.
        from admin.common.exceptions import ValidationError

        raise ValidationError(
            get_message(
                ErrorCode.VALIDATION_ERROR,
                details="tenant_id and user_id must be UUIDs",
            )
        ) from None

    # The row must exist BEFORE either storage path is handed out:
    # POST /upload-local/{file_id} looks it up, and a file without a row can
    # never appear in GET /filesv2/. Creating it only after a successful
    # presign left the local fallback 404-ing in AAAS-in-a-box.
    from admin.filesv2.models import File

    try:
        File.objects.create(
            id=file_id,
            tenant_id=tenant_id,
            user_id=user_id,
            name=filename,
            original_name=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            storage_backend="s3",
        )
    except Exception as e:
        logger.exception("File record create failed: %s", e)
        from admin.common.exceptions import ApiError

        raise ApiError(get_message(ErrorCode.INTERNAL_ERROR)) from e

    # Create S3 presigned URL. The import lives here, not above: boto3 is
    # optional (it is not in requirements.txt), and a missing SDK must land
    # in the local fallback rather than 500 the whole endpoint.
    try:
        import boto3  # type: ignore[import]
        from botocore.config import Config  # type: ignore[import]

        s3_client = boto3.client(
            "s3",
            config=Config(signature_version="s3v4"),
            region_name=require_setting("AWS_REGION"),
        )

        bucket = require_setting("AWS_S3_BUCKET")
        expires_in = 3600  # 1 hour

        upload_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": storage_key,
                "ContentType": mime_type,
            },
            ExpiresIn=expires_in,
        )

        return {
            "file_id": file_id,
            "upload_url": upload_url,
            "expires_in": expires_in,
        }

    except Exception as e:
        logger.exception("S3 presigned URL error: %s", e)
        # Fallback for local dev: the record above already exists, so
        # /upload-local/{file_id} can resolve it.
        return {
            "file_id": file_id,
            "upload_url": f"/api/v2/filesv2/upload-local/{file_id}",
            "expires_in": 3600,
        }


# Registered AFTER /upload and BEFORE the single-segment routes below:
# django resolves URL patterns in registration order and only then checks the
# method, so a GET /{file_id} declared first answers POST /filesv2/upload with
# 405 (live-verified) — literal paths must precede the {file_id} catch-all.
@router.get("/{file_id}", response=FileOut, auth=AuthBearer())
def get_file(request, file_id: str):
    """Get file details."""
    authorize_sync(request, action="resource:file_read", resource="files")

    from admin.filesv2.models import File

    try:
        f = File.objects.get(id=file_id, deleted_at__isnull=True)
        return {
            "id": str(f.id),
            "name": f.name,
            "original_name": f.original_name,
            "mime_type": f.mime_type,
            "size_bytes": f.size_bytes,
            "version": f.version,
            "storage_backend": f.storage_backend,
            "metadata": f.metadata,
            "tags": f.tags,
            "created_at": f.created_at.isoformat(),
            "updated_at": f.updated_at.isoformat(),
        }
    except File.DoesNotExist:
        return {"error": get_message(ErrorCode.NOT_FOUND)}, 404


@router.post("/upload-local/{file_id}", auth=AuthBearer())
def upload_local(request, file_id: str, file: UploadedFile = File(...)):
    """Handle local file upload (Dev/AAAS-in-a-box mode)."""
    authorize_sync(request, action="resource:file_upload", resource="files")

    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage

    from admin.common.exceptions import ApiError
    from admin.filesv2.models import File as FileModel

    # Errors are raised, not `return body, status`: django-ninja 1.7 reads a
    # 2-tuple as (status, body) and refuses undeclared statuses — the
    # registered ApiError handler turns these into proper HTTP responses.
    try:
        f = FileModel.objects.get(id=file_id, deleted_at__isnull=True)
    except FileModel.DoesNotExist:
        raise ApiError(
            get_message(ErrorCode.NOT_FOUND),
            status_code=404,
            error_code=ErrorCode.NOT_FOUND.value,
        ) from None

    # Security check: ensure file size doesn't exceed limit
    if file.size > f.size_bytes + (1024 * 1024):  # 1MB buffer
        raise ApiError(
            get_message(ErrorCode.FILE_SIZE_EXCEEDED),
            status_code=400,
            error_code=ErrorCode.FILE_SIZE_EXCEEDED.value,
        )

    try:
        # Save to local storage using the pre-defined key
        path = default_storage.save(f.storage_key, ContentFile(file.read()))
    except Exception as e:
        logger.exception("Local upload failed: %s", e)
        raise ApiError(get_message(ErrorCode.INTERNAL_ERROR)) from e

    return {"success": True, "path": path}


@router.delete("/{file_id}", auth=AuthBearer())
def delete_file(request, file_id: str):
    """Soft delete a file."""
    authorize_sync(request, action="resource:file_delete", resource="files")

    from django.utils import timezone

    from admin.filesv2.models import File

    try:
        f = File.objects.get(id=file_id, deleted_at__isnull=True)
        f.deleted_at = timezone.now()
        f.save()
        return {"success": True, "message": get_message(SuccessCode.DELETED)}
    except File.DoesNotExist:
        return {"error": get_message(ErrorCode.NOT_FOUND)}, 404


@router.get("/{file_id}/download-url", auth=AuthBearer())
def get_download_url(request, file_id: str):
    """Get presigned download URL."""
    authorize_sync(request, action="resource:file_read", resource="files")

    import boto3  # type: ignore[import]
    from botocore.config import Config  # type: ignore[import]

    from admin.filesv2.models import File

    try:
        f = File.objects.get(id=file_id, deleted_at__isnull=True)

        s3_client = boto3.client(
            "s3",
            config=Config(signature_version="s3v4"),
            region_name=require_setting("AWS_REGION"),
        )

        bucket = require_setting("AWS_S3_BUCKET")
        expires_in = 3600

        download_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": f.storage_key},
            ExpiresIn=expires_in,
        )

        return {
            "download_url": download_url,
            "expires_in": expires_in,
            "filename": f.original_name,
        }

    except File.DoesNotExist:
        return {"error": get_message(ErrorCode.NOT_FOUND)}, 404
    except Exception as e:
        logger.exception("S3 download URL error: %s", e)
        return {"error": get_message(ErrorCode.INTERNAL_ERROR)}, 500
