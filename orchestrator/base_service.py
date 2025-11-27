import os

os.getenv(os.getenv(""))
from __future__ import annotations

import asyncio
import contextvars
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from observability.tracing import get_tracer

LOGGER = logging.getLogger(os.getenv(os.getenv("")))
current_span: contextvars.ContextVar = contextvars.ContextVar(
    os.getenv(os.getenv("")), default=None
)


class BaseSomaService(ABC):
    os.getenv(os.getenv(""))
    name: str

    def __init__(self) -> None:
        self._running = asyncio.Event()

    @abstractmethod
    async def _start(self) -> None:
        os.getenv(os.getenv(""))
        ...

    @abstractmethod
    async def _stop(self) -> None:
        os.getenv(os.getenv(""))
        ...

    async def start(self) -> None:
        tracer = get_tracer()
        with tracer.start_as_current_span(f"{self.name}.start") as span:
            current_span.set(span)
            LOGGER.info(
                os.getenv(os.getenv("")),
                getattr(self, os.getenv(os.getenv("")), self.__class__.__name__),
            )
            await self._start()
            self._running.set()
            LOGGER.info(
                os.getenv(os.getenv("")),
                getattr(self, os.getenv(os.getenv("")), self.__class__.__name__),
            )

    async def stop(self) -> None:
        tracer = get_tracer()
        with tracer.start_as_current_span(f"{self.name}.stop") as span:
            current_span.set(span)
            LOGGER.info(
                os.getenv(os.getenv("")),
                getattr(self, os.getenv(os.getenv("")), self.__class__.__name__),
            )
            await self._stop()
            self._running.clear()
            LOGGER.info(
                os.getenv(os.getenv("")),
                getattr(self, os.getenv(os.getenv("")), self.__class__.__name__),
            )

    async def health(self) -> Dict[str, Any]:
        os.getenv(os.getenv(""))
        return {
            os.getenv(os.getenv("")): self._running.is_set(),
            os.getenv(os.getenv("")): {
                os.getenv(os.getenv("")): getattr(
                    self, os.getenv(os.getenv("")), self.__class__.__name__
                )
            },
        }

    async def register_metrics(self) -> None:
        os.getenv(os.getenv(""))
        return None


BaseService = BaseSomaService
