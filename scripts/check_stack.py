#!/usr/bin/env python3
"""Smoke checks for the local messaging stack.

This script verifies that the docker-compose deployment required by the messaging
roadmap is healthy. It talks to the *real* services—no mocks, no stubs.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Iterable

import httpx
import psycopg
import redis.asyncio as redis
from aiokafka.admin import AIOKafkaAdminClient
from aiokafka.errors import KafkaConnectionError

LOGGER = logging.getLogger("check_stack")


@dataclass(slots=True)
class StackConfig:
    gateway_url: str
    kafka_bootstrap: str
    required_topics: tuple[str, ...]
    consumer_group: str
    redis_url: str
    postgres_dsn: str
    timeout_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> "StackConfig":
        host_gateway_port = int(os.getenv("GATEWAY_PORT", "20016"))
        gateway_url = os.getenv("CHECK_GATEWAY_URL", f"http://localhost:{host_gateway_port}")
        kafka_host = os.getenv("CHECK_KAFKA_BOOTSTRAP", "localhost")
        kafka_port = int(os.getenv("KAFKA_PORT", "20000"))
        kafka_bootstrap = os.getenv("CHECK_KAFKA_BOOTSTRAP_SERVERS", f"{kafka_host}:{kafka_port}")
        topics = tuple(
            filter(
                None,
                (
                    os.getenv("CONVERSATION_INBOUND", "conversation.inbound"),
                    os.getenv("CONVERSATION_OUTBOUND", "conversation.outbound"),
                    os.getenv("TOOL_REQUESTS_TOPIC", "tool.requests"),
                    os.getenv("TOOL_RESULTS_TOPIC", "tool.results"),
                ),
            )
        )
        redis_url = os.getenv("REDIS_URL", "redis://localhost:20001/0")
        postgres_dsn = os.getenv(
            "POSTGRES_DSN",
            "postgresql://soma:soma@localhost:20002/somaagent01",
        )
        consumer_group = os.getenv("CONVERSATION_GROUP", "conversation-worker")
        timeout = float(os.getenv("CHECK_TIMEOUT_SECONDS", "5"))
        return cls(
            gateway_url=gateway_url.rstrip("/"),
            kafka_bootstrap=kafka_bootstrap,
            required_topics=topics,
            consumer_group=consumer_group,
            redis_url=redis_url,
            postgres_dsn=postgres_dsn,
            timeout_seconds=timeout,
        )


async def check_gateway(config: StackConfig) -> None:
    url = f"{config.gateway_url}/health"
    LOGGER.info("Checking gateway health", extra={"url": url})
    try:
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Gateway health probe failed: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(f"Gateway unhealthy: HTTP {response.status_code}")
    LOGGER.info("Gateway responded with 200 OK")


async def check_kafka(config: StackConfig) -> None:
    LOGGER.info(
        "Checking Kafka connectivity",
        extra={"bootstrap_servers": config.kafka_bootstrap, "topics": config.required_topics},
    )
    admin = AIOKafkaAdminClient(
        bootstrap_servers=config.kafka_bootstrap,
        request_timeout_ms=int(config.timeout_seconds * 1000),
    )
    try:
        await admin.start()
        metadata = await admin.list_topics(timeout_ms=int(config.timeout_seconds * 1000))
        missing = sorted(set(config.required_topics) - set(metadata))
        if missing:
            raise RuntimeError(f"Kafka topics missing: {', '.join(missing)}")

        groups = await admin.list_consumer_groups()
        group_state = {group_id: state for group_id, state in groups}
        state = group_state.get(config.consumer_group)
        if state is None:
            raise RuntimeError(
                "conversation worker consumer group not registered yet; "
                "ensure the worker is running and committing offsets"
            )
        LOGGER.info(
            "Kafka topics present and consumer group detected",
            extra={"group": config.consumer_group, "state": state},
        )
    except KafkaConnectionError as exc:
        raise RuntimeError(f"Unable to reach Kafka at {config.kafka_bootstrap}: {exc}") from exc
    finally:
        await admin.close()


async def check_redis(config: StackConfig) -> None:
    LOGGER.info("Checking Redis", extra={"url": config.redis_url})
    client = redis.from_url(config.redis_url)
    try:
        pong = await client.ping()
    except redis.ConnectionError as exc:  # type: ignore[attr-defined]
        raise RuntimeError(f"Redis connection failed: {exc}") from exc
    finally:
        await client.close()
    if not pong:
        raise RuntimeError("Redis PING returned falsy result")
    LOGGER.info("Redis responded to PING")


async def check_postgres(config: StackConfig) -> None:
    LOGGER.info("Checking Postgres", extra={"dsn": redact_password(config.postgres_dsn)})

    def _sync_check() -> None:
        with psycopg.connect(config.postgres_dsn, connect_timeout=config.timeout_seconds) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'sessions'
                      AND table_name = 'events'
                    """
                )
                if cur.fetchone() is None:
                    raise RuntimeError(
                        "sessions.events table missing; run migrations from infra/postgres/init"
                    )

    await asyncio.to_thread(_sync_check)
    LOGGER.info("Postgres schema check succeeded")


def redact_password(dsn: str) -> str:
    # Basic DSN redaction for logging
    if "@" not in dsn:
        return dsn
    prefix, suffix = dsn.split("@", 1)
    if ":" in prefix:
        user = prefix.split(":", 1)[0]
        return f"{user}:***@{suffix}"
    return f"***@{suffix}"


async def run_checks(config: StackConfig, selected: Iterable[str]) -> None:
    checks = {
        "gateway": check_gateway,
        "kafka": check_kafka,
        "redis": check_redis,
        "postgres": check_postgres,
    }
    unknown = sorted(set(selected) - checks.keys())
    if unknown:
        raise ValueError(f"Unknown checks requested: {', '.join(unknown)}")

    for name in selected:
        await checks[name](config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the local messaging stack.")
    parser.add_argument(
        "--checks",
        metavar="CHECK",
        nargs="*",
        default=["gateway", "kafka", "redis", "postgres"],
        help="Subset of checks to run (default: gateway kafka redis postgres)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging output.",
    )
    return parser.parse_args()


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s	%(message)s")
    handler.setFormatter(formatter)
    LOGGER.setLevel(level)
    LOGGER.addHandler(handler)
    logging.getLogger("aiokafka").setLevel(logging.WARNING)


async def async_main() -> int:
    args = parse_args()
    _configure_logging(args.verbose)
    config = StackConfig.from_env()

    LOGGER.info("Starting stack validation", extra={"checks": args.checks})
    try:
        await run_checks(config, args.checks)
    except Exception as exc:  # pragma: no cover - surfaced to CLI
        LOGGER.error("Stack validation failed", extra={"error": str(exc)})
        if args.verbose:
            LOGGER.exception("Detailed failure trace")
        return 1

    LOGGER.info("All checks succeeded")
    return 0


def main() -> None:
    exit_code = asyncio.run(async_main())
    raise SystemExit(exit_code)


if __name__ == "__main__":  # pragma: no cover
    main()
