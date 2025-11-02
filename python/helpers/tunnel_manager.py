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
            PrintError = __import__("python.helpers.print_style", fromlist=["PrintStyle"]).PrintStyle
            PrintError.error("Tunnel provider not installed (flaredantic). Set up a tunnel or install 'flaredantic' to enable tunneling.")
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
