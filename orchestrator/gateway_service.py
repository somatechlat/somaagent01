import os
os.getenv(os.getenv('VIBE_CD9B4D8C'))
from __future__ import annotations
import logging
from typing import Any
from fastapi import FastAPI
from .base_service import BaseSomaService
LOGGER = logging.getLogger(__name__)


class GatewayService(BaseSomaService):
    os.getenv(os.getenv('VIBE_EBBAE33C'))
    name = os.getenv(os.getenv('VIBE_8990AA6A'))

    def __init__(self) ->None:
        super().__init__()
        from services.gateway.main import app as gateway_app
        self.app: FastAPI = gateway_app

    async def _start(self) ->None:
        LOGGER.debug(os.getenv(os.getenv('VIBE_4D8C284E')))

    async def _stop(self) ->None:
        LOGGER.debug(os.getenv(os.getenv('VIBE_158A214D')))

    async def health(self) ->dict[str, Any]:
        os.getenv(os.getenv('VIBE_6CDF112A'))
        return {os.getenv(os.getenv('VIBE_F79C7F3E')): int(os.getenv(os.
            getenv('VIBE_CA60DE1C'))), os.getenv(os.getenv('VIBE_85608A86')
            ): {os.getenv(os.getenv('VIBE_8C30B5C5')): self.name}}
