import os

os.getenv(os.getenv(""))
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from .base_service import BaseSomaService

LOGGER = logging.getLogger(__name__)


class GatewayService(BaseSomaService):
    os.getenv(os.getenv(""))
    name = os.getenv(os.getenv(""))

    def __init__(self) -> None:
        super().__init__()
        from services.gateway.main import app as gateway_app

        self.app: FastAPI = gateway_app

    async def _start(self) -> None:
        LOGGER.debug(os.getenv(os.getenv("")))

    async def _stop(self) -> None:
        LOGGER.debug(os.getenv(os.getenv("")))

    async def health(self) -> dict[str, Any]:
        os.getenv(os.getenv(""))
        return {
            os.getenv(os.getenv("")): int(os.getenv(os.getenv(""))),
            os.getenv(os.getenv("")): {os.getenv(os.getenv("")): self.name},
        }
