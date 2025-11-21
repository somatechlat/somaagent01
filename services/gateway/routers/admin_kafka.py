"""Developer/admin Kafka debug endpoints extracted from the monolith."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.common.event_bus import KafkaSettings

router = APIRouter(prefix="/v1/admin/kafka", tags=["admin"])


def _kafka_settings() -> KafkaSettings:
    return KafkaSettings.from_env()


@router.get("/status")
async def kafka_status(topic: str = Query(...), group: str = Query(...)) -> dict:
    try:
        from aiokafka import AIOKafkaConsumer  # type: ignore
        from aiokafka.structs import TopicPartition  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"aiokafka unavailable: {exc}")

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


@router.post("/seek_to_end")
async def kafka_seek_to_end(topic: str = Query(...), group: str = Query(...)) -> dict:
    try:
        from aiokafka import AIOKafkaConsumer  # type: ignore
        from aiokafka.structs import TopicPartition  # type: ignore
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"aiokafka unavailable: {exc}")

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
