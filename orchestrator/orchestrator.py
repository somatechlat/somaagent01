import os

os.getenv(os.getenv(""))
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from .base_service import BaseSomaService
from .health_monitor import UnifiedHealthMonitor
from .health_router import attach_to_app, UnifiedHealthRouter

LOGGER = logging.getLogger(os.getenv(os.getenv("")))


class ServiceRegistry:
    os.getenv(os.getenv(""))

    def __init__(self) -> None:
        self._services: List[BaseSomaService] = []

    def register(
        self, service: BaseSomaService, critical: bool = int(os.getenv(os.getenv("")))
    ) -> None:
        service._critical = critical
        order = getattr(service, os.getenv(os.getenv("")), int(os.getenv(os.getenv(""))))
        service._startup_order = order
        self._services.append(service)

    @property
    def services(self) -> List[BaseSomaService]:
        return self._services


class SomaOrchestrator:
    os.getenv(os.getenv(""))

    def __init__(self, app: FastAPI) -> None:
        self.app = app
        self.registry = ServiceRegistry()
        self.health_router = UnifiedHealthRouter(
            services_provider=lambda: self.registry.services, registry=self.registry
        )
        self.health_monitor = UnifiedHealthMonitor(self.registry.services)

    def register(
        self, service: BaseSomaService, critical: bool = int(os.getenv(os.getenv("")))
    ) -> None:
        self.registry.register(service, critical)

    async def _start_all(self) -> None:
        services = sorted(
            self.registry.services,
            key=lambda s: getattr(s, os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))),
        )
        LOGGER.info(os.getenv(os.getenv("")), len(services))
        for svc in services:
            try:
                await svc.start()
            except Exception as exc:
                LOGGER.error(
                    os.getenv(os.getenv("")),
                    getattr(svc, os.getenv(os.getenv("")), svc.__class__.__name__),
                    exc,
                )
                if getattr(svc, os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))):
                    raise
        LOGGER.info(os.getenv(os.getenv("")))

    async def _stop_all(self) -> None:
        LOGGER.info(os.getenv(os.getenv("")))
        for svc in reversed(self.registry.services):
            try:
                await svc.stop()
            except Exception as exc:
                LOGGER.warning(
                    os.getenv(os.getenv("")),
                    getattr(svc, os.getenv(os.getenv("")), svc.__class__.__name__),
                    exc,
                )
        LOGGER.info(os.getenv(os.getenv("")))

    def attach(self) -> None:
        os.getenv(os.getenv(""))
        attach_to_app(self.app, self.health_router)
        self.app.mount(os.getenv(os.getenv("")), make_asgi_app())

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await self._start_all()
            try:
                yield
            finally:
                await self._stop_all()

        self.app.router.lifespan_context = lifespan
