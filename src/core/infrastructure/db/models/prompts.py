"""Prompt management SQLAlchemy models.

Matches the schema defined in: infra/postgres/init/018_prompts.sql

Tables:
- prompts: Dynamic prompt management with versioning
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.infrastructure.db.models.base import Base


class Prompt(Base):
    """Dynamic prompt management.

    Stores versioned prompts for agent behavior customization.

    Matches: CREATE TABLE IF NOT EXISTS prompts (...)
    """

    __tablename__ = "prompts"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    # Prompt identification
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
