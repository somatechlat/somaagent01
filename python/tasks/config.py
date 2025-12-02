"""
Centralized Celery/Redis configuration for SomaAgent01 tasks.
Centralized Celery/Redis configuration using the canonical config facade.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Any

from redis import Redis

from src.core.config import cfg


@dataclass(frozen=True)
class CelerySettings:
    """Resolved Celery configuration."""

    broker_url: str
    result_backend: str
    default_queue: str
    task_time_limit: int
    task_soft_time_limit: int
    worker_prefetch_multiplier: int

    def queue_definitions(self) -> Dict[str, Dict[str, str]]:
        """Return Celery task_queues definition for all canonical queues."""
        queues = [
            "delegation",
            "browser",
            "code",
            "heavy",
            "fast_a2a",
            "dlq",
        ]
        definitions = {}
        for q in queues:
            definitions[q] = {"exchange": q, "routing_key": q}
        # keep default queue mapping
        definitions[self.default_queue] = {
            "exchange": self.default_queue,
            "routing_key": self.default_queue,
        }
        return definitions


@dataclass(frozen=True)
class RedisSettings:
    """Redis connection settings for task + conversation storage."""

    url: str
    socket_connect_timeout: int = 5
    socket_timeout: int = 5
    health_check_interval: int = 30
    retry_on_timeout: bool = True
    decode_responses: bool = True


@lru_cache(maxsize=1)
def get_celery_settings() -> CelerySettings:
    """Return memoized Celery settings derived from central config."""
    redis_default = cfg.env("REDIS_URL", "redis://localhost:6379/0")
    broker = cfg.env("CELERY_BROKER_URL", redis_default) or redis_default
    backend = cfg.env("CELERY_RESULT_BACKEND", broker) or broker
    queue = cfg.env("CELERY_DEFAULT_QUEUE", "fast_a2a") or "fast_a2a"

    def _int_env(key: str, default: int) -> int:
        value = cfg.env(key)
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    return CelerySettings(
        broker_url=broker,
        result_backend=backend,
        default_queue=queue,
        task_time_limit=_int_env("CELERY_TASK_TIME_LIMIT", 30 * 60),
        task_soft_time_limit=_int_env("CELERY_TASK_SOFT_TIME_LIMIT", 25 * 60),
        worker_prefetch_multiplier=_int_env("CELERY_WORKER_PREFETCH_MULTIPLIER", 1),
    )


@lru_cache(maxsize=1)
def get_redis_settings() -> RedisSettings:
    """
    Return memoized Redis settings.
    Prefers FAST_A2A_TASK_REDIS_URL > CELERY_RESULT_BACKEND > canonical redis_url.
    """
    redis_default = cfg.env("REDIS_URL", "redis://localhost:6379/0")
    backend = get_celery_settings().result_backend
    redis_url = cfg.env("FAST_A2A_TASK_REDIS_URL", backend) or backend or redis_default

    return RedisSettings(url=redis_url)


def create_redis_client() -> Redis:
    """Instantiate a Redis client using shared settings."""
    settings = get_redis_settings()
    return Redis.from_url(
        url=settings.url,
        decode_responses=settings.decode_responses,
        socket_connect_timeout=settings.socket_connect_timeout,
        socket_timeout=settings.socket_timeout,
        retry_on_timeout=settings.retry_on_timeout,
        health_check_interval=settings.health_check_interval,
    )


def celery_conf_overrides() -> Dict[str, Any]:
    """Static Celery configuration dict shared across worker entrypoints."""
    settings = get_celery_settings()
    return {
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
        "task_track_started": True,
        "task_time_limit": settings.task_time_limit,
        "task_soft_time_limit": settings.task_soft_time_limit,
        "worker_prefetch_multiplier": settings.worker_prefetch_multiplier,
        "task_acks_late": True,
        "worker_disable_rate_limits": False,
        "task_compression": "gzip",
        "result_compression": "gzip",
        "result_expires": 3600,
        "task_default_queue": settings.default_queue,
        "task_queues": settings.queue_definitions(),
        "task_routes": {
            "python.tasks.core_tasks.delegate": {"queue": "delegation"},
            "python.tasks.core_tasks.build_context": {"queue": "heavy"},
            "python.tasks.core_tasks.evaluate_policy": {"queue": "delegation"},
            "python.tasks.core_tasks.store_interaction": {"queue": "fast_a2a"},
            "python.tasks.core_tasks.feedback_loop": {"queue": "fast_a2a"},
            "python.tasks.core_tasks.rebuild_index": {"queue": "heavy"},
            "python.tasks.core_tasks.publish_metrics": {"queue": "fast_a2a"},
            "python.tasks.core_tasks.cleanup_sessions": {"queue": "heavy"},
            "a2a_chat": {"queue": "fast_a2a"},
            "python.tasks.core_tasks.dead_letter": {"queue": "dlq"},
        },
        "broker_transport_options": {"visibility_timeout": 7200},
        "task_reject_on_worker_lost": True,
    }
