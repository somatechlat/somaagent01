"""BridgeDriver protocol — external messaging network adapter contract.

Behaviour parity source: Agent Zero ``plugins/_whatsapp_integration/helpers/
wa_client.py`` (GET /messages, POST /send, GET /health, GET /qr) plus the
normalized event shape emitted by ``whatsapp-bridge/bridge.js``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@dataclass
class InboundEnvelope:
    """Normalized inbound message from an external messaging network.

    Field names mirror the A0 bridge.js event so WhatsApp stays a thin map and
    future drivers (Telegram/Email) normalize into the same shape.
    """

    external_id: str
    chat_id: str
    sender_id: str = ""
    sender_number: str = ""
    sender_name: str = ""
    chat_name: str = ""
    is_group: bool = False
    mentioned_me: bool = False
    replied_to_me: bool = False
    body: str = ""
    has_media: bool = False
    media_type: str = ""
    media_urls: List[str] = field(default_factory=list)
    timestamp: Any = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        """Persistable normalized payload for ``InboundMessage.payload``."""
        return {
            "external_id": self.external_id,
            "chat_id": self.chat_id,
            "sender_id": self.sender_id,
            "sender_number": self.sender_number,
            "sender_name": self.sender_name,
            "chat_name": self.chat_name,
            "is_group": self.is_group,
            "mentioned_me": self.mentioned_me,
            "replied_to_me": self.replied_to_me,
            "body": self.body,
            "has_media": self.has_media,
            "media_type": self.media_type,
            "media_urls": list(self.media_urls),
            "timestamp": self.timestamp,
        }


@dataclass
class OutboundPayload:
    """Outbound message ready for the network driver."""

    chat_id: str
    text: str = ""
    reply_to: str = ""
    media_path: str = ""
    media_type: str = ""
    caption: str = ""
    file_name: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "text": self.text,
            "reply_to": self.reply_to,
            "media_path": self.media_path,
            "media_type": self.media_type,
            "caption": self.caption,
            "file_name": self.file_name,
        }


@dataclass
class DriverHealth:
    """Driver / sidecar health snapshot."""

    status: str = "unknown"
    detail: str = ""
    queue_length: int = 0
    uptime: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "detail": self.detail,
            "queue_length": self.queue_length,
            "uptime": self.uptime,
            **self.extra,
        }


@runtime_checkable
class BridgeDriver(Protocol):
    """Adapter contract for a messaging network.

    Implementations must be safe to call from the bridge worker loop and must
    raise (not swallow) on send failure so the dispatcher can retry + DLQ.
    """

    async def start(self) -> None:
        """Acquire resources / ensure sidecar is reachable."""

    async def stop(self) -> None:
        """Release resources. Must be idempotent."""

    async def poll_inbound(self) -> List[InboundEnvelope]:
        """Drain the inbound queue. Empty list when nothing new.

        Poll is destructive (A0 ``GET /messages`` splices the queue) — the
        caller is responsible for persisting envelopes before processing.
        """

    async def send_outbound(self, payload: OutboundPayload) -> Dict[str, Any]:
        """Send one message. Raise ``BridgeSendError`` on failure."""

    async def health(self) -> DriverHealth:
        """Return current driver/sidecar health."""

    async def get_qr(self) -> Optional[Dict[str, Any]]:
        """Return pairing QR state, or None when not applicable."""


class BridgeSendError(Exception):
    """Outbound send failed. Carries the driver-level status for retry policy."""

    def __init__(self, message: str, *, status_code: int = 0, retryable: bool = True):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable
