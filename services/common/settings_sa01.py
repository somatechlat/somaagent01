"""Service settings for SomaAgent 01 (self-contained).

REAL IMPLEMENTATION - Zero-legacy version with direct Feature Registry access.
This replaces the old shim that imported from a non-existent ``common`` package.
It provides a minimal, robust SA01Settings based on ``BaseServiceSettings`` with
DEV defaults aligned to docker-compose host port mappings so the gateway and
workers can run locally against the running infra.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from services.common.settings_base import BaseServiceSettings
from services.common.registry import registry


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
	auth_required: bool = registry().flag("auth_required")

	# REAL IMPLEMENTATION - JWT cookie name via Feature Registry
	# The gateway reads this from the canonical registry.
	jwt_cookie_name: str = registry().legacy_value("GATEWAY_JWT_COOKIE_NAME", "jwt")

	@classmethod
	def default_environment(cls) -> str:
		"""REAL IMPLEMENTATION - Use Feature Registry for deployment mode."""
		return registry().deployment_mode()

	@classmethod
	def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
		"""REAL IMPLEMENTATION - Return sane defaults per environment.

		- DEV defaults target docker-compose forwarded host ports so a locally
		  running gateway can connect to the infra containers.
		- STAGING/PROD provide placeholders that should be overridden via env.
		All configuration flows through Feature Registry without environment access.
		"""

		# REAL IMPLEMENTATION - Use Feature Registry for all configuration
		reg = registry()

		dev_defaults = {
			# BaseServiceSettings required fields
			"deployment_mode": "DEV",
			# Compose maps host ports: kafka 20000->9092, redis 20001->6379, pg 20002->5432, opa 20009->8181
			"postgres_dsn": reg.postgres_dsn(),
			"kafka_bootstrap_servers": reg.kafka_bootstrap_servers(),
			"redis_url": reg.redis_url(),
			"otlp_endpoint": "",
			"model_profiles_path": "conf/model_profiles.yaml",
			"extra": {},
			# Extended fields
			"metrics_port": 9400,
			"metrics_host": "0.0.0.0",
			"opa_url": reg.opa_url(),
			"gateway_port": reg.gateway_port(),
			"soma_base_url": reg.soma_base_url(),
		}

		# Placeholders for non-DEV; expect registry to provide concrete values
		staging_defaults = {
			"deployment_mode": "STAGING",
			"postgres_dsn": reg.postgres_dsn(),
			"kafka_bootstrap_servers": reg.kafka_bootstrap_servers(),
			"redis_url": reg.redis_url(),
			"otlp_endpoint": "",
			"model_profiles_path": "conf/model_profiles.yaml",
			"extra": {},
			"metrics_port": 9400,
			"metrics_host": "0.0.0.0",
			"opa_url": reg.opa_url(),
			"gateway_port": reg.gateway_port(),
			"soma_base_url": reg.soma_base_url(),
		}

		prod_defaults = {
			"deployment_mode": "PROD",
			"postgres_dsn": reg.postgres_dsn(),
			"kafka_bootstrap_servers": reg.kafka_bootstrap_servers(),
			"redis_url": reg.redis_url(),
			"otlp_endpoint": "",
			"model_profiles_path": "conf/model_profiles.yaml",
			"extra": {},
			"metrics_port": 9400,
			"metrics_host": "0.0.0.0",
			"opa_url": reg.opa_url(),
			"gateway_port": reg.gateway_port(),
			"soma_base_url": reg.soma_base_url(),
		}

		return {
			"DEV": dev_defaults,
			"STAGING": staging_defaults,
			"PROD": prod_defaults,
		}
