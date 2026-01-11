"""Configuration helpers for tool executor service."""

import os

from services.common.event_bus import KafkaSettings

SERVICE_SETTINGS = os.environ


def kafka_settings() -> KafkaSettings:
    """Build Kafka connection settings from configuration."""
    return KafkaSettings(
        bootstrap_servers=os.environ.get(
            "KAFKA_BOOTSTRAP_SERVERS",
            os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
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
        SERVICE_SETTINGS.extra.get("tenant_config_path", "conf/tenants.yaml"),
    )


def policy_requeue_prefix() -> str:
    """Get Redis prefix for policy requeue operations."""
    return os.environ.get(
        "POLICY_REQUEUE_PREFIX",
        SERVICE_SETTINGS.extra.get("policy_requeue_prefix", "policy:requeue"),
    )


def get_stream_config() -> dict[str, str]:
    """Get Kafka topic configuration for tool executor."""
    stream_defaults = SERVICE_SETTINGS.extra.get(
        "tool_executor_topics",
        {
            "requests": "tool.requests",
            "results": "tool.results",
            "group": "tool-executor",
        },
    )
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
