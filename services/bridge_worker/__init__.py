"""Bridge worker package (WP D3/D4 — WhatsApp + Telegram Capsule bridges).

Long-running worker that polls messaging bridges (WhatsApp BR-01, Telegram
BR-02), dispatches inbound messages through the V3 chat orchestrator, and
sends replies with retry/DLQ semantics.

Clones Agent Zero ``plugins/_whatsapp_integration`` and
``plugins/_telegram_integration`` behaviour per SOMA-A0-PARITY-001 §4.5 and
Annex D.5.
"""

from __future__ import annotations

__all__ = ["BridgeWorker"]
