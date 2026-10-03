"""
SOMA Centralized Configuration System
======================================

VIBE Rule 100: Centralized Sovereignty - ALL settings in ONE place
VIBE Rule 91: Zero-Fallback Mandate - Fail-fast on missing config
VIBE Rule 164: Vault-Mandatory - ALL secrets from Vault

This module is the SINGLE SOURCE OF TRUTH for configuration dispatch
based on SA01_DEPLOYMENT_MODE (STANDALONE | AAAS | DEV | PROD).

Where a value lives, and why
----------------------------

========================  ==============================  ====================
Kind of value             Store                           Why
========================  ==============================  ====================
**Secrets**               Vault                           Rule 164. Never env,
                                                          never Django, never DB.
**Topology**              THIS FILE, per mode             It is needed before
                                                          Django and Postgres
                                                          exist, so it cannot
                                                          live in either. It is
                                                          Python config.
**Per-agent behaviour**   ``AgentSetting``                Per-agent and mutable
                                                          at runtime (model
                                                          names, recall limits).
**Mode selector**         ``SA01_DEPLOYMENT_MODE`` env    The one bootstrap
                                                          input: the same image
                                                          serves every mode, so
                                                          something outside has
                                                          to say which one.
========================  ==============================  ====================

Topology is **not** read from ``os.environ`` and **not** staged in a ``.env``
file. That is the whole point of Rule 100: one dict per mode, in one file,
reviewable in one diff. ``.env`` files carry no configuration — at most a
compose file injects the mode selector.

The ``overrides`` parameter is the escape hatch, and it is Python rather than
env on purpose: tests need ``localhost:63932`` topology and a deployer may
need to point at a differently-named stack. Passing a dict beats an
environment variable because it is typed, scoped to one process, and cannot
leak into ``ps`` or ``/proc/*/environ``.
"""

from __future__ import annotations

import logging
import os
from abc import ABC
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Mapping, Optional, TypeVar

from services.common.unified_secret_manager import get_secret_manager

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseSettings")

# The single bootstrap input. Everything else is derived from it.
MODE_ENV_VAR = "SA01_DEPLOYMENT_MODE"

_VALID_MODES = ("STANDALONE", "AAAS", "AAASMODE", "DEV", "PROD")


# ═══════════════════════════════════════════════════════════════════════════════
# Base Settings Abstract Class
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class BaseSettings(ABC):
    """Abstract base for deployment-specific settings."""

    # Core identification
    deployment_mode: str = field(default="")
    deployment_target: str = field(default="LOCAL")  # LOCAL | EKS | GKE

    # Database
    postgres_host: str = field(default="")
    postgres_port: int = field(default=5432)
    postgres_db: str = field(default="")
    postgres_user: str = field(default="")

    # Redis
    redis_host: str = field(default="")
    redis_port: int = field(default=6379)
    redis_db: int = field(default=0)

    # SpiceDB
    spicedb_host: str = field(default="")
    spicedb_port: int = field(default=50051)
    # Absent (None) is meaningful: no pre-shared key means SpiceDB is disabled
    # for this deployment, not that it authenticates with an empty string.
    spicedb_token: Optional[str] = field(default=None)
    spicedb_insecure: bool = field(default=False)

    # Vault
    vault_addr: str = field(default="")
    vault_mount: str = field(default="secret")
    vault_path_prefix: str = field(default="")

    # Application
    debug: bool = field(default=False)
    allowed_hosts: str = field(default="*")
    log_level: str = field(default="INFO")

    # Kafka
    kafka_bootstrap_servers: str = field(default="")
    kafka_security_protocol: str = field(default="PLAINTEXT")
    kafka_sasl_mechanism: str = field(default="")
    kafka_sasl_username: str = field(default="")
    # Absent (None) means the broker uses PLAINTEXT / mTLS — no SASL password
    # exists to hold. A present value is a credential and comes from Vault.
    kafka_sasl_password: Optional[str] = field(default=None)
    publish_kafka_timeout_seconds: float = field(default=2.0)

    # Requeue store
    sa01_redis_url: str = field(default="")
    policy_requeue_prefix: str = field(default="policy:requeue")

    # Auth / Account lockout
    auth_max_attempts: int = field(default=5)
    auth_lockout_duration: int = field(default=900)
    auth_attempt_window: int = field(default=900)

    # Authorization
    #
    # There is deliberately no fail-open switch. Authorization is fail-closed
    # in every deployment; a configuration value must not be able to turn a
    # missing policy engine into a grant. The former `sa01_authz_fail_open`
    # field and the SA01_AUTHZ_FAIL_OPEN environment variable are removed.

    # Features
    sa01_feature_profile: str = field(default="enhanced")

    # Idempotency
    sa01_tenant_id: str = field(default="default")
    sa01_memory_namespace: str = field(default="wm")

    # Budget
    sa01_default_token_budget: int = field(default=4096)

    # Integrations
    # Temporal is topology (a host:port). Empty means "no temporal for this
    # deployment", which is a real state, not a fallback.
    temporal_host: str = field(default="")

    # HTTP-probed services this deployment actually runs: name -> health URL.
    #
    # Rule 100 — this map is the inventory. ``InfrastructureHealthChecker``
    # probes exactly these and nothing else, which is how the stack stopped
    # advertising Flink, Qdrant, Whisper, Kokoro and a "SomaBrain Core" that
    # no compose file under ``infra/`` runs. A service absent from this map is
    # not deployed here; that is a real state, not a missing value.
    #
    # Postgres and Redis are not in here on purpose: they are probed by
    # connecting, from the ``postgres_*`` / ``redis_*`` topology above.
    service_health_endpoints: Dict[str, str] = field(default_factory=dict)
    # Optional LiteLLM gateway base URL. Empty means the provider library's
    # own defaults apply — again a real state, not a missing value.
    llm_base_url: str = field(default="")

    # ------------------------------------------------------------------
    # Derived / credential properties
    # ------------------------------------------------------------------

    @property
    def postgres_password(self) -> str:
        """Postgres password — Vault only (VIBE Rule 164)."""
        password = get_secret_manager().get_credential("postgres_password")
        if not password:
            raise RuntimeError(
                "VIBE Rule 164 VIOLATION: no postgres_password in Vault at "
                "credential:postgres_password. Secrets are never read from the "
                "environment or from a settings store."
            )
        return password

    @property
    def postgres_dsn(self) -> str:
        """Postgres DSN. Built here so the password never appears in a config file."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def django_database_config(self) -> dict:
        """Django DATABASES['default'] entry."""
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": self.postgres_db,
            "USER": self.postgres_user,
            "PASSWORD": self.postgres_password,
            "HOST": self.postgres_host,
            "PORT": str(self.postgres_port),
        }

    @property
    def redis_url(self) -> str:
        """Redis URL. Topology only — no credential is embedded."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def as_dict(self) -> Dict[str, Any]:
        """Every field as a plain dict. Credentials are absent, not blanked.

        Deliberately does not include ``postgres_password`` / ``postgres_dsn``:
        those are properties that resolve Vault at call time, so they cannot
        be serialised by accident. This is the shape that makes "the export
        never carries a credential" true for free.
        """
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ═══════════════════════════════════════════════════════════════════════════════
# Mode topology — THE single source for non-secret config
# ═══════════════════════════════════════════════════════════════════════════════
#
# One dict per mode. Topology only. Credentials are resolved from Vault at
# load time and never appear here (Rule 164).
#
# These replace a 73-call `os.environ` read and the four `.env` files that
# staged the same values with 13 mutually-conflicting keys. A value that is
# the same in both modes is duplicated on purpose: reading it here is a
# one-line diff, and inventing a "shared" third place is how the four files
# happened in the first place.

_STANDALONE_TOPOLOGY: Dict[str, Any] = {
    "deployment_target": "LOCAL",
    # Docker service names of the standalone compose project.
    "postgres_host": "somaagent_postgres",
    "postgres_port": 5432,
    "postgres_db": "somaagent",
    "postgres_user": "somaagent",
    "redis_host": "somaagent_redis",
    "redis_port": 6379,
    "redis_db": 0,
    "sa01_redis_url": "",
    "spicedb_host": "localhost",
    "spicedb_port": 50051,
    "spicedb_insecure": False,
    "vault_addr": "http://somaagent_vault:8200",
    "vault_mount": "secret",
    "vault_path_prefix": "somaagent",
    "debug": False,
    "allowed_hosts": "*",
    "log_level": "INFO",
    "kafka_bootstrap_servers": "",
    "kafka_security_protocol": "PLAINTEXT",
    "kafka_sasl_mechanism": "",
    "kafka_sasl_username": "",
    "publish_kafka_timeout_seconds": 2.0,
    "policy_requeue_prefix": "policy:requeue",
    "auth_max_attempts": 5,
    "auth_lockout_duration": 900,
    "auth_attempt_window": 900,
    "sa01_feature_profile": "enhanced",
    "sa01_tenant_id": "default",
    "sa01_memory_namespace": "wm",
    "sa01_default_token_budget": 4096,
    "temporal_host": "temporal:7233",
    "llm_base_url": "",
    # Only services that exist in infra/standalone/docker-compose.yml.
    # Postgres and Redis are connected to, not HTTP-probed.
    "service_health_endpoints": {
        "keycloak": "http://somaagent_keycloak:8080/health/ready",
        "temporal": "http://temporal:7233/health",
    },
}

_AAAS_TOPOLOGY: Dict[str, Any] = {
    "deployment_target": "LOCAL",
    # Docker service names of the shared somastack compose project.
    "postgres_host": "somastack_postgres",
    "postgres_port": 5432,
    "postgres_db": "soma",
    "postgres_user": "soma",
    "redis_host": "somastack_redis",
    "redis_port": 6379,
    "redis_db": 0,
    "sa01_redis_url": "",
    "spicedb_host": "localhost",
    "spicedb_port": 50051,
    "spicedb_insecure": False,
    "vault_addr": "http://somastack_vault:8200",
    "vault_mount": "secret",
    "vault_path_prefix": "soma",
    "debug": False,
    "allowed_hosts": "*",
    "log_level": "INFO",
    "milvus_host": "somastack_milvus",
    "milvus_port": 19530,
    # AAAS direct-mode for sub-millisecond latency. A real toggle, so it is an
    # override key — not derived from the mode name.
    "aaas_direct_mode": False,
    "kafka_bootstrap_servers": "somastack_kafka:9092",
    "kafka_security_protocol": "PLAINTEXT",
    "kafka_sasl_mechanism": "",
    "kafka_sasl_username": "",
    "publish_kafka_timeout_seconds": 2.0,
    "policy_requeue_prefix": "policy:requeue",
    "auth_max_attempts": 5,
    "auth_lockout_duration": 900,
    "auth_attempt_window": 900,
    "sa01_feature_profile": "enhanced",
    "sa01_tenant_id": "default",
    "sa01_memory_namespace": "wm",
    "sa01_default_token_budget": 4096,
    "temporal_host": "somastack_temporal:7233",
    "llm_base_url": "",
    # Only services that exist in infra/aaas/aaas/docker-compose.yml.
    "service_health_endpoints": {
        "keycloak": "http://somastack_keycloak:8080/health/ready",
        "temporal": "http://somastack_temporal:7233/health",
    },
}


def _credentials() -> Dict[str, Any]:
    """Every credential, resolved from Vault once per load. Rule 164.

    Absent means the service is disabled for this deployment (SpiceDB without
    a pre-shared key, a broker on PLAINTEXT) — not that it authenticates with
    an empty string. That distinction is why these are ``Optional``.
    """
    return {
        "spicedb_token": get_secret_manager().get_credential("spicedb_token"),
        "kafka_sasl_password": get_secret_manager().get_credential("kafka_sasl_password"),
    }


def _apply_overrides(params: Dict[str, Any], overrides: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """Apply explicit overrides, rejecting unknown keys.

    Rejecting rather than ignoring is Rule 91: a typo in an override that is
    silently dropped is a fallback in disguise — the stack boots on a value
    nobody chose.
    """
    if not overrides:
        return params
    unknown = set(overrides) - set(params)
    if unknown:
        raise RuntimeError(
            f"VIBE Rule 91 VIOLATION: unknown settings override key(s) {sorted(unknown)}. "
            f"Known keys: {sorted(params)}. An override that does not land is a "
            f"silent fallback."
        )
    params.update(overrides)
    return params


# ═══════════════════════════════════════════════════════════════════════════════
# Mode classes
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class StandaloneSettings(BaseSettings):
    """Settings for Agent-only Standalone deployment (Port 20xxx)."""

    # Full triad always on (Agent + SomaBrain + SFM) — never a memory bypass.
    somabrain_enabled: bool = field(default=True)
    fractalmemory_enabled: bool = field(default=True)

    @classmethod
    def load(cls, overrides: Optional[Mapping[str, Any]] = None) -> "StandaloneSettings":
        """Build Standalone settings. No environment is read.

        `overrides` is the only injection point — Python, typed, scoped to the
        process. It is what tests use for `localhost:63932` topology instead
        of polluting the environment.
        """
        LOGGER.info("Loading STANDALONE configuration...")
        params = _apply_overrides(dict(_STANDALONE_TOPOLOGY), overrides)
        params.update(_credentials())
        params["deployment_mode"] = "STANDALONE"
        params["somabrain_enabled"] = True
        params["fractalmemory_enabled"] = True
        return cls(**params)


@dataclass
class AAASSettings(BaseSettings):
    """Settings for Unified Monolith AAAS deployment (Port 63xxx)."""

    # AAAS-specific: Brain + Memory enabled
    soma_aaas_mode: bool = field(default=True)
    somabrain_enabled: bool = field(default=True)
    fractalmemory_enabled: bool = field(default=True)

    # AAAS direct-mode for sub-millisecond latency
    aaas_direct_mode: bool = field(default=False)

    # Milvus (Vector DB - AAAS only)
    milvus_host: str = field(default="")
    milvus_port: int = field(default=19530)

    @classmethod
    def load(cls, overrides: Optional[Mapping[str, Any]] = None) -> "AAASSettings":
        """Build AAAS settings. No environment is read except the mode selector.

        `soma_aaas_mode` / `aaas_direct_mode` used to be parsed from
        `SOMA_AAAS_MODE` (`true` / `direct` / `false`). Being in AAAS mode is
        now established by `SA01_DEPLOYMENT_MODE=AAAS` — the same fact, stated
        once. `aaas_direct_mode` stays a real toggle and is an override key.
        """
        LOGGER.info("Loading AAAS configuration...")
        params = _apply_overrides(dict(_AAAS_TOPOLOGY), overrides)
        params.update(_credentials())
        params["deployment_mode"] = "AAAS"
        params["soma_aaas_mode"] = True
        params["somabrain_enabled"] = True
        params["fractalmemory_enabled"] = True
        return cls(**params)


# ═══════════════════════════════════════════════════════════════════════════════
# Settings Registry - THE SINGLE SOURCE OF TRUTH
# ═══════════════════════════════════════════════════════════════════════════════


class SettingsRegistry:
    """
    Centralized settings dispatcher based on deployment mode.

    VIBE Rule 100: This is the ONLY entry point for configuration.

    Usage:
        from config.settings_registry import SettingsRegistry
        settings = SettingsRegistry.load()
        host = settings.postgres_host  # example
    """

    _instance: Optional[BaseSettings] = None

    @classmethod
    def load(
        cls,
        force_reload: bool = False,
        overrides: Optional[Mapping[str, Any]] = None,
    ) -> BaseSettings:
        """Load settings for ``SA01_DEPLOYMENT_MODE``.

        Returns the cached instance unless ``force_reload=True``. ``overrides``
        is applied on load and therefore implies a reload.
        """
        if overrides:
            force_reload = True

        if cls._instance is not None and not force_reload:
            return cls._instance

        mode = os.environ.get(MODE_ENV_VAR, "STANDALONE").upper()

        LOGGER.info("SettingsRegistry: Loading configuration for mode=%s", mode)

        if mode == "STANDALONE":
            cls._instance = StandaloneSettings.load(overrides)
        elif mode in ("AAAS", "AAASMODE"):
            cls._instance = AAASSettings.load(overrides)
        elif mode == "DEV":
            # DEV mode defaults to Standalone for simplicity
            LOGGER.info("DEV mode detected, using Standalone config")
            cls._instance = StandaloneSettings.load(overrides)
        elif mode == "PROD":
            # PROD requires the mode to be stated explicitly via the mode
            # selector — it must not guess. `SOMA_AAAS_MODE` used to arbitrate
            # here, which was the same fact told twice and twice the chance to
            # disagree.
            raise RuntimeError(
                f"VIBE Rule 91 VIOLATION: {MODE_ENV_VAR}=PROD is not a "
                f"deployment. Set {MODE_ENV_VAR}=AAAS or STANDALONE. "
                f"PROD is an environment, not a topology."
            )
        elif mode in _VALID_MODES:  # pragma: no cover - guarded above
            raise RuntimeError(
                f"VIBE Rule 91 VIOLATION: Unknown {MODE_ENV_VAR}={mode}. "
                f"Valid values: STANDALONE, AAAS, DEV"
            )
        else:
            raise RuntimeError(
                f"VIBE Rule 91 VIOLATION: Unknown {MODE_ENV_VAR}={mode}. "
                f"Valid values: STANDALONE, AAAS, DEV"
            )

        LOGGER.info("SettingsRegistry: Configuration loaded successfully")
        return cls._instance

    @classmethod
    def get(cls) -> BaseSettings:
        """Get cached settings or load if not initialized."""
        if cls._instance is None:
            return cls.load()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset cached settings (for testing)."""
        cls._instance = None

    @classmethod
    def set(cls, instance: BaseSettings) -> BaseSettings:
        """Install a fully-built settings object. For tests and programmatic boot.

        This is the supported way to run the suite against `localhost:63932`
        topology. It is not an environment variable and not a `.env` file.
        """
        cls._instance = instance
        return cls._instance


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level convenience
# ═══════════════════════════════════════════════════════════════════════════════


def get_settings() -> BaseSettings:
    """Convenience function to get current settings."""
    return SettingsRegistry.get()
