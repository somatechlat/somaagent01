"""Multimodal Degradation Service - Audio, Voice, Uploads.

Handles degradation for audio (TTS/STT), voice, uploads, and storage.
Provides automatic failover for audio providers.


"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class AudioProviderStatus(Enum):
    """Status of an audio provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class AudioProviderHealth:
    """Health status of an audio provider."""

    provider: str
    service_type: str  # "tts" or "stt"
    status: AudioProviderStatus = AudioProviderStatus.UNKNOWN
    last_check: float = 0.0
    last_success: float = 0.0
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    latency_ms: float = 0.0


@dataclass
class AudioFallbackChain:
    """Fallback chain for audio providers."""

    primary: str
    fallbacks: List[str] = field(default_factory=list)
    current_index: int = 0

    def get_current(self) -> str:
        """Retrieve current.
            """

        if self.current_index == 0:
            return self.primary
        return self.fallbacks[self.current_index - 1]

    def get_next_fallback(self) -> Optional[str]:
        """Retrieve next fallback.
            """

        if self.current_index >= len(self.fallbacks):
            return None
        self.current_index += 1
        return self.get_current()


class MultimodalDegradationService:
    """Multimodal (Audio/Voice/Upload) Degradation Service.

    Manages degradation and failover for:
    - Text-to-Speech (TTS) providers
    - Speech-to-Text (STT) providers
    - Voice synthesis services
    - Upload/storage services

    When a service fails:
    1. Marks as degraded/unavailable
    2. Switches to fallback
    3. Queues operations for retry
    4. Notifies via degradation topic

    Usage:
        service = MultimodalDegradationService()
        await service.initialize()

        # Get available TTS provider
        tts = await service.get_available_tts()

        # Report success/failure
        await service.record_audio_success("elevenlabs", "tts", latency_ms=150)
        await service.record_audio_failure("elevenlabs", "tts", "Rate limit")
    """

    # Default TTS providers
    DEFAULT_TTS_CHAIN = AudioFallbackChain(
        primary="elevenlabs",
        fallbacks=["openai/tts-1", "kokoro/local", "browser/native"],
    )

    # Default STT providers
    DEFAULT_STT_CHAIN = AudioFallbackChain(
        primary="openai/whisper",
        fallbacks=["deepgram", "browser/native"],
    )

    # Storage providers
    DEFAULT_STORAGE_CHAIN = AudioFallbackChain(
        primary="s3",
        fallbacks=["local/filesystem", "redis/temp"],
    )

    def __init__(self):
        """Initialize the instance."""

        self._tts_chain: Optional[AudioFallbackChain] = None
        self._stt_chain: Optional[AudioFallbackChain] = None
        self._storage_chain: Optional[AudioFallbackChain] = None
        self._provider_health: Dict[str, AudioProviderHealth] = {}
        self._initialized = False
        self._pending_uploads: List[Dict[str, Any]] = []  # Queue for failed uploads

    async def initialize(self):
        """Initialize the multimodal degradation service."""
        if self._initialized:
            return

        # Load chains from settings or use defaults
        tts_config = getattr(settings, "TTS_FALLBACK_CHAIN", None)
        stt_config = getattr(settings, "STT_FALLBACK_CHAIN", None)
        storage_config = getattr(settings, "STORAGE_FALLBACK_CHAIN", None)

        self._tts_chain = AudioFallbackChain(
            primary=tts_config["primary"] if tts_config else self.DEFAULT_TTS_CHAIN.primary,
            fallbacks=(
                tts_config.get("fallbacks", []) if tts_config else self.DEFAULT_TTS_CHAIN.fallbacks
            ),
        )

        self._stt_chain = AudioFallbackChain(
            primary=stt_config["primary"] if stt_config else self.DEFAULT_STT_CHAIN.primary,
            fallbacks=(
                stt_config.get("fallbacks", []) if stt_config else self.DEFAULT_STT_CHAIN.fallbacks
            ),
        )

        self._storage_chain = AudioFallbackChain(
            primary=(
                storage_config["primary"] if storage_config else self.DEFAULT_STORAGE_CHAIN.primary
            ),
            fallbacks=(
                storage_config.get("fallbacks", [])
                if storage_config
                else self.DEFAULT_STORAGE_CHAIN.fallbacks
            ),
        )

        # Initialize health tracking for all providers
        for provider in [self._tts_chain.primary] + self._tts_chain.fallbacks:
            self._provider_health[f"tts:{provider}"] = AudioProviderHealth(
                provider=provider, service_type="tts"
            )

        for provider in [self._stt_chain.primary] + self._stt_chain.fallbacks:
            self._provider_health[f"stt:{provider}"] = AudioProviderHealth(
                provider=provider, service_type="stt"
            )

        for provider in [self._storage_chain.primary] + self._storage_chain.fallbacks:
            self._provider_health[f"storage:{provider}"] = AudioProviderHealth(
                provider=provider, service_type="storage"
            )

        self._initialized = True
        logger.info("MultimodalDegradationService initialized")

    async def get_available_tts(self) -> Optional[str]:
        """Get the best available TTS provider."""
        return await self._get_available_provider(self._tts_chain, "tts")

    async def get_available_stt(self) -> Optional[str]:
        """Get the best available STT provider."""
        return await self._get_available_provider(self._stt_chain, "stt")

    async def get_available_storage(self) -> Optional[str]:
        """Get the best available storage provider."""
        return await self._get_available_provider(self._storage_chain, "storage")

    async def _get_available_provider(
        self, chain: AudioFallbackChain, service_type: str
    ) -> Optional[str]:
        """Get best available provider from a chain."""
        if not chain:
            return None

        # Check primary
        primary_key = f"{service_type}:{chain.primary}"
        primary_health = self._provider_health.get(primary_key)
        if primary_health and primary_health.status != AudioProviderStatus.UNAVAILABLE:
            return chain.primary

        # Check fallbacks
        for fallback in chain.fallbacks:
            fallback_key = f"{service_type}:{fallback}"
            fallback_health = self._provider_health.get(fallback_key)
            if fallback_health and fallback_health.status != AudioProviderStatus.UNAVAILABLE:
                return fallback

        # All unavailable - return primary as last resort
        logger.error(f"All {service_type} providers unavailable")
        return chain.primary

    async def record_audio_success(self, provider: str, service_type: str, latency_ms: float = 0.0):
        """Record a successful audio operation."""
        key = f"{service_type}:{provider}"
        health = self._provider_health.get(key)
        if not health:
            return

        health.last_check = time.time()
        health.last_success = time.time()
        health.latency_ms = latency_ms
        health.consecutive_failures = 0
        health.last_error = None

        if health.status != AudioProviderStatus.HEALTHY:
            old_status = health.status
            health.status = AudioProviderStatus.HEALTHY
            logger.info(f"Audio provider {key} recovered from {old_status.value}")

    async def record_audio_failure(self, provider: str, service_type: str, error: str):
        """Record a failed audio operation."""
        key = f"{service_type}:{provider}"
        health = self._provider_health.get(key)
        if not health:
            return

        health.last_check = time.time()
        health.last_error = error
        health.consecutive_failures += 1

        old_status = health.status
        if health.consecutive_failures >= 3:
            health.status = AudioProviderStatus.UNAVAILABLE
        elif health.consecutive_failures >= 1:
            health.status = AudioProviderStatus.DEGRADED

        if old_status != health.status:
            logger.warning(f"Audio provider {key} degraded to {health.status.value}: {error}")

    async def queue_failed_upload(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        metadata: Dict[str, Any],
    ):
        """Queue a failed upload for retry.

        When storage is unavailable, uploads are queued and retried
        when connection is restored.
        """
        import base64
        import hashlib

        from admin.core.models import OutboxMessage

        # Create idempotency key
        file_hash = hashlib.sha256(file_data).hexdigest()[:16]
        idempotency_key = f"upload:{filename}:{file_hash}"

        # Store in outbox for retry
        OutboxMessage.objects.create(
            idempotency_key=idempotency_key,
            topic="upload.retry",
            partition_key=filename,
            payload={
                "filename": filename,
                "content_type": content_type,
                "metadata": metadata,
                # Store small files inline, large files reference
                "data_b64": (
                    base64.b64encode(file_data).decode() if len(file_data) < 1024 * 1024 else None
                ),
                "size": len(file_data),
            },
            headers={
                "operation": "upload",
                "retry": "true",
            },
        )

        logger.info(f"Upload queued for retry: {filename}")

    def get_audio_status(self) -> Dict[str, Any]:
        """Get status of all audio providers."""
        return {
            "tts": {
                "primary": self._tts_chain.primary if self._tts_chain else None,
                "current": self._tts_chain.get_current() if self._tts_chain else None,
                "providers": {
                    provider: {
                        "status": health.status.value,
                        "latency_ms": health.latency_ms,
                        "last_error": health.last_error,
                    }
                    for key, health in self._provider_health.items()
                    if key.startswith("tts:")
                    for provider in [key.split(":", 1)[1]]
                },
            },
            "stt": {
                "primary": self._stt_chain.primary if self._stt_chain else None,
                "current": self._stt_chain.get_current() if self._stt_chain else None,
                "providers": {
                    provider: {
                        "status": health.status.value,
                        "latency_ms": health.latency_ms,
                        "last_error": health.last_error,
                    }
                    for key, health in self._provider_health.items()
                    if key.startswith("stt:")
                    for provider in [key.split(":", 1)[1]]
                },
            },
            "storage": {
                "primary": self._storage_chain.primary if self._storage_chain else None,
                "current": self._storage_chain.get_current() if self._storage_chain else None,
                "providers": {
                    provider: {
                        "status": health.status.value,
                        "last_error": health.last_error,
                    }
                    for key, health in self._provider_health.items()
                    if key.startswith("storage:")
                    for provider in [key.split(":", 1)[1]]
                },
            },
        }

    def is_voice_available(self) -> bool:
        """Check if voice services (TTS + STT) are available."""
        tts_available = any(
            h.status != AudioProviderStatus.UNAVAILABLE
            for k, h in self._provider_health.items()
            if k.startswith("tts:")
        )
        stt_available = any(
            h.status != AudioProviderStatus.UNAVAILABLE
            for k, h in self._provider_health.items()
            if k.startswith("stt:")
        )
        return tts_available and stt_available

    def get_voice_degradation_message(self) -> Optional[str]:
        """Get user-friendly message about voice degradation."""
        if not self._initialized:
            return "Voice service initializing..."

        if not self.is_voice_available():
            return "Voice services are temporarily unavailable. Please use text input."

        # Check if on fallback
        tts_current = self._tts_chain.get_current() if self._tts_chain else None
        stt_current = self._stt_chain.get_current() if self._stt_chain else None

        if tts_current != self._tts_chain.primary or stt_current != self._stt_chain.primary:
            return "Voice services running in fallback mode. Quality may vary."

        return None  # All healthy


# Global singleton instance
multimodal_degradation_service = MultimodalDegradationService()


class BackupDegradationService:
    """Backup service degradation handling.

    Manages backup operations with retry and fallback.
    """

    def __init__(self):
        """Initialize the instance."""

        self._initialized = False
        self._backup_queue: List[Dict[str, Any]] = []

    async def queue_backup_task(
        self,
        backup_type: str,
        source: str,
        destination: str,
        metadata: Dict[str, Any],
    ):
        """Queue a backup task for execution."""
        from admin.core.models import OutboxMessage

        OutboxMessage.objects.create(
            idempotency_key=f"backup:{backup_type}:{source}:{int(time.time())}",
            topic="backup.tasks",
            payload={
                "type": backup_type,
                "source": source,
                "destination": destination,
                "metadata": metadata,
                "queued_at": time.time(),
            },
            headers={
                "operation": "backup",
            },
        )

        logger.info(f"Backup task queued: {backup_type} from {source}")


# Global backup service instance
backup_degradation_service = BackupDegradationService()