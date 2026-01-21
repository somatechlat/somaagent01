"""Flink Stream Processing Schemas.

Pydantic models and dataclasses for Flink/Kafka event processing.

- PhD Dev: Stream processing theory
- DevOps: Kafka integration
- ML Eng: Anomaly detection patterns
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# =============================================================================
# FLINK JOB SCHEMAS
# =============================================================================


class FlinkJobStatus(str, Enum):
    """Flink job status enumeration."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    FAILING = "FAILING"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELED = "CANCELED"
    FINISHED = "FINISHED"
    RESTARTING = "RESTARTING"
    SUSPENDED = "SUSPENDED"


class FlinkJob(BaseModel):
    """Flink job status."""

    job_id: str
    name: str
    status: str
    start_time: Optional[str] = None
    duration_ms: Optional[int] = None
    parallelism: int = 1
    tasks_total: int = 0
    tasks_running: int = 0


class KafkaTopic(BaseModel):
    """Kafka topic info."""

    name: str
    partitions: int
    replication_factor: int
    message_count: int = 0
    bytes_in_per_sec: float = 0.0


class StreamMetrics(BaseModel):
    """Stream processing metrics."""

    records_in_per_sec: float
    records_out_per_sec: float
    bytes_in_per_sec: float
    bytes_out_per_sec: float
    late_records: int
    watermark_lag_ms: int


# =============================================================================
# EVENT SCHEMAS (for Kafka)
# =============================================================================


@dataclass
class ConversationEvent:
    """Conversation event for Kafka."""

    event_id: str
    event_type: str  # started, message, ended
    tenant_id: str
    agent_id: str
    conversation_id: str
    user_id: str
    timestamp: str
    tokens_used: int = 0
    model: str = ""
    latency_ms: int = 0


@dataclass
class UsageMeteringEvent:
    """Usage metering event for billing."""

    event_id: str
    tenant_id: str
    resource_type: str  # tokens, api_calls, storage
    quantity: int
    unit: str  # tokens, calls, bytes
    timestamp: str
    metadata: dict = None


@dataclass
class PermissionAuditEvent:
    """Permission audit event."""

    event_id: str
    user_id: str
    tenant_id: str
    permission: str
    resource_id: str
    allowed: bool
    timestamp: str
    ip_address: str = ""
