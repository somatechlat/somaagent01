"""Session embeddings SQLAlchemy models.

Matches the schema defined in: infra/sql/embedding_table.sql

Tables:
- session_embeddings: Vector embeddings for session content

Note: This model uses pgvector's VECTOR type for similarity search.
The pgvector extension must be enabled in PostgreSQL.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    LargeBinary,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.infrastructure.db.models.base import Base

# Try to import pgvector types, fall back to generic if not available
try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
    VECTOR_TYPE = Vector(384)
except ImportError:
    # Fallback: use LargeBinary as placeholder
    # The actual VECTOR type is created in the migration with raw SQL
    PGVECTOR_AVAILABLE = False
    VECTOR_TYPE = LargeBinary


class SessionEmbedding(Base):
    """Vector embeddings for session content.

    Stores text content with 384-dimensional vector embeddings
    for semantic similarity search.

    Matches: CREATE TABLE IF NOT EXISTS session_embeddings (...)

    Note: The sessions table FK is commented out as it's not defined
    in the current init scripts. The session_id is stored as UUID
    without FK constraint for flexibility.
    """

    __tablename__ = "session_embeddings"

    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Session reference (no FK as sessions table may not exist)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Content
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Vector embedding (384 dimensions for OpenAI small model)
    # Using Column() directly to avoid Mapped type annotation issues with Vector
    # The actual VECTOR type is created in the migration with raw SQL if pgvector unavailable
    vector = Column("vector", VECTOR_TYPE, nullable=True)

    # Metadata
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict
    )

    # Audit fields
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("session_id", "text", name="session_embeddings_session_text_key"),
        # Note: The ivfflat index is created in the migration with raw SQL
        # as SQLAlchemy doesn't natively support ivfflat index type
    )
