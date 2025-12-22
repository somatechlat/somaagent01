"""PostgreSQL ENUM type definitions for SomaAgent01.

These enums match the types defined in the SQL init scripts:
- 017_multimodal_schema.sql

Each enum is defined as both a Python enum and a SQLAlchemy ENUM type
for use in model column definitions.
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum


class AssetType(str, enum.Enum):
    """Type of multimodal asset.

    Matches: CREATE TYPE asset_type AS ENUM (...)
    """

    IMAGE = "image"
    VIDEO = "video"
    DIAGRAM = "diagram"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"


class JobStatus(str, enum.Enum):
    """Status of a multimodal job plan.

    Matches: CREATE TYPE job_status AS ENUM (...)
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatus(str, enum.Enum):
    """Status of a multimodal execution step.

    Matches: CREATE TYPE execution_status AS ENUM (...)
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class CapabilityHealth(str, enum.Enum):
    """Health status of a multimodal capability.

    Matches: CREATE TYPE capability_health AS ENUM (...)
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class CostTier(str, enum.Enum):
    """Cost tier for multimodal capabilities.

    Matches: CREATE TYPE cost_tier AS ENUM (...)
    """

    FREE = "free"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PREMIUM = "premium"


# SQLAlchemy ENUM types for use in column definitions
# These create the actual PostgreSQL ENUM types in the database
AssetTypeEnum = SAEnum(
    AssetType,
    name="asset_type",
    create_constraint=True,
    metadata=None,
    inherit_schema=False,
)

JobStatusEnum = SAEnum(
    JobStatus,
    name="job_status",
    create_constraint=True,
    metadata=None,
    inherit_schema=False,
)

ExecutionStatusEnum = SAEnum(
    ExecutionStatus,
    name="execution_status",
    create_constraint=True,
    metadata=None,
    inherit_schema=False,
)

CapabilityHealthEnum = SAEnum(
    CapabilityHealth,
    name="capability_health",
    create_constraint=True,
    metadata=None,
    inherit_schema=False,
)

CostTierEnum = SAEnum(
    CostTier,
    name="cost_tier",
    create_constraint=True,
    metadata=None,
    inherit_schema=False,
)
