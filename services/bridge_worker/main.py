"""BridgeWorker — long-running poll/dispatch loop (WP D3/D4).

Pattern: ``services/conversation_worker/main.py`` (Django setup → service loop).

Per A0 ``extensions/python/job_loop/_10_wa_poll.py``:
- poll every ``poll_interval_seconds`` (default 3s, min 2s)
- consecutive-failure circuit (5) before parking a channel
- feature flag + Channel.status gates each iteration (fail-closed)

Channels of kind ``whatsapp`` (BR-01) and ``telegram`` (BR-02) are both
served by this loop; each kind is gated by its own feature flag.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Set

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()  # noqa: E402 — required before ORM imports

from services.bridge_worker.dispatcher import (  # noqa: E402
    BridgeDispatcher,
    is_bridge_enabled,
    is_telegram_bridge_enabled,
    is_whatsapp_bridge_enabled,
)
from services.bridge_worker.drivers.base import InboundEnvelope  # noqa: E402
from services.bridge_worker.drivers.telegram import build_telegram_driver  # noqa: E402
from services.bridge_worker.drivers.whatsapp import build_whatsapp_driver  # noqa: E402

logger = logging.getLogger(__name__)

# A0 job_loop defaults: DEFAULT_INTERVAL=3, MIN_INTERVAL=2, MAX_CONSECUTIVE_FAILURES=5
DEFAULT_POLL_INTERVAL = 3
MIN_POLL_INTERVAL = 2
MAX_CONSECUTIVE_FAILURES = 5
CHANNEL_REFRESH_SECONDS = float(os.environ.get("SA01_BRIDGE_CHANNEL_REFRESH", "30"))

# Channel kinds this worker serves (each with its own feature flag).
SERVED_KINDS = ("whatsapp", "telegram")


class _ChannelRuntime:
    """Per-Channel driver + dispatcher runtime state."""

    def __init__(self, channel: Any):
        self.channel_id = str(channel.id)
        self.channel = channel
        self.driver: Optional[Any] = None
        self.dispatcher: Optional[BridgeDispatcher] = None
        self.failures = 0
        self.poll_interval = DEFAULT_POLL_INTERVAL

    def matches(self, channel: Any) -> bool:
        return str(channel.id) == self.channel_id

    async def close(self) -> None:
        if self.driver is not None:
            try:
                await self.driver.stop()
            except Exception:  # noqa: BLE001
                logger.debug("driver stop failed for %s", self.channel_id, exc_info=True)
        self.driver = None
        self.dispatcher = None


class BridgeWorker:
    """Long-running bridge worker: poll → dispatch → reply."""

    def __init__(self) -> None:
        self._runtimes: Dict[str, _ChannelRuntime] = {}
        self._stop = asyncio.Event()
        self._stop.set()  # not started yet — start() clears it

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> None:
        """Run until stop() is called. Entry point for main/service."""
        self._stop.clear()
        logger.info(
            "BridgeWorker starting (bridge_whatsapp=%s bridge_telegram=%s)",
            is_whatsapp_bridge_enabled(),
            is_telegram_bridge_enabled(),
        )
        last_channel_refresh = 0.0
        try:
            while not self._stop.is_set():
                if not self._enabled_kinds():
                    # Fail-closed: tear down any running drivers and idle.
                    await self._close_all()
                    await self._sleep(CHANNEL_REFRESH_SECONDS)
                    continue

                now = asyncio.get_event_loop().time()
                if now - last_channel_refresh >= CHANNEL_REFRESH_SECONDS:
                    await self._refresh_channels()
                    last_channel_refresh = now

                if not self._runtimes:
                    await self._sleep(CHANNEL_REFRESH_SECONDS)
                    continue

                tasks = [
                    asyncio.create_task(self._poll_channel(rt))
                    for rt in list(self._runtimes.values())
                ]
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                min_interval = min(
                    (rt.poll_interval for rt in self._runtimes.values()),
                    default=DEFAULT_POLL_INTERVAL,
                )
                await self._sleep(max(min_interval, MIN_POLL_INTERVAL))
        finally:
            await self._close_all()
            logger.info("BridgeWorker stopped")

    async def stop(self) -> None:
        self._stop.set()

    async def _sleep(self, seconds: float) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=max(seconds, 0.5))
        except asyncio.TimeoutError:
            return

    async def _close_all(self) -> None:
        for rt in list(self._runtimes.values()):
            await rt.close()
        self._runtimes.clear()

    # -- channel discovery -------------------------------------------------

    def _enabled_kinds(self) -> Set[str]:
        """Channel kinds whose feature flag is on (per-kind, fail-closed)."""
        return {kind for kind in SERVED_KINDS if is_bridge_enabled(kind)}

    async def _refresh_channels(self) -> None:
        from asgiref.sync import sync_to_async

        enabled = self._enabled_kinds()

        @sync_to_async
        def _load(kinds: tuple) -> List[Any]:
            from admin.bridges.models import Channel

            return list(
                Channel.objects.filter(
                    kind__in=list(kinds),
                    status=Channel.STATUS_ACTIVE,
                )
                .select_related("tenant", "capsule")
                .order_by("-created_at")
            )

        try:
            channels = await _load(tuple(enabled)) if enabled else []
        except Exception:  # noqa: BLE001
            logger.exception("channel refresh failed")
            return

        seen: set[str] = set()
        for ch in channels:
            cid = str(ch.id)
            seen.add(cid)
            existing = self._runtimes.get(cid)
            if existing is not None:
                existing.channel = ch
                # Config change → rebuild driver (A0 desired != running restart).
                if existing.driver is not None:
                    continue
            await self._ensure_runtime(ch)

        # Drop runtimes for channels that disappeared / deactivated.
        for cid in list(self._runtimes.keys()):
            if cid not in seen:
                rt = self._runtimes.pop(cid)
                await rt.close()
                logger.info("channel %s no longer active — runtime closed", cid)

    async def _ensure_runtime(self, channel: Any) -> _ChannelRuntime:
        rt = _ChannelRuntime(channel)
        config = dict(getattr(channel, "config", None) or {})
        kind = str(getattr(channel, "kind", "") or "").lower()
        try:
            driver = self._build_driver(channel, kind, config)
            await driver.start()
            rt.driver = driver
            rt.dispatcher = BridgeDispatcher(driver, channel)
            rt.poll_interval = int(
                config.get("poll_interval_seconds")
                or os.environ.get("SA01_BRIDGE_POLL_INTERVAL", DEFAULT_POLL_INTERVAL)
            )
            self._runtimes[str(channel.id)] = rt
            logger.info("bridge runtime up for %s channel %s", kind, channel.id)
        except Exception as exc:  # noqa: BLE001
            logger.error("failed to start %s driver for channel %s: %s", kind, channel.id, exc)
            await self._mark_channel_error(channel, str(exc))
            await rt.close()
        return rt

    @staticmethod
    def _build_driver(channel: Any, kind: str, config: Dict[str, Any]) -> Any:
        """Build the per-kind driver. Unknown kind raises (fail-closed)."""
        if kind == "telegram":
            return build_telegram_driver(
                str(channel.id),
                config,
                credentials_ref=str(getattr(channel, "credentials_ref", "") or ""),
            )
        if kind == "whatsapp":
            return build_whatsapp_driver(str(channel.id), config)
        raise ValueError(f"unsupported bridge channel kind '{kind}'")

    async def _mark_channel_error(self, channel: Any, detail: str) -> None:
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _mark() -> None:
            from admin.bridges.models import Channel

            Channel.objects.filter(id=channel.id).update(status=Channel.STATUS_ERROR)
            # Keep the reason in config for the UI without storing secrets.
            Channel.objects.filter(id=channel.id).update(
                config={**(getattr(channel, "config", None) or {}), "last_error": detail[:500]}
            )

        try:
            await _mark()
        except Exception:  # noqa: BLE001
            logger.exception("failed to mark channel %s error", channel.id)

    # -- per-channel poll (A0 _poll_loop) ----------------------------------

    async def _poll_channel(self, rt: _ChannelRuntime) -> None:
        if rt.driver is None or rt.dispatcher is None:
            return
        try:
            envelopes: List[InboundEnvelope] = await rt.driver.poll_inbound()
            rt.failures = 0
        except Exception as exc:  # noqa: BLE001
            rt.failures += 1
            logger.warning(
                "poll failed for channel %s (%d/%d): %s",
                rt.channel_id,
                rt.failures,
                MAX_CONSECUTIVE_FAILURES,
                exc,
            )
            if rt.failures >= MAX_CONSECUTIVE_FAILURES:
                logger.error(
                    "channel %s parked after %d consecutive poll failures",
                    rt.channel_id,
                    rt.failures,
                )
                await self._mark_channel_error(rt.channel, f"poll failures: {exc}")
                rt.channel = await self._reload_channel(rt.channel_id) or rt.channel
                # Drop runtime so next refresh can rebuild; A0 stops the loop.
                await rt.close()
                self._runtimes.pop(rt.channel_id, None)
            return

        for msg in envelopes:
            try:
                result = await rt.dispatcher.dispatch(msg)
                logger.info(
                    "dispatched inbound %s on %s → %s",
                    msg.external_id,
                    rt.channel_id,
                    result.get("status"),
                )
            except Exception as exc:  # noqa: BLE001 — one bad message must not kill the loop
                logger.exception(
                    "dispatch failed for inbound %s on %s: %s",
                    msg.external_id,
                    rt.channel_id,
                    exc,
                )

    async def _reload_channel(self, channel_id: str) -> Optional[Any]:
        from asgiref.sync import sync_to_async

        @sync_to_async
        def _get() -> Optional[Any]:
            from admin.bridges.models import Channel

            return Channel.objects.filter(id=channel_id).select_related("tenant", "capsule").first()

        try:
            return await _get()
        except Exception:  # noqa: BLE001
            return None


async def main() -> None:
    worker = BridgeWorker()
    try:
        await worker.start()
    except asyncio.CancelledError:
        await worker.stop()
        raise
    except KeyboardInterrupt:
        await worker.stop()


BridgeWorkerImpl = BridgeWorker

if __name__ == "__main__":
    logging.basicConfig(
        level=os.environ.get("SA01_BRIDGE_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped")
