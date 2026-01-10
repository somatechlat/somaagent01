"""Service endpoint registry for SOMA Stack.

Centralized service discovery with environment-aware URL resolution.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ServiceEndpoint:
    """Service endpoint configuration."""

    name: str
    env_var: str
    description: str
    default_port: int
    path: str = ""
    required: bool = True
    health_check: Optional[str] = None

    def get_url(self, environment: str = "development", host: Optional[str] = None) -> str:
        """Resolve service URL from environment or defaults."""
        url = os.environ.get(self.env_var)
        if url:
            return url.rstrip("/") + self.path

        if environment == "production" and self.required:
            raise ValueError(
                f"Missing required service: {self.env_var}\n"
                f"Service: {self.name} - {self.description}"
            )

        if not host:
            host = self.name.lower().replace(" ", "").replace("-", "")
        if environment == "development":
            host = "localhost"

        return f"http://{host}:{self.default_port}{self.path}"


class ServiceRegistry:
    """SOMA Stack service catalog."""

    REDIS = ServiceEndpoint(
        name="redis",
        env_var="SA01_REDIS_URL",
        description="Cache and session store",
        default_port=6379,
        required=True,
        health_check="/ping",
    )

    KAFKA = ServiceEndpoint(
        name="kafka",
        env_var="SA01_KAFKA_BOOTSTRAP_SERVERS",
        description="Event streaming",
        default_port=9092,
        required=True,
    )

    SOMABRAIN = ServiceEndpoint(
        name="somabrain",
        env_var="SA01_SOMA_BASE_URL",
        description="Cognitive runtime",
        default_port=30101,
        required=True,
        health_check="/health",
    )

    SOMAFRACTALMEMORY = ServiceEndpoint(
        name="somafractalmemory",
        env_var="SOMA_MEMORY_URL",
        description="Memory system",
        default_port=10101,
        required=True,
        health_check="/health",
    )

    KEYCLOAK = ServiceEndpoint(
        name="keycloak",
        env_var="SA01_KEYCLOAK_URL",
        description="Identity provider",
        default_port=8080,
        required=True,
        health_check="/health",
    )

    OPA = ServiceEndpoint(
        name="opa",
        env_var="SA01_OPA_URL",
        description="Policy engine",
        default_port=8181,
        required=True,
        health_check="/health",
    )

    SPICEDB = ServiceEndpoint(
        name="spicedb",
        env_var="SPICEDB_GRPC_ADDR",
        description="Permissions database",
        default_port=50051,
        required=False,
    )

    LAGO = ServiceEndpoint(
        name="lago",
        env_var="LAGO_API_URL",
        description="Billing system",
        default_port=3000,
        path="/api/v1",
        required=False,
        health_check="/health",
    )

    TEMPORAL = ServiceEndpoint(
        name="temporal",
        env_var="SA01_TEMPORAL_HOST",
        description="Workflow engine",
        default_port=7233,
        required=False,
    )

    FLINK = ServiceEndpoint(
        name="flink",
        env_var="FLINK_REST_URL",
        description="Stream processor",
        default_port=8081,
        required=False,
        health_check="/overview",
    )

    WHISPER = ServiceEndpoint(
        name="whisper",
        env_var="WHISPER_URL",
        description="Speech-to-text",
        default_port=9100,
        required=False,
    )

    KOKORO = ServiceEndpoint(
        name="kokoro",
        env_var="KOKORO_URL",
        description="Text-to-speech",
        default_port=9200,
        required=False,
    )

    MERMAID = ServiceEndpoint(
        name="mermaid-cli",
        env_var="MERMAID_CLI_URL",
        description="Diagram renderer",
        default_port=9300,
        required=False,
    )

    PROMETHEUS = ServiceEndpoint(
        name="prometheus",
        env_var="PROMETHEUS_URL",
        description="Metrics collector",
        default_port=9090,
        required=False,
        health_check="/-/healthy",
    )

    GRAFANA = ServiceEndpoint(
        name="grafana",
        env_var="GRAFANA_URL",
        description="Metrics visualization",
        default_port=3000,
        required=False,
        health_check="/api/health",
    )

    OTLP_EXPORTER = ServiceEndpoint(
        name="otel-collector",
        env_var="OTEL_EXPORTER_OTLP_ENDPOINT",
        description="OpenTelemetry collector",
        default_port=4317,
        required=False,
    )

    @classmethod
    def get_all_services(cls) -> dict[str, ServiceEndpoint]:
        """Return all registered services."""
        return {
            name: getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), ServiceEndpoint)
        }

    @classmethod
    def validate_required(cls, environment: str) -> list[str]:
        """Return list of missing required service environment variables."""
        missing = []
        for name, service in cls.get_all_services().items():
            if service.required:
                try:
                    service.get_url(environment=environment)
                except ValueError:
                    missing.append(service.env_var)
        return missing


SERVICES = ServiceRegistry()

__all__ = ["ServiceEndpoint", "ServiceRegistry", "SERVICES"]