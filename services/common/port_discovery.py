"""Port discovery service for automatic port assignment."""

import logging
import socket
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PortDiscovery:
    PORT_RANGE_START = 68000
    PORT_RANGE_END = 69000

    def __init__(self):
        self.port_file = Path(".port_assignments.txt")
        self._load_assignments()

    def is_port_available(self, port: int) -> bool:
        """Check if a port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return True
        except Exception:
            return False

    def find_next_available_port(self, start_port: int) -> Optional[int]:
        """Find the next available port starting from start_port."""
        current_port = start_port
        while current_port < self.PORT_RANGE_END:
            if self.is_port_available(current_port):
                return current_port
            current_port += 1
        return None

    def _load_assignments(self):
        """Load port assignments (disabled: no file I/O)."""
        self.assignments = {}

    def _save_assignments(self):
        """Persisting assignments is disabled (no file saving)."""
        return

    def get_service_port(self, service_name: str, preferred_port: int) -> int:
        """Get port for a service, assign if not exists."""
        # Try to get existing port assignment
        if service_name in self.assignments:
            return self.assignments[service_name]

        # Try preferred port first
        if self.is_port_available(preferred_port):
            assigned_port = preferred_port
        else:
            # Find next available port
            assigned_port = self.find_next_available_port(self.PORT_RANGE_START)
            if not assigned_port:
                raise RuntimeError(f"No available ports found for {service_name}")

        # Store the assignment
        self.assignments[service_name] = assigned_port
        self._save_assignments()
        return assigned_port

    def get_all_service_ports(self) -> Dict[str, int]:
        """Get all assigned service ports."""
        return self.assignments.copy()

    def clear_port_assignments(self):
        """Clear all port assignments."""
        self.assignments.clear()
        if self.port_file.exists():
            self.port_file.unlink()


# Service name to default port mapping
SERVICE_PORTS = {
    "kafka": 68001,
    "redis": 68002,
    "postgres": 68003,
    "opa": 68011,
    "gateway": 68016,
    "agent_ui": 68014,
}
