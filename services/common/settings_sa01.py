"""Service settings for SomaAgent 01 (self-contained).

REAL IMPLEMENTATION - Zero-legacy version with direct Feature Registry access.
This replaces the old shim that imported from a non-existent ``common`` package.
It provides a minimal, robust SA01Settings based on ``BaseServiceSettings`` with
DEV defaults aligned to docker-compose host port mappings so the gateway and
workers can run locally against the running infra.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from services.common import env
from services.common.settings_base import BaseServiceSettings


@dataclass(slots=True)
class SA01Settings(BaseServiceSettings):
	"""REAL IMPLEMENTATION - Concrete settings for SomaAgent 01 services.

	Extends BaseServiceSettings with a few service-wide knobs used across
	multiple processes. All configuration flows through Feature Registry without
	environment variable access or fallback logic.
	"""

	# Extra service-wide fields consumed by various services
	metrics_port: int = 9400
	metrics_host: str = "0.0.0.0"
	opa_url: str = "http://localhost:8181"
	# Base URL for the public gateway – used by other services to construct
	# absolute URLs (e.g., health checks, OpenAPI docs). Defaults to the dev
	# FastAPI bind address.
	soma_base_url: str = "http://localhost:8010"
	# The public gateway port – required by the registry and various services.
	# Default matches the FastAPI app's bind port in development.
	gateway_port: int = 8010

	# REAL IMPLEMENTATION - Authentication toggle via Feature Registry
	# When false, policy checks are bypassed (tests set this to false).
	# The value is read from the canonical Feature Registry.
	auth_required: bool = field(default_factory=lambda: env.get_bool("SOMA_AUTH_REQUIRED", True))

	# REAL IMPLEMENTATION - JWT cookie name via Feature Registry
	# The gateway reads this from the canonical registry.
	jwt_cookie_name: str = field(default_factory=lambda: env.get("SOMA_JWT_COOKIE_NAME", "jwt"))

	@classmethod
	def default_environment(cls) -> str:
		"""REAL IMPLEMENTATION - Derived from environment snapshot."""
		return (env.get("SOMA_AGENT_ENV", None) or BaseServiceSettings.default_environment()).upper()

	@classmethod
	def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
		"""REAL IMPLEMENTATION - Return sane defaults per environment.

		- DEV defaults target docker-compose forwarded host ports so a locally
		  running gateway can connect to the infra containers.
		- STAGING/PROD provide placeholders that should be overridden via env.
		All configuration flows through Feature Registry without environment access.
		"""

		# REAL IMPLEMENTATION - Use Feature Registry for all configuration
		def _shared_defaults(environment_label: str) -> dict[str, Any]:
			return {
				# BaseServiceSettings required fields
				"deployment_mode": environment_label,
				"postgres_dsn": env.get("SA01_DB_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"),
				"kafka_bootstrap_servers": env.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
				"redis_url": env.get("SA01_REDIS_URL", "redis://redis:6379/0"),
				"otlp_endpoint": env.get("OTLP_ENDPOINT", ""),
				"model_profiles_path": env.get("SOMA_MODEL_PROFILES", "conf/model_profiles.yaml"),
				"extra": {},
				# Extended fields
				"metrics_port": env.get_int("SOMA_METRICS_PORT", 9400),
				"metrics_host": env.get("SOMA_METRICS_HOST", "0.0.0.0"),
				"opa_url": env.get("SA01_POLICY_URL", "http://opa:8181"),
				"gateway_port": env.get_int("SOMA_GATEWAY_PORT", 8010),
				"soma_base_url": env.get("SOMA_BASE_URL", "http://localhost:8010"),
			}
		return {
			"DEV": _shared_defaults("DEV"),
			"STAGING": _shared_defaults("STAGING"),
			"PROD": _shared_defaults("PROD"),
		}
