"""Configuration helpers for tool executor service."""

from src.core.config import cfg
from services.common.event_bus import KafkaSettings

SERVICE_SETTINGS = cfg.settings()


def kafka_settings() -> KafkaSettings:
    """Build Kafka connection settings from configuration."""
    return KafkaSettings(
        bootstrap_servers=cfg.env(
            "KAFKA_BOOTSTRAP_SERVERS", cfg.settings().kafka.bootstrap_servers
        ),
        security_protocol=cfg.env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=cfg.env("KAFKA_SASL_MECHANISM"),
        sasl_username=cfg.env("KAFKA_SASL_USERNAME"),
        sasl_password=cfg.env("KAFKA_SASL_PASSWORD"),
    )


def redis_url() -> str:
    """Get Redis URL from configuration."""
    return cfg.env("REDIS_URL", cfg.settings().redis.url)


def tenant_config_path() -> str:
    """Get tenant configuration file path."""
    return cfg.env(
        "TENANT_CONFIG_PATH",
        SERVICE_SETTINGS.extra.get("tenant_config_path", "conf/tenants.yaml"),
    )


def policy_requeue_prefix() -> str:
    """Get Redis prefix for policy requeue operations."""
    return cfg.env(
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
        "requests": cfg.env(
            "TOOL_REQUESTS_TOPIC", stream_defaults.get("requests", "tool.requests")
        ),
        "results": cfg.env(
            "TOOL_RESULTS_TOPIC", stream_defaults.get("results", "tool.results")
        ),
        "group": cfg.env("TOOL_EXECUTOR_GROUP", stream_defaults.get("group", "tool-executor")),
    }
