"""Task registry SQLAlchemy models.

Matches the schema defined in: infra/postgres/init/016_task_registry.sql

Tables:
- task_registry: Runtime-registered tasks/tools with policy and observability metadata
- task_artifacts: Versioned task artifacts with SHA256 checksums
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.infrastructure.db.models.base import Base


class TaskRegistry(Base):
    """Task/Tool registry for runtime-registered tasks.

    Enables runtime-registered tasks/tools with policy, safety,
    and observability metadata.

    Matches: CREATE TABLE IF NOT EXISTS task_registry (...)
    """

    __tablename__ = "task_registry"

    # Primary key
    name: Mapped[str] = mapped_column(Text, primary_key=True)

    # Task classification
    kind: Mapped[str] = mapped_column(
        Text,
        CheckConstraint("kind IN ('task', 'tool')", name="task_registry_kind_check"),
        nullable=False,
    )
    module_path: Mapped[str] = mapped_column(Text, nullable=False)
    callable: Mapped[str] = mapped_column(Text, nullable=False)
    queue: Mapped[str] = mapped_column(Text, nullable=False)

    # Rate limiting and timeouts
    rate_limit: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_retries: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    soft_time_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status and scoping
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tenant_scope: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    persona_scope: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )

    # Schema and metadata
    arg_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    artifact_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soma_tags: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )

    # Audit fields
    created_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Indexes
    __table_args__ = (
        Index("task_registry_enabled_idx", "enabled"),
        Index("task_registry_queue_idx", "queue"),
        Index("task_registry_kind_idx", "kind"),
    )


class TaskArtifact(Base):
    """Versioned task artifacts with integrity verification.

    Stores artifact metadata with SHA256 checksums for verification.

    Matches: CREATE TABLE IF NOT EXISTS task_artifacts (...)
    """

    __tablename__ = "task_artifacts"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Artifact identification
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)

    # Storage and integrity
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    signed_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("name", "version", name="task_artifacts_unique"),
    )
