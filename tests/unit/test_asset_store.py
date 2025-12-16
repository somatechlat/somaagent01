"""Unit tests for AssetStore (no DB required).

Tests verify checksum computation, MIME type detection, dataclass logic,
and row conversion without requiring database connections.

Pattern Reference: test_capability_registry.py
"""

import pytest
from datetime import datetime
from uuid import uuid4

from services.common.asset_store import (
    AssetStore,
    AssetRecord,
    AssetType,
)


def make_asset(**kwargs) -> AssetRecord:
    """Create a test AssetRecord with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "tenant_id": "test-tenant",
        "asset_type": AssetType.IMAGE,
        "format": "png",
        "checksum_sha256": "abc123def456" * 5 + "ab",  # 64 chars
        "mime_type": "image/png",
        "content_size_bytes": 1024,
        "session_id": None,
        "storage_path": None,
        "content": b"fakeimagecontent",
        "original_filename": "test.png",
        "dimensions": {"width": 512, "height": 512},
        "metadata": {"prompt": "test prompt"},
        "created_at": datetime.now(),
        "expires_at": None,
    }
    defaults.update(kwargs)
    return AssetRecord(**defaults)


class TestAssetRecord:
    """Tests for AssetRecord dataclass."""

    def test_create_with_defaults(self):
        asset_id = uuid4()
        record = AssetRecord(
            id=asset_id,
            tenant_id="test",
            asset_type=AssetType.IMAGE,
            format="png",
            checksum_sha256="a" * 64,
            mime_type="image/png",
        )
        assert record.id == asset_id
        assert record.tenant_id == "test"
        assert record.asset_type == AssetType.IMAGE
        assert record.content_size_bytes == 0
        assert record.content is None

    def test_create_full_record(self):
        record = make_asset(
            content=b"imagedata",
            dimensions={"width": 1024, "height": 768},
        )
        assert record.content == b"imagedata"
        assert record.dimensions["width"] == 1024
        assert record.dimensions["height"] == 768

    def test_is_inline_property(self):
        inline = make_asset(content=b"data", storage_path=None)
        assert inline.is_inline is True
        assert inline.is_external is False

    def test_is_external_property(self):
        external = make_asset(content=None, storage_path="s3://bucket/key")
        assert external.is_inline is False
        assert external.is_external is True


class TestAssetType:
    """Tests for AssetType enum."""

    def test_type_values(self):
        assert AssetType.IMAGE.value == "image"
        assert AssetType.VIDEO.value == "video"
        assert AssetType.DIAGRAM.value == "diagram"
        assert AssetType.SCREENSHOT.value == "screenshot"
        assert AssetType.DOCUMENT.value == "document"

    def test_type_from_string(self):
        assert AssetType("image") == AssetType.IMAGE
        assert AssetType("diagram") == AssetType.DIAGRAM


class TestChecksumComputation:
    """Tests for checksum computation."""

    def test_compute_checksum(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        content = b"hello world"
        checksum = store.compute_checksum(content)
        
        # SHA-256 of "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert checksum == expected

    def test_checksum_length(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        checksum = store.compute_checksum(b"test")
        assert len(checksum) == 64  # SHA-256 hex = 64 chars

    def test_checksum_deterministic(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        content = b"reproducible content"
        c1 = store.compute_checksum(content)
        c2 = store.compute_checksum(content)
        assert c1 == c2


class TestMimeTypeDetection:
    """Tests for MIME type detection."""

    def test_png_format(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        mime = store._get_mime_type("png", None)
        assert mime == "image/png"

    def test_jpg_format(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        mime = store._get_mime_type("jpg", None)
        assert mime == "image/jpeg"

    def test_svg_format(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        mime = store._get_mime_type("svg", None)
        assert mime == "image/svg+xml"

    def test_mp4_format(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        mime = store._get_mime_type("mp4", None)
        assert mime == "video/mp4"

    def test_pdf_format(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        mime = store._get_mime_type("pdf", None)
        assert mime == "application/pdf"

    def test_unknown_format_with_filename(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        mime = store._get_mime_type("xyz", "document.xml")
        assert "xml" in mime.lower() or mime == "application/octet-stream"

    def test_unknown_format_fallback(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        mime = store._get_mime_type("xyz", None)
        assert mime == "application/octet-stream"


class TestRowConversion:
    """Tests for row-to-record conversion logic."""

    def test_row_to_record_complete(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        asset_id = uuid4()
        
        mock_row = {
            "id": asset_id,
            "tenant_id": "acme-corp",
            "session_id": "session-123",
            "asset_type": "image",
            "format": "png",
            "storage_path": None,
            "content": b"imagedata",
            "content_size_bytes": 9,
            "checksum_sha256": "a" * 64,
            "original_filename": "logo.png",
            "mime_type": "image/png",
            "dimensions": '{"width": 512, "height": 512}',
            "metadata": '{"prompt": "generate logo"}',
            "created_at": datetime(2025, 12, 16, 10, 0, 0),
            "expires_at": None,
        }
        
        record = store._row_to_record(mock_row)
        
        assert record.id == asset_id
        assert record.tenant_id == "acme-corp"
        assert record.asset_type == AssetType.IMAGE
        assert record.content == b"imagedata"
        assert record.dimensions["width"] == 512
        assert record.metadata["prompt"] == "generate logo"

    def test_row_to_record_nulls(self):
        store = AssetStore(dsn="postgresql://test@localhost/test")
        asset_id = uuid4()
        
        mock_row = {
            "id": asset_id,
            "tenant_id": "test",
            "session_id": None,
            "asset_type": "diagram",
            "format": "svg",
            "storage_path": None,
            "content_size_bytes": 0,
            "checksum_sha256": "b" * 64,
            "original_filename": None,
            "mime_type": "image/svg+xml",
            "dimensions": None,
            "metadata": None,
            "created_at": None,
            "expires_at": None,
        }
        
        record = store._row_to_record(mock_row, include_content=False)
        
        assert record.id == asset_id
        assert record.asset_type == AssetType.DIAGRAM
        assert record.dimensions is None
        assert record.metadata == {}
        assert record.content is None


class TestMaxInlineSize:
    """Tests for inline storage size limits."""

    def test_max_inline_size(self):
        assert AssetStore.MAX_INLINE_SIZE_BYTES == 10 * 1024 * 1024  # 10 MB


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
