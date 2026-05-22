"""Configuration helpers for tool executor service."""

import os

# Lazy import to avoid circular dependency at module level
from typing import TYPE_CHECKING

from django.conf import settings

from services.common.event_bus import KafkaSettings

if TYPE_CHECKING:
    from admin.core.config.models import Config


def _get_config() -> "Config":
    from admin.core.config.registry import get_config
    return get_config()


SERVICE_SETTINGS = _get_config()


def kafka_settings() -> KafkaSettings:
    """Build Kafka connection settings from configuration."""
    return KafkaSettings(
        bootstrap_servers=os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS",
            getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        ),
        security_protocol=os.environ.get("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.environ.get("KAFKA_SASL_MECHANISM"),
        sasl_username=os.environ.get("KAFKA_SASL_USERNAME"),
        sasl_password=os.environ.get("KAFKA_SASL_PASSWORD"),
    )


def redis_url() -> str:
    """Get Redis URL from configuration."""
    return os.environ.get("REDIS_URL", os.environ.get("SA01_REDIS_URL", ""))


def tenant_config_path() -> str:
    """Get tenant configuration file path."""
    return os.environ.get(
        "TENANT_CONFIG_PATH",
        os.environ.get("TENANT_CONFIG_PATH_EXTRA", "conf/tenants.yaml"),
    )


def policy_requeue_prefix() -> str:
    """Get Redis prefix for policy requeue operations."""
    return os.environ.get(
        "POLICY_REQUEUE_PREFIX",
        os.environ.get("POLICY_REQUEUE_PREFIX_EXTRA", "policy:requeue"),
    )


def get_stream_config() -> dict[str, str]:
    """Get Kafka topic configuration for tool executor."""
    stream_defaults_raw = os.environ.get("TOOL_EXECUTOR_TOPICS")
    if stream_defaults_raw:
        import json

        try:
            stream_defaults = json.loads(stream_defaults_raw)
        except json.JSONDecodeError:
            stream_defaults = {
                "requests": "tool.requests",
                "results": "tool.results",
                "group": "tool-executor",
            }
    else:
        stream_defaults = {
            "requests": "tool.requests",
            "results": "tool.results",
            "group": "tool-executor",
        }
    return {
        "requests": os.environ.get(
            "TOOL_REQUESTS_TOPIC", stream_defaults.get("requests", "tool.requests")
        ),
        "results": os.environ.get(
            "TOOL_RESULTS_TOPIC", stream_defaults.get("results", "tool.results")
        ),
        "group": os.environ.get(
            "TOOL_EXECUTOR_GROUP", stream_defaults.get("group", "tool-executor")
        ),
    }
