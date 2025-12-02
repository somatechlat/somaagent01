"""Thin façade for the SomaBrain client.

All production‑ready logic lives in ``python.integrations.soma_client``. This
module exists only for backward compatibility with imports that expect
``src.core.clients.somabrain``. It re‑exports the concrete client class and its
error type without duplicating any implementation, satisfying the VIBE rule of
*single source of truth*.
"""

from __future__ import annotations

import logging

from python.integrations.soma_client import SomaClient, SomaClientError, SomaMemoryRecord

logger = logging.getLogger(__name__)


class SomaBrainClient(SomaClient):
    """Compatibility alias – retains the historic ``SomaBrainClient`` name."""


__all__ = ["SomaClient", "SomaClientError", "SomaMemoryRecord", "SomaBrainClient"]
