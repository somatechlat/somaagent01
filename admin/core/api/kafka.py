"""Kafka admin API endpoints.

Migrated from: services/gateway/routers/admin_kafka.py
"""

from __future__ import annotations

import logging
from typing import Any

from ninja import Router, Query
from django.http import HttpRequest
from pydantic import BaseModel, Field

from admin.common.auth import RoleRequired
from admin.common.exceptions import ServiceUnavailableError

router = Router(tags=["admin-kafka"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class PartitionInfo(BaseModel):
    """Kafka partition information."""

    partition: int
    committed: int
    end: int
    lag: int


class KafkaStatusResponse(BaseModel):
    """Kafka consumer status response."""

    topic: str
    group: str
    bootstrap: str
    partitions: list[PartitionInfo]


class KafkaSeekResponse(BaseModel):
    """Response after seeking to end."""

    status: str
    topic: str
    group: str


# =============================================================================
# HELPERS
# =============================================================================


def _kafka_settings():
    """Get Kafka settings from environment."""
    from services.common.event_bus import KafkaSettings

    return KafkaSettings.from_env()


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "/status",
    response=KafkaStatusResponse,
    summary="Get Kafka consumer status",
    auth=RoleRequired("admin", "saas_admin"),
)
async def kafka_status(
    request: HttpRequest,
    topic: str = Query(..., description="Kafka topic name"),
    group: str = Query(..., description="Consumer group ID"),
) -> dict:
    """Get Kafka consumer lag status for a topic/group."""
    try:
        from aiokafka import AIOKafkaConsumer
        from aiokafka.structs import TopicPartition
    except ImportError as exc:
        raise ServiceUnavailableError("aiokafka", f"aiokafka unavailable: {exc}")

    ks = _kafka_settings()
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=ks.bootstrap_servers,
        group_id=group,
        enable_auto_commit=False,
        security_protocol=ks.security_protocol,
        sasl_mechanism=ks.sasl_mechanism,
        sasl_plain_username=ks.sasl_username,
        sasl_plain_password=ks.sasl_password,
    )

    await consumer.start()
    try:
        parts = consumer.partitions_for_topic(topic) or set()
        tps = [TopicPartition(topic, p) for p in sorted(parts)]
        end_offsets = await consumer.end_offsets(tps) if tps else {}
        committed = {tp: (await consumer.committed(tp)) for tp in tps}

        return {
            "topic": topic,
            "group": group,
            "bootstrap": ks.bootstrap_servers,
            "partitions": [
                {
                    "partition": tp.partition,
                    "committed": int(committed.get(tp) or -1),
                    "end": int(end_offsets.get(tp) or -1),
                    "lag": max(0, int((end_offsets.get(tp) or 0) - (committed.get(tp) or 0))),
                }
                for tp in tps
            ],
        }
    finally:
        await consumer.stop()


@router.post(
    "/seek_to_end",
    response=KafkaSeekResponse,
    summary="Seek consumer group to end of topic",
    auth=RoleRequired("admin", "saas_admin"),
)
async def kafka_seek_to_end(
    request: HttpRequest,
    topic: str = Query(..., description="Kafka topic name"),
    group: str = Query(..., description="Consumer group ID"),
) -> dict:
    """Seek a consumer group to the end of all partitions.

    This effectively skips all pending messages.
    """
    try:
        from aiokafka import AIOKafkaConsumer
        from aiokafka.structs import TopicPartition
    except ImportError as exc:
        raise ServiceUnavailableError("aiokafka", f"aiokafka unavailable: {exc}")

    ks = _kafka_settings()
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=ks.bootstrap_servers,
        group_id=group,
        enable_auto_commit=False,
        security_protocol=ks.security_protocol,
        sasl_mechanism=ks.sasl_mechanism,
        sasl_plain_username=ks.sasl_username,
        sasl_plain_password=ks.sasl_password,
    )

    await consumer.start()
    try:
        parts = consumer.partitions_for_topic(topic) or set()
        tps = [TopicPartition(topic, p) for p in sorted(parts)]
        end_offsets = await consumer.end_offsets(tps) if tps else {}

        for tp in tps:
            end = end_offsets.get(tp)
            if end is not None:
                await consumer.commit({tp: end})

        return {"status": "ok", "topic": topic, "group": group}
    finally:
        await consumer.stop()
