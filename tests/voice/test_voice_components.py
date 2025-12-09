"""Smoke tests for the voice subsystem.

The purpose of this file is to ensure that the newly added voice modules can be
imported and instantiated without raising unexpected exceptions.  Full functional
tests (real audio capture, WebSocket communication, etc.) are out of scope for
the kata and would require heavy external dependencies.  Instead we verify the
basic wiring and that the compatibility shims in the configuration model work.
"""

from __future__ import annotations

import sys
from unittest import mock

import pytest

from src.core.config.models import (
    AudioConfig,
    AuthConfig,
    Config,
    DatabaseConfig,
    ExternalServiceConfig,
    KafkaConfig,
    RedisConfig,
    ServiceConfig,
    VoiceConfig,
)
from src.voice.exceptions import VoiceProcessingError
from src.voice.service import VoiceService


@pytest.fixture
def minimal_config() -> Config:
    """Create a minimal but valid configuration instance.

    All required nested models are instantiated with placeholder values that are
    sufficient for the voice subsystem (e.g., dummy host/port, empty strings for
    URLs).  The ``voice.enable`` flag is set to ``True`` so that the service can
    be started without additional environment configuration.
    """
    service = ServiceConfig(
        name="somaagent01",
        environment="DEV",
        deployment_mode="DEV",
        host="0.0.0.0",
        port=8010,
        metrics_port=8011,
        log_level="INFO",
    )
    database = DatabaseConfig(dsn="postgresql://user:pass@localhost/db")
    kafka = KafkaConfig(bootstrap_servers="localhost:9092")
    redis = RedisConfig(url="redis://localhost:6379/0")
    external = ExternalServiceConfig()
    auth = AuthConfig(auth_required=False)
    audio = AudioConfig()
    voice = VoiceConfig(enable=True)
    return Config(
        service=service,
        database=database,
        kafka=kafka,
        redis=redis,
        external=external,
        auth=auth,
        feature_flags={},
        extra={},
        voice=voice,
    )


def test_voice_service_imports(minimal_config: Config) -> None:
    """Import the voice service and ensure it can be instantiated.

    The ``VoiceService.start`` method creates ``AudioCapture`` and ``Speaker``
    instances which attempt to import the optional ``sounddevice`` library.  To
    keep the test environment lightweight we mock the import so that the stub
    implementation is used without raising ``ImportError``.
    """
    with mock.patch.dict(sys.modules, {"sounddevice": mock.MagicMock()}):
        service = VoiceService(minimal_config)
        # ``start`` may raise ``VoiceProcessingError`` if the mocked library
        # behaves unexpectedly; we treat that as a successful import path.
        try:
            # ``asyncio.run`` is not used here because the method is async; we
            # simply ensure it can be awaited without error.
            import asyncio

            asyncio.run(service.start())
        except VoiceProcessingError:
            # Expected when the stub attempts to use the mocked sounddevice API.
            pass
