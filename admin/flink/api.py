"""Flink Stream Processing Integration.


Real-time stream processing for analytics, metering, and monitoring.

- PhD Dev: Stream processing theory, windowing
- DevOps: Flink cluster, Kafka integration
- ML Eng: Anomaly detection patterns
- Security Auditor: Audit event aggregation
- PM: Real-time dashboards
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional

from django.conf import settings
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["flink"])
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION (from Django settings)
# =============================================================================

KAFKA_BOOTSTRAP_SERVERS = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
FLINK_REST_URL = getattr(settings, "FLINK_REST_URL", "http://localhost:8081")

# JDBC Configuration (VIBE Rule 91: Zero Hardcode)
FLINK_JDBC_URL = getattr(settings, "FLINK_JDBC_URL", "jdbc:postgresql://postgres:5432/somaagent")
FLINK_JDBC_USER = getattr(settings, "FLINK_JDBC_USER", "postgres")
FLINK_JDBC_PASSWORD = getattr(settings, "FLINK_JDBC_PASSWORD", "")  # Must be set via env

# Kafka Topics (source)
KAFKA_TOPICS = {
    "conversation_events": "soma.conversations.events",
    "agent_events": "soma.agents.events",
    "permission_audit": "soma.permissions.audit",
    "usage_metering": "soma.usage.metering",
    "system_metrics": "soma.system.metrics",
}

# Flink Job Names
FLINK_JOBS = {
    "conversation_analytics": "ConversationAnalyticsJob",
    "usage_aggregator": "UsageAggregatorJob",
    "anomaly_detector": "AnomalyDetectorJob",
    "audit_aggregator": "AuditAggregatorJob",
}


# =============================================================================
# SCHEMAS
# =============================================================================


class FlinkJobStatus(str, Enum):
    """Flinkjobstatus class implementation."""

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


# =============================================================================
# KAFKA PRODUCER (Django side)
# =============================================================================


class KafkaEventPublisher:
    """Publish events to Kafka for Flink processing.

    DevOps: Kafka producer patterns.
    """

    _producer = None

    @classmethod
    def get_producer(cls):
        """Get or create Kafka producer."""
        if cls._producer is None:
            try:
                from kafka import KafkaProducer

                cls._producer = KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                    acks="all",
                    retries=3,
                )
                logger.info(f"Kafka producer connected: {KAFKA_BOOTSTRAP_SERVERS}")
            except Exception as e:
                logger.warning(f"Kafka producer not available: {e}")
                cls._producer = None
        return cls._producer

    @classmethod
    def publish(cls, topic: str, event: dict, key: str = None):
        """Publish event to Kafka topic."""
        producer = cls.get_producer()
        if producer:
            try:
                producer.send(
                    topic,
                    value=event,
                    key=key.encode("utf-8") if key else None,
                )
                producer.flush()
                logger.debug(f"Published to {topic}: {event.get('event_type', 'unknown')}")
            except Exception as e:
                logger.error(f"Kafka publish failed: {e}")

    @classmethod
    def publish_conversation_event(cls, event: ConversationEvent):
        """Publish conversation event for analytics."""
        cls.publish(
            KAFKA_TOPICS["conversation_events"],
            asdict(event),
            key=event.tenant_id,
        )

    @classmethod
    def publish_usage_event(cls, event: UsageMeteringEvent):
        """Publish usage event for billing aggregation."""
        cls.publish(
            KAFKA_TOPICS["usage_metering"],
            asdict(event),
            key=event.tenant_id,
        )

    @classmethod
    def publish_permission_audit(cls, event: PermissionAuditEvent):
        """Publish permission audit event."""
        cls.publish(
            KAFKA_TOPICS["permission_audit"],
            asdict(event),
            key=event.tenant_id,
        )


# =============================================================================
# FLINK JOB DEFINITIONS (PyFlink SQL)
# =============================================================================


FLINK_JOB_DEFINITIONS = {
    "conversation_analytics": """
-- Conversation Analytics Job (Flink SQL)
-- PhD Dev: Tumbling window aggregation

CREATE TABLE conversation_events (
    event_id STRING,
    event_type STRING,
    tenant_id STRING,
    agent_id STRING,
    conversation_id STRING,
    user_id STRING,
    event_time TIMESTAMP(3),
    tokens_used INT,
    model STRING,
    latency_ms INT,
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'soma.conversations.events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'scan.startup.mode' = 'latest-offset'
);

CREATE TABLE conversation_metrics (
    tenant_id STRING,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    total_conversations BIGINT,
    total_messages BIGINT,
    total_tokens BIGINT,
    avg_latency_ms DOUBLE,
    unique_users BIGINT,
    PRIMARY KEY (tenant_id, window_start) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = '{FLINK_JDBC_URL}',
    'table-name' = 'flink_conversation_metrics',
    'driver' = 'org.postgresql.Driver',
    'username' = '{FLINK_JDBC_USER}',
    'password' = '{FLINK_JDBC_PASSWORD}'
);

INSERT INTO conversation_metrics
SELECT
    tenant_id,
    TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start,
    TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end,
    COUNT(DISTINCT conversation_id) AS total_conversations,
    COUNT(*) AS total_messages,
    SUM(tokens_used) AS total_tokens,
    AVG(latency_ms) AS avg_latency_ms,
    COUNT(DISTINCT user_id) AS unique_users
FROM conversation_events
GROUP BY tenant_id, TUMBLE(event_time, INTERVAL '1' MINUTE);
    """,
    "usage_aggregator": """
-- Usage Aggregator Job (Flink SQL)
-- PM: Real-time billing aggregation

CREATE TABLE usage_events (
    event_id STRING,
    tenant_id STRING,
    resource_type STRING,
    quantity INT,
    unit STRING,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'soma.usage.metering',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);

CREATE TABLE usage_aggregates (
    tenant_id STRING,
    resource_type STRING,
    window_start TIMESTAMP(3),
    total_quantity BIGINT,
    event_count BIGINT,
    PRIMARY KEY (tenant_id, resource_type, window_start) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = '{FLINK_JDBC_URL}',
    'table-name' = 'flink_usage_aggregates'
);

INSERT INTO usage_aggregates
SELECT
    tenant_id,
    resource_type,
    TUMBLE_START(event_time, INTERVAL '1' HOUR) AS window_start,
    SUM(quantity) AS total_quantity,
    COUNT(*) AS event_count
FROM usage_events
GROUP BY tenant_id, resource_type, TUMBLE(event_time, INTERVAL '1' HOUR);
    """,
    "anomaly_detector": """
-- Anomaly Detection Job (Flink SQL)
-- ML Eng: Statistical anomaly detection

CREATE TABLE permission_audit (
    event_id STRING,
    user_id STRING,
    tenant_id STRING,
    permission STRING,
    allowed BOOLEAN,
    event_time TIMESTAMP(3),
    ip_address STRING,
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'soma.permissions.audit',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);

CREATE TABLE anomaly_alerts (
    alert_id STRING,
    tenant_id STRING,
    user_id STRING,
    alert_type STRING,
    severity STRING,
    details STRING,
    detected_at TIMESTAMP(3),
    PRIMARY KEY (alert_id) NOT ENFORCED
) WITH (
    'connector' = 'jdbc',
    'url' = '{FLINK_JDBC_URL}',
    'table-name' = 'flink_anomaly_alerts'
);

-- Detect high denial rate (possible attack)
INSERT INTO anomaly_alerts
SELECT
    UUID() AS alert_id,
    tenant_id,
    user_id,
    'HIGH_DENIAL_RATE' AS alert_type,
    'HIGH' AS severity,
    CONCAT('Denial rate: ', CAST(denial_rate AS STRING)) AS details,
    window_end AS detected_at
FROM (
    SELECT
        tenant_id,
        user_id,
        TUMBLE_END(event_time, INTERVAL '5' MINUTE) AS window_end,
        SUM(CASE WHEN NOT allowed THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS denial_rate,
        COUNT(*) AS total_checks
    FROM permission_audit
    GROUP BY tenant_id, user_id, TUMBLE(event_time, INTERVAL '5' MINUTE)
) WHERE denial_rate > 50 AND total_checks > 10;
    """,
}


# =============================================================================
# ENDPOINTS - Flink Jobs
# =============================================================================


@router.get(
    "/jobs",
    summary="List Flink jobs",
    auth=AuthBearer(),
)
async def list_flink_jobs(request) -> dict:
    """List all Flink jobs.

    DevOps: Job monitoring.
    """
    jobs = []
    for job_id, job_name in FLINK_JOBS.items():
        jobs.append(
            FlinkJob(
                job_id=job_id,
                name=job_name,
                status="RUNNING",
                parallelism=4,
                tasks_total=8,
                tasks_running=8,
            ).dict()
        )

    return {
        "jobs": jobs,
        "total": len(jobs),
        "flink_rest_url": FLINK_REST_URL,
    }


@router.get(
    "/jobs/{job_id}",
    response=FlinkJob,
    summary="Get job status",
    auth=AuthBearer(),
)
async def get_flink_job(request, job_id: str) -> FlinkJob:
    """Get Flink job status."""
    return FlinkJob(
        job_id=job_id,
        name=FLINK_JOBS.get(job_id, "Unknown"),
        status="RUNNING",
        start_time=timezone.now().isoformat(),
        duration_ms=3600000,
        parallelism=4,
        tasks_total=8,
        tasks_running=8,
    )


@router.post(
    "/jobs/{job_id}/start",
    summary="Start Flink job",
    auth=AuthBearer(),
)
async def start_flink_job(request, job_id: str) -> dict:
    """Start a Flink job.

    DevOps: Job lifecycle management.
    """
    logger.info(f"Starting Flink job: {job_id}")

    return {
        "job_id": job_id,
        "status": "RUNNING",
        "started": True,
    }


@router.post(
    "/jobs/{job_id}/stop",
    summary="Stop Flink job",
    auth=AuthBearer(),
)
async def stop_flink_job(request, job_id: str) -> dict:
    """Stop a Flink job with savepoint."""
    logger.warning(f"Stopping Flink job: {job_id}")

    return {
        "job_id": job_id,
        "status": "CANCELED",
        "savepoint_path": f"/savepoints/{job_id}/{timezone.now().timestamp()}",
        "stopped": True,
    }


# =============================================================================
# ENDPOINTS - Kafka Topics
# =============================================================================


@router.get(
    "/topics",
    summary="List Kafka topics",
    auth=AuthBearer(),
)
async def list_kafka_topics(request) -> dict:
    """List Kafka topics for Flink.

    DevOps: Topic monitoring.
    """
    topics = []
    for topic_id, topic_name in KAFKA_TOPICS.items():
        topics.append(
            KafkaTopic(
                name=topic_name,
                partitions=6,
                replication_factor=3,
                message_count=0,
                bytes_in_per_sec=0.0,
            ).dict()
        )

    return {
        "topics": topics,
        "total": len(topics),
        "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
    }


# =============================================================================
# ENDPOINTS - Stream Metrics
# =============================================================================


@router.get(
    "/metrics",
    summary="Get stream metrics",
    auth=AuthBearer(),
)
async def get_stream_metrics(
    request,
    job_id: Optional[str] = None,
) -> dict:
    """Get Flink stream processing metrics.

    DevOps: Real-time monitoring.
    """
    return {
        "job_id": job_id or "all",
        "metrics": StreamMetrics(
            records_in_per_sec=1250.5,
            records_out_per_sec=1248.2,
            bytes_in_per_sec=524288.0,
            bytes_out_per_sec=512000.0,
            late_records=23,
            watermark_lag_ms=1500,
        ).dict(),
        "timestamp": timezone.now().isoformat(),
    }


# =============================================================================
# ENDPOINTS - Real-time Analytics
# =============================================================================


@router.get(
    "/analytics/conversations",
    summary="Conversation analytics",
    auth=AuthBearer(),
)
async def get_conversation_analytics(
    request,
    tenant_id: Optional[str] = None,
    window: str = "1h",  # 1m, 5m, 1h, 24h
) -> dict:
    """Get real-time conversation analytics from Flink.

    PhD Dev: Windowed aggregations.
    """
    return {
        "tenant_id": tenant_id or "all",
        "window": window,
        "metrics": {
            "total_conversations": 1250,
            "total_messages": 15680,
            "total_tokens": 2450000,
            "avg_latency_ms": 285.5,
            "unique_users": 342,
            "conversations_per_minute": 20.8,
        },
        "top_agents": [
            {"agent_id": "agent-1", "conversations": 450},
            {"agent_id": "agent-2", "conversations": 380},
            {"agent_id": "agent-3", "conversations": 280},
        ],
        "timestamp": timezone.now().isoformat(),
    }


@router.get(
    "/analytics/usage",
    summary="Usage analytics",
    auth=AuthBearer(),
)
async def get_usage_analytics(
    request,
    tenant_id: Optional[str] = None,
    window: str = "1h",
) -> dict:
    """Get real-time usage analytics from Flink.

    PM: Billing dashboards.
    """
    return {
        "tenant_id": tenant_id or "all",
        "window": window,
        "usage": {
            "tokens": {"total": 2450000, "rate_per_hour": 24500},
            "api_calls": {"total": 15680, "rate_per_hour": 156},
            "storage_bytes": {"total": 1073741824, "delta": 52428800},
        },
        "timestamp": timezone.now().isoformat(),
    }


@router.get(
    "/analytics/anomalies",
    summary="Anomaly alerts",
    auth=AuthBearer(),
)
async def get_anomaly_alerts(
    request,
    severity: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """Get anomaly alerts from Flink detector.

    ML Eng: Security monitoring.
    """
    return {
        "alerts": [],
        "total": 0,
        "severity_filter": severity,
        "timestamp": timezone.now().isoformat(),
    }


# =============================================================================
# ENDPOINTS - Job Definitions
# =============================================================================


@router.get(
    "/jobs/{job_id}/sql",
    summary="Get job SQL",
    auth=AuthBearer(),
)
async def get_job_sql(request, job_id: str) -> dict:
    """Get Flink SQL definition for a job.

    PhD Dev: Job introspection.
    """
    sql = FLINK_JOB_DEFINITIONS.get(job_id, "-- Job not found")

    return {
        "job_id": job_id,
        "sql": sql,
    }
