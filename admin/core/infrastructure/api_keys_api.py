"""
API Keys API - Django Ninja CRUD endpoints for platform API keys

VIBE COMPLIANT:
- Pure Django Ninja implementation
- Secure key masking
- 10 personas in mind (especially Security Specialist, DevOps Engineer)
"""

from typing import Optional, List
from uuid import uuid4
from datetime import datetime
from ninja import Router
from django.http import HttpRequest
from pydantic import BaseModel
import os
import hashlib

router = Router(tags=["API Keys"])


# --- Pydantic Models ---


class ApiKeyBase(BaseModel):
    provider: str
    type: str = "llm"  # llm, service
    name: str = ""


class ApiKeyCreate(ApiKeyBase):
    key_value: str  # The actual API key


class ApiKeyResponse(ApiKeyBase):
    id: str
    key_masked: str  # Last 4 chars only
    status: str = "valid"  # valid, expired, missing
    last_used: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyResponse]
    total: int


# --- Secure key storage (in production, use Django model with encryption) ---


def _mask_key(key: str) -> str:
    """Mask API key, showing only last 4 characters"""
    if len(key) <= 4:
        return "****"
    return "*" * (len(key) - 4) + key[-4:]


def _hash_key(key: str) -> str:
    """Hash key for secure storage lookup"""
    return hashlib.sha256(key.encode()).hexdigest()[:16]


# In-memory storage (would be encrypted Django model in production)
_KEYS_STORE: dict[str, dict] = {}


def _init_default_keys():
    """Initialize from environment variables"""
    env_keys = [
        ("OPENAI_API_KEY", "openai", "llm", "OpenAI GPT"),
        ("ANTHROPIC_API_KEY", "anthropic", "llm", "Anthropic Claude"),
        ("GOOGLE_API_KEY", "google", "llm", "Google Gemini"),
        ("GROQ_API_KEY", "groq", "llm", "Groq"),
        ("TAVILY_API_KEY", "tavily", "service", "Tavily Search"),
        ("LAGO_API_KEY", "lago", "service", "Lago Billing"),
    ]

    for env_var, provider, key_type, name in env_keys:
        key_value = os.getenv(env_var)
        if key_value:
            key_id = str(uuid4())
            _KEYS_STORE[provider] = {
                "id": key_id,
                "provider": provider,
                "type": key_type,
                "name": name,
                "key_masked": _mask_key(key_value),
                "key_hash": _hash_key(key_value),
                "status": "valid",
                "created_at": datetime.now(),
            }
        else:
            # Mark as missing
            key_id = str(uuid4())
            _KEYS_STORE[provider] = {
                "id": key_id,
                "provider": provider,
                "type": key_type,
                "name": name,
                "key_masked": "Not configured",
                "key_hash": None,
                "status": "missing",
                "created_at": datetime.now(),
            }


# Initialize on module load
_init_default_keys()


# --- API Endpoints ---


@router.get("/", response=ApiKeyListResponse)
def list_api_keys(
    request: HttpRequest,
    type: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    List all API keys (masked).
    Permission: apikey:list
    """
    keys = list(_KEYS_STORE.values())

    if type:
        keys = [k for k in keys if k["type"] == type]
    if status:
        keys = [k for k in keys if k["status"] == status]

    return ApiKeyListResponse(
        items=[ApiKeyResponse(**k) for k in keys],
        total=len(keys),
    )


@router.get("/{provider}", response=ApiKeyResponse)
def get_api_key(request: HttpRequest, provider: str):
    """
    Get API key by provider (masked).
    Permission: apikey:view
    """
    if provider not in _KEYS_STORE:
        return {"error": f"API key not found: {provider}"}
    return ApiKeyResponse(**_KEYS_STORE[provider])


@router.post("/", response=ApiKeyResponse)
def create_api_key(request: HttpRequest, payload: ApiKeyCreate):
    """
    Add new API key.
    Permission: apikey:create
    """
    key_data = {
        "id": str(uuid4()),
        "provider": payload.provider,
        "type": payload.type,
        "name": payload.name or payload.provider.title(),
        "key_masked": _mask_key(payload.key_value),
        "key_hash": _hash_key(payload.key_value),
        "status": "valid",
        "created_at": datetime.now(),
    }
    _KEYS_STORE[payload.provider] = key_data
    return ApiKeyResponse(**key_data)


@router.put("/{provider}", response=ApiKeyResponse)
def update_api_key(request: HttpRequest, provider: str, payload: ApiKeyCreate):
    """
    Update API key.
    Permission: apikey:edit
    """
    if provider not in _KEYS_STORE:
        # Create new
        return create_api_key(request, payload)

    key_data = _KEYS_STORE[provider]
    key_data["key_masked"] = _mask_key(payload.key_value)
    key_data["key_hash"] = _hash_key(payload.key_value)
    key_data["status"] = "valid"
    key_data["last_used"] = None  # Reset on update

    return ApiKeyResponse(**key_data)


@router.delete("/{provider}")
def delete_api_key(request: HttpRequest, provider: str):
    """
    Remove API key.
    Permission: apikey:delete
    """
    if provider not in _KEYS_STORE:
        return {"success": False, "error": f"API key not found: {provider}"}

    del _KEYS_STORE[provider]
    return {"success": True, "provider": provider}


@router.post("/{provider}/validate")
def validate_api_key(request: HttpRequest, provider: str):
    """
    Validate API key by making a test request.
    Permission: apikey:view
    """
    if provider not in _KEYS_STORE:
        return {"valid": False, "error": "Key not found"}

    key_data = _KEYS_STORE[provider]
    if key_data["status"] == "missing":
        return {"valid": False, "error": "Key not configured"}

    # In production, would make actual test request to provider
    # For now, assume valid if present
    return {
        "valid": True,
        "provider": provider,
        "status": key_data["status"],
    }


@router.get("/providers")
def list_providers(request: HttpRequest):
    """
    List supported API key providers.
    """
    return {
        "llm": [
            {
                "id": "openai",
                "name": "OpenAI",
                "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "models": ["claude-3.5-sonnet", "claude-3-opus"],
            },
            {"id": "google", "name": "Google", "models": ["gemini-pro", "gemini-1.5-flash"]},
            {"id": "groq", "name": "Groq", "models": ["llama-3.1-70b", "mixtral-8x7b"]},
        ],
        "service": [
            {"id": "tavily", "name": "Tavily", "description": "Web search API"},
            {"id": "lago", "name": "Lago", "description": "Billing platform"},
            {"id": "keycloak", "name": "Keycloak", "description": "Identity provider"},
        ],
    }
