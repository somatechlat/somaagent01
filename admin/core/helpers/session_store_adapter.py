"""Session store adapter for agent context persistence.

Provides save_context for the task scheduler to checkpoint agent state.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)


async def save_context(context: Any, reason: Optional[str] = None) -> None:
    """Save agent context to persistent storage.

    Args:
        context: Agent context object
        reason: Reason for the checkpoint

    Raises:
        RuntimeError: Context persistence is not yet implemented.
    """
    raise RuntimeError("Session store adapter save_context is not implemented")
