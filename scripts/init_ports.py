#!/usr/bin/env python3
"""Port scanner and assignment utility for SomaAgent cluster."""
import socket
import sys
from pathlib import Path
from typing import Dict, Optional

# Service name to default port mapping
DEFAULT_PORTS = {
    "kafka": 68001,
    "redis": 68002,
    "postgres": 68003,
    "opa": 68011,
    "gateway": 68016,
    "agent_ui": 68014
}

def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        # Try IPv4
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            s.listen(1)
            s.close()
            return True
    except Exception:
        try:
            # Try IPv6
            with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('::', port))
                s.listen(1)
                s.close()
                return True
        except Exception:
            return False

def find_next_available_port(start_port: int, end_port: int = 69000) -> Optional[int]:
    """Find the next available port in range."""
    current_port = start_port
    while current_port < end_port:
        if is_port_available(current_port):
            return current_port
        current_port += 1
    return None

def assign_ports() -> Dict[str, int]:
    """Assign ports for all services."""
    assignments = {}
    base_port = 68100  # Start from a higher range
    
    for service in DEFAULT_PORTS.keys():
        port = base_port
        while port < 69000:
            if is_port_available(port):
                assignments[service] = port
                print(f"Assigned port {port} to {service}")
                base_port = port + 1
                break
            port += 1
        else:
            print(f"Error: No available ports found for {service}", file=sys.stderr)
            sys.exit(1)
    
    return assignments

def write_env_file(assignments: Dict[str, int]) -> None:
    """Write port assignments to .env.ports file."""
    env_content = []
    for service, port in assignments.items():
        env_var = f"{service.upper()}_PORT={port}"
        env_content.append(env_var)
    
    with open(".env.ports", "w") as f:
        f.write("\n".join(env_content))

def main():
    """Main entry point."""
    print("Scanning for available ports...")
    assignments = assign_ports()
    
    print("\nWriting port assignments to .env.ports")
    write_env_file(assignments)
    
    print("\nPort assignments complete!")

if __name__ == "__main__":
    main()