"""Bridge worker package (WP D3/D4 — WhatsApp + Telegram Capsule bridges).

Long-running worker that polls messaging bridges (WhatsApp BR-01, Telegram
BR-02), dispatches inbound messages through the V3 chat orchestrator, and
sends replies with retry/DLQ semantics.

Clones Agent Zero ``plugins/_whatsapp_integration`` and
``plugins/_telegram_integration`` behaviour per SOMA-A0-PARITY-001 §4.5 and
Annex D.5.

``BridgeWorker`` lives in :mod:`services.bridge_worker.main`. This package root
deliberately does not re-export it: ``main`` pulls in Django at import time and
needs the app registry ready, so importing it from here would make a bare
``import services.bridge_worker`` fail outside a configured Django process.
Import the class from ``main`` directly.
"""

from __future__ import annotations

__all__: list[str] = []
