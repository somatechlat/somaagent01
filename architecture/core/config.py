# Deprecated configuration module.

# This file previously contained a standalone configuration implementation.
# The project now uses the single source of truth located in
# ``src.core.config``. Importing this module will raise an ImportError to make
# the deprecation explicit and to prevent accidental usage.

raise ImportError(
    "The module 'architecture.core.config' is deprecated. "
    "Please import configuration from 'src.core.config' instead."
)
import os
from typing import Any, Dict


class CentralizedConfig:
    """VIBE COMPLIANT - Single configuration authority for entire system."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CentralizedConfig, cls).__new__(cls)
            cls._instance._config = cls._instance._load_canonical_config()
        return cls._instance

    def _load_canonical_config(self) -> Dict[str, Any]:
        """Load configuration from SA01_ prefixed variables only."""
        return {
            # Infrastructure
            "deployment_mode": os.getenv("SA01_DEPLOYMENT_MODE", "DEV"),
            "postgres_dsn": os.getenv("SA01_DB_DSN"),
            "kafka_bootstrap_servers": os.getenv("SA01_KAFKA_BOOTSTRAP_SERVERS"),
            "redis_url": os.getenv("SA01_REDIS_URL"),
            "policy_url": os.getenv("SA01_POLICY_URL"),
            # Services
            "gateway_port": int(os.getenv("SA01_GATEWAY_PORT", 8010)),
            "soma_base_url": os.getenv("SA01_SOMA_BASE_URL"),  # ONLY SA01_ PREFIX
            # Auth
            "auth_required": os.getenv("SA01_AUTH_REQUIRED", "false").lower() == "true",
            # SSE
            "sse_enabled": os.getenv("SA01_SSE_ENABLED", "true").lower() in {"true", "1", "yes"},
            "conversation_outbound_topic": os.getenv(
                "CONVERSATION_OUTBOUND", "conversation.outbound"
            ),
            # Features
            "feature_flags_ttl_seconds": int(os.getenv("FEATURE_FLAGS_TTL_SECONDS", "30") or "30"),
            # Metrics
            "metrics_port": int(os.getenv("SOMA_METRICS_PORT", 9400)),
            "metrics_host": os.getenv("SOMA_METRICS_HOST", "0.0.0.0"),
            "otlp_endpoint": os.getenv("OTLP_ENDPOINT", ""),
            # JWT
            "jwt_cookie_name": os.getenv("SOMA_JWT_COOKIE_NAME", "jwt"),
            # Model Profiles
            "model_profiles_path": os.getenv("SOMA_MODEL_PROFILES", "conf/model_profiles.yaml"),
            # Speech-to-Text
            "stt_max_audio_bytes": int(os.getenv("STT_MAX_AUDIO_BYTES", "12582912")),
            "stt_model_size": os.getenv("STT_MODEL_SIZE", "tiny"),
            "stt_language": os.getenv("STT_LANGUAGE", "en"),
            # Text-to-Speech
            "tts_max_text_chars": int(os.getenv("TTS_MAX_TEXT_CHARS", "2000")),
            # Realtime Speech
            "realtime_session_ttl_seconds": int(os.getenv("REALTIME_SESSION_TTL_SECONDS", "45")),
            "realtime_sample_rate": int(os.getenv("REALTIME_SAMPLE_RATE", "16000")),
            "realtime_frame_ms": int(os.getenv("REALTIME_FRAME_MS", "20")),
            "realtime_max_session_secs": int(os.getenv("REALTIME_MAX_SESSION_SECS", "600")),
            # Gateway
            "gateway_api_version": os.getenv("GATEWAY_API_VERSION", "v1"),
            # Kafka
            "kafka_security_protocol": os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            "kafka_sasl_mechanism": os.getenv("KAFKA_SASL_MECHANISM"),
            "kafka_sasl_username": os.getenv("KAFKA_SASL_USERNAME"),
            "kafka_sasl_password": os.getenv("KAFKA_SASL_PASSWORD"),
            # Security Headers
            "gateway_frame_options": os.getenv("GATEWAY_FRAME_OPTIONS", "DENY"),
            "gateway_referrer_policy": os.getenv("GATEWAY_REFERRER_POLICY", "no-referrer"),
            "gateway_hsts_max_age": os.getenv("GATEWAY_HSTS_MAX_AGE", "15552000"),
            # Remove all non-SA01_ prefixed variables
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dictionary-style access."""
        return self._config[key]

    def flag(self, key: str, tenant: Any = None) -> bool:
        """Check a feature flag."""
        # The tenant parameter is ignored, but kept for compatibility.
        env_key = f"SA01_ENABLE_{key.upper()}"
        return os.getenv(env_key, "false").lower() in {"true", "1", "yes", "on"}


# Create a single instance of the config
config = CentralizedConfig()
