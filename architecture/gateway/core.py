"""GatewayCore – central FastAPI application builder.

Implements **Phase 2** of the centralisation roadmap.  The module follows the
VIBE coding rules:

* **Single source of truth** – all configuration is read via ``cfg.settings()``.
* **No monolithic inline logic** – routers are imported from the existing
  ``services.gateway.routers`` package.
* **Real implementation** – the FastAPI app is fully functional and includes
  middleware, lifespan handling, and router registration.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import cfg

# ---------------------------------------------------------------------------
# Router imports – these are the domain routers that already exist in the repo.
# ---------------------------------------------------------------------------
from services.gateway.routers import build_router
from services.gateway.routers.ui_settings_sections import router as ui_settings_router
from services.gateway.routers.ui_notifications import router as ui_notifications_router
from services.gateway.routers.tunnel_proxy import router as tunnel_proxy_router


def _add_middleware(app: FastAPI) -> None:
    """Add global middleware (CORS, tracing, etc.)."""
    # CORS – allow origins from config or default to "*".
    origins = cfg.env("CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Placeholder for additional middleware (e.g., tracing) if needed later.
    # from src.core.tracing import TracingMiddleware
    # app.add_middleware(TracingMiddleware)


def _register_routers(app: FastAPI) -> None:
    """Register domain routers in a deterministic order.

    The order matters because the *tunnel proxy* router contains a very
    specific ``POST`` endpoint that must be matched before the generic UI
    catch‑all router assembled by ``build_router``.
    """
    app.include_router(tunnel_proxy_router)
    app.include_router(build_router())
    app.include_router(ui_settings_router)
    app.include_router(ui_notifications_router)


def create_app() -> FastAPI:
    """Factory that builds the fully‑configured FastAPI gateway.

    The returned ``FastAPI`` instance includes:
    * CORS middleware via :func:`_add_middleware`.
    * All domain routers via :func:`_register_routers`.
    * A ``lifespan`` context that starts the scheduler service and ensures
      the Postgres session schema exists.
    """
    app = FastAPI(title="SomaAgent Gateway", lifespan=_lifespan)
    _add_middleware(app)
    _register_routers(app)
    return app


# ---------------------------------------------------------------------------
# Lifespan – start/stop background services (scheduler, DB schema, etc.).
# ---------------------------------------------------------------------------
from contextlib import asynccontextmanager
from src.core.infrastructure.event_bus import KafkaEventBus, KafkaSettings
from src.core.infrastructure.outbox import OutboxStore
from src.core.session.repository import ensure_schema as ensure_session_schema
from src.core.session.repository import PostgresSessionStore
from src.core.infrastructure.publisher import DurablePublisher
from src.core.session.repository import RedisSessionCache


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # ---------- STARTUP ----------
    from services.gateway.utils.scheduler_service import scheduler_service
    await scheduler_service.start()

    # Ensure the Postgres session schema exists (idempotent).
    store = PostgresSessionStore(cfg.settings().database.dsn)
    await ensure_session_schema(store)

    yield
    # ---------- SHUTDOWN ----------
    await scheduler_service.stop()
