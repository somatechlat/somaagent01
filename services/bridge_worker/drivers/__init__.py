"""Bridge drivers — external messaging network adapters."""

from __future__ import annotations

from services.bridge_worker.drivers.base import (
    BridgeDriver,
    DriverHealth,
    InboundEnvelope,
    OutboundPayload,
)
from services.bridge_worker.drivers.telegram import (
    build_telegram_driver,
    TelegramBotDriver,
    TelegramDriver,
)
from services.bridge_worker.drivers.whatsapp import (
    BaileysSidecarDriver,
    build_whatsapp_driver,
    CloudApiDriver,
    WhatsAppDriver,
)

__all__ = [
    "BridgeDriver",
    "DriverHealth",
    "InboundEnvelope",
    "OutboundPayload",
    "BaileysSidecarDriver",
    "CloudApiDriver",
    "WhatsAppDriver",
    "build_whatsapp_driver",
    "TelegramBotDriver",
    "TelegramDriver",
    "build_telegram_driver",
]
