"""Asset Store for multimodal asset storage and retrieval.

PostgreSQL-backed storage for generated multimodal assets (images, diagrams,
videos, screenshots) with SHA-256 checksum deduplication and optional S3
integration for large assets.

SRS Reference: Section 16.4 (Asset Pipeline)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg

from src.core.config import cfg

__all__ = [
    "AssetRecord",
    "AssetType",
    "AssetFormat",
    "AssetStore",
]

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    """Type classification for multimodal assets."""
    IMAGE = "image"
    VIDEO = "video"
    DIAGRAM = "diagram"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"


class AssetFormat(str, Enum):
    """Supported file formats."""
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    SVG = "svg"
    MP4 = "mp4"
    MD = "md"
    PDF = "pdf"



@dataclass(slots=True)
class AssetRecord:
    """Multimodal asset record.
    
    Represents a stored asset with its content, metadata, and integrity
    information. Assets can be stored inline (bytea) or externally (S3).
    
    Attributes:
        id: Unique asset identifier (UUID)
        tenant_id: Owning tenant
        session_id: Optional session this asset belongs to
        asset_type: Classification (image, video, diagram, etc.)
        format: File format (png, svg, mp4, etc.)
        storage_path: S3/MinIO path (if external storage used)
        content: Raw bytes (if inline storage used)
        content_size_bytes: Size of content in bytes
        checksum_sha256: SHA-256 hash for integrity and deduplication
        original_filename: Original name if uploaded
        mime_type: MIME type (e.g., image/png)
        dimensions: Optional dimensions (width, height for images/video)
        metadata: Additional metadata dictionary
        created_at: Creation timestamp
        expires_at: Optional expiration for retention policy
    """
    id: UUID
    tenant_id: str
    asset_type: AssetType
    format: str
    checksum_sha256: str
    mime_type: str
    content_size_bytes: int = 0
    session_id: Optional[str] = None
    storage_path: Optional[str] = None
    content: Optional[bytes] = None
    original_filename: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    @property
    def is_inline(self) -> bool:
        """True if content is stored inline (bytea)."""
        return self.content is not None

    @property
    def is_external(self) -> bool:
        """True if content is stored externally (S3)."""
        return self.storage_path is not None


class AssetStore:
    """PostgreSQL-backed store for multimodal assets.
    
    Provides asset storage with SHA-256 checksum deduplication, tenant
    isolation, and optional S3 integration for large assets.
    
    Usage:
        store = AssetStore()
        
        # Store a new asset
        record = await store.create(
            tenant_id="acme-corp",
            asset_type=AssetType.IMAGE,
            format="png",
            content=image_bytes,
            metadata={"prompt": "..."}
        )
        
        # Retrieve by ID
        asset = await store.get(record.id)
        
        # Check for duplicate
        existing = await store.get_by_checksum(tenant_id, checksum)
    """

    # Maximum size for inline storage (10 MB)
    MAX_INLINE_SIZE_BYTES = 10 * 1024 * 1024

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize store with database connection string.
        
        Args:
            dsn: PostgreSQL connection string. Defaults to config value.
        """
        self._dsn = dsn or cfg.settings().database.dsn

    async def ensure_schema(self) -> None:
        """Verify the multimodal_assets table exists.
        
        Raises RuntimeError if table doesn't exist, as schema should be
        created by migration 017_multimodal_schema.sql.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'multimodal_assets'
                )
            """)
            if not exists:
                raise RuntimeError(
                    "multimodal_assets table does not exist. "
                    "Run migration 017_multimodal_schema.sql."
                )
        finally:
            await conn.close()

    async def create(
        self,
        tenant_id: str,
        asset_type: AssetType,
        format: str,
        content: bytes,
        session_id: Optional[str] = None,
        original_filename: Optional[str] = None,
        dimensions: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
    ) -> AssetRecord:
        """Store a new asset.
        
        Computes SHA-256 checksum for integrity and deduplication.
        Returns existing asset if duplicate found.
        
        Args:
            tenant_id: Owning tenant
            asset_type: Asset classification
            format: File format (e.g., 'png', 'svg')
            content: Raw bytes of asset
            session_id: Optional session association
            original_filename: Original name if applicable
            dimensions: Optional {width, height} for images/video
            metadata: Additional metadata
            expires_at: Optional expiration datetime
            
        Returns:
            AssetRecord with assigned ID
            
        Raises:
            ValueError: If content is empty
            asyncpg.PostgresError: On database errors
        """
        if not content:
            raise ValueError("Content cannot be empty")
        
        # Compute checksum for deduplication
        checksum = hashlib.sha256(content).hexdigest()
        
        # Check for existing duplicate
        existing = await self.get_by_checksum(tenant_id, checksum)
        if existing:
            logger.info(
                "Duplicate asset found: %s (checksum=%s)",
                existing.id, checksum[:16]
            )
            return existing
        
        # Determine MIME type
        mime_type = self._get_mime_type(format, original_filename)
        
        # Generate ID
        asset_id = uuid4()
        content_size = len(content)
        
        # For v1, always use inline storage
        # S3 integration would be added in v2
        storage_path = None
        
        conn = await asyncpg.connect(self._dsn)
        try:
            import json
            
            await conn.execute("""
                INSERT INTO multimodal_assets (
                    id, tenant_id, session_id, asset_type, format,
                    storage_path, content, content_size_bytes,
                    checksum_sha256, original_filename, mime_type,
                    dimensions, metadata, expires_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                )
            """,
                asset_id,
                tenant_id,
                session_id,
                asset_type.value,
                format,
                storage_path,
                content,
                content_size,
                checksum,
                original_filename,
                mime_type,
                json.dumps(dimensions) if dimensions else None,
                json.dumps(metadata or {}),
                expires_at,
            )
            
            logger.info(
                "Created asset: %s (type=%s, size=%d, checksum=%s)",
                asset_id, asset_type.value, content_size, checksum[:16]
            )
            
            return AssetRecord(
                id=asset_id,
                tenant_id=tenant_id,
                session_id=session_id,
                asset_type=asset_type,
                format=format,
                storage_path=storage_path,
                content=content,
                content_size_bytes=content_size,
                checksum_sha256=checksum,
                original_filename=original_filename,
                mime_type=mime_type,
                dimensions=dimensions,
                metadata=metadata or {},
                created_at=datetime.now(),
                expires_at=expires_at,
            )
        finally:
            await conn.close()

    async def get(
        self, 
        asset_id: UUID,
        include_content: bool = True,
    ) -> Optional[AssetRecord]:
        """Retrieve an asset by ID.
        
        Args:
            asset_id: UUID of the asset
            include_content: Whether to fetch content bytes (default True)
            
        Returns:
            AssetRecord if found, None otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            if include_content:
                row = await conn.fetchrow(
                    "SELECT * FROM multimodal_assets WHERE id = $1",
                    asset_id,
                )
            else:
                row = await conn.fetchrow("""
                    SELECT id, tenant_id, session_id, asset_type, format,
                           storage_path, content_size_bytes, checksum_sha256,
                           original_filename, mime_type, dimensions, metadata,
                           created_at, expires_at
                    FROM multimodal_assets WHERE id = $1
                """,
                    asset_id,
                )
            
            if not row:
                return None
            
            return self._row_to_record(row, include_content=include_content)
        finally:
            await conn.close()

    async def get_by_checksum(
        self,
        tenant_id: str,
        checksum: str,
    ) -> Optional[AssetRecord]:
        """Find an asset by checksum (for deduplication).
        
        Args:
            tenant_id: Tenant to search in
            checksum: SHA-256 checksum
            
        Returns:
            AssetRecord if found, None otherwise
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            row = await conn.fetchrow("""
                SELECT * FROM multimodal_assets 
                WHERE tenant_id = $1 AND checksum_sha256 = $2
                LIMIT 1
            """,
                tenant_id, checksum,
            )
            
            if not row:
                return None
            
            return self._row_to_record(row)
        finally:
            await conn.close()

    async def list(
        self,
        tenant_id: str,
        session_id: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AssetRecord]:
        """List assets with optional filters.
        
        Args:
            tenant_id: Tenant to list from
            session_id: Optional session filter
            asset_type: Optional type filter
            limit: Maximum results (default 100)
            offset: Pagination offset
            
        Returns:
            List of AssetRecord (without content bytes)
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            query_parts = ["""
                SELECT id, tenant_id, session_id, asset_type, format,
                       storage_path, content_size_bytes, checksum_sha256,
                       original_filename, mime_type, dimensions, metadata,
                       created_at, expires_at
                FROM multimodal_assets
                WHERE tenant_id = $1
            """]
            params = [tenant_id]
            param_idx = 2
            
            if session_id:
                query_parts.append(f"AND session_id = ${param_idx}")
                params.append(session_id)
                param_idx += 1
            
            if asset_type:
                query_parts.append(f"AND asset_type = ${param_idx}")
                params.append(asset_type.value)
                param_idx += 1
            
            query_parts.append(f"ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}")
            params.extend([limit, offset])
            
            query = " ".join(query_parts)
            rows = await conn.fetch(query, *params)
            
            return [self._row_to_record(r, include_content=False) for r in rows]
        finally:
            await conn.close()

    async def delete(self, asset_id: UUID) -> bool:
        """Delete an asset by ID.
        
        Args:
            asset_id: UUID of the asset
            
        Returns:
            True if deleted, False if not found
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            result = await conn.execute(
                "DELETE FROM multimodal_assets WHERE id = $1",
                asset_id,
            )
            _, count_str = result.split(" ")
            deleted = int(count_str) > 0
            
            if deleted:
                logger.info("Deleted asset: %s", asset_id)
            
            return deleted
        finally:
            await conn.close()

    async def update_metadata(
        self,
        asset_id: UUID,
        metadata: Dict[str, Any],
        merge: bool = True,
    ) -> bool:
        """Update asset metadata.
        
        Args:
            asset_id: UUID of the asset
            metadata: New metadata to set or merge
            merge: If True, merge with existing; if False, replace
            
        Returns:
            True if updated, False if not found
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            import json
            
            if merge:
                # Merge with existing metadata
                result = await conn.execute("""
                    UPDATE multimodal_assets
                    SET metadata = metadata || $2::jsonb
                    WHERE id = $1
                """,
                    asset_id, json.dumps(metadata),
                )
            else:
                # Replace metadata
                result = await conn.execute("""
                    UPDATE multimodal_assets
                    SET metadata = $2::jsonb
                    WHERE id = $1
                """,
                    asset_id, json.dumps(metadata),
                )
            
            _, count_str = result.split(" ")
            return int(count_str) > 0
        finally:
            await conn.close()

    def compute_checksum(self, content: bytes) -> str:
        """Compute SHA-256 checksum of content.
        
        Exposed for external use (e.g., pre-check deduplication).
        
        Args:
            content: Raw bytes
            
        Returns:
            Lowercase hex digest
        """
        return hashlib.sha256(content).hexdigest()

    def _get_mime_type(
        self, 
        format: str, 
        filename: Optional[str]
    ) -> str:
        """Determine MIME type from format or filename.
        
        Args:
            format: File format (e.g., 'png')
            filename: Optional filename for guessing
            
        Returns:
            MIME type string
        """
        # Known format mappings
        format_to_mime = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "gif": "image/gif",
            "webp": "image/webp",
            "svg": "image/svg+xml",
            "pdf": "application/pdf",
            "mp4": "video/mp4",
            "webm": "video/webm",
            "md": "text/markdown",
            "html": "text/html",
            "json": "application/json",
        }
        
        mime = format_to_mime.get(format.lower())
        if mime:
            return mime
        
        if filename:
            guessed, _ = mimetypes.guess_type(filename)
            if guessed:
                return guessed
        
        return "application/octet-stream"

    def _row_to_record(
        self, 
        row: asyncpg.Record,
        include_content: bool = True,
    ) -> AssetRecord:
        """Convert database row to AssetRecord.
        
        Args:
            row: asyncpg Record from query
            include_content: Whether content field is included
            
        Returns:
            AssetRecord instance
        """
        import json
        
        dimensions = None
        if row.get("dimensions"):
            dimensions = json.loads(row["dimensions"])
        
        metadata = {}
        if row.get("metadata"):
            metadata = json.loads(row["metadata"])
        
        content = None
        if include_content and "content" in row.keys():
            content = row["content"]
        
        return AssetRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            session_id=row.get("session_id"),
            asset_type=AssetType(row["asset_type"]),
            format=row["format"],
            storage_path=row.get("storage_path"),
            content=content,
            content_size_bytes=row.get("content_size_bytes", 0),
            checksum_sha256=row["checksum_sha256"],
            original_filename=row.get("original_filename"),
            mime_type=row["mime_type"],
            dimensions=dimensions,
            metadata=metadata,
            created_at=row.get("created_at"),
            expires_at=row.get("expires_at"),
        )
