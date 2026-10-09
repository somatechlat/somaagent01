"""
Settings API - Django Ninja endpoints for service configuration


- Pure Django Ninja implementation
- Django ORM for persistence (``InfrastructureConfig`` / ``ServiceHealth``)
- Permission-aware read *and* write — both directions are gated
"""

import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import ServiceError, ValidationError
from admin.common.messages import ErrorCode, get_message
from config.settings_registry import get_settings as get_registry_settings
from services.common import publisher as publisher_mod
from services.common.authorization import authorize
from services.common.secret_policy import (
    assert_no_secret_value,
    is_secret_shaped_key,
)

LOGGER = logging.getLogger("settings_v2")

# Audit topic for settings writes (Kafka, durable publisher).
SETTINGS_CHANGED_TOPIC = "settings.changed"

router = Router(tags=["Settings"])


class SettingsResponse(BaseModel):
    """Settings for a specific service"""

    entity: str
    values: dict
    source: str  # 'database' | 'registry' | 'default'
    last_modified: Optional[str] = None


class SettingsUpdateRequest(BaseModel):
    """Request to update settings"""

    values: dict


class SettingsUpdateResponse(BaseModel):
    """Response for updating settings."""

    success: bool
    entity: str
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Where each value comes from, and why
# ─────────────────────────────────────────────────────────────────────────────
#
# Three stores, and the split is not arbitrary:
#
#   registry   Bootstrap topology. Needed before Django and Postgres exist,
#              so it cannot live in either. Exposed here READ-ONLY: pointing
#              the running stack at a different Postgres from inside Postgres
#              is not a real operation. Changing it is a deploy.
#   database   Everything else — pool sizes, timeouts, retention, model
#              names, integration URLs. Mutable at runtime, so it lives in
#              ``InfrastructureConfig`` where RBAC can gate every read and
#              every write.
#   default    The seed for a database key that has never been written. A
#              declared policy value, not a fallback for missing config.
#
# Secrets appear in none of them. A secret-shaped key stores a Vault *path*
# and ``InfrastructureConfig.save()`` refuses anything else (Rule 164).
#
# ``os.environ`` is not consulted. Rule 100 retired it as a config store.

# entity -> { local_key: {"type", "editable", "default"?, "registry"?, "setting"?} }
#
# `registry` names an attribute on the settings registry instance. A key that
# carries one is topology and is never editable through this API.
#
# `setting` is the canonical UPPER name the rest of the codebase resolves
# through `require_service_url` / `require_setting` (InfrastructureConfig.key).
# Without it the operator layer is written under a local alias the resolver
# never reads, so a UI edit of SOMABRAIN_URL would not repoint the memory lane.
ENTITY_SPECS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "postgresql": {
        "host": {"type": "url", "editable": False, "registry": "postgres_host"},
        "port": {"type": "integer", "editable": False, "registry": "postgres_port"},
        "database": {"type": "string", "editable": False, "registry": "postgres_db"},
        "user": {"type": "string", "editable": False, "registry": "postgres_user"},
        "pool_size": {"type": "integer", "editable": True, "default": 20},
        "max_overflow": {"type": "integer", "editable": True, "default": 10},
        "timeout": {"type": "integer", "editable": True, "default": 30},
    },
    "redis": {
        "url": {"type": "url", "editable": False, "registry": "redis_url"},
        "max_connections": {"type": "integer", "editable": True, "default": 100},
        "ttl_default": {"type": "integer", "editable": True, "default": 3600},
    },
    "kafka": {
        "brokers": {
            "type": "string",
            "editable": False,
            "registry": "kafka_bootstrap_servers",
        },
        "group_id": {"type": "string", "editable": True, "default": "somaagent-group"},
        "auto_offset_reset": {"type": "string", "editable": True, "default": "latest"},
    },
    "temporal": {
        "host": {"type": "string", "editable": False, "registry": "temporal_host"},
        "namespace": {"type": "string", "editable": True, "default": "default"},
        "task_queue": {"type": "string", "editable": True, "default": "soma-tasks"},
        "workflow_timeout": {"type": "integer", "editable": True, "default": 3600},
        "activity_timeout": {"type": "integer", "editable": True, "default": 300},
        "retry_max": {"type": "integer", "editable": True, "default": 3},
    },
    # Keycloak / SomaBrain / Voice are integration endpoints, not bootstrap
    # topology: nothing needs them before the ORM is up. They are therefore
    # ordinary editable settings — which is what makes them RBAC-addressable
    # rather than a deploy. Seeds are empty: a docker hostname in a default is
    # a guessed host the operator never chose (SOMA-STD-CONFIG-001).
    "keycloak": {
        "url": {
            "type": "url",
            "editable": True,
            "default": "",
            "setting": "KEYCLOAK_URL",
        },
        "realm": {"type": "string", "editable": True, "default": "master"},
        "client_id": {"type": "string", "editable": True, "default": ""},
        # The client secret is not here. It lives in Vault; the settings row
        # would hold `secret/agent/credentials/keycloak_client_secret`.
    },
    "somabrain": {
        "url": {
            "type": "url",
            "editable": True,
            "default": "",
            "setting": "SOMABRAIN_URL",
        },
        "namespace": {
            "type": "string",
            "editable": True,
            "default": "",
            "setting": "SOMABRAIN_NAMESPACE",
        },
        "retention_days": {"type": "integer", "editable": True, "default": 365},
        "sleep_interval": {"type": "integer", "editable": True, "default": 21600},
        "consolidation_enabled": {"type": "boolean", "editable": True, "default": True},
    },
    "memory": {
        "url": {
            "type": "url",
            "editable": True,
            "default": "",
            "setting": "SOMAFRACTALMEMORY_URL",
        },
        "recall_top_k": {
            "type": "integer",
            "editable": True,
            "setting": "MEM_RECALL_TOP_K",
        },
        "history_limit": {
            "type": "integer",
            "editable": True,
            "setting": "MEM_HISTORY_LIMIT",
        },
        "similarity_threshold": {
            "type": "number",
            "editable": True,
            "setting": "MEM_SIMILARITY_THRESHOLD",
        },
    },
    "llm": {
        "api_url": {
            "type": "url",
            "editable": True,
            "default": "",
            "setting": "LLM_API_URL",
        },
        "connect_timeout_s": {
            "type": "number",
            "editable": True,
            "setting": "LLM_CONNECT_TIMEOUT_S",
        },
        "read_timeout_s": {
            "type": "number",
            "editable": True,
            "setting": "LLM_READ_TIMEOUT_S",
        },
        "max_retries": {
            "type": "integer",
            "editable": True,
            "setting": "LLM_MAX_RETRIES",
        },
    },
    "agent": {
        "tool_max_iterations": {
            "type": "integer",
            "editable": True,
            "setting": "TOOL_MAX_ITERATIONS",
        },
        "tool_exec_timeout_s": {
            "type": "number",
            "editable": True,
            "setting": "TOOL_EXEC_TIMEOUT_S",
        },
        "tool_result_max_chars": {
            "type": "integer",
            "editable": True,
            "setting": "TOOL_RESULT_MAX_CHARS",
        },
        "login_rate_limit": {
            "type": "integer",
            "editable": True,
            "setting": "LOGIN_RATE_LIMIT",
        },
        "login_rate_window": {
            "type": "integer",
            "editable": True,
            "setting": "LOGIN_RATE_WINDOW",
        },
    },
    "voice": {
        "whisper_url": {
            "type": "url",
            "editable": True,
            "default": "",
            "setting": "WHISPER_URL",
        },
        "whisper_model": {"type": "string", "editable": True, "default": "base"},
        "kokoro_url": {
            "type": "url",
            "editable": True,
            "default": "",
            "setting": "KOKORO_URL",
        },
        "kokoro_voice": {"type": "string", "editable": True, "default": "af_nicole"},
    },
}


def setting_name_for(entity: str, key: str) -> str:
    """InfrastructureConfig.key for one entity field (canonical chain name)."""
    spec = ENTITY_SPECS[entity][key]
    return str(spec.get("setting") or key)


def _registry_value(attr: str) -> Any:
    """Read one topology attribute off the settings registry.

    The registry is the single source for a deployment's shape. Reading it
    here rather than re-declaring the host is what keeps "one place" true.
    """
    return getattr(get_registry_settings(), attr)


def seed_defaults(entity: str) -> Dict[str, Any]:
    """The full declared shape of one entity, before any operator edit.

    Topology keys resolve through the registry; everything else uses its
    declared default. This is what a fresh deployment sees, and it is what
    ``GET`` reports as ``source="default"`` when no row has been written.
    """
    values: Dict[str, Any] = {}
    for key, spec in ENTITY_SPECS[entity].items():
        if "registry" in spec:
            values[key] = _registry_value(spec["registry"])
        else:
            values[key] = spec.get("default")
    return values


# `DEFAULT_SETTINGS` used to be a module-level dict built by reading
# `os.environ` at import time. It is gone: building it here would force a
# registry load — and therefore a Vault round-trip — the moment this module
# is imported. Use `seed_defaults(entity)` when the declared shape is needed.


def get_settings_from_db(entity: str) -> Optional[dict]:
    """Read the operator-written overrides for one entity.

    Returns ``None`` when nothing has been written, which is a real state
    ("use the declared shape"), not an error. A database that cannot be read
    is an error and raises — swallowing it is how "cannot read the store"
    becomes "not configured", and then the stack boots on values nobody chose.

    A secret-shaped key comes back as its Vault *path*, never as a credential
    (Rule 164).
    """
    from admin.core.infrastructure.models import InfrastructureConfig

    spec = ENTITY_SPECS.get(entity, {})
    # Canonical chain name -> local form key.
    by_setting = {
        setting_name_for(entity, local): local for local in spec
    }

    rows = InfrastructureConfig.objects.filter(service__service_name=entity)
    if not rows.exists():
        return None

    out: Dict[str, Any] = {}
    for row in rows:
        assert_no_secret_value(
            row.key, row.value, where=f"InfrastructureConfig({entity}.{row.key})"
        )
        local = by_setting.get(str(row.key), str(row.key))
        out[local] = row.value
    return out


def save_settings_to_db(entity: str, values: dict) -> bool:
    """Persist operator overrides for one entity.

    Every row goes through ``InfrastructureConfig.save()``, which is the
    Rule 164 write gate — a credential here is refused before the DB is
    touched. The check is repeated in this layer so a caller cannot reach
    persistence around the model, and so the failure names the entity.
    """
    from admin.core.infrastructure.models import InfrastructureConfig, ServiceHealth

    for key, value in values.items():
        assert_no_secret_value(key, value, where=f"settings[{entity}].{key}")

    service, _ = ServiceHealth.objects.get_or_create(
        service_name=entity,
        defaults={
            "display_name": entity.replace("_", " ").title(),
            "category": "core",
            "status": "unknown",
        },
    )

    spec = ENTITY_SPECS.get(entity, {})
    for key, value in values.items():
        key_spec = spec.get(key, {})
        # Persist under the canonical chain name so require_service_url /
        # require_setting actually see the operator's edit.
        row_key = setting_name_for(entity, key) if key in spec else key
        row, _created = InfrastructureConfig.objects.get_or_create(
            service=service,
            key=row_key,
            defaults={
                "value": "" if value is None else str(value),
                "default_value": str(key_spec.get("default", "")),
                "is_secret": is_secret_shaped_key(row_key),
                "is_editable": bool(key_spec.get("editable", True)),
                "value_type": key_spec.get("type", "string"),
            },
        )
        if not _created:
            if not row.is_editable:
                raise ValidationError(
                    get_message(
                        ErrorCode.VALIDATION_ERROR,
                        details=f"{entity}.{key} is topology and is not editable at runtime",
                    ),
                    details={"entity": entity, "key": key},
                )
            row.value = "" if value is None else str(value)
            row.save()
    return True


@router.get("/{entity}", response=SettingsResponse, auth=AuthBearer())
async def get_settings(request: HttpRequest, entity: str):
    """
    Get settings for a service entity.

    Gated: configuration is not public. Reads and writes both go through
    ``authorize()``, so a principal who may not see a service's shape cannot
    probe it here.

    ``auth=AuthBearer()`` is load-bearing: ``authorize()`` reads roles from
    ``request.auth``, and Django Ninja only sets it when the route carries an
    auth callback. Without one every caller — a sysadmin included — reaches the
    gate as a principal with no roles and is denied 403.
    """
    await authorize(request, action="system:view", resource="settings")

    if entity not in ENTITY_SPECS:
        raise ValidationError(
            get_message(ErrorCode.VALIDATION_ERROR, details=f"Unknown entity: {entity}"),
            details={"entity": entity},
        )

    defaults = seed_defaults(entity)
    # sync_to_async: these views are async, Django's ORM is not. Reaching for
    # the ORM directly here raises SynchronousOnlyOperation rather than
    # blocking the loop, which is the failure this wrapper exists to avoid.
    db_settings = await sync_to_async(get_settings_from_db)(entity)
    if db_settings is not None:
        return SettingsResponse(
            entity=entity,
            values={**defaults, **db_settings},
            source="database",
        )

    # Nothing written yet — the declared shape. `source` says which, so the
    # caller can tell "operator chose this" from "nobody has chosen yet".
    topology_only = all("registry" in s for s in ENTITY_SPECS[entity].values())
    return SettingsResponse(
        entity=entity,
        values=defaults,
        source="registry" if topology_only else "default",
    )


@router.put(
    "/{entity}",
    response=SettingsUpdateResponse,
    summary="Update service settings",
    auth=AuthBearer(),
)
async def update_settings(request: HttpRequest, entity: str, payload: SettingsUpdateRequest):
    """
    Update settings for a service entity.

    Every write is OPA-gated (fail-closed: an evaluation error denies) and
    emits a ``settings.changed`` audit event through the durable publisher.
    """
    # Gate first — no unauthenticated probing of validation errors.
    await authorize(request, action="system:configure", resource="settings")

    # Validate entity
    if entity not in ENTITY_SPECS:
        raise ValidationError(
            get_message(ErrorCode.VALIDATION_ERROR, details=f"Unknown entity: {entity}"),
            details={"entity": entity},
        )

    spec = ENTITY_SPECS[entity]
    for key in payload.values:
        if key in spec and not spec[key].get("editable", True):
            raise ValidationError(
                get_message(
                    ErrorCode.VALIDATION_ERROR,
                    details=(
                        f"{entity}.{key} is deployment topology. It is readable "
                        f"here but changes with a deploy, not a request."
                    ),
                ),
                details={"entity": entity, "key": key},
            )

    # Only the operator's keys are written. The declared shape is the seed
    # a reader merges in; persisting it too would overwrite a registry change
    # with a snapshot taken at some earlier request.
    if not await sync_to_async(save_settings_to_db)(entity, payload.values):
        raise ServiceError(
            get_message(ErrorCode.INTERNAL_ERROR),
            details={"entity": entity},
        )

    # Audit event — the save is committed; a broker outage must not flip the
    # result to failure. The durable publisher owns retries.
    await _emit_settings_changed(request, entity, list(payload.values.keys()))

    return SettingsUpdateResponse(
        success=True, entity=entity, message="Settings saved"
    )


async def _emit_settings_changed(request: HttpRequest, entity: str, changed_keys: list) -> None:
    """Publish the settings.changed audit event; never fail the write on outage."""
    tenant = request.headers.get("X-Tenant-Id", "default")
    event = {
        "type": "settings.changed",
        "entity": entity,
        "changed_keys": changed_keys,
        "tenant": tenant,
    }
    try:
        publisher = await publisher_mod.get_durable_publisher()
        if publisher is None:
            LOGGER.error(
                "settings.changed not emitted: durable publisher unavailable",
                extra={"entity": entity, "tenant": tenant},
            )
            return
        await publisher.publish(SETTINGS_CHANGED_TOPIC, event, tenant=tenant)
    except Exception as exc:
        LOGGER.error(
            "settings.changed emit failed after successful save",
            extra={"entity": entity, "tenant": tenant, "error": str(exc)},
        )


ENTITY_META: Dict[str, Dict[str, str]] = {
    "postgresql": {"name": "PostgreSQL", "icon": "database"},
    "redis": {"name": "Redis", "icon": "bolt"},
    "kafka": {"name": "Kafka", "icon": "mail"},
    "temporal": {"name": "Temporal", "icon": "schedule"},
    "keycloak": {"name": "Keycloak", "icon": "lock"},
    "somabrain": {"name": "SomaBrain", "icon": "neurology"},
    "memory": {"name": "Memory", "icon": "psychology"},
    "llm": {"name": "LLM Gateway", "icon": "smart_toy"},
    "agent": {"name": "Agent", "icon": "settings_suggest"},
    "voice": {"name": "Voice Services", "icon": "mic"},
}


class FieldSchema(BaseModel):
    """One editable setting, as the form must render it."""

    key: str
    setting: str
    label: str
    type: str
    editable: bool
    description: str = ""


class EntitySchema(BaseModel):
    """Server-owned form shape for one entity. The UI never invents fields."""

    entity: str
    name: str
    icon: str
    fields: list[FieldSchema]


def _label_for(local: str) -> str:
    """Human label from the field key. Formatting, not a lookup table."""
    return local.replace("_", " ").strip().capitalize()


@router.get("/schema/{entity}", response=EntitySchema, auth=AuthBearer())
async def get_entity_schema(request: HttpRequest, entity: str):
    """Field catalog for one entity — the lookup table lives here, not in TS."""
    await authorize(request, action="system:view", resource="settings")
    if entity not in ENTITY_SPECS:
        raise ValidationError(
            get_message(ErrorCode.VALIDATION_ERROR, details=f"Unknown entity: {entity}"),
            details={"entity": entity},
        )
    meta = ENTITY_META.get(entity, {"name": entity, "icon": "settings"})
    fields = [
        FieldSchema(
            key=local,
            setting=setting_name_for(entity, local),
            label=_label_for(local),
            type=str(spec.get("type", "string")),
            editable=bool(spec.get("editable", True)),
            description=str(spec.get("description", "")),
        )
        for local, spec in ENTITY_SPECS[entity].items()
    ]
    return EntitySchema(
        entity=entity, name=meta["name"], icon=meta["icon"], fields=fields
    )


@router.get("/", response=list, auth=AuthBearer())
async def list_services(request: HttpRequest):
    """List all configurable services.

    Gated like every other settings surface — the inventory of what the
    platform is wired to is itself configuration. The list is derived from
    ENTITY_SPECS so a new entity cannot be missing from the UI.
    """
    await authorize(request, action="system:view", resource="settings")
    return [
        {
            "entity": entity,
            "name": ENTITY_META.get(entity, {}).get("name", entity),
            "icon": ENTITY_META.get(entity, {}).get("icon", "settings"),
        }
        for entity in ENTITY_SPECS
    ]
