"""Helper for loading UI settings from the database.

Centralizes logic previously duplicated between gateway and worker services.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

import asyncpg

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


async def load_ui_settings_sections() -> List[Dict[str, Any]]:
    """Fetch and parse the 'sections' key from the ui_settings table."""
    dsn = cfg.settings().database.dsn
    pool_min = cfg.settings().db_pool_min
    pool_max = cfg.settings().db_pool_max

    try:
        async with asyncpg.create_pool(dsn, min_size=pool_min, max_size=pool_max) as pool:
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key='sections'")
                raw = row["value"] if row else []
    except Exception:
        LOGGER.warning("Failed to fetch ui_settings from database", exc_info=True)
        return []

    # Parse JSON string if needed (database may return JSONB as string)
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            LOGGER.warning("Failed to parse ui_settings JSON", exc_info=True)
            return []

    # Handle both storage formats:
    # 1. Dict with "sections" key: {"sections": [{...}]}
    # 2. Plain list: [{...}]
    if isinstance(raw, dict) and "sections" in raw:
        return raw["sections"]
    elif isinstance(raw, list):
        return raw

    return []


async def load_llm_settings() -> Dict[str, Any]:
    """Extract LLM configuration from UI settings sections."""
    sections = await load_ui_settings_sections()

    model = None
    base_url = None
    temperature: float | None = None

    for sec in sections:
        for fld in sec.get("fields", []):
            fid = fld.get("id")
            if not fid:
                continue
            if fid == "llm_model":
                model = fld.get("value")
            elif fid == "llm_base_url":
                base_url = fld.get("value")
            elif fid == "llm_temperature":
                try:
                    temperature = float(fld.get("value"))
                except Exception:
                    temperature = None

    if not model or not base_url:
        raise RuntimeError("LLM settings missing in ui_settings sections (llm_model/llm_base_url)")

    return {"model": model, "base_url": base_url, "temperature": temperature}
