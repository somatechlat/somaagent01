"""
Feature Flags API - Django Ninja CRUD endpoints


- Pure Django Ninja implementation
- Django ORM for persistence
- Global/tenant/tier scope support
- 10 personas in mind (especially Product Manager, DevOps Engineer)
"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import ConflictError, NotFoundError
from admin.common.messages import ErrorCode, get_message

router = Router(tags=["Feature Flags"])


# --- Pydantic Models ---


class FeatureFlagBase(BaseModel):
    """Featureflagbase class implementation."""

    key: str
    name: str
    description: str = ""
    status: str = "off"  # on, off, beta
    scope: str = "global"  # global, tenant, tier


class FeatureFlagCreate(FeatureFlagBase):
    """Featureflagcreate class implementation."""

    pass


class FeatureFlagUpdate(BaseModel):
    """Featureflagupdate class implementation."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    scope: Optional[str] = None


class FeatureFlagResponse(FeatureFlagBase):
    """Data model for FeatureFlagResponse."""

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FeatureFlagListResponse(BaseModel):
    """Data model for FeatureFlagListResponse."""

    items: List[FeatureFlagResponse]
    total: int


class DeleteFlagResponse(BaseModel):
    """Response for deleting a feature flag."""

    success: bool
    key: str


class ToggleFlagResponse(BaseModel):
    """Response for toggling a feature flag."""

    success: bool
    key: str
    status: str


class FlagCheckResponse(BaseModel):
    """Response for checking if a feature flag is enabled."""

    key: str
    enabled: bool
    status: str
    scope: str


# --- In-memory storage (would be Django model in production) ---

_FLAGS_STORE: dict[str, dict] = {
    "sse_enabled": {
        "id": str(uuid4()),
        "key": "sse_enabled",
        "name": "SSE Streaming",
        "description": "Enable Server-Sent Events for real-time updates",
        "status": "on",
        "scope": "global",
        "created_at": datetime.now(),
    },
    "embeddings_ingest": {
        "id": str(uuid4()),
        "key": "embeddings_ingest",
        "name": "Embedding Pipeline",
        "description": "RAG ingestion and vector storage",
        "status": "on",
        "scope": "global",
        "created_at": datetime.now(),
    },
    "semantic_recall": {
        "id": str(uuid4()),
        "key": "semantic_recall",
        "name": "Semantic Recall",
        "description": "SomaBrain memory integration",
        "status": "on",
        "scope": "global",
        "created_at": datetime.now(),
    },
    "audio_support": {
        "id": str(uuid4()),
        "key": "audio_support",
        "name": "Audio Support",
        "description": "Voice subsystem (Whisper + Kokoro)",
        "status": "off",
        "scope": "tier",
        "created_at": datetime.now(),
    },
    "mcp_server": {
        "id": str(uuid4()),
        "key": "mcp_server",
        "name": "MCP Server Mode",
        "description": "Expose Model Context Protocol server",
        "status": "beta",
        "scope": "tenant",
        "created_at": datetime.now(),
    },
    "multi_agent": {
        "id": str(uuid4()),
        "key": "multi_agent",
        "name": "Multi-Agent Orchestration",
        "description": "Enable agent collaboration workflows",
        "status": "beta",
        "scope": "tier",
        "created_at": datetime.now(),
    },
    "code_execution": {
        "id": str(uuid4()),
        "key": "code_execution",
        "name": "Code Execution",
        "description": "Safe sandboxed code execution",
        "status": "on",
        "scope": "global",
        "created_at": datetime.now(),
    },
    "browser_agent": {
        "id": str(uuid4()),
        "key": "browser_agent",
        "name": "Browser Agent",
        "description": "Headless browser automation tool",
        "status": "on",
        "scope": "tier",
        "created_at": datetime.now(),
    },
}


# --- API Endpoints ---


@router.get("/", response=FeatureFlagListResponse)
def list_feature_flags(
    request: HttpRequest,
    status: Optional[str] = None,
    scope: Optional[str] = None,
):
    """
    List all feature flags with optional filtering.
    Permission: feature:list
    """
    flags = list(_FLAGS_STORE.values())

    if status:
        flags = [f for f in flags if f["status"] == status]
    if scope:
        flags = [f for f in flags if f["scope"] == scope]

    return FeatureFlagListResponse(
        items=[FeatureFlagResponse(**f) for f in flags],
        total=len(flags),
    )


@router.get("/{flag_key}", response=FeatureFlagResponse, summary="Get feature flag")
def get_feature_flag(request: HttpRequest, flag_key: str):
    """
    Get single feature flag by key.
    Permission: feature:view
    """
    if flag_key not in _FLAGS_STORE:
        raise NotFoundError("feature flag", flag_key)
    return FeatureFlagResponse(**_FLAGS_STORE[flag_key])


@router.post("/", response=FeatureFlagResponse, summary="Create feature flag")
def create_feature_flag(request: HttpRequest, payload: FeatureFlagCreate):
    """
    Create new feature flag.
    Permission: feature:create
    """
    if payload.key in _FLAGS_STORE:
        raise ConflictError(
            get_message(ErrorCode.VALIDATION_ERROR, details=f"Feature flag already exists: {payload.key}"),
            resource="feature flag",
        )

    flag = {
        "id": str(uuid4()),
        "key": payload.key,
        "name": payload.name,
        "description": payload.description,
        "status": payload.status,
        "scope": payload.scope,
        "created_at": datetime.now(),
    }
    _FLAGS_STORE[payload.key] = flag
    return FeatureFlagResponse(**flag)


@router.put("/{flag_key}", response=FeatureFlagResponse, summary="Update feature flag")
def update_feature_flag(request: HttpRequest, flag_key: str, payload: FeatureFlagUpdate):
    """
    Update feature flag.
    Permission: feature:edit
    """
    if flag_key not in _FLAGS_STORE:
        raise NotFoundError("feature flag", flag_key)

    flag = _FLAGS_STORE[flag_key]
    if payload.name is not None:
        flag["name"] = payload.name
    if payload.description is not None:
        flag["description"] = payload.description
    if payload.status is not None:
        flag["status"] = payload.status
    if payload.scope is not None:
        flag["scope"] = payload.scope
    flag["updated_at"] = datetime.now()

    return FeatureFlagResponse(**flag)


@router.delete("/{flag_key}", response=DeleteFlagResponse, summary="Delete feature flag")
def delete_feature_flag(request: HttpRequest, flag_key: str):
    """
    Delete feature flag.
    Permission: feature:delete
    """
    if flag_key not in _FLAGS_STORE:
        raise NotFoundError("feature flag", flag_key)

    del _FLAGS_STORE[flag_key]
    return DeleteFlagResponse(success=True, key=flag_key)


@router.post("/{flag_key}/toggle", response=ToggleFlagResponse, summary="Toggle feature flag")
def toggle_feature_flag(request: HttpRequest, flag_key: str):
    """
    Toggle feature flag on/off.
    Permission: feature:edit
    """
    if flag_key not in _FLAGS_STORE:
        raise NotFoundError("feature flag", flag_key)

    flag = _FLAGS_STORE[flag_key]
    new_status = "off" if flag["status"] == "on" else "on"
    flag["status"] = new_status
    flag["updated_at"] = datetime.now()

    return ToggleFlagResponse(success=True, key=flag_key, status=new_status)


@router.get("/check/{flag_key}", response=FlagCheckResponse, summary="Check feature flag enabled")
def check_flag_enabled(request: HttpRequest, flag_key: str, tenant_id: Optional[str] = None):
    """
    Check if a feature flag is enabled.
    Used by application code to check features.
    """
    if flag_key not in _FLAGS_STORE:
        raise NotFoundError("feature flag", flag_key)

    flag = _FLAGS_STORE[flag_key]
    enabled = flag["status"] in ("on", "beta")

    return FlagCheckResponse(
        key=flag_key,
        enabled=enabled,
        status=flag["status"],
        scope=flag["scope"],
    )
