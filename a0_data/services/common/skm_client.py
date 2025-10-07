"""SomaKamachiq client stubs.

These functions provide typed placeholders for future SomaKamachiq (SKM)
APIs. They do not perform any network operations yet but capture the
request/response structure so the conversation worker can emit progress
and provisioning hooks without introducing mocks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class ProgressPayload:
    session_id: str
    persona_id: Optional[str]
    status: str
    detail: str
    metadata: dict[str, Any]


class SKMClient:
    """Placeholder client. Extend when SKM endpoints are available."""

    def __init__(self) -> None:
        self.enabled = False  # flip to True once SKM endpoints exist

    async def publish_progress(self, payload: ProgressPayload) -> None:
        if not self.enabled:
            LOGGER.debug("SKM publish skipped", extra={"status": payload.status})
            return
        # Insert real HTTP calls once SKM is deployed.
        raise NotImplementedError("SKM integration not implemented yet")

    async def close(self) -> None:
        return
