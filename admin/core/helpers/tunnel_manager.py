"""Module tunnel_manager."""

import threading

try:
    from flaredantic import FlareConfig, FlareTunnel, ServeoConfig, ServeoTunnel

    _FLAREDANTIC_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    _FLAREDANTIC_AVAILABLE = False


class TunnelManager:
    """Singleton to manage the tunnel instance.

    Requires the optional `flaredantic` dependency; methods raise when absent.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """Retrieve instance."""

        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        """Initialize the instance."""

        self.tunnel = None
        self.tunnel_url = None
        self.is_running = False
        self.provider = None

    def start_tunnel(self, port=80, provider="serveo"):
        """Execute start tunnel.

        Args:
            port: The port.
            provider: The provider.
        """

        if not _FLAREDANTIC_AVAILABLE:
            raise RuntimeError(
                "Tunnel provider not installed (flaredantic). Install 'flaredantic' to enable tunneling."
            )

        # Start tunnel in a separate thread to avoid blocking
        self.provider = provider

        try:

            def run_tunnel():
                """Execute run tunnel."""

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
        """Execute stop tunnel."""

        if not _FLAREDANTIC_AVAILABLE:
            raise RuntimeError(
                "Tunnel provider not installed (flaredantic). Install 'flaredantic' to enable tunneling."
            )
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
        """Retrieve tunnel url."""

        if not _FLAREDANTIC_AVAILABLE:
            raise RuntimeError(
                "Tunnel provider not installed (flaredantic). Install 'flaredantic' to enable tunneling."
            )
        return self.tunnel_url if self.is_running else None
