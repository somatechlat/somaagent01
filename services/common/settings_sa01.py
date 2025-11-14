"""Service settings for SomaAgent 01 (self-contained).

This replaces the old shim that imported from a non-existent ``common`` package.
It provides a minimal, robust SA01Settings based on ``BaseServiceSettings`` with
DEV defaults aligned to docker-compose host port mappings so the gateway and
workers can run locally against the running infra.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

from services.common.settings_base import BaseServiceSettings


@dataclass(slots=True)
class SA01Settings(BaseServiceSettings):
	"""Concrete settings for SomaAgent 01 services.

	Extends BaseServiceSettings with a few service-wide knobs used across
	multiple processes. Environment variables at runtime can still override
	specific connection strings; these defaults are primarily for local DEV.
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

	# Authentication toggle – mirrors the historic ``SA01_AUTH_REQUIRED`` flag.
	# When false, policy checks are bypassed (tests set this to false).
	# The value is read from the environment at construction time.
	auth_required: bool = os.getenv("SA01_AUTH_REQUIRED", "false").lower() in {"true", "1", "yes"}

	# Name of the cookie that may carry a JWT token.  The gateway reads this
	# environment variable ``GATEWAY_JWT_COOKIE_NAME`` but the test suite also
	# accesses it via ``APP_SETTINGS.jwt_cookie_name``.  Providing a default
	# keeps backward‑compatibility.
	jwt_cookie_name: str = os.getenv("GATEWAY_JWT_COOKIE_NAME", "jwt")

	# Authentication toggle – mirrors the historic SA01_AUTH_REQUIRED flag.
	# When false, policy checks are bypassed (tests set this to false).
	# The value is read from the environment at construction time.
	auth_required: bool = os.getenv("SA01_AUTH_REQUIRED", "false").lower() in {"true", "1", "yes"}

	@classmethod
	def default_environment(cls) -> str:
		# Keep DEV as the standard local mode
		return os.getenv("SA01_ENV", os.getenv("SOMA_AGENT_ENV", "DEV")).upper()

	@classmethod
	def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
		"""Return sane defaults per environment.

		- DEV defaults target docker-compose forwarded host ports so a locally
		  running gateway can connect to the infra containers.
		- STAGING/PROD provide placeholders that should be overridden via env.
		"""
		dev_defaults = {
			# BaseServiceSettings required fields
			"deployment_mode": "DEV",
			# Compose maps host ports: kafka 20000->9092, redis 20001->6379, pg 20002->5432, opa 20009->8181
			"postgres_dsn": os.getenv("SA01_POSTGRES_DSN", "postgresql://soma:soma@localhost:20002/somaagent01"),
			"kafka_bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:20000"),
			"redis_url": os.getenv("REDIS_URL", "redis://localhost:20001/0"),
			"otlp_endpoint": os.getenv("OTLP_ENDPOINT", ""),
			"model_profiles_path": os.getenv("MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
			"extra": {},
			# Extended fields
			"metrics_port": int(os.getenv("GATEWAY_METRICS_PORT", "9400")),
			"metrics_host": os.getenv("GATEWAY_METRICS_HOST", "0.0.0.0"),
			"opa_url": os.getenv("OPA_URL", "http://localhost:20009"),
			"gateway_port": int(os.getenv("GATEWAY_PORT", "8010")),
			"soma_base_url": os.getenv("SOMA_BASE_URL", "http://localhost:8010"),
		}

		# Placeholders for non-DEV; expect env to provide concrete values
		staging_defaults = {
			"deployment_mode": "STAGING",
			"postgres_dsn": os.getenv("SA01_POSTGRES_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"),
			"kafka_bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
			"redis_url": os.getenv("REDIS_URL", "redis://redis:6379/0"),
			"otlp_endpoint": os.getenv("OTLP_ENDPOINT", ""),
			"model_profiles_path": os.getenv("MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
			"extra": {},
			"metrics_port": int(os.getenv("GATEWAY_METRICS_PORT", "9400")),
			"metrics_host": os.getenv("GATEWAY_METRICS_HOST", "0.0.0.0"),
			"opa_url": os.getenv("OPA_URL", "http://opa:8181"),
			"gateway_port": int(os.getenv("GATEWAY_PORT", "8010")),
			"soma_base_url": os.getenv("SOMA_BASE_URL", "http://localhost:8010"),
		}

		prod_defaults = {
			"deployment_mode": "PROD",
			"postgres_dsn": os.getenv("SA01_POSTGRES_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"),
			"kafka_bootstrap_servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
			"redis_url": os.getenv("REDIS_URL", "redis://redis:6379/0"),
			"otlp_endpoint": os.getenv("OTLP_ENDPOINT", ""),
			"model_profiles_path": os.getenv("MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
			"extra": {},
			"metrics_port": int(os.getenv("GATEWAY_METRICS_PORT", "9400")),
			"metrics_host": os.getenv("GATEWAY_METRICS_HOST", "0.0.0.0"),
			"opa_url": os.getenv("OPA_URL", "http://opa:8181"),
			"gateway_port": int(os.getenv("GATEWAY_PORT", "8010")),
			"soma_base_url": os.getenv("SOMA_BASE_URL", "http://localhost:8010"),
		}

		return {
			"DEV": dev_defaults,
			"STAGING": staging_defaults,
			"PROD": prod_defaults,
		}

