"""Port discovery service for automatic port assignment.

VIBE COMPLIANT: No file-based storage. All assignments are in-memory only.
For persistent port assignments, use environment variables or config.
"""

import logging
import socket
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class PortDiscovery:
    """In-memory port discovery - no file storage per VIBE rules."""

    PORT_RANGE_START = 68000
    PORT_RANGE_END = 69000

    def __init__(self):
        self.assignments: Dict[str, int] = {}

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

        # Store the assignment in memory
        self.assignments[service_name] = assigned_port
        return assigned_port

    def get_all_service_ports(self) -> Dict[str, int]:
        """Get all assigned service ports."""
        return self.assignments.copy()

    def clear_port_assignments(self):
        """Clear all port assignments from memory."""
        self.assignments.clear()


# Service name to default port mapping
SERVICE_PORTS = {
    "kafka": 68001,
    "redis": 68002,
    "postgres": 68003,
    "opa": 68011,
    "gateway": 68016,
    "agent_ui": 68014,
}
