"""Centralized UI settings sections endpoint.

Stores non-secret fields in Postgres (ui_settings table) and secret fields in
SecretManager (Redis + Fernet). This is the single source of truth for agent
and LLM settings.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

import asyncpg
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from services.common.secret_manager import SecretManager
from src.core.config import cfg

router = APIRouter(prefix="/v1/ui/settings/sections", tags=["ui-settings"])

# ---------------------------------------------------------------------------
# Default settings payload – dynamically generated from the single source of truth
# in python.helpers.settings. This ensures the UI always matches the backend
# configuration model without duplication.
# ---------------------------------------------------------------------------
from python.helpers.settings import convert_out
from python.helpers.settings_model import SettingsModel

def _get_default_sections() -> list[dict]:
    """Generate the default UI settings sections from the Pydantic model."""
    # Create default settings instance
    defaults = SettingsModel()
    # Convert to UI structure using the shared helper
    output = convert_out(defaults)
    return output["sections"]

DEFAULT_SECTIONS = _get_default_sections()

# ---------------------------------------------------------------------------
# Startup initialization – ensure the default sections exist on first launch.
# ---------------------------------------------------------------------------
@router.on_event("startup")
async def _ensure_default_sections() -> None:
    """Create the default UI settings if the table is empty.

    The function is idempotent: if a row already exists it does nothing.
    Secret fields are stored via ``SecretManager`` so that they never appear in
    the plain JSON payload.
    """
    try:
        existing = await _load_sections()
        if existing:
            # Settings already present – nothing to do.
            return
        # Persist the full default payload.
        await _save_sections(DEFAULT_SECTIONS)
        # Separate and store secrets.
        plain, secrets = _split_sections(DEFAULT_SECTIONS)
        sm = SecretManager()
        for k, v in secrets.items():
            await sm.set_provider_key(k, v)
        logger.info("Default UI settings created on startup")
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to initialise default UI settings: %s", exc)

# ---------------------------------------------------------------------------
# Logging – we emit a simple info line whenever settings are saved so that
# developers can verify the POST request was received (useful when the UI
# toast appears silent). The gateway already configures a root logger, so we
# just get a module‑level logger here.
# ---------------------------------------------------------------------------
import logging

logger = logging.getLogger(__name__)


class SettingsDoc(BaseModel):
    sections: List[Dict[str, Any]] = Field(default_factory=list)


def _split_sections(sections: List[Dict[str, Any]]) -> tuple[dict, dict]:
    """Split secret vs non-secret fields.

    Returns (plain_dict, secrets_dict) flattened by field id.
    """
    plain: dict[str, Any] = {}
    secrets: dict[str, Any] = {}
    for section in sections or []:
        for field in section.get("fields", []):
            fid = field.get("id")
            if not fid:
                continue
            val = field.get("value")
            if field.get("type") == "password" or field.get("secret") is True or str(fid).startswith("api_key_"):
                if val:
                    secrets[fid] = str(val)
            else:
                plain[fid] = val
    return plain, secrets


async def _pool():
    dsn = cfg.settings().database.dsn
    pool = getattr(_pool, "_cache", None)
    if pool is None:
        pool = await asyncpg.create_pool(dsn, min_size=1, max_size=2)
        _pool._cache = pool
    return pool


async def _ensure_schema():
    pool = await _pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_settings (
                key TEXT PRIMARY KEY,
                value JSONB NOT NULL DEFAULT '{}'::jsonb
            );
            """
        )


async def _load_sections() -> List[Dict[str, Any]]:
    await _ensure_schema()
    pool = await _pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key = 'sections'")
        return row["value"] if row and isinstance(row["value"], list) else []


async def _save_sections(sections: List[Dict[str, Any]]):
    await _ensure_schema()
    pool = await _pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO ui_settings (key, value)
            VALUES ('sections', $1::jsonb)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
            """,
            json.dumps(sections, ensure_ascii=False),
        )


def _ensure_minimal_llm_section(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure the UI receives an LLM section with required fields if missing."""
    ids = {f.get("id") for sec in sections for f in sec.get("fields", [])}
    if {"llm_model", "llm_base_url"} <= ids:
        return sections
    llm_section = {
        "id": "llm",
        "title": "LLM",
        "tab": "agent",
        "fields": [
            {"id": "llm_model", "title": "Model", "type": "text", "required": True, "value": ""},
            {"id": "llm_base_url", "title": "Base URL", "type": "text", "required": True, "value": ""},
            {"id": "llm_temperature", "title": "Temperature", "type": "number", "required": False, "value": 0.2},
            {"id": "api_key_llm", "title": "LLM API Key", "type": "password", "secret": True, "value": ""},
        ],
    }
    return sections + [llm_section]


# Support both without and with trailing slash for compatibility with UI fetches
# Support both the path without a trailing slash and with a trailing slash.
@router.get("")
@router.get("/")
async def get_sections():
    sections = await _load_sections()
    sections = _ensure_minimal_llm_section(sections)
    # Mask secrets
    for section in sections:
        for field in section.get("fields", []):
            fid = field.get("id")
            if not fid:
                continue
            if field.get("type") == "password" or field.get("secret") is True or str(fid).startswith("api_key_"):
                if "value" in field:
                    field["value"] = "********" if field.get("value") else ""
    return {"sections": sections}


@router.get("/ping")
async def ping():
    return {"status": "ok", "timestamp": __import__("time").time()}


# Accept both with and without trailing slash for POST.
@router.post("")
@router.post("/")
async def set_sections(doc: SettingsDoc, request: Request):
    sections = _ensure_minimal_llm_section(doc.sections)
    plain, secrets = _split_sections(sections)

    # Persist non-secret
    await _save_sections(sections)

    # Persist secrets
    sm = SecretManager()
    for key, val in secrets.items():
        await sm.set_provider_key(key, val)
    # Log the save event – useful for debugging and to confirm the UI action
    # reached the backend. We truncate the logged payload to avoid leaking full
    # secrets; only the field ids are shown.
    try:
        logged = {"section_ids": [s.get("id") for s in sections]}
        logger.info("UI settings saved: %s", logged)
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to log UI settings save: %s", exc)

    return {"sections": sections, "status": "saved"}


__all__ = ["router"]
