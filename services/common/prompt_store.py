"""Prompt Store for retrieving dynamic prompts from the database.

Retrieves prompts by name from the `prompts` table.
"""

from __future__ import annotations

import logging
from typing import Optional
import asyncpg
from src.core.config import cfg

logger = logging.getLogger(__name__)

class PromptStore:
    """PostgreSQL-backed store for prompts.
    
    Usage:
        store = PromptStore()
        prompt_text = await store.get_prompt("multimodal_critic")
    """

    def __init__(self, dsn: Optional[str] = None) -> None:
        self._dsn = dsn or cfg.settings().database.dsn

    async def get_prompt(self, name: str) -> Optional[str]:
        """Retrieve the latest version of a prompt by name.
        
        Args:
            name: Unique name of the prompt
            
        Returns:
            Prompt content string if found, None otherwise.
        """
        conn = await asyncpg.connect(self._dsn)
        try:
            val = await conn.fetchval(
                "SELECT content FROM prompts WHERE name = $1",
                name
            )
            return val
        except Exception as e:
            logger.error(f"Failed to fetch prompt '{name}': {e}")
            return None
        finally:
            await conn.close()
