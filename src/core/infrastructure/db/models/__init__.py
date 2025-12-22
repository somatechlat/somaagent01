"""SQLAlchemy model definitions for SomaAgent01.

This package exports all database models and the Base class for Alembic migrations.
"""

from src.core.infrastructure.db.models.base import Base
from src.core.infrastructure.db.models.embeddings import SessionEmbedding
from src.core.infrastructure.db.models.enums import (
    AssetType,
    CapabilityHealth,
    CostTier,
    ExecutionStatus,
    JobStatus,
)
from src.core.infrastructure.db.models.multimodal import (
    AssetProvenance,
    MultimodalAsset,
    MultimodalCapability,
    MultimodalExecution,
    MultimodalJobPlan,
    MultimodalOutcome,
)
from src.core.infrastructure.db.models.prompts import Prompt
from src.core.infrastructure.db.models.task_registry import TaskArtifact, TaskRegistry
from src.core.infrastructure.db.models.tools import TenantToolFlag, ToolCatalog

__all__ = [
    # Base
    "Base",
    # Enums
    "AssetType",
    "JobStatus",
    "ExecutionStatus",
    "CapabilityHealth",
    "CostTier",
    # Task Registry
    "TaskRegistry",
    "TaskArtifact",
    # Multimodal
    "MultimodalAsset",
    "MultimodalCapability",
    "MultimodalJobPlan",
    "MultimodalExecution",
    "AssetProvenance",
    "MultimodalOutcome",
    # Tools
    "ToolCatalog",
    "TenantToolFlag",
    # Prompts
    "Prompt",
    # Embeddings
    "SessionEmbedding",
]
