"""Secrets API — Vault-backed LLM provider keys (write-only).

MD-04: Per-provider key vault. Keys are never echoed back.
Path in Vault: secret/agent/api_keys/{provider}_api_key
Uses UnifiedSecretManager (HashiCorp Vault) — VIBE Rule 164.
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from admin.common.auth import AuthBearer

logger = logging.getLogger(__name__)
router = Router(tags=["secrets"])


class ProviderKeyStatus(Schema):
    """Key presence only. Never includes key material."""

    provider: str
    configured: bool


class ProviderKeyWrite(Schema):
    """Write-only API key body. The value is never returned."""

    api_key: str


class ProviderKeyWriteResult(Schema):
    """Result of a key write."""

    provider: str
    configured: bool
    saved: bool
    detail: str = ""


def _sm():
    from services.common.unified_secret_manager import get_secret_manager

    return get_secret_manager()


def _validate_provider(provider: str) -> str:
    pid = provider.strip().lower()
    if not pid or not pid.replace("-", "").replace("_", "").isalnum():
        raise HttpError(400, f"invalid_provider_id: {provider}")
    return pid


@router.get(
    "/providers",
    response=list[ProviderKeyStatus],
    auth=AuthBearer(),
    summary="List provider key status",
)
def list_provider_keys(request) -> list[ProviderKeyStatus]:
    """Which providers have keys in Vault. Never returns key material."""
    sm = _sm()
    # Known + whatever list_providers can see
    known = ["openai", "anthropic", "google", "groq", "ollama", "custom", "openrouter", "fireworks"]
    seen: set[str] = set()
    result: list[ProviderKeyStatus] = []
    for pid in known:
        seen.add(pid)
        result.append(ProviderKeyStatus(provider=pid, configured=bool(sm.get_provider_key(pid))))
    for pid in sm.list_providers():
        if pid not in seen:
            result.append(ProviderKeyStatus(provider=pid, configured=True))
    return result


@router.put(
    "/providers/{provider}",
    response=ProviderKeyWriteResult,
    auth=AuthBearer(),
    summary="Set provider API key (write-only)",
)
def set_provider_key(request, provider: str, body: ProviderKeyWrite) -> ProviderKeyWriteResult:
    """Store API key in Vault. Request and response never echo the key."""
    pid = _validate_provider(provider)
    if not body.api_key or not body.api_key.strip():
        raise HttpError(400, "api_key_required")
    try:
        sm = _sm()
        saved = sm.set_provider_key(pid, body.api_key.strip())
    except Exception as exc:
        logger.error("Failed to save provider key for %s", pid, exc_info=True)
        return ProviderKeyWriteResult(
            provider=pid,
            configured=False,
            saved=False,
            detail=f"vault_error: {exc}",
        )
    return ProviderKeyWriteResult(
        provider=pid,
        configured=saved,
        saved=saved,
        detail="saved_to_vault" if saved else "vault_unavailable",
    )


@router.delete(
    "/providers/{provider}",
    response=ProviderKeyWriteResult,
    auth=AuthBearer(),
    summary="Delete provider API key",
)
def delete_provider_key(request, provider: str) -> ProviderKeyWriteResult:
    """Remove provider key from Vault."""
    pid = _validate_provider(provider)
    try:
        sm = _sm()
        deleted = sm.delete_provider_key(pid)
        configured = bool(sm.get_provider_key(pid))
    except Exception as exc:
        logger.error("Failed to delete provider key for %s", pid, exc_info=True)
        return ProviderKeyWriteResult(
            provider=pid,
            configured=False,
            saved=False,
            detail=f"vault_error: {exc}",
        )
    return ProviderKeyWriteResult(
        provider=pid,
        configured=configured,
        saved=deleted,
        detail="deleted" if deleted else "delete_failed",
    )


@router.get(
    "/providers/{provider}",
    response=ProviderKeyStatus,
    auth=AuthBearer(),
    summary="Get provider key status",
)
def get_provider_key_status(request, provider: str) -> ProviderKeyStatus:
    """Configured flag only. Never returns key material."""
    pid = _validate_provider(provider)
    try:
        configured = bool(_sm().get_provider_key(pid))
    except Exception:
        configured = False
    return ProviderKeyStatus(provider=pid, configured=configured)
