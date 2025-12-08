"""Tests for the voice provider selector.

These tests verify that :func:`src.voice.provider_selector.get_provider_client`
instantiates the correct client class based on the ``voice.provider`` setting in
the global configuration model.
"""

from __future__ import annotations

import pytest

from src.core.config.models import Config, VoiceConfig
from src.voice.provider_selector import get_provider_client, ProviderNotSupportedError


@pytest.fixture
def base_config() -> Config:
    # Minimal configuration sufficient for the selector – other fields use their
    # defaults.
    return Config(
        service=Config.ServiceConfig(
            name="test",
            environment="DEV",
            deployment_mode="DEV",
            host="0.0.0.0",
            port=8000,
            metrics_port=8001,
            log_level="INFO",
        ),
        database=Config.DatabaseConfig(dsn="postgresql://user:pass@localhost/db"),
        kafka=Config.KafkaConfig(bootstrap_servers="localhost:9092"),
        redis=Config.RedisConfig(url="redis://localhost:6379"),
        external=Config.ExternalServiceConfig(),
        auth=Config.AuthConfig(auth_required=False),
        voice=VoiceConfig(),
    )


def test_get_openai_client(base_config: Config):
    base_config.voice.provider = "openai"
    client = get_provider_client(base_config)
    # The stub client class is defined in ``src.voice.openai_client``.
    from src.voice.openai_client import OpenAIClient

    assert isinstance(client, OpenAIClient)
    # Verify that the client received the correct OpenAIConfig instance.
    assert client._config.model == "gpt-4o-realtime"


def test_get_local_client(base_config: Config):
    base_config.voice.provider = "local"
    client = get_provider_client(base_config)
    from src.voice.local_client import LocalClient

    assert isinstance(client, LocalClient)
    # The stub client stores the LocalVoiceConfig.
    assert client._config.stt_engine == "kokoro"


def test_unsupported_provider_raises(base_config: Config):
    base_config.voice.provider = "unknown"  # type: ignore
    with pytest.raises(ProviderNotSupportedError) as exc:
        get_provider_client(base_config)
    assert "unknown" in str(exc.value)
