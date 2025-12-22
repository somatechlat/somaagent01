"""Multimodal capability SQLAlchemy models.

Matches the schema defined in:
- infra/postgres/init/017_multimodal_schema.sql
- infra/postgres/init/019_multimodal_outcomes.sql

Tables:
- multimodal_assets: Generated assets (images, videos, diagrams, screenshots)
- multimodal_capabilities: Registry of tools/models with modality metadata
- multimodal_job_plans: Task DSL plans for multimodal workflows
- multimodal_executions: Execution history per plan step
- asset_provenance: Audit trail linking assets to generation context
- multimodal_outcomes: Execution outcomes for learning and ranking
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.types import REAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.infrastructure.db.models.base import Base
from src.core.infrastructure.db.models.enums import (
    AssetType,
    AssetTypeEnum,
    CapabilityHealth,
    CapabilityHealthEnum,
    CostTier,
    CostTierEnum,
    ExecutionStatus,
    ExecutionStatusEnum,
    JobStatus,
    JobStatusEnum,
)


class MultimodalAsset(Base):
    """Stores generated multimodal assets.

    Assets include images, videos, diagrams, and screenshots with
    content stored either inline (BYTEA) or via external storage path.

    Matches: CREATE TABLE IF NOT EXISTS multimodal_assets (...)
    """

    __tablename__ = "multimodal_assets"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Asset classification
    asset_type: Mapped[AssetType] = mapped_column(AssetTypeEnum, nullable=False)
    format: Mapped[str] = mapped_column(Text, nullable=False)

    # Storage (PostgreSQL bytea for v1, S3 path for v2)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    content_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Integrity
    checksum_sha256: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    original_filename: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    dimensions: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    provenance: Mapped[Optional["AssetProvenance"]] = relationship(
        "AssetProvenance", back_populates="asset", uselist=False
    )
    executions: Mapped[list["MultimodalExecution"]] = relationship(
        "MultimodalExecution", back_populates="asset"
    )

    __table_args__ = (
        CheckConstraint(
            "storage_path IS NOT NULL OR content IS NOT NULL",
            name="chk_storage_location",
        ),
        Index("idx_mm_assets_tenant", "tenant_id"),
        Index("idx_mm_assets_type", "asset_type"),
        Index(
            "idx_mm_assets_session",
            "session_id",
            postgresql_where=text("session_id IS NOT NULL"),
        ),
        Index("idx_mm_assets_checksum", "checksum_sha256"),
        Index("idx_mm_assets_created", "created_at"),
        Index(
            "idx_mm_assets_expires",
            "expires_at",
            postgresql_where=text("expires_at IS NOT NULL"),
        ),
    )


class MultimodalCapability(Base):
    """Registry of tools/models with modality metadata.

    Enables capability discovery for multimodal operations.

    Matches: CREATE TABLE IF NOT EXISTS multimodal_capabilities (...)
    """

    __tablename__ = "multimodal_capabilities"

    # Identity (composite primary key)
    tool_id: Mapped[str] = mapped_column(Text, primary_key=True)
    provider: Mapped[str] = mapped_column(Text, primary_key=True)

    # Tenant scoping (NULL = global/system capability)
    tenant_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Modality support
    modalities: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    # Schema definitions (JSON Schema format)
    input_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    output_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Constraints and limits
    constraints: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Cost and performance
    cost_tier: Mapped[CostTier] = mapped_column(
        CostTierEnum, nullable=False, default=CostTier.MEDIUM
    )
    latency_p95_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Health tracking
    health_status: Mapped[CapabilityHealth] = mapped_column(
        CapabilityHealthEnum, nullable=False, default=CapabilityHealth.HEALTHY
    )
    last_health_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Feature flags
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Metadata
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    documentation_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        Index(
            "idx_mm_caps_tenant",
            "tenant_id",
            postgresql_where=text("tenant_id IS NOT NULL"),
        ),
        Index("idx_mm_caps_modalities", "modalities", postgresql_using="gin"),
        Index("idx_mm_caps_health", "health_status"),
        Index(
            "idx_mm_caps_enabled",
            "enabled",
            postgresql_where=text("enabled = TRUE"),
        ),
        Index("idx_mm_caps_cost", "cost_tier"),
    )


class MultimodalJobPlan(Base):
    """Task DSL plans for multimodal workflows.

    Stores the full Task DSL document with status and budget tracking.

    Matches: CREATE TABLE IF NOT EXISTS multimodal_job_plans (...)
    """

    __tablename__ = "multimodal_job_plans"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    request_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Plan content (Task DSL v1.0)
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    plan_version: Mapped[str] = mapped_column(Text, nullable=False, default="1.0")

    # Status tracking
    status: Mapped[JobStatus] = mapped_column(
        JobStatusEnum, nullable=False, default=JobStatus.PENDING
    )
    total_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_steps: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Budget tracking
    budget_limit_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    budget_used_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_details: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    executions: Mapped[list["MultimodalExecution"]] = relationship(
        "MultimodalExecution", back_populates="plan"
    )
    provenance_records: Mapped[list["AssetProvenance"]] = relationship(
        "AssetProvenance", back_populates="plan"
    )

    __table_args__ = (
        Index("idx_mm_plans_tenant", "tenant_id"),
        Index("idx_mm_plans_session", "session_id"),
        Index("idx_mm_plans_status", "status"),
        Index("idx_mm_plans_created", "created_at"),
        Index("idx_mm_plans_tenant_status", "tenant_id", "status", "created_at"),
    )


class MultimodalExecution(Base):
    """Execution history per plan step.

    Tracks execution status, performance metrics, and quality scores
    for observability and learning.

    Matches: CREATE TABLE IF NOT EXISTS multimodal_executions (...)
    """

    __tablename__ = "multimodal_executions"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multimodal_job_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Execution context
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    tool_id: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)

    # Status
    status: Mapped[ExecutionStatus] = mapped_column(
        ExecutionStatusEnum, nullable=False, default=ExecutionStatus.PENDING
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Results
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multimodal_assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Performance metrics
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_estimate_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    quality_feedback: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # Error tracking
    error_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    plan: Mapped["MultimodalJobPlan"] = relationship(
        "MultimodalJobPlan", back_populates="executions"
    )
    asset: Mapped[Optional["MultimodalAsset"]] = relationship(
        "MultimodalAsset", back_populates="executions"
    )
    provenance: Mapped[Optional["AssetProvenance"]] = relationship(
        "AssetProvenance", back_populates="execution"
    )

    __table_args__ = (
        UniqueConstraint(
            "plan_id", "step_index", "attempt_number", name="uq_execution_step_attempt"
        ),
        Index("idx_mm_exec_plan", "plan_id"),
        Index("idx_mm_exec_tenant", "tenant_id"),
        Index("idx_mm_exec_status", "status"),
        Index("idx_mm_exec_tool", "tool_id", "provider"),
        Index("idx_mm_exec_tenant_status", "tenant_id", "status", "created_at"),
        Index(
            "idx_mm_exec_quality",
            "quality_score",
            postgresql_where=text("quality_score IS NOT NULL"),
        ),
    )


class AssetProvenance(Base):
    """Audit trail linking assets to generation context.

    Provides reproducibility and compliance tracking for generated assets.

    Matches: CREATE TABLE IF NOT EXISTS asset_provenance (...)
    """

    __tablename__ = "asset_provenance"

    # Identity (foreign key to asset)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multimodal_assets.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Correlation IDs
    request_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multimodal_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multimodal_job_plans.id", ondelete="SET NULL"),
        nullable=True,
    )

    # User context
    user_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[str] = mapped_column(Text, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Generation context (for reproducibility)
    prompt_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_params: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    # Tool/model used
    tool_id: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tracing
    trace_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    span_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Quality gate results
    quality_gate_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    rework_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    asset: Mapped["MultimodalAsset"] = relationship(
        "MultimodalAsset", back_populates="provenance"
    )
    execution: Mapped[Optional["MultimodalExecution"]] = relationship(
        "MultimodalExecution", back_populates="provenance"
    )
    plan: Mapped[Optional["MultimodalJobPlan"]] = relationship(
        "MultimodalJobPlan", back_populates="provenance_records"
    )

    __table_args__ = (
        Index("idx_prov_tenant", "tenant_id"),
        Index(
            "idx_prov_user",
            "user_id",
            postgresql_where=text("user_id IS NOT NULL"),
        ),
        Index(
            "idx_prov_request",
            "request_id",
            postgresql_where=text("request_id IS NOT NULL"),
        ),
        Index(
            "idx_prov_execution",
            "execution_id",
            postgresql_where=text("execution_id IS NOT NULL"),
        ),
        Index("idx_prov_tool", "tool_id", "provider"),
        Index(
            "idx_prov_trace",
            "trace_id",
            postgresql_where=text("trace_id IS NOT NULL"),
        ),
    )


class MultimodalOutcome(Base):
    """Execution outcomes for SomaBrain learning system.

    Stores outcomes for portfolio ranking and learning.

    Matches: CREATE TABLE IF NOT EXISTS multimodal_outcomes (...)
    """

    __tablename__ = "multimodal_outcomes"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Correlation IDs
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    task_id: Mapped[str] = mapped_column(Text, nullable=False)

    # Execution context
    step_type: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)

    # Outcome metrics
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[float] = mapped_column(REAL, nullable=False)
    cost_cents: Mapped[float] = mapped_column(REAL, nullable=False, default=0.0)

    # Quality assessment
    quality_score: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint("latency_ms >= 0", name="chk_latency_positive"),
        CheckConstraint("cost_cents >= 0", name="chk_cost_positive"),
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0.0 AND quality_score <= 1.0)",
            name="chk_quality_range",
        ),
        Index("idx_mm_outcomes_step_type", "step_type", "timestamp"),
        Index("idx_mm_outcomes_provider", "provider", "success"),
        Index("idx_mm_outcomes_plan", "plan_id"),
        Index("idx_mm_outcomes_timestamp", "timestamp"),
        Index("idx_mm_outcomes_success", "success", "step_type"),
    )
