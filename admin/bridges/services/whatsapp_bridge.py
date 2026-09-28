"""WhatsApp bridge lifecycle service (WP D3 — BR-01 / BR-05).

Manages the WhatsApp driver / Baileys sidecar for a Channel:

- ``start``            spawn/ensure Node Baileys sidecar (Option A) or validate
                       Cloud API credentials (Option B); set Channel.status
- ``stop``             stop sidecar / mark channel disabled
- ``test_connection``  probe driver health (A0 ``api/test_connection.py``)
- ``get_qr``           pairing QR for the UI (A0 ``api/qr_code.py``)
- ``handle_cloud_webhook``  Meta Cloud API webhook verify + inbound ingest

A0 behaviour cloned (plugins/_whatsapp_integration):
- ``helpers/bridge_manager.py``  sidecar process lifecycle
- ``api/{start,disconnect,qr_code,test_connection}.py``  control surface

Fail-closed: missing Channel.tenant or Channel.capsule is a hard error on
start; feature flag ``bridge_whatsapp`` must be on.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import signal
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Optional Baileys sidecar (A0 whatsapp-bridge/bridge.js).
# Set WA_BRIDGE_SIDECAR_CMD to an explicit launch command, or point
# WA_BRIDGE_SIDECAR_DIR at the directory containing bridge.js.
_SIDECAR_PROCS: Dict[str, subprocess.Popen] = {}


class WhatsAppBridgeError(Exception):
    """Lifecycle / configuration error for the WhatsApp bridge."""


@dataclass
class BridgeControlResult:
    ok: bool
    status: str
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "detail": self.detail,
            **self.data,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _feature_enabled() -> bool:
    try:
        from services.common.features import build_default_registry

        return bool(build_default_registry().is_enabled("bridge_whatsapp"))
    except Exception as exc:  # noqa: BLE001 — fail-closed
        logger.error("bridge_whatsapp flag check failed: %s", exc)
        return False


def _require_channel(channel_id: str) -> Any:
    from admin.bridges.models import Channel

    channel = Channel.objects.filter(id=channel_id).select_related("tenant", "capsule").first()
    if channel is None:
        raise WhatsAppBridgeError(f"channel '{channel_id}' not found")
    return channel


def _require_binding(channel: Any) -> None:
    """Fail-closed on missing tenant or capsule (T-5 / BR-09)."""
    if not getattr(channel, "tenant_id", None):
        raise WhatsAppBridgeError(
            f"channel {channel.id} has no tenant binding — refuse to start"
        )
    if not getattr(channel, "capsule_id", None):
        raise WhatsAppBridgeError(
            f"channel {channel.id} has no capsule binding — refuse to start"
        )


def _channel_config(channel: Any) -> Dict[str, Any]:
    return dict(getattr(channel, "config", None) or {})


def _bridge_url(config: Dict[str, Any]) -> str:
    """A0 bridge_manager.get_bridge_url(port) default 127.0.0.1:3100."""
    explicit = config.get("bridge_base_url") or os.environ.get("WA_BRIDGE_BASE_URL")
    if explicit:
        return str(explicit).rstrip("/")
    port = int(config.get("bridge_port") or os.environ.get("WA_BRIDGE_PORT", "3100"))
    return f"http://127.0.0.1:{port}"


def _mode(config: Dict[str, Any]) -> str:
    return str(config.get("mode") or os.environ.get("WA_BRIDGE_MODE", "baileys")).lower()


# ---------------------------------------------------------------------------
# Sidecar process management (Option A — A0 bridge_manager parity)
# ---------------------------------------------------------------------------


def _sidecar_command(config: Dict[str, Any]) -> Optional[List[str]]:
    """Resolve the Node sidecar launch command, or None when not installed."""
    explicit = config.get("sidecar_cmd") or os.environ.get("WA_BRIDGE_SIDECAR_CMD")
    if explicit:
        return str(explicit).split()
    # Default: node bridge.js inside WA_BRIDGE_SIDECAR_DIR (or the A0 layout).
    sidecar_dir = (
        config.get("sidecar_dir")
        or os.environ.get("WA_BRIDGE_SIDECAR_DIR")
        or ""
    )
    bridge_js = Path(sidecar_dir) / "bridge.js" if sidecar_dir else None
    if bridge_js is None or not bridge_js.is_file():
        return None
    node = shutil.which("node")
    if not node:
        return None
    return [node, str(bridge_js)]


def _sidecar_env(channel: Any, config: Dict[str, Any]) -> Dict[str, str]:
    env = dict(os.environ)
    session_dir = config.get("session_dir") or os.environ.get(
        "WA_BRIDGE_SESSION_DIR", str(Path.home() / ".soma" / "wa-session")
    )
    media_dir = config.get("media_dir") or os.environ.get(
        "WA_BRIDGE_MEDIA_DIR", str(Path.home() / ".soma" / "wa-media")
    )
    Path(session_dir).mkdir(parents=True, exist_ok=True)
    Path(media_dir).mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "PORT": str(config.get("bridge_port") or os.environ.get("WA_BRIDGE_PORT", "3100")),
            "SESSION_DIR": str(session_dir),
            "CACHE_DIR": str(media_dir),
            "MODE": str(config.get("mode_self_chat", "self-chat")),
            "ALLOWED_NUMBERS": str(config.get("allowed_numbers") or ""),
            "ALLOW_GROUP": "true" if config.get("allow_group") else "false",
        }
    )
    return env


def _is_proc_alive(pid_key: str) -> bool:
    proc = _SIDECAR_PROCS.get(pid_key)
    return proc is not None and proc.poll() is None


def _stop_sidecar(pid_key: str) -> bool:
    proc = _SIDECAR_PROCS.pop(pid_key, None)
    if proc is None:
        return False
    if proc.poll() is not None:
        return False
    try:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    except Exception:  # noqa: BLE001
        logger.exception("sidecar stop failed for %s", pid_key)
    return True


# ---------------------------------------------------------------------------
# Public lifecycle API
# ---------------------------------------------------------------------------


async def start(channel_id: str) -> BridgeControlResult:
    """Start the WhatsApp bridge for a channel (A0 api/start.py + bridge_manager).

    Option A: ensure the Node Baileys sidecar HTTP is up (spawn if a sidecar
    command is configured), then flip Channel.status → active.
    Option B (cloud): validate credentials and mark active; inbound arrives via
    the Meta webhook.
    """
    if not _feature_enabled():
        return BridgeControlResult(
            False, "disabled", "feature flag bridge_whatsapp is off (fail-closed)"
        )

    channel = _require_channel(channel_id)
    _require_binding(channel)
    config = _channel_config(channel)
    mode = _mode(config)

    if mode == "baileys":
        started = await _ensure_sidecar(channel, config)
        if not started.ok:
            _set_status(channel_id, "error", started.detail)
            return started
    elif mode == "cloud":
        check = await test_connection(channel_id)
        if not check.ok:
            _set_status(channel_id, "error", check.detail)
            return check
    else:
        return BridgeControlResult(False, "error", f"unknown mode '{mode}'")

    _set_status(channel_id, "active", "")
    return BridgeControlResult(True, "active", f"bridge started ({mode})", {"mode": mode})


async def _ensure_sidecar(channel: Any, config: Dict[str, Any]) -> BridgeControlResult:
    """Spawn sidecar if configured; otherwise require an already-running HTTP API."""
    cid = str(channel.id)
    url = _bridge_url(config)

    if _is_proc_alive(cid):
        health = await _probe_health(url)
        return BridgeControlResult(True, "running", "sidecar already up", {"url": url, **health})

    cmd = _sidecar_command(config)
    if cmd is not None:
        try:
            proc = subprocess.Popen(  # noqa: S603 — command from trusted config/env
                cmd,
                env=_sidecar_env(channel, config),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(Path(cmd[-1]).parent) if cmd[-1].endswith("bridge.js") else None,
            )
            _SIDECAR_PROCS[cid] = proc
            # Give the HTTP server a moment (A0 waits for health).
            for _ in range(20):
                await asyncio.sleep(0.5)
                if proc.poll() is not None:
                    break
                health = await _probe_health(url)
                if health.get("reachable"):
                    return BridgeControlResult(
                        True, "running", "sidecar spawned", {"url": url, **health}
                    )
            if proc.poll() is not None:
                return BridgeControlResult(
                    False, "error", f"sidecar exited early (code {proc.returncode})"
                )
        except FileNotFoundError:
            return BridgeControlResult(
                False, "error", "node/sidecar command not found (install Node.js)"
            )
        except Exception as exc:  # noqa: BLE001
            return BridgeControlResult(False, "error", f"sidecar spawn failed: {exc}")

    # No spawn command: require the sidecar to already answer (ops-managed).
    health = await _probe_health(url)
    if health.get("reachable"):
        return BridgeControlResult(
            True, "external", "using externally managed sidecar", {"url": url, **health}
        )
    return BridgeControlResult(
        False,
        "error",
        "baileys sidecar not reachable and WA_BRIDGE_SIDECAR_CMD/DIR not set "
        f"(tried {url})",
        {"url": url},
    )


async def stop(channel_id: str) -> BridgeControlResult:
    """Stop the sidecar (if we own it) and disable the channel (A0 disconnect)."""
    channel = _require_channel(channel_id)
    config = _channel_config(channel)
    stopped = _stop_sidecar(str(channel.id))
    _set_status(channel_id, "disabled", "stopped by operator")
    return BridgeControlResult(
        True,
        "disabled",
        "bridge stopped",
        {"sidecar_stopped": stopped, "mode": _mode(config)},
    )


async def test_connection(channel_id: str) -> BridgeControlResult:
    """Probe driver/sidecar health (A0 api/test_connection.py)."""
    channel = _require_channel(channel_id)
    config = _channel_config(channel)
    mode = _mode(config)

    if mode == "baileys":
        url = _bridge_url(config)
        health = await _probe_health(url)
        if health.get("reachable"):
            return BridgeControlResult(
                True,
                str(health.get("status") or "ok"),
                "sidecar reachable",
                {"mode": mode, "url": url, **health},
            )
        return BridgeControlResult(
            False, "unreachable", f"sidecar not reachable at {url}", {"mode": mode, "url": url}
        )

    if mode == "cloud":
        token = config.get("api_token") or os.environ.get("WA_CLOUD_API_TOKEN", "")
        phone_number_id = config.get("phone_number_id") or os.environ.get(
            "WA_CLOUD_PHONE_NUMBER_ID", ""
        )
        missing = [
            name
            for name, val in (
                ("WA_CLOUD_API_TOKEN", token),
                ("WA_CLOUD_PHONE_NUMBER_ID", phone_number_id),
            )
            if not val
        ]
        if missing:
            return BridgeControlResult(
                False,
                "misconfigured",
                f"missing cloud credentials: {', '.join(missing)}",
                {"mode": mode},
            )
        return BridgeControlResult(
            True, "ok", "cloud credentials present (token not validated live)", {"mode": mode}
        )

    return BridgeControlResult(False, "error", f"unknown mode '{mode}'")


async def get_qr(channel_id: str) -> BridgeControlResult:
    """Pairing QR (A0 api/qr_code.py). Baileys-only; Cloud API has no QR."""
    channel = _require_channel(channel_id)
    config = _channel_config(channel)
    mode = _mode(config)

    if mode == "cloud":
        return BridgeControlResult(
            True,
            "connected",
            "Cloud API uses a permanent access token — QR pairing is Baileys-only",
            {"qr": None, "mode": mode},
        )

    url = _bridge_url(config)
    try:
        import httpx

        async with httpx.AsyncClient(base_url=url, timeout=5.0) as client:
            resp = await client.get("/qr")
            if resp.status_code != 200:
                return BridgeControlResult(
                    False, "error", f"QR endpoint HTTP {resp.status_code}", {"mode": mode}
                )
            data = resp.json() if isinstance(resp.json(), dict) else {}
    except Exception as exc:  # noqa: BLE001
        return BridgeControlResult(
            False,
            "unreachable",
            f"cannot fetch QR (is the sidecar running?): {exc}",
            {"mode": mode, "url": url},
        )

    return BridgeControlResult(
        True,
        str(data.get("status") or "unknown"),
        "QR state fetched",
        {"qr": data.get("qr"), "mode": mode, "url": url},
    )


# ---------------------------------------------------------------------------
# Cloud API webhook (Option B inbound)
# ---------------------------------------------------------------------------


def verify_subscription(
    *,
    mode: str,
    token: str,
    challenge: str,
    verify_token: Optional[str] = None,
) -> Optional[str]:
    """Meta webhook verification handshake.

    Returns the hub.challenge on success, None on failure (fail-closed).
    """
    expected = verify_token or os.environ.get("WA_CLOUD_WEBHOOK_VERIFY_TOKEN", "")
    from services.bridge_worker.drivers.whatsapp import verify_webhook_challenge

    return verify_webhook_challenge(mode, token, challenge, expected)


def handle_cloud_webhook(
    channel_id: str,
    body: Dict[str, Any],
    *,
    raw_body: bytes = b"",
    signature_header: str = "",
) -> BridgeControlResult:
    """Ingest a Meta Cloud API webhook payload.

    Persists normalized ``InboundMessage`` rows (processed_at=null) so the
    bridge worker ``CloudApiDriver.poll_inbound`` can pick them up.
    Optionally validates X-Hub-Signature-256 when WA_CLOUD_APP_SECRET is set.
    """
    app_secret = os.environ.get("WA_CLOUD_APP_SECRET", "")
    if app_secret:
        from services.bridge_worker.drivers.whatsapp import verify_cloud_signature

        if not verify_cloud_signature(app_secret, raw_body, signature_header):
            return BridgeControlResult(False, "forbidden", "invalid webhook signature")

    if not _feature_enabled():
        return BridgeControlResult(False, "disabled", "bridge_whatsapp flag is off")

    channel = _require_channel(channel_id)
    _require_binding(channel)

    entries = (
        (body.get("entry") or [])
        if isinstance(body, dict)
        else []
    )
    stored: List[str] = []
    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            messages = value.get("messages") or []
            contacts = value.get("contacts") or []
            contact = contacts[0] if contacts else {}
            for m in messages:
                if not isinstance(m, dict):
                    continue
                msg_id = str(m.get("id") or "")
                if not msg_id:
                    continue
                from_m = str(m.get("from") or "")
                msg_type = str(m.get("type") or "text")
                text = ""
                if msg_type == "text":
                    text = str((m.get("text") or {}).get("body") or "")
                elif msg_type in {"image", "video", "document", "audio"}:
                    text = f"[{msg_type} received]"

                is_group = from_m.endswith("@g.us") or from_m.endswith("-")
                row_id = _store_inbound(
                    channel=channel,
                    external_id=msg_id,
                    chat_id=from_m,
                    sender_id=from_m,
                    sender_number=from_m,
                    sender_name=str(contact.get("profile") or {}).get("name", "")
                    if isinstance(contact, dict)
                    else "",
                    is_group=is_group,
                    body=text,
                    has_media=msg_type != "text",
                    media_type="" if msg_type == "text" else msg_type,
                    raw=m,
                )
                if row_id:
                    stored.append(row_id)

    return BridgeControlResult(
        True, "accepted", f"stored {len(stored)} inbound message(s)", {"inbound_ids": stored}
    )


def _store_inbound(
    *,
    channel: Any,
    external_id: str,
    chat_id: str,
    sender_id: str,
    sender_number: str,
    sender_name: str,
    is_group: bool,
    body: str,
    has_media: bool,
    media_type: str,
    raw: Dict[str, Any],
) -> Optional[str]:
    from admin.bridges.models import InboundMessage

    if InboundMessage.objects.filter(
        channel_id=channel.id, external_id=external_id
    ).exists():
        return None

    row = InboundMessage.objects.create(
        channel_id=channel.id,
        external_id=external_id,
        direction="inbound",
        payload={
            "chat_id": chat_id,
            "sender_id": sender_id,
            "sender_number": sender_number,
            "sender_name": sender_name,
            "chat_name": "",
            "is_group": is_group,
            "mentioned_me": False,
            "replied_to_me": False,
            "body": body,
            "has_media": has_media,
            "media_type": media_type,
            "media_urls": [],
            "timestamp": raw.get("timestamp"),
        },
        attachments=[],
    )
    return str(row.id)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


async def _probe_health(base_url: str) -> Dict[str, Any]:
    try:
        import httpx

        async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
            resp = await client.get("/health")
            if resp.status_code != 200:
                return {"reachable": False, "status": f"HTTP {resp.status_code}"}
            data = resp.json() if isinstance(resp.json(), dict) else {}
            return {
                "reachable": True,
                "status": data.get("status", "ok"),
                "queue_length": data.get("queueLength", 0),
                "uptime": data.get("uptime", 0),
            }
    except Exception as exc:  # noqa: BLE001
        return {"reachable": False, "status": "unreachable", "error": str(exc)}


def _set_status(channel_id: str, status: str, detail: str) -> None:
    from admin.bridges.models import Channel

    updates: Dict[str, Any] = {"status": status}
    Channel.objects.filter(id=channel_id).update(**updates)
    if detail:
        ch = Channel.objects.filter(id=channel_id).first()
        if ch is not None:
            cfg = dict(ch.config or {})
            cfg["last_status_detail"] = detail[:500]
            ch.config = cfg
            ch.save(update_fields=["config", "updated_at"])
