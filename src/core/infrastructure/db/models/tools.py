"""Tool catalog SQLAlchemy models.

Matches the schema defined in: infra/sql/tool_catalog.sql

Tables:
- tool_catalog: Centralized tool catalog with parameters schema
- tenant_tool_flags: Per-tenant tool overrides (fail-closed)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.infrastructure.db.models.base import Base


class ToolCatalog(Base):
    """Centralized tool catalog.

    Stores tool definitions with JSON Schema for parameters,
    cost impact classification, and profile assignments.

    Matches: CREATE TABLE IF NOT EXISTS tool_catalog (...)
    """

    __tablename__ = "tool_catalog"

    # Primary key
    name: Mapped[str] = mapped_column(Text, primary_key=True)

    # Tool definition
    description: Mapped[str] = mapped_column(Text, nullable=False)
    parameters_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    # Status and classification
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
    cost_impact: Mapped[str] = mapped_column(
        Text,
        CheckConstraint(
            "cost_impact IN ('low', 'medium', 'high')",
            name="tool_catalog_cost_impact_check",
        ),
        nullable=True,
        default="low",
    )

    # Profile assignments
    profiles: Mapped[List[str]] = mapped_column(
        ARRAY(Text), nullable=True, default=lambda: ["standard"]
    )

    # Audit fields
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    tenant_flags: Mapped[list["TenantToolFlag"]] = relationship(
        "TenantToolFlag", back_populates="tool", cascade="all, delete-orphan"
    )


class TenantToolFlag(Base):
    """Per-tenant tool overrides.

    Allows tenants to enable/disable specific tools.
    Uses fail-closed semantics (disabled by default if flag exists).

    Matches: CREATE TABLE IF NOT EXISTS tenant_tool_flags (...)
    """

    __tablename__ = "tenant_tool_flags"

    # Composite primary key
    tenant_id: Mapped[str] = mapped_column(Text, primary_key=True)
    tool_name: Mapped[str] = mapped_column(
        Text,
        ForeignKey("tool_catalog.name", ondelete="CASCADE"),
        primary_key=True,
    )

    # Override flag
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Audit fields
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    tool: Mapped["ToolCatalog"] = relationship(
        "ToolCatalog", back_populates="tenant_flags"
    )
