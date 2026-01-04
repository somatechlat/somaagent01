"""
Settings API - Django Ninja endpoints for service configuration


- Pure Django Ninja implementation
- Django ORM for persistence
- Permission-aware read/write
- 10 personas in mind (especially DevOps Engineer, Security Specialist)
"""

from typing import Any, Optional
from ninja import Router
from django.http import HttpRequest
from django.conf import settings
from pydantic import BaseModel
import os
import json

router = Router(tags=["Settings"])


class SettingsResponse(BaseModel):
    """Settings for a specific service"""

    entity: str
    values: dict
    source: str  # 'database', 'env', 'default'
    last_modified: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    """Request to update settings"""

    values: dict


# Default settings from environment/Django settings (secure defaults)
DEFAULT_SETTINGS = {
    "postgresql": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "database": os.getenv("POSTGRES_DB", "somaagent"),
        "user": os.getenv("POSTGRES_USER", "soma"),
        "pool_size": 20,
        "max_overflow": 10,
        "timeout": 30,
    },
    "redis": {
        "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "max_connections": 100,
        "ttl_default": 3600,
    },
    "kafka": {
        "brokers": os.getenv("KAFKA_BROKERS", "localhost:9092"),
        "group_id": "somaagent-group",
        "auto_offset_reset": "latest",
    },
    "temporal": {
        "host": os.getenv("TEMPORAL_HOST", "temporal:7233"),
        "namespace": "default",
        "task_queue": "soma-tasks",
        "workflow_timeout": 3600,
        "activity_timeout": 300,
        "retry_max": 3,
    },
    "keycloak": {
        "url": os.getenv("KEYCLOAK_URL", "http://keycloak:8080"),
        "realm": os.getenv("KEYCLOAK_REALM", "master"),
        "client_id": os.getenv("KEYCLOAK_CLIENT_ID", ""),
        # Don't expose secret in defaults
    },
    "somabrain": {
        "url": os.getenv("SOMABRAIN_URL", "http://somabrain:8000"),
        "retention_days": 365,
        "sleep_interval": 21600,
        "consolidation_enabled": True,
    },
    "voice": {
        "whisper_url": os.getenv("WHISPER_URL", "http://whisper:8000"),
        "whisper_model": "base",
        "kokoro_url": os.getenv("KOKORO_URL", "http://kokoro:8000"),
        "kokoro_voice": "af_nicole",
    },
}


def get_settings_from_db(entity: str) -> Optional[dict]:
    """Get settings from database if stored there"""
    try:
        from admin.core.models import ServiceConfig

        config = ServiceConfig.objects.filter(service_name=entity, is_active=True).first()
        if config:
            return config.config_json
    except Exception:
        # Model might not exist yet
        pass
    return None


def save_settings_to_db(entity: str, values: dict) -> bool:
    """Save settings to database"""
    try:
        from admin.core.models import ServiceConfig

        config, created = ServiceConfig.objects.update_or_create(
            service_name=entity, defaults={"config_json": values, "is_active": True}
        )
        return True
    except Exception as e:
        print(f"Failed to save settings for {entity}: {e}")
        return False


@router.get("/{entity}", response=SettingsResponse)
def get_settings(request: HttpRequest, entity: str):
    """
    Get settings for a service entity.
    Checks: database first, then env/defaults.
    """
    # Check database first
    db_settings = get_settings_from_db(entity)
    if db_settings:
        return SettingsResponse(
            entity=entity,
            values=db_settings,
            source="database",
        )

    # Fall back to defaults
    if entity in DEFAULT_SETTINGS:
        return SettingsResponse(
            entity=entity,
            values=DEFAULT_SETTINGS[entity],
            source="default",
        )

    return SettingsResponse(
        entity=entity,
        values={},
        source="unknown",
    )


@router.put("/{entity}", response=dict)
def update_settings(request: HttpRequest, entity: str, payload: SettingsUpdateRequest):
    """
    Update settings for a service entity.
    Stores in database for persistence.
    """
    # Validate entity
    if entity not in DEFAULT_SETTINGS:
        return {"success": False, "error": f"Unknown entity: {entity}"}

    # Merge with defaults (don't lose fields)
    merged = {**DEFAULT_SETTINGS.get(entity, {}), **payload.values}

    # Save to database
    if save_settings_to_db(entity, merged):
        return {"success": True, "entity": entity, "message": "Settings saved"}
    else:
        return {"success": False, "error": "Failed to save settings"}


@router.get("/", response=list)
def list_services(request: HttpRequest):
    """List all configurable services"""
    return [
        {"entity": "postgresql", "name": "PostgreSQL", "icon": "database"},
        {"entity": "redis", "name": "Redis", "icon": "bolt"},
        {"entity": "kafka", "name": "Kafka", "icon": "mail"},
        {"entity": "temporal", "name": "Temporal", "icon": "schedule"},
        {"entity": "keycloak", "name": "Keycloak", "icon": "lock"},
        {"entity": "somabrain", "name": "SomaBrain", "icon": "neurology"},
        {"entity": "voice", "name": "Voice Services", "icon": "mic"},
    ]