"""Common lifecycle helpers for long‑running worker services.

Provides a minimal `run_service` utility that installs SIGINT/SIGTERM handlers
to trigger cooperative cancellation (task.cancel()) and optionally invokes a
shutdown coroutine for resource cleanup (closing Kafka producers, pools, etc.).

Intent: unify graceful shutdown across workers without introducing heavy
framework dependencies. Keep implementation deliberately small so it is easy
to audit and extend.
"""

from __future__ import annotations

import asyncio
import logging
import signal
from typing import Awaitable, Callable, Optional

from services.common.lifecycle_metrics import now as _lm_now, observe_shutdown as _lm_stop

LOGGER = logging.getLogger(__name__)


def run_service(
    main_coro_factory: Callable[[], Awaitable[None]],
    *,
    service_name: str,
    shutdown_coro: Optional[Callable[[], Awaitable[None]]] = None,
) -> None:
    """Run an async service main coroutine with graceful shutdown.

    Parameters
    ----------
    main_coro_factory: Callable returning the primary `async` coroutine to run.
        Using a factory (instead of passing an already created coroutine) avoids
        accidental reuse between test runs.
    service_name: Stable identifier for logging context.
    shutdown_coro: Optional async callable invoked after cancellation to close
        resources. Executed inside the event loop.
    """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    stop_flag = {"stopping": False}

    def _request_shutdown(signame: str) -> None:  # pragma: no cover (signal path)
        """Execute request shutdown.

            Args:
                signame: The signame.
            """

        if stop_flag["stopping"]:
            return
        stop_flag["stopping"] = True
        LOGGER.info(
            "Signal received; initiating shutdown",
            extra={"service": service_name, "signal": signame},
        )
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):  # pragma: no cover
        try:
            loop.add_signal_handler(sig, _request_shutdown, sig.name)
        except NotImplementedError:
            # Windows may not support all signals; ignore gracefully
            pass

    async def _runner() -> None:
        """Execute runner.
            """

        try:
            await main_coro_factory()
        except asyncio.CancelledError:  # cooperative shutdown
            pass
        except Exception as exc:  # pragma: no cover - unexpected runtime errors
            LOGGER.exception(
                "Service main crashed", extra={"service": service_name, "error": str(exc)}
            )
        finally:
            if shutdown_coro is not None:
                try:
                    ts = _lm_now()
                    await shutdown_coro()
                    _lm_stop(service_name, ts)
                except Exception:
                    LOGGER.debug("Shutdown coroutine failed", exc_info=True)
            LOGGER.info("Service stopped", extra={"service": service_name})

    try:
        loop.run_until_complete(_runner())
    finally:
        try:
            loop.run_until_complete(loop.shutdown_asyncgens())
        except Exception:
            pass
        asyncio.set_event_loop(None)
        loop.close()