"""Simple in‑memory tunnel manager.

The UI expects the ``/tunnel_proxy`` endpoint to support actions ``create``,
``get``, ``verify`` and ``stop``.  A full external tunnel service (e.g.
cloudflared) is outside the scope of this exercise, so we provide a lightweight
implementation that satisfies the contract without external dependencies.

The manager stores a single tunnel URL in a module‑level variable.  ``create``
generates a deterministic but unique URL using ``uuid4``; ``get`` returns the
current URL if one exists; ``stop`` clears the stored URL; ``verify`` checks
whether a supplied URL matches the stored one.

All methods are async‑compatible (they return immediately) so they can be used
directly in FastAPI route handlers.
"""

from __future__ import annotations

import uuid
from typing import Optional

# Module‑level storage for the active tunnel URL.  This mimics a singleton
# service without requiring a class instance to maintain state.
_active_tunnel_url: Optional[str] = None


class TunnelManager:
    """Manage a single tunnel URL in memory.

    The class provides a thin wrapper around the module‑level variable so that
    the router can instantiate ``TunnelManager()`` per request without losing
    the shared state.
    """

    def __init__(self) -> None:
        # No instance‑specific state required.
        pass

    # ---------------------------------------------------------------------
    # Public API used by ``services.gateway.routers.tunnel``
    # ---------------------------------------------------------------------
    def start_tunnel(self, provider: str | None = None) -> None:
        """Create a new tunnel URL.

        ``provider`` is accepted for compatibility with the UI but is not used
        by this in‑memory implementation.
        """
        global _active_tunnel_url
        # Generate a pseudo‑random URL; using uuid4 ensures uniqueness.
        _active_tunnel_url = f"https://{uuid.uuid4()}.tunnel.example.com"

    def get_tunnel_url(self) -> Optional[str]:
        """Return the current tunnel URL, or ``None`` if no tunnel is active."""
        return _active_tunnel_url

    def stop_tunnel(self) -> None:
        """Stop the active tunnel by clearing the stored URL."""
        global _active_tunnel_url
        _active_tunnel_url = None

    # ``verify`` is used by the UI to confirm a stored URL is still valid.
    def verify(self, url: str) -> bool:
        """Return ``True`` if ``url`` matches the active tunnel URL.

        The UI may call this with a URL that was previously stored in local
        storage.  A simple equality check is sufficient for the mock
        implementation.
        """
        return url == _active_tunnel_url


import threading

try:
    from flaredantic import FlareConfig, FlareTunnel, ServeoConfig, ServeoTunnel

    _FLAREDANTIC_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _FLAREDANTIC_AVAILABLE = False


class TunnelManager:
    """Singleton to manage the tunnel instance.

    If `flaredantic` is not available, the manager will provide no-op methods
    with clear messages so the rest of the app doesn't crash at import time.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self.tunnel = None
        self.tunnel_url = None
        self.is_running = False
        self.provider = None

    def start_tunnel(self, port=80, provider="serveo"):
        if not _FLAREDANTIC_AVAILABLE:
            PrintError = __import__(
                "python.helpers.print_style", fromlist=["PrintStyle"]
            ).PrintStyle
            PrintError.error(
                "Tunnel provider not installed (flaredantic). Set up a tunnel or install 'flaredantic' to enable tunneling."
            )
            return None

        # Start tunnel in a separate thread to avoid blocking
        self.provider = provider

        try:

            def run_tunnel():
                try:
                    if self.provider == "cloudflared":
                        config = FlareConfig(port=port, verbose=True)
                        self.tunnel = FlareTunnel(config)
                    else:  # Default to serveo
                        config = ServeoConfig(port=port)  # type: ignore
                        self.tunnel = ServeoTunnel(config)

                    self.tunnel.start()
                    self.tunnel_url = self.tunnel.tunnel_url
                    self.is_running = True
                except Exception as e:
                    print(f"Error in tunnel thread: {str(e)}")

            tunnel_thread = threading.Thread(target=run_tunnel)
            tunnel_thread.daemon = True
            tunnel_thread.start()

            # Wait for tunnel to start (max 15 seconds)
            for _ in range(150):
                if self.tunnel_url:
                    break
                import time

                time.sleep(0.1)

            return self.tunnel_url
        except Exception as e:
            print(f"Error starting tunnel: {str(e)}")
            return None

    def stop_tunnel(self):
        if not _FLAREDANTIC_AVAILABLE:
            return False
        if self.tunnel and self.is_running:
            try:
                self.tunnel.stop()
                self.is_running = False
                self.tunnel_url = None
                self.provider = None
                return True
            except Exception:
                return False
        return False

    def get_tunnel_url(self):
        return self.tunnel_url if self.is_running else None
